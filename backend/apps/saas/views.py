"""SaaS / platform-operations API views.

All platform-admin endpoints reuse ``IsPlatformAdmin`` from the schools app
(superuser OR the ``super_admin`` role), keeping one definition of "platform
layer".
"""

import datetime

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.schools.platform_views import IsPlatformAdmin

from .models import DailyUsageSnapshot, FeatureFlag, Plan, Subscription
from .serializers import (
    DailyUsageSnapshotSerializer,
    FeatureFlagSerializer,
    PlanSerializer,
    SubscriptionSerializer,
)
from .services import coerce_bool, flush_usage, get_subscription, set_feature_flag


def active_institution(request):
    return getattr(request, "institution", None)


# =============================================================================
# FEATURE FLAGS
# =============================================================================


class CurrentFlagsView(APIView):
    """Effective flags for the caller's active institution.

    GET /api/saas/flags/current/
    Each entry reports the resolved ``enabled`` value (override wins over the
    global default).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        institution = active_institution(request)
        flags = FeatureFlag.objects.select_related("institution").all()

        global_on = {
            f.name: f for f in flags if f.institution_id is None and f.enabled
        }
        overrides = {
            f.name: f for f in flags
            if institution is not None and f.institution_id == institution.pk
        }

        names = sorted(set(list(global_on.keys()) + list(overrides.keys())))
        rows = []
        for name in names:
            override = overrides.get(name)
            enabled = bool(override.enabled) if override else True
            label = (override or global_on.get(name)).label or name
            rows.append(
                {
                    "name": name,
                    "label": label,
                    "enabled": enabled,
                    "overridden": override is not None,
                }
            )
        return Response({"flags": rows})


class FeatureFlagAdminView(APIView):
    """Platform admin management of feature flags.

    GET  /api/saas/flags/        -> list global + all overrides
    POST /api/saas/flags/        -> create/update a flag (scope determined by
                                    ``institution_id`` presence)
    DELETE /api/saas/flags/<pk>/ -> remove a flag
    """

    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        flags = FeatureFlag.objects.select_related("institution").order_by(
            "name", "institution_id"
        )
        name = request.query_params.get("name")
        if name:
            flags = flags.filter(name=name)
        return Response(FeatureFlagSerializer(flags, many=True).data)

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        if not name:
            return Response(
                {"detail": "name is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        institution_id = request.data.get("institution_id")
        institution = None
        if institution_id:
            from apps.schools.models import School

            institution = School.objects.filter(pk=institution_id).first()
            if institution is None:
                return Response(
                    {"detail": "Unknown institution_id."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        flag = set_feature_flag(
            name,
            enabled=coerce_bool(request.data.get("enabled", False)),
            institution=institution,
            label=(request.data.get("label") or "").strip(),
            description=(request.data.get("description") or "").strip(),
        )
        return Response(
            FeatureFlagSerializer(flag).data, status=status.HTTP_201_CREATED
        )


class FeatureFlagDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def delete(self, request, pk):
        flag = FeatureFlag.objects.filter(pk=pk).first()
        if flag is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        name, institution_id = flag.name, flag.institution_id
        flag.delete()
        from django.core.cache import cache

        scope = "global" if institution_id is None else str(institution_id)
        cache.delete(f"saas:flag:{scope}:{name}")
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================================================
# SUBSCRIPTIONS
# =============================================================================


class SubscriptionSummaryView(APIView):
    """Current institution's subscription (plan + status + limits)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        institution = active_institution(request)
        if institution is None:
            return Response({"detail": "No active institution."},
                            status=status.HTTP_404_NOT_FOUND)
        subscription, _ = get_subscription(institution)
        return Response(SubscriptionSerializer(subscription).data)


