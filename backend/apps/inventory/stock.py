"""Stock engine: applies movements to per-campus stock levels atomically.

Every change to on-hand quantity goes through :func:`apply_movement`, which
writes an append-only :class:`StockMovement` row and updates the matching
:class:`StockLevel`. In-bound types add, out-bound types subtract (rejected
when insufficient), ``adjust`` sets an absolute stocktake figure and
``transfer_out`` automatically moves stock to the destination campus.
"""

from decimal import Decimal

from django.db import models, transaction

from apps.inventory.models import StockLevel, StockMovement

INBOUND_TYPES = {"receive", "return", "transfer_in"}
OUTBOUND_TYPES = {"issue", "transfer_out", "write_off"}
TRANSFER_TYPES = {"transfer_in", "transfer_out"}


class StockError(ValueError):
    """Domain error for invalid stock operations (mapped to HTTP 400)."""


def apply_movement(
    *,
    asset,
    campus,
    movement_type,
    quantity,
    institution=None,
    unit_cost=None,
    destination_campus=None,
    reference="",
    notes="",
    created_by=None,
):
    """Apply a stock movement and return the created ``StockMovement`` row."""
    quantity = int(quantity)

    if quantity < 0 or (quantity == 0 and movement_type != "adjust"):
        raise StockError("Quantity must be greater than zero.")
    if movement_type not in dict(StockMovement.MOVEMENT_TYPES):
        raise StockError("Unknown movement type.")
    if movement_type in TRANSFER_TYPES and destination_campus is None:
        raise StockError("A destination campus is required for transfers.")
    if campus == destination_campus:
        raise StockError("Source and destination campus must differ.")

    with transaction.atomic():
        if movement_type == "transfer_out":
            # Symmetric inbound on the destination campus (same transaction).
            apply_movement(
                asset=asset,
                campus=destination_campus,
                movement_type="transfer_in",
                quantity=quantity,
                institution=institution,
                destination_campus=campus,
                reference=reference,
                notes=notes,
                created_by=created_by,
            )

        level = StockLevel.objects.filter(campus=campus, asset=asset).first()
        if level is None:
            level = StockLevel.objects.create(
                institution=institution or asset.institution,
                campus=campus,
                asset=asset,
                quantity=0,
            )

        if movement_type == "adjust":
            level.quantity = quantity
        elif movement_type in INBOUND_TYPES:
            level.quantity += quantity
        else:
            if level.quantity < quantity:
                raise StockError(
                    f"Insufficient stock: only {level.quantity} available."
                )
            level.quantity -= quantity

        level.save(update_fields=["quantity", "updated_at"])

        if movement_type == "receive" and unit_cost is not None:
            _update_average_cost(asset, quantity, unit_cost)

        _sync_asset_quantity(asset)

        return StockMovement.objects.create(
            institution=institution or asset.institution,
            campus=campus,
            asset=asset,
            movement_type=movement_type,
            quantity=quantity,
            unit_cost=unit_cost or Decimal("0"),
            destination_campus=destination_campus,
            reference=reference or "",
            notes=notes or "",
            created_by=created_by if getattr(created_by, "is_authenticated", False) else None,
        )


def _update_average_cost(asset, quantity, unit_cost):
    """Blend in the incoming quantity at its cost into the running average."""
    old_qty = Decimal(str(asset.quantity or 0))
    old_cost = asset.unit_cost or Decimal("0")
    incoming_qty = Decimal(str(quantity))
    incoming_cost = Decimal(str(unit_cost))

    if old_qty + incoming_qty:
        average = (old_qty * old_cost + incoming_qty * incoming_cost) / (old_qty + incoming_qty)
    else:
        average = incoming_cost

    asset.unit_cost = average.quantize(Decimal("0.01"))


def _sync_asset_quantity(asset):
    """Keep ``Asset.quantity`` equal to the sum of all campus stock levels."""
    total = (
        StockLevel.objects.filter(asset=asset)
        .aggregate(total=models.Sum("quantity"))["total"]
        or 0
    )
    asset.quantity = total
    asset.save(update_fields=["quantity", "unit_cost", "updated_at"])