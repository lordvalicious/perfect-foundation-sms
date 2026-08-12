from rest_framework import generics

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
        queryset = Asset.objects.select_related("category", "supplier")

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


class AssetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssetSerializer
    permission_classes = [IsAccountantRole]
    queryset = Asset.objects.all()


class AssetAssignmentListView(generics.ListCreateAPIView):
    serializer_class = AssetAssignmentSerializer
    permission_classes = [IsAccountantRole]
    queryset = AssetAssignment.objects.select_related("asset")


class AssetAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssetAssignmentSerializer
    permission_classes = [IsAccountantRole]
    queryset = AssetAssignment.objects.all()


class MaintenanceRecordListView(generics.ListCreateAPIView):
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsAccountantRole]
    queryset = MaintenanceRecord.objects.select_related("asset")


class MaintenanceRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsAccountantRole]
    queryset = MaintenanceRecord.objects.all()