class TenantSubscriptionView(APIView):
    """Platform-admin read/set of a tenant's subscription.

    GET  /api/saas/tenants/<pk>/subscription/
    POST /api/saas/tenants/<pk>/subscription/  {"plan_code": "startup",
                                               "status": "active"}
    """

    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get_object(self, school_id):
        from apps.schools.models import School

        return School.objects.filter(pk=school_id).first()

    def get(self, request, school_id):
        school = self.get_object(school_id)
        if school is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        subscription, _ = get_subscription(school)
        return Response(SubscriptionSerializer(subscription).data)

    def post(self, request, school_id):
        school = self.get_object(school_id)
        if school is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        subscription, _ = get_subscription(school)
        plan_code = request.data.get("plan_code")
        if plan_code:
            plan = Plan.objects.filter(code=plan_code, is_active=True).first()
            if plan is None:
                return Response(
                    {"detail": f"Unknown/inactive plan: {plan_code}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription.plan = plan

        new_status = request.data.get("status")
        if new_status:
            valid = {v for v, _ in Subscription.STATUS_CHOICES}
            if new_status not in valid:
                return Response(
                    {"detail": f"Invalid status: {new_status}. Choices: {sorted(valid)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription.status = new_status

        if "seats_used" in request.data:
            try:
                seats = int(request.data["seats_used"] or 0)
            except (TypeError, ValueError):
                return Response(
                    {"detail": "seats_used must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if seats < 0:
                return Response(
                    {"detail": "seats_used must be non-negative."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription.seats_used = seats

        subscription.save(update_fields=["plan", "status", "seats_used", "updated_at"])

        from apps.audit.models import record_audit

        record_audit(
            request=request,
            action="subscription_changed",
            model_name="Subscription",
            object_id=str(subscription.pk),
            details={
                "school_id": school.pk,
                "plan_code": subscription.plan.code,
                "status": subscription.status,
            },
        )
        return Response(SubscriptionSerializer(subscription).data)


class PlansListView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        plans = Plan.objects.filter(is_active=True).order_by("sort_order", "code")
        return Response(PlanSerializer(plans, many=True).data)


# =============================================================================
# USAGE ANALYTICS
# =============================================================================


class UsageAnalyticsView(APIView):
    """Platform-wide usage analytics over the last ``days`` (default 30).

    Flushes buffered counters first so the numbers are up to date when
    queried interactively.
    """

    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        try:
            days = min(int(request.query_params.get("days", 30)), 365)
        except (TypeError, ValueError):
            days = 30

        flush_usage()

        since = timezone.localdate() - datetime.timedelta(days=days - 1)
        rows = list(
            DailyUsageSnapshot.objects.filter(date__gte=since)
            .select_related("school")
            .order_by("-date", "school__name")
        )

        totals = {
            "logins": sum(r.logins for r in rows),
            "failed_logins": sum(r.failed_logins for r in rows),
            "api_requests": sum(r.api_requests for r in rows),
        }
        per_school = {}
        for row in rows:
            entry = per_school.setdefault(
                row.school_id,
                {
                    "school_id": row.school_id,
                    "school_name": row.school.name,
                    "logins": 0,
                    "failed_logins": 0,
                    "api_requests": 0,
                    "days_active": 0,
                    "latest": None,
                },
            )
            entry["logins"] += row.logins
            entry["failed_logins"] += row.failed_logins
            entry["api_requests"] += row.api_requests
            entry["days_active"] += 1
            entry["latest"] = row.date

        top_by_requests = sorted(
            per_school.values(), key=lambda e: e["api_requests"], reverse=True
        )[:20]

        return Response(
            {
                "days": days,
                "total_requests": totals["api_requests"],
                "total_logins": totals["logins"],
                "total_failed_logins": totals["failed_logins"],
                "active_schools": len(per_school),
                "top_schools": top_by_requests,
                "rows": DailyUsageSnapshotSerializer(rows, many=True).data,
            }
        )


# =============================================================================
# PLATFORM OVERVIEW / STATUS / SECURITY
# =============================================================================


class PlatformOverviewView(APIView):
    """Platform-wide live aggregate dashboard for the Super Admin."""

    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        from apps.accounts.models import FailedLoginAttempt, RoleAssignment
        from apps.schools.models import Campus, School
        from apps.students.models import Student
        from django.contrib.auth import get_user_model

        User = get_user_model()
        now = timezone.now()
        day_ago = now - datetime.timedelta(days=1)
        week_ago = now - datetime.timedelta(days=7)

        schools = School.objects.all()
        school_count = schools.count()
        active_schools = schools.filter(status="active", is_paused=False).count()

        sub_totals = dict(
            Subscription.objects.values("status").annotate(
                n=Count("id")
            ).values_list("status", "n")
        )

        admins = (
            RoleAssignment.objects.filter(role="admin")
            .values("membership__institution_id")
            .distinct()
            .count()
        )

        return Response(
            {
                "schools": {
                    "total": school_count,
                    "active": active_schools,
                    "paused": schools.filter(is_paused=True).count(),
                    "archived": schools.filter(status="archived").count(),
                },
                "campuses": Campus.objects.count(),
                "users": User.objects.count(),
                "students": Student.objects.count(),
                "subscriptions": {
                    s: sub_totals.get(s, 0)
                    for s in ("trial", "active", "past_due", "canceled", "expired")
                },
                "schools_with_admin": admins,
                "auth": {
                    "logins_24h": sum(
                        s.logins for s in _last_n_days_snapshots(1)
                    ),
                    "logins_7d": sum(
                        s.logins for s in _last_n_days_snapshots(7)
                    ),
                    "failed_logins_24h": FailedLoginAttempt.objects.filter(
                        attempted_at__gte=day_ago
                    ).count(),
                    "failed_logins_7d": FailedLoginAttempt.objects.filter(
                        attempted_at__gte=week_ago
                    ).count(),
                    "locked_users": User.objects.filter(
                        locked_until__gt=now
                    ).count(),
                },
                "recent_schools": list(
                    schools.order_by("-created_at")
                    .values("id", "name", "code", "status", "created_at")[:10]
                ),
            }
        )


def _last_n_days_snapshots(days):
    from .models import DailyUsageSnapshot

    since = timezone.localdate() - datetime.timedelta(days=days - 1)
    return list(
        DailyUsageSnapshot.objects.filter(date__gte=since).only(
            "logins", "failed_logins", "api_requests"
        )
    )


class SecurityOverviewView(APIView):
    """Security-monitoring roll-up for the platform admin."""

    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        from apps.accounts.models import FailedLoginAttempt, User
        from apps.audit.models import AuditLog

        now = timezone.now()
        day_ago = now - datetime.timedelta(days=1)
        week_ago = now - datetime.timedelta(days=7)

        top_ips = list(
            FailedLoginAttempt.objects.filter(attempted_at__gte=day_ago)
            .values("ip_address")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        return Response(
            {
                "failed_logins_24h": FailedLoginAttempt.objects.filter(
                    attempted_at__gte=day_ago
                ).count(),
                "failed_logins_7d": FailedLoginAttempt.objects.filter(
                    attempted_at__gte=week_ago
                ).count(),
                "top_ip_sources": top_ips,
                "locked_users": list(
                    User.objects.filter(locked_until__gt=now)
                    .values("id", "username", "email", "locked_until")
                ),
                "brute_force_alerts_7d": AuditLog.objects.filter(
                    action="brute_force_detected",
                    timestamp__gte=week_ago,
                ).count(),
                "suspicious_actions_7d": AuditLog.objects.filter(
                    action__in=(
                        "login_failed",
                        "password_reset",
                        "permission_change",
                        "role_change",
                    ),
                    timestamp__gte=week_ago,
                ).count(),
            }
        )


class PlatformStatusView(APIView):
    """Backend health + stats for the platform admin.

    Lighter than the overview: DB connectivity, cache connectivity, and a few
    headline counts. Used by the admin's status page / runbook.
    """

    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        from django.db import connection

        db_ok = True
        db_error = None
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as exc:  # noqa: BLE001
            db_ok = False
            db_error = str(exc)

        from django.core.cache import cache

        cache_ok = True
        cache_error = None
        try:
            cache.set("saas:liveness", "ok", 10)
            cache_ok = cache.get("saas:liveness") == "ok"
        except Exception as exc:  # noqa: BLE001
            cache_ok = False
            cache_error = str(exc)

        return Response(
            {
                "status": "ok" if (db_ok and cache_ok) else "degraded",
                "database": {"ok": db_ok, "error": db_error},
                "cache": {"ok": cache_ok, "error": cache_error},
                "utc_now": timezone.now().isoformat(),
            }
        )