"""API views for message templates."""

from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import get_institution
from apps.accounts.permissions import IsAdminRole

from .models import MessageTemplate


def _visible_templates(request):
    """Templates of the active institution.

    Blocks every school from seeing another school's templates. Legacy
    rows (created before the institution FK was stamped) resolve through
    their creator's membership so the seeded templates keep working.
    """
    qs = MessageTemplate.objects.select_related("created_by")

    institution = getattr(request, "institution", None)
    if institution is None:
        institution = get_institution(request)

    if institution is None:
        return qs.none()

    return qs.filter(
        Q(institution_id=institution.pk)
        | Q(
            institution__isnull=True,
            created_by__memberships__status="active",
            created_by__memberships__institution_id=institution.pk,
        )
    )


class MessageTemplateListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        channel = request.query_params.get("channel", "")
        templates = _visible_templates(request)
        if channel:
            templates = templates.filter(channel=channel)

        data = []
        for t in templates:
            data.append({
                "id": t.id,
                "name": t.name,
                "channel": t.channel,
                "channel_display": t.get_channel_display(),
                "subject": t.subject,
                "body": t.body,
                "variables": t.variables,
                "is_active": t.is_active,
                "created_at": t.created_at.isoformat(),
            })
        return Response(data)

    def post(self, request):
        name = request.data.get("name", "").strip()
        body = request.data.get("body", "").strip()

        if not name or not body:
            return Response(
                {"detail": "name and body are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        institution = get_institution(request)

        template = MessageTemplate.objects.create(
            name=name,
            channel=request.data.get("channel", "sms"),
            subject=request.data.get("subject", ""),
            body=body,
            variables=request.data.get("variables", []),
            created_by=request.user,
            institution=institution,
        )

        return Response({
            "id": template.id,
            "name": template.name,
            "detail": "Template created.",
        }, status=status.HTTP_201_CREATED)


class MessageTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_object(self, request, pk):
        return (
            _visible_templates(request)
            .filter(pk=pk)
            .first()
        )

    def get(self, request, pk):
        template = self.get_object(request, pk)
        if not template:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "id": template.id,
            "name": template.name,
            "channel": template.channel,
            "channel_display": template.get_channel_display(),
            "subject": template.subject,
            "body": template.body,
            "variables": template.variables,
            "is_active": template.is_active,
            "created_at": template.created_at.isoformat(),
        })

    def put(self, request, pk):
        template = self.get_object(request, pk)
        if not template:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        template.name = request.data.get("name", template.name)
        template.channel = request.data.get("channel", template.channel)
        template.subject = request.data.get("subject", template.subject)
        template.body = request.data.get("body", template.body)
        template.variables = request.data.get("variables", template.variables)
        template.is_active = request.data.get("is_active", template.is_active)
        template.save()

        return Response({"detail": "Template updated."})

    def delete(self, request, pk):
        template = self.get_object(request, pk)
        if not template:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        template.delete()
        return Response({"detail": "Template deleted."})


class MessageTemplatePreviewView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request, pk):
        template = (
            _visible_templates(request)
            .filter(pk=pk)
            .first()
        )

        if not template:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        context = request.data.get("context", {})
        rendered = template.render(context)

        return Response({
            "subject": template.subject,
            "body": rendered,
            "channel": template.channel,
        })
