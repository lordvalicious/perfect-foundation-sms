"""Service helpers for feature flags, subscriptions and usage counters.

These functions are the single entry point for evaluating flags and reading
subscriptions so views/tests stay thin and behaviour is consistent.
"""

import logging

from django.core.cache import cache
from django.utils import timezone

from .models import DailyUsageSnapshot, FeatureFlag, Plan, Subscription

logger = logging.getLogger(__name__)

# Cache TTL for feature-flag lookups (kept short: a flag change must become
# effective within minutes).
FLAG_CACHE_TTL = 300

# How long a buffered usage counter may live in the cache before it is
# considered stale and dropped (it is flushed by ``collect_usage`` before then).
USAGE_BUFFER_TTL = 60 * 60 * 26

#: Cache key prefixes used by the usage buffer.
_USAGE_COUNTER_PREFIX = "saas:usage:counter:"
_USAGE_REGISTRY_KEY = "saas:usage:registry"


# =============================================================================
# FEATURE FLAGS
# =============================================================================


def coerce_bool(value):
    """Coerce a client-supplied value into a strict boolean.

    ``bool("false")`` is ``True``, which would silently enable a flag, so
    string payloads are parsed explicitly.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def _flag_cache_key(name, institution_id):
    return f"saas:flag:{institution_id or 'global'}:{name}"


def feature_enabled(name, institution=None):
    """Return whether ``name`` is enabled for ``institution``.

    Resolution order:
      1. per-institution override (if any),
      2. global flag,
      3. ``False`` (flags opt in by default).
    """
    institution_id = getattr(institution, "pk", None)

    cache_key = _flag_cache_key(name, institution_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return bool(cached)

    enabled = None
    if institution_id is not None:
        override = FeatureFlag.objects.filter(
            name=name,
            institution_id=institution_id,
        ).only("enabled").first()
        if override is not None:
            enabled = override.enabled

    if enabled is None:
        global_flag = FeatureFlag.objects.filter(
            name=name,
            institution=None,
        ).only("enabled").first()
        if global_flag is not None:
            enabled = global_flag.enabled

    if enabled is None:
        enabled = False

    cache.set(cache_key, enabled, FLAG_CACHE_TTL)
    return enabled


def set_feature_flag(name, enabled, institution=None, label="", description=""):
    """Create/update a flag and invalidate its cached evaluation.

    ``institution=None`` manages the *global* flag; passing an institution
    manages that tenant's override.
    """
    instance, _ = FeatureFlag.objects.update_or_create(
        name=name,
        institution=institution,
        defaults={
            "enabled": coerce_bool(enabled),
            "label": label,
            "description": description,
        },
    )
    cache.delete(_flag_cache_key(name, getattr(institution, "pk", None)))
    return instance


# =============================================================================
# SUBSCRIPTIONS
# =============================================================================

DEFAULT_PLAN_CODE = "free"


def get_default_plan():
    """Return the free plan (creating it as a fallback row if missing)."""
    plan, _ = Plan.objects.get_or_create(
        code=DEFAULT_PLAN_CODE,
        defaults={
            "name": "Free",
            "description": "Free tier for a single campus.",
            "sort_order": 0,
            "is_active": True,
        },
    )
    return plan


def get_subscription(school):
    """Return ``(subscription, created)`` for ``school``.

    Tenant created without a plan gets the default free plan on first access,
    so every school always has a subscription row to attach analytics to.
    """
    sub, created = Subscription.objects.get_or_create(
        school=school,
        defaults={"plan": get_default_plan(), "status": "trial"},
    )
    return sub, created


# =============================================================================
# USAGE COUNTERS (cache-buffered, flushed by ``collect_usage``)
# =============================================================================

USAGE_METRICS = ("api_requests", "logins", "failed_logins")


def _usage_counter_key(metric, school_id, day):
    return f"{_USAGE_COUNTER_PREFIX}{metric}:{day.isoformat()}:{school_id}"


def _register_counter(school_id, day):
    """Remember a (school, day) bucket so ``collect_usage`` can find it."""
    entries = cache.get(_USAGE_REGISTRY_KEY) or []
    key = f"{day.isoformat()}:{school_id}"
    try:
        if key in entries:
            return
        entries.append(key)
        # Cap the registry size so one noisy key can never balloon memory.
        cache.set(_USAGE_REGISTRY_KEY, entries[-20000:], USAGE_BUFFER_TTL)
    except Exception:  # pragma: no cover - best-effort bookkeeping
        logger.warning("Usage registry update failed for %s", key, exc_info=True)


def record_usage(school_id, metric):
    """Increment a buffered usage counter for ``school_id`` (best effort).

    No DB write happens here; the counters are flushed by
    ``collect_usage`` into ``DailyUsageSnapshot``.
    """
    if school_id is None:
        return
    if metric not in USAGE_METRICS:
        return

    today = timezone.localdate()
    counter_key = _usage_counter_key(metric, school_id, today)
    try:
        value = cache.get(counter_key, 0)
        cache.set(counter_key, value + 1, USAGE_BUFFER_TTL)
        _register_counter(school_id, today)
    except Exception:  # pragma: no cover - never break the request path
        logger.warning(
            "Usage counter increment failed for school %s metric %s",
            school_id, metric, exc_info=True,
        )


def flush_usage(day=None):
    """Persist all buffered usage counters into ``DailyUsageSnapshot`` rows.

    Live dimensions (students/staff/payments) are recomputed from the DB so a
    stale cache never produces nonsense counts.
    """
    from apps.accounts.models import StaffProfile
    from apps.finance.models import Payment
    from apps.students.models import Student

    if day is None:
        day = timezone.localdate()

    entries = cache.get(_USAGE_REGISTRY_KEY) or []
    by_school = {}
    for entry in entries:
        entry_day, _, school_id = entry.partition(":")
        try:
            school_id_int = int(school_id)
        except (TypeError, ValueError):
            continue
        if entry_day != day.isoformat():
            continue
        by_school[school_id_int] = True

    total = 0
    for school_id in list(by_school.keys()):
        row = {}
        for metric in USAGE_METRICS:
            row[metric] = cache.get(_usage_counter_key(metric, school_id, day), 0)

        total += max(row.values())

        students = Student.objects.filter(
            enrollments__campus__school_id=school_id,
            enrollments__status="active",
        ).distinct().count()
        staff = StaffProfile.objects.filter(
            institution_id=school_id, status="active"
        ).count()
        payments = Payment.objects.filter(
            institution_id=school_id,
            created_at__date=day,
        ).count()

        DailyUsageSnapshot.objects.update_or_create(
            school_id=school_id,
            date=day,
            defaults={
                "logins": row["logins"],
                "failed_logins": row["failed_logins"],
                "api_requests": row["api_requests"],
                "students": students,
                "staff": staff,
                "payments": payments,
            },
        )

    # Drop the flushed buckets from the cache registry.
    clean = [
        e for e in entries
        if not e.startswith(f"{day.isoformat()}:")
    ]
    cache.set(_USAGE_REGISTRY_KEY, clean, USAGE_BUFFER_TTL)
    return total