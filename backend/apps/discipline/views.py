from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope, restrict_to_allowed_campuses
from apps.accounts.permissions import IsStaffRole

from .models import DisciplinaryAction, Incident
from .serializers import (
    DisciplinaryActionSerializer,
    IncidentSerializer,
)


class IncidentListCreateView(generics.ListCreateAPIView):
    serializer_class = IncidentSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        queryset = Incident.objects.select_related(
            "student",
            "campus",
            "reported_by",
        )

        queryset = apply_campus_scope(queryset, self.request)

        severity = self.request.query_params.get("severity")

        if severity:
            queryset = queryset.filter(severity=severity)

        incident_status = self.request.query_params.get("status")

        if incident_status:
            queryset = queryset.filter(status=incident_status)

        student = self.request.query_params.get("student")

        if student:
            queryset = queryset.filter(student_id=student)

        search = (
            self.request.query_params.get("search", "")
            .strip()
        )

        if search:
            from django.db.models import Q

            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(student__first_name__icontains=search)
                | Q(student__last_name__icontains=search)
                | Q(student__admission_number__icontains=search)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)


class IncidentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = IncidentSerializer
    permission_classes = [IsStaffRole]

    def get_queryset(self):
        queryset = Incident.objects.select_related(
            "student",
            "campus",
            "reported_by",
        )

        return apply_campus_scope(queryset, self.request)


class IncidentActionListCreateView(generics.ListCreateAPIView):
    serializer_class = DisciplinaryActionSerializer
    permission_classes = [IsStaffRole]

    def get_incident(self):
        base = Incident.objects.all()

        return get_object_or_404(
            apply_campus_scope(base, self.request),
            pk=self.kwargs["incident_id"],
        )

    def get_queryset(self):
        return (
            DisciplinaryAction.objects
            .filter(incident=self.get_incident())
            .select_related("incident", "recorded_by")
        )

    def perform_create(self, serializer):
        serializer.save(
            incident=self.get_incident(),
            recorded_by=self.request.user,
        )


class DisciplineSummaryView(APIView):
    """Counts by severity and status for the discipline dashboard."""

    permission_classes = [IsStaffRole]

    def get(self, request):
        from django.db.models import Count

        queryset = restrict_to_allowed_campuses(
            Incident.objects.all(),
            request.user,
        )
        queryset = apply_campus_scope(queryset, request)

        by_severity = dict(
            queryset.values_list("severity")
            .annotate(total=Count("id"))
            .values_list("severity", "total")
        )

        by_status = dict(
            queryset.values_list("status")
            .annotate(total=Count("id"))
            .values_list("status", "total")
        )

        offenders = {}

        for incident in queryset:
            key = incident.student_id

            entry = offenders.setdefault(
                key,
                {
                    "student": incident.student.full_name,
                    "admission_number": incident.student.admission_number,
                    "incidents": 0,
                    "points": 0,
                },
            )

            entry["incidents"] += 1
            entry["points"] += incident.points or 0

        return Response(
            {
                "total": queryset.count(),
                "by_severity": [
                    {"severity": name.title(), "count": count}
                    for name, count in sorted(by_severity.items())
                ],
                "by_status": [
                    {"status": name.replace("_", " ").title(), "count": count}
                    for name, count in sorted(by_status.items())
                ],
                "top_students": sorted(
                    offenders.values(),
                    key=lambda item: item["points"],
                    reverse=True,
                )[:10],
            }
        )
