from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from apps.accounts.access import apply_campus_scope, assert_campus_allowed
from apps.accounts.permissions import IsAccountantRole

from .models import (
    Asset,
    AssetAssignment,
    AssetCategory,
    MaintenanceRecord,
    Supplier,
)
from .serializers import (
    AssetAssignmentSerializer,
    AssetCategorySerializer,
    AssetSerializer,
    MaintenanceRecordSerializer,
    SupplierSerializer,
)


class AssetCategoryListView(generics.ListCreateAPIView):
    serializer_class = AssetCategorySerializer
    permission_classes = [IsAccountantRole]
    queryset = AssetCategory.objects.all()


class AssetCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssetCategorySerializer
    permission_classes = [IsAccountantRole]
    queryset = AssetCategory.objects.all()


class SupplierListView(generics.ListCreateAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [IsAccountantRole]
    queryset = Supplier.objects.all()


class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [IsAccountantRole]
    queryset = Supplier.objects.all()


class AssetListView(generics.ListCreateAPIView):
    serializer_class = AssetSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = apply_campus_scope(
            Asset.objects.select_related("campus", "category", "supplier"),
            self.request,
            "campus_id",
        )

        search = self.request.query_params.get("q")

        if search:
            queryset = queryset.filter(name__icontains=search)

        category = self.request.query_params.get("category")

        if category:
            queryset = queryset.filter(category_id=category)

        status_filter = self.request.query_params.get("status")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def perform_create(self, serializer):
        assert_campus_allowed(self.request.user, serializer.validated_data.get("campus"))
        serializer.save()


class AssetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssetSerializer
    permission_classes = [IsAccountantRole]
    def get_queryset(self):
        return apply_campus_scope(
            Asset.objects.all(),
            self.request,
            "campus_id",
        )

    def perform_update(self, serializer):
        assert_campus_allowed(self.request.user, serializer.validated_data.get("campus", serializer.instance.campus))
        serializer.save()


class AssetAssignmentListView(generics.ListCreateAPIView):
    serializer_class = AssetAssignmentSerializer
    permission_classes = [IsAccountantRole]
    def get_queryset(self):
        return apply_campus_scope(
            AssetAssignment.objects.select_related("asset"),
            self.request,
            "asset__campus_id",
        )

    def perform_create(self, serializer):
        asset = serializer.validated_data["asset"]
        if not self.get_queryset().filter(asset=asset).exists():
            raise PermissionDenied("The asset is outside your campus scope.")
        serializer.save()


class AssetAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssetAssignmentSerializer
    permission_classes = [IsAccountantRole]
    def get_queryset(self):
        return apply_campus_scope(
            AssetAssignment.objects.all(),
            self.request,
            "asset__campus_id",
        )

    def perform_update(self, serializer):
        if not self.get_queryset().filter(
            asset=serializer.validated_data.get("asset", serializer.instance.asset),
        ).exists():
            raise PermissionDenied("The asset is outside your campus scope.")
        serializer.save()


class MaintenanceRecordListView(generics.ListCreateAPIView):
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsAccountantRole]
    def get_queryset(self):
        return apply_campus_scope(
            MaintenanceRecord.objects.select_related("asset"),
            self.request,
            "asset__campus_id",
        )

    def perform_create(self, serializer):
        asset = serializer.validated_data["asset"]
        if not self.get_queryset().filter(asset=asset).exists():
            raise PermissionDenied("The asset is outside your campus scope.")
        serializer.save()


class MaintenanceRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsAccountantRole]
    def get_queryset(self):
        return apply_campus_scope(
            MaintenanceRecord.objects.all(),
            self.request,
            "asset__campus_id",
        )

    def perform_update(self, serializer):
        if not self.get_queryset().filter(
            asset=serializer.validated_data.get("asset", serializer.instance.asset),
        ).exists():
            raise PermissionDenied("The asset is outside your campus scope.")
        serializer.save()
