"""Inventory Reports."""

from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum, Avg, Max, Min
from django.utils import timezone
from rest_framework.response import Response

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.base_views import AggregateReportView, BaseReportView
from apps.reports.utils import quantize, to_csv


class InventoryMasterReportView(AggregateReportView):
    """Inventory master report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "inventory_master"
    model = "apps.inventory.models.Asset"

    def get_base_queryset(self, request):
        from apps.inventory.models import Asset
        return Asset.objects.select_related("category", "campus", "supplier")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        category = request.query_params.get("category")
        if category:
            queryset = queryset.filter(category_id=category)

        status = request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_summary(self, queryset, request):
        total_items = queryset.count()
        total_quantity = sum(a.quantity for a in queryset)
        total_value = sum(Decimal(str(a.unit_cost)) * a.quantity for a in queryset)

        by_category = queryset.values("category__name").annotate(
            items=Count("id"),
            quantity=Sum("quantity"),
        )
        by_campus = queryset.values("campus__name").annotate(
            items=Count("id"),
            quantity=Sum("quantity"),
        )
        by_status = queryset.values("status").annotate(count=Count("id"))

        return {
            "total_items": total_items,
            "total_quantity": total_quantity,
            "total_value": quantize(total_value),
            "by_category": list(by_category),
            "by_campus": list(by_campus),
            "by_status": list(by_status),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for asset in queryset:
            rows.append({
                "name": asset.name,
                "code": asset.code or "-",
                "category": asset.category.name if asset.category else "-",
                "campus": asset.campus.name if asset.campus else "-",
                "quantity": asset.quantity,
                "unit_cost": quantize(asset.unit_cost),
                "total_value": quantize(Decimal(str(asset.unit_cost)) * asset.quantity),
                "status": asset.get_status_display(),
                "supplier": asset.supplier.name if asset.supplier else "-",
                "purchase_date": asset.purchase_date,
                "warranty_expiry": asset.warranty_expiry,
            })
        return rows


class StockReportView(AggregateReportView):
    """Current stock report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "inventory_stock"
    model = "apps.inventory.models.Asset"

    def get_base_queryset(self, request):
        from apps.inventory.models import Asset
        return Asset.objects.filter(status="available").select_related("category", "campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")
        return queryset

    def get_summary(self, queryset, request):
        total_items = queryset.count()
        total_quantity = sum(a.quantity for a in queryset)

        return {
            "total_items": total_items,
            "total_quantity": total_quantity,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for asset in queryset:
            rows.append({
                "name": asset.name,
                "code": asset.code or "-",
                "category": asset.category.name if asset.category else "-",
                "campus": asset.campus.name if asset.campus else "-",
                "quantity": asset.quantity,
                "unit": asset.unit or "-",
            })
        return rows


class LowStockReportView(AggregateReportView):
    """Low stock report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "inventory_low_stock"
    model = "apps.inventory.models.Asset"

    def get_base_queryset(self, request):
        from apps.inventory.models import Asset
        return Asset.objects.filter(status="available").select_related("category", "campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        threshold = request.query_params.get("threshold", "10")
        queryset = queryset.filter(quantity__lte=threshold)
        return queryset

    def get_summary(self, queryset, request):
        return {
            "low_stock_items": queryset.count(),
            "threshold": request.query_params.get("threshold", "10"),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for asset in queryset:
            rows.append({
                "name": asset.name,
                "code": asset.code or "-",
                "category": asset.category.name if asset.category else "-",
                "campus": asset.campus.name if asset.campus else "-",
                "quantity": asset.quantity,
                "unit": asset.unit or "-",
                "reorder_level": asset.reorder_level or "-",
            })
        return rows


class OutOfStockReportView(LowStockReportView):
    """Out of stock report."""
    report_definition_key = "inventory_out_of_stock"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.filter(quantity=0)
        return queryset


class StockMovementReportView(AggregateReportView):
    """Stock movement report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "inventory_movement"
    model = "apps.inventory.models.StockMovement"

    def get_base_queryset(self, request):
        from apps.inventory.models import StockMovement
        return StockMovement.objects.select_related(
            "asset__category", "asset__campus", "created_by"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "asset__campus_id")

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        movement_type = request.query_params.get("movement_type")
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_type = queryset.values("movement_type").annotate(count=Count("id"))

        return {
            "total_movements": total,
            "by_type": list(by_type),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for movement in queryset:
            rows.append({
                "date": movement.date,
                "asset": movement.asset.name,
                "code": movement.asset.code or "-",
                "category": movement.asset.category.name if movement.asset.category else "-",
                "campus": movement.asset.campus.name if movement.asset.campus else "-",
                "type": movement.get_movement_type_display(),
                "quantity": movement.quantity,
                "reference": movement.reference or "-",
                "notes": movement.notes or "-",
                "created_by": movement.created_by.get_full_name() if movement.created_by else "-",
            })
        return rows


class PurchaseReportView(AggregateReportView):
    """Purchases report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "inventory_purchases"
    model = "apps.inventory.models.PurchaseOrder"

    def get_base_queryset(self, request):
        from apps.inventory.models import PurchaseOrder
        return PurchaseOrder.objects.select_related(
            "supplier", "campus", "created_by"
        ).prefetch_related("items__asset")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(order_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(order_date__lte=date_to)

        status = request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        total_amount = sum(Decimal(str(p.total_amount)) for p in queryset)

        return {
            "total_orders": total,
            "total_amount": quantize(total_amount),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for po in queryset:
            rows.append({
                "order_number": po.order_number,
                "date": po.order_date,
                "supplier": po.supplier.name if po.supplier else "-",
                "campus": po.campus.name if po.campus else "-",
                "status": po.get_status_display(),
                "total_amount": quantize(po.total_amount),
                "items_count": po.items.count(),
                "expected_delivery": po.expected_delivery,
            })
        return rows


class IssueReportView(AggregateReportView):
    """Issues report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "inventory_issues"
    model = "apps.inventory.models.AssetIssue"

    def get_base_queryset(self, request):
        from apps.inventory.models import AssetIssue
        return AssetIssue.objects.select_related(
            "asset", "asset__category", "asset__campus", "issued_to", "issued_by"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "asset__campus_id")

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        pending = queryset.filter(status="pending").count()
        issued = queryset.filter(status="issued").count()
        returned = queryset.filter(status="returned").count()

        return {
            "total_issues": total,
            "pending": pending,
            "issued": issued,
            "returned": returned,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for issue in queryset:
            rows.append({
                "issue_number": issue.issue_number,
                "date": issue.issue_date,
                "asset": issue.asset.name,
                "code": issue.asset.code or "-",
                "issued_to": issue.issued_to.full_name if issue.issued_to else "-",
                "issued_by": issue.issued_by.get_full_name() if issue.issued_by else "-",
                "quantity": issue.quantity,
                "status": issue.get_status_display(),
                "expected_return": issue.expected_return_date,
                "actual_return": issue.actual_return_date,
            })
        return rows


class ReturnReportView(AggregateReportView):
    """Returns report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "inventory_returns"
    model = "apps.inventory.models.AssetReturn"

    def get_base_queryset(self, request):
        from apps.inventory.models import AssetReturn
        return AssetReturn.objects.select_related(
            "issue__asset", "issue__asset__category", "issue__asset__campus",
            "received_by", "issue__issued_to"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "issue__asset__campus_id")

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(return_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(return_date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()

        return {
            "total_returns": total,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for ret in queryset:
            rows.append({
                "return_number": ret.return_number,
                "date": ret.return_date,
                "asset": ret.issue.asset.name,
                "issued_to": ret.issue.issued_to.full_name if ret.issue.issued_to else "-",
                "quantity": ret.quantity,
                "condition": ret.get_condition_display(),
                "received_by": ret.received_by.get_full_name() if ret.received_by else "-",
                "notes": ret.notes or "-",
            })
        return rows


class DamagedItemsReportView(AggregateReportView):
    """Damaged items report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "inventory_damaged"
    model = "apps.inventory.models.Asset"

    def get_base_queryset(self, request):
        from apps.inventory.models import Asset
        return Asset.objects.filter(status="damaged").select_related("category", "campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")
        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        total_value = sum(Decimal(str(a.unit_cost)) * a.quantity for a in queryset)

        return {
            "total_damaged": total,
            "total_value": quantize(total_value),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for asset in queryset:
            rows.append({
                "name": asset.name,
                "code": asset.code or "-",
                "category": asset.category.name if asset.category else "-",
                "campus": asset.campus.name if asset.campus else "-",
                "quantity": asset.quantity,
                "unit_cost": quantize(asset.unit_cost),
                "total_value": quantize(Decimal(str(asset.unit_cost)) * asset.quantity),
                "supplier": asset.supplier.name if asset.supplier else "-",
            })
        return rows


class LostItemsReportView(DamagedItemsReportView):
    """Lost items report."""
    report_definition_key = "inventory_lost"

    def get_base_queryset(self, request):
        from apps.inventory.models import Asset
        return Asset.objects.filter(status="lost").select_related("category", "campus")


class CategoryReportView(AggregateReportView):
    """Category-wise inventory report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "inventory_category"
    model = "apps.inventory.models.AssetCategory"

    def get_base_queryset(self, request):
        from apps.inventory.models import AssetCategory
        return AssetCategory.objects.all()

    def get_queryset(self, request):
        return super().get_queryset(request)

    def get_summary(self, queryset, request):
        return {"total_categories": queryset.count()}

    def get_detail_rows(self, queryset, request):
        from apps.inventory.models import Asset

        rows = []
        for category in queryset:
            assets = Asset.objects.filter(category=category)
            total_qty = sum(a.quantity for a in assets)
            total_value = sum(Decimal(str(a.unit_cost)) * a.quantity for a in assets)

            rows.append({
                "category": category.name,
                "items_count": assets.count(),
                "total_quantity": total_qty,
                "total_value": quantize(total_value),
            })
        return rows


class SupplierReportView(AggregateReportView):
    """Supplier-wise inventory report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "inventory_supplier"
    model = "apps.inventory.models.Supplier"

    def get_base_queryset(self, request):
        from apps.inventory.models import Supplier
        return Supplier.objects.all()

    def get_queryset(self, request):
        return super().get_queryset(request)

    def get_summary(self, queryset, request):
        return {"total_suppliers": queryset.count()}

    def get_detail_rows(self, queryset, request):
        from apps.inventory.models import Asset, PurchaseOrder

        rows = []
        for supplier in queryset:
            assets = Asset.objects.filter(supplier=supplier)
            total_qty = sum(a.quantity for a in assets)
            total_value = sum(Decimal(str(a.unit_cost)) * a.quantity for a in assets)

            orders = PurchaseOrder.objects.filter(supplier=supplier)
            order_count = orders.count()
            order_value = sum(Decimal(str(p.total_amount)) for p in orders)

            rows.append({
                "supplier": supplier.name,
                "contact": supplier.contact_person or "-",
                "phone": supplier.phone or "-",
                "email": supplier.email or "-",
                "assets_count": assets.count(),
                "total_quantity": total_qty,
                "total_value": quantize(total_value),
                "orders_count": order_count,
                "orders_value": quantize(order_value),
            })
        return rows


class InventoryValuationReportView(AggregateReportView):
    """Inventory valuation report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "inventory_value"
    model = "apps.inventory.models.Asset"

    def get_base_queryset(self, request):
        from apps.inventory.models import Asset
        return Asset.objects.select_related("category", "campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")
        return queryset

    def get_summary(self, queryset, request):
        categories = {}
        campuses = {}
        statuses = {}
        total_value = Decimal("0")
        total_items = 0
        total_quantity = 0

        for asset in queryset:
            value = Decimal(str(asset.unit_cost)) * asset.quantity
            total_value += value
            total_items += 1
            total_quantity += asset.quantity

            statuses[asset.status] = statuses.get(asset.status, 0) + 1

            cat = asset.category.name if asset.category else "Uncategorized"
            if cat not in categories:
                categories[cat] = {"items": 0, "quantity": 0, "value": Decimal("0")}
            categories[cat]["items"] += 1
            categories[cat]["quantity"] += asset.quantity
            categories[cat]["value"] += value

            campus = asset.campus.name if asset.campus else "Unassigned"
            if campus not in campuses:
                campuses[campus] = {"items": 0, "quantity": 0, "value": Decimal("0")}
            campuses[campus]["items"] += 1
            campuses[campus]["quantity"] += asset.quantity
            campuses[campus]["value"] += value

        return {
            "total_items": total_items,
            "total_quantity": total_quantity,
            "total_value": quantize(total_value),
            "by_category": [
                {"category": k, "items": v["items"], "quantity": v["quantity"], "value": quantize(v["value"])}
                for k, v in sorted(categories.items(), key=lambda x: x[1]["value"], reverse=True)
            ],
            "by_campus": [
                {"campus": k, "items": v["items"], "quantity": v["quantity"], "value": quantize(v["value"])}
                for k, v in sorted(campuses.items(), key=lambda x: x[1]["value"], reverse=True)
            ],
            "by_status": [
                {"status": k.title(), "count": v} for k, v in sorted(statuses.items())
            ],
        }

    def get_detail_rows(self, queryset, request):
        return []