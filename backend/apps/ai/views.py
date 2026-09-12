from rest_framework import permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    IsAccountantRole,
    IsAnnouncementRole,
    IsTeacherRole,
)
from apps.accounts.scopes import (
    is_manager,
    is_parent,
    is_student,
    is_teacher,
)

from . import services


_VISIBLE_MESSAGE = "This AI feature is not available to your account."


def _audit(request, action, object_repr="", details=None):
    from apps.audit.models import record_audit

    record_audit(
        request=request,
        action=action,
        model_name="ai",
        object_repr=(object_repr or "")[:255],
        details=details or {},
    )


class InsightPermission(permissions.BasePermission):
    """Gate AI access: authenticated, active institution, no explicit deny."""

    message = _VISIBLE_MESSAGE

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return False
        if services.ai_institution(request) is None:
            return False
        codename = getattr(view, "deny_codename", None)
        if codename and services.effective_deny(request, codename):
            return False
        return True


class AiOverviewView(APIView):
    permission_classes = [IsAuthenticated, InsightPermission]
    deny_codename = "insight.view"

    def get(self, request):
        user = request.user

        role_label = "manager"
        if is_teacher(user) and not is_manager(user):
            role_label = "teacher"
        elif is_parent(user):
            role_label = "parent"
        elif is_student(user):
            role_label = "student"

        capabilities = []
        if is_manager(user) or is_teacher(user):
            capabilities += [
                "student_insights",
                "attendance_insights",
                "academic_insights",
                "anomalies",
            ]
        if services._finance_allowed(user):
            capabilities += ["finance_insights"]
        if services._finance_allowed(user) or is_manager(user):
            capabilities += ["communication_drafts"]
        capabilities += ["ask", "search"]

        payload = {
            "role": role_label,
            "institution": services.ai_institution(request).id,
            "institution_name": services.ai_institution(request).name,
            "capabilities": capabilities,
            "students_in_scope": services.scoped_students_qs(request).count(),
        }

        attendance = services.attendance_insights(request)
        payload["attendance"] = {
            "days": attendance["days"],
            "overall_rate": attendance["overall_rate"],
        }

        if services._finance_allowed(user):
            finance = services.finance_insights(request)
            payload["finance"] = {
                "total_outstanding": finance["total_outstanding"],
                "overdue_count": finance["overdue_count"],
            }

        _audit(request, "ai_insight", object_repr="overview")

        return Response(payload)


class AiAskView(APIView):
    permission_classes = [IsAuthenticated, InsightPermission]
    deny_codename = "insight.ask"

    def post(self, request):
        query = (request.data or {}).get("query") or ""
        answer = services.answer_ask(request, query)
        _audit(
            request,
            "ai_ask",
            object_repr=(query or "")[:100],
            details={"intent": answer.get("intent")},
        )
        return Response({"ok": True, **answer})


class AiSearchView(APIView):
    permission_classes = [IsAuthenticated, InsightPermission]
    deny_codename = "insight.search"

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        result = services.resolve_entities(request, query)
        _audit(
            request,
            "ai_search",
            object_repr=(query or "")[:100],
            details={"entities": len(result["entities"])},
        )
        return Response(result)


class AiStudentInsightsView(APIView):
    permission_classes = [IsAuthenticated, IsTeacherRole, InsightPermission]
    deny_codename = "insight.student.view"

    def get(self, request):
        raw = request.query_params.get("student_id", "").strip()
        student_id = int(raw) if raw.isdigit() else None
        rows = services.student_insights(request, student_id=student_id)
        _audit(
            request,
            "ai_insight",
            object_repr="student",
            details={"count": len(rows)},
        )
        return Response({"insights": rows})


class AiAttendanceInsightsView(APIView):
    permission_classes = [IsAuthenticated, IsTeacherRole, InsightPermission]
    deny_codename = "insight.attendance.view"

    def get(self, request):
        data = services.attendance_insights(request)
        _audit(request, "ai_insight", object_repr="attendance")
        return Response(data)


class AiAcademicInsightsView(APIView):
    permission_classes = [IsAuthenticated, IsTeacherRole, InsightPermission]
    deny_codename = "insight.academic.view"

    def get(self, request):
        raw = request.query_params.get("exam_id", "").strip()
        exam_id = int(raw) if raw.isdigit() else None
        data = services.academic_insights(request, exam_id=exam_id)
        _audit(request, "ai_insight", object_repr="academic")
        return Response(data)


class AiFinanceInsightsView(APIView):
    permission_classes = [IsAuthenticated, IsAccountantRole, InsightPermission]
    deny_codename = "insight.finance.view"

    def get(self, request):
        data = services.finance_insights(request)
        _audit(request, "ai_insight", object_repr="finance")
        return Response(data)


class AiAnomaliesView(APIView):
    permission_classes = [IsAuthenticated, IsTeacherRole, InsightPermission]
    deny_codename = "insight.anomaly"

    def get(self, request):
        items = services.anomalies(request)
        _audit(
            request,
            "ai_anomaly",
            object_repr="scan",
            details={"items": len(items)},
        )
        return Response({"anomalies": items})


class AiCommunicationDraftView(APIView):
    permission_classes = [IsAuthenticated, IsAnnouncementRole, InsightPermission]
    deny_codename = "insight.communicate"

    def post(self, request):
        payload = request.data or {}
        try:
            draft = services.draft_communication(request, payload)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        _audit(
            request,
            "ai_draft",
            object_repr=draft.get("type", ""),
            details={"recipients": draft.get("recipient_count")},
        )
        return Response(draft)