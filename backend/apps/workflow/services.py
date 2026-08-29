"""Reusable workflow engine logic shared by the REST API, admin and CLI."""

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.workflow.models import WorkflowApproval, WorkflowDefinition, WorkflowInstance, WorkflowTransition

ACTION_SUBMIT = "submit"
ACTION_APPROVE = "approve"
ACTION_REJECT = "reject"


class WorkflowError(ValueError):
    """Domain error (invalid state, unknown action) — mapped to HTTP 400."""


class WorkflowPermissionError(PermissionDenied):
    """Authenticated but not allowed to perform the action — HTTP 403."""


def get_definition(object_type):
    """Active definition for ``object_type`` or ``None``."""
    return (
        WorkflowDefinition.objects.filter(object_type=object_type, is_active=True)
        .order_by("slug")
        .first()
    )


def _matches_roles(user, roles, institution):
    if not roles:
        return True
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    return user.has_any_role(roles, institution=institution)


def _actor_or_none(user):
    if user is not None and getattr(user, "is_authenticated", False):
        return user
    return None


def _record_transition(instance, action, from_state, to_state, actor, comment=""):
    return WorkflowTransition.objects.create(
        instance=instance,
        action=action,
        from_state=from_state or "",
        to_state=to_state,
        actor=_actor_or_none(actor),
        comment=comment or "",
    )


def _create_approvals(instance):
    """Create the pending approval queue from the definition."""
    for index, role in enumerate(instance.definition.approval_steps or []):
        WorkflowApproval.objects.create(
            instance=instance,
            sequence=index,
            role=role,
        )


def _current_pending_approval(instance):
    return (
        instance.approvals.filter(status=WorkflowApproval.Status.PENDING)
        .order_by("sequence")
        .first()
    )


def start(object_type, object_id, *, institution=None, campus=None, actor=None, comment=""):
    """Open a new workflow instance for ``object_type`` object ``object_id``.

    The instance starts in ``initial_state``. If a terminal instance already
    exists for the object the caller may open a new one — no data is deleted.
    """
    definition = get_definition(object_type)
    if definition is None:
        raise WorkflowError("No active workflow definition for this object type.")

    instance = WorkflowInstance.objects.create(
        definition=definition,
        institution=institution,
        campus=campus,
        object_type=object_type,
        object_id=object_id,
        current_state=definition.initial_state,
        created_by=_actor_or_none(actor),
    )
    _record_transition(instance, "start", "", definition.initial_state, actor, comment or "Workflow started.")
    return instance


def _state_error(instance, action):
    """Error message when the action cannot run on ``instance``, else ``None``.

    Covers unknown actions, transitions that are not allowed from the current
    state, and approval actions with an empty queue. These are domain errors
    (HTTP 400), unrelated to who is asking.
    """
    transition = (instance.definition.transitions or {}).get(action)
    if not transition:
        return "Unknown action."

    if instance.current_state not in (transition.get("from") or []):
        return f"'{action}' is not allowed from state '{instance.current_state}'."

    if action in (ACTION_APPROVE, ACTION_REJECT) and instance.definition.approval_steps:
        if _current_pending_approval(instance) is None:
            return "There is nothing waiting for approval."

    return None


def can_perform(instance, user, action):
    """Return ``(allowed, reason)``. Role gating only; caller validates the state."""
    transition = (instance.definition.transitions or {}).get(action)
    if not transition:
        return False, "Unknown action."
    if instance.current_state not in (transition.get("from") or []):
        return False, f"'{action}' is not allowed from state '{instance.current_state}'."

    roles = list(transition.get("roles") or [])

    if action in (ACTION_APPROVE, ACTION_REJECT) and instance.definition.approval_steps:
        approval = _current_pending_approval(instance)
        if approval is None:
            return False, "There is nothing waiting for approval."
        roles = list(dict.fromkeys([approval.role] + roles))

    institution = instance.institution_id
    if not _matches_roles(user, roles, institution):
        return False, "You do not have permission to perform this action."

    return True, ""


@transaction.atomic
def perform(instance, user, action, comment=""):
    """Execute ``action`` on ``instance`` and persist the audit transition."""
    error = _state_error(instance, action)
    if error:
        raise WorkflowError(error)

    allowed, reason = can_perform(instance, user, action)
    if not allowed:
        raise WorkflowPermissionError(reason)

    transition = instance.definition.transitions[action]
    from_state = instance.current_state
    approval = _current_pending_approval(instance)

    if action in (ACTION_APPROVE, ACTION_REJECT) and instance.definition.approval_steps:
        approval.status = (
            WorkflowApproval.Status.APPROVED
            if action == ACTION_APPROVE
            else WorkflowApproval.Status.REJECTED
        )
        approval.approver = _actor_or_none(user)
        approval.comment = comment or ""
        approval.decided_at = timezone.now()
        approval.save(update_fields=["status", "approver", "comment", "decided_at"])

        if action == ACTION_APPROVE:
            if _current_pending_approval(instance) is None:
                instance.current_state = transition["to"]
        else:
            instance.approvals.filter(status=WorkflowApproval.Status.PENDING).update(
                status=WorkflowApproval.Status.SKIPPED
            )
            instance.current_state = transition["to"]
    else:
        instance.current_state = transition["to"]

    if action == ACTION_SUBMIT and instance.current_state == "pending_approval":
        _create_approvals(instance)
        if instance.submitted_at is None:
            instance.submitted_at = timezone.now()

    if instance.definition.is_terminal(instance.current_state) and instance.completed_at is None:
        instance.completed_at = timezone.now()

    instance.save(update_fields=["current_state", "submitted_at", "completed_at", "updated_at"])
    _record_transition(instance, action, from_state, instance.current_state, user, comment)
    return instance


def submit(instance, user, comment=""):
    return perform(instance, user, ACTION_SUBMIT, comment)


def approve(instance, user, comment=""):
    return perform(instance, user, ACTION_APPROVE, comment)


def reject(instance, user, comment=""):
    return perform(instance, user, ACTION_REJECT, comment)


def pending_approvals_for_user(user, institution=None):
    """Ordered list of pending approvals the user is allowed to decide.

    Returns approvals whose queue is live and whose assigned role matches
    one of the user's roles inside ``institution`` (primary institution when
    ``institution`` is ``None``).
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return []

    target = institution
    if target is None:
        target = getattr(user, "primary_institution", None)

    approvals = (
        WorkflowApproval.objects
        .filter(status=WorkflowApproval.Status.PENDING)
        .filter(instance__current_state="pending_approval")
        .select_related("instance", "instance__definition")
        .order_by("instance_id", "sequence")
    )
    if target is not None:
        approvals = approvals.filter(instance__institution_id=target.id)

    return [
        approval
        for approval in approvals
        if user.has_any_role([approval.role], institution=target)
    ]