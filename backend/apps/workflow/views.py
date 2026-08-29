from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope, assert_campus_allowed, get_institution
from apps.workflow import services
from apps.workflow.models import WorkflowApproval, WorkflowDefinition, WorkflowInstance, WorkflowTransition
from apps.workflow.serializers import (
    WorkflowActionSerializer,
    WorkflowApprovalDecideSerializer,
    WorkflowApprovalSerializer,
    WorkflowDefinitionSerializer,
    WorkflowDefinitionWriteSerializer,
    WorkflowDefinitionTestSerializer,
    WorkflowInstanceDetailSerializer,
    WorkflowInstanceSerializer,
    WorkflowTransitionSerializer,
)


def _active_institution(request):
    """Active institution from the middleware or the user's primary one."""
    institution = get_institution(request)
    if institution is not None:
        return institution
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return getattr(user, "primary_institution", None)
    return None


def _scoped_instances(request):
    """Instances visible to the caller: campus + institution scoping."""
    queryset = apply_campus_scope(
        WorkflowInstance.objects.select_related(
            "definition", "institution", "campus", "created_by"
        ),
        request,
        campus_field="campus_id",
        institution_field=None,
    )
    institution = _active_institution(request)
    if institution is not None:
        queryset = queryset.filter(
            Q(institution_id=institution.id) | Q(institution_id__isnull=True)
        )
    return queryset


class WorkflowDefinitionListView(generics.ListAPIView):
    """List active workflow definitions, optionally filtered by ``object_type``."""

    permission_classes = [IsAuthenticated]
    serializer_class = WorkflowDefinitionSerializer

    def get_queryset(self):
        queryset = WorkflowDefinition.objects.filter(is_active=True)
        object_types = self.request.query_params.getlist("object_type")
        if object_types:
            queryset = queryset.filter(object_type__in=object_types)
        return queryset.order_by("object_type", "slug")


class WorkflowInstanceListCreateView(generics.ListCreateAPIView):
    """List instances for the active institution (campus-scoped) or start a new one."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WorkflowInstanceSerializer
        return WorkflowInstanceDetailSerializer

    def get_queryset(self):
        queryset = _scoped_instances(self.request)

        object_type = self.request.query_params.get("object_type")
        object_id = self.request.query_params.get("object_id")
        if object_type:
            queryset = queryset.filter(object_type=object_type)
        if object_id:
            queryset = queryset.filter(object_id=object_id)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        campus = serializer.validated_data.get("campus")
        if campus is not None:
            assert_campus_allowed(request.user, campus.id)

        instance = serializer.save()
        return Response(
            WorkflowInstanceDetailSerializer(instance, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )


class WorkflowInstanceDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WorkflowInstanceDetailSerializer

    def get_queryset(self):
        return _scoped_instances(self.request)


class WorkflowInstanceActionView(APIView):
    """POST an action (``submit``, ``approve``, ``reject``, ...) on an instance."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        payload = WorkflowActionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        instance = get_object_or_404(_scoped_instances(request), pk=pk)

        try:
            instance = services.perform(
                instance,
                request.user,
                payload.validated_data["action"],
                payload.validated_data.get("comment") or "",
            )
        except services.WorkflowPermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        except services.WorkflowError as exc:
            raise ValidationError(str(exc)) from exc

        return Response(
            WorkflowInstanceDetailSerializer(instance, context={"request": request}).data
        )


class WorkflowTransitionListView(generics.ListAPIView):
    """History of actions for one instance (how-when-by-whom with old/new state)."""

    permission_classes = [IsAuthenticated]
    serializer_class = WorkflowTransitionSerializer

    def get_queryset(self):
        instance = get_object_or_404(_scoped_instances(self.request), pk=self.kwargs["pk"])
        return WorkflowTransition.objects.filter(instance_id=instance.id)


class WorkflowApprovalListView(APIView):
    """Everything currently waiting for the authenticated user to decide."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        institution = _active_institution(request)
        approvals = services.pending_approvals_for_user(request.user, institution=institution)
        return Response(WorkflowApprovalSerializer(approvals, many=True).data)


class WorkflowApprovalDecideView(APIView):
    """Decide the current pending approval (``approve`` or ``reject``)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        payload = WorkflowApprovalDecideSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        approval = get_object_or_404(
            WorkflowApproval.objects.select_related("instance").filter(
                instance__in=_scoped_instances(request)
            ),
            pk=pk,
        )

        instance = approval.instance
        pending = services._current_pending_approval(instance)
        if pending is None or pending.pk != approval.pk:
            raise ValidationError("This approval is not the next pending step.")

        try:
            instance = services.perform(
                instance,
                request.user,
                payload.validated_data["decision"],
                payload.validated_data.get("comment") or "",
            )
        except services.WorkflowPermissionError as exc:
            raise PermissionDenied(str(exc)) from exc

        return Response(
            WorkflowInstanceDetailSerializer(instance, context={"request": request}).data
        )


class WorkflowDefinitionCreateUpdateDeleteView(generics.CreateUpdateAPIView):
    """Create, update, or delete workflow definitions (admin only)."""

    permission_classes = [IsAuthenticated]
    serializer_class = WorkflowDefinitionWriteSerializer
    queryset = WorkflowDefinition.objects.all()

    def check_admin_permission(self, request):
        """Ensure user is admin."""
        user = request.user
        if not user.is_staff and not user.is_superuser:
            raise PermissionDenied("Only administrators can manage workflow definitions.")

    def create(self, request, *args, **kwargs):
        self.check_admin_permission(request)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self.check_admin_permission(request)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self.check_admin_permission(request)
        definition = self.get_object()
        definition.is_active = False
        definition.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkflowDefinitionTestView(APIView):
    """Test workflow transitions without creating an instance."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        definition = get_object_or_404(WorkflowDefinition, pk=pk)
        
        serializer = WorkflowDefinitionTestSerializer(
            data=request.data,
            context={"definition": definition}
        )
        serializer.is_valid(raise_exception=True)

        from_state = serializer.validated_data["from_state"]
        action = serializer.validated_data["action"]

        # Simulate the transition
        transitions = definition.transitions.get(action, {})
        allowed_from_states = transitions.get("from", [])

        if from_state not in allowed_from_states:
            raise ValidationError(
                {"from_state": f"Action '{action}' not allowed from state '{from_state}'."}
            )

        to_state = transitions.get("to", None)
        if to_state is None:
            raise ValidationError({"action": f"Transition for action '{action}' not configured."})

        # If this action has approval steps, create a dummy queue
        approval_steps = []
        if action == "submit":
            approval_steps = [
                {"sequence": i, "role": role}
                for i, role in enumerate(definition.approval_steps or [])
            ]

        return Response({
            "from_state": from_state,
            "action": action,
            "to_state": to_state,
            "approval_steps": approval_steps,
            "is_terminal": definition.is_terminal(to_state),
        })


class WorkflowInstanceStatsView(APIView):
    """Get workflow statistics for the active institution."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        institution = _active_institution(request)
        
        queryset = _scoped_instances(request)
        if institution:
            queryset = queryset.filter(
                Q(institution_id=institution.id) | Q(institution_id__isnull=True)
            )

        total_instances = queryset.count()
        pending_approvals = queryset.filter(
            current_state="pending_approval"
        ).count()
        
        # Count by definition
        by_definition = {}
        for definition in WorkflowDefinition.objects.filter(is_active=True):
            count = queryset.filter(definition_id=definition.id).count()
            by_definition[definition.slug] = count

        return Response({
            "total_instances": total_instances,
            "pending_approvals": pending_approvals,
            "by_definition": by_definition,
        })