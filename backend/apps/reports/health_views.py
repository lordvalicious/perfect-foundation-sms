"""System health monitoring views."""

import time
import platform
from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole


class SystemHealthView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        health = {}

        # Database check
        start = time.time()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_time = round((time.time() - start) * 1000, 2)
            health["database"] = {
                "status": "healthy",
                "response_ms": db_time,
                "engine": settings.DATABASES.get("default", {}).get("ENGINE", "unknown"),
            }
        except Exception as e:
            health["database"] = {
                "status": "error",
                "error": str(e),
            }

        # API health
        start = time.time()
        health["api"] = {
            "status": "healthy",
            "response_ms": round((time.time() - start) * 1000, 2),
        }

        # User stats
        from django.contrib.auth import get_user_model
        User = get_user_model()

        now = timezone.now()
        active_users_today = User.objects.filter(
            last_login__date=now.date()
        ).count()
        total_users = User.objects.count()
        staff_count = User.objects.filter(is_staff=True).count()

        health["users"] = {
            "total": total_users,
            "active_today": active_users_today,
            "staff": staff_count,
            "is_active_count": User.objects.filter(is_active=True).count(),
        }

        # System info
        health["system"] = {
            "python_version": platform.python_version(),
            "django_version": getattr(settings, "DJANGO_VERSION", "unknown"),
            "platform": platform.platform(),
            "hostname": platform.node(),
            "debug_mode": settings.DEBUG,
        }

        # Record counts
        from apps.students.models import Student, Enrollment
        from apps.teachers.models import Teacher
        from apps.finance.models import Invoice, Payment

        health["records"] = {
            "students": Student.objects.count(),
            "active_enrollments": Enrollment.objects.filter(status="active").count(),
            "teachers": Teacher.objects.count(),
            "invoices": Invoice.objects.count(),
            "payments": Payment.objects.count(),
        }

        # Recent audit activity
        from apps.audit.models import AuditLog
        recent_logs = AuditLog.objects.order_by("-timestamp")[:5]
        health["recent_activity"] = [
            {
                "action": log.action,
                "user": str(log.user) if log.user else "System",
                "timestamp": log.timestamp.isoformat() if log.timestamp else "",
            }
            for log in recent_logs
        ]

        # Overall status
        db_ok = health["database"].get("status") == "healthy"
        health["overall_status"] = "healthy" if db_ok else "degraded"

        return Response(health)
