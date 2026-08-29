from django.urls import path

from .views import (
    AssetAssignmentDetailView,
    AssetAssignmentListView,
    AssetCategoryDetailView,
    AssetCategoryListView,
    AssetDetailView,
    AssetListView,
    MaintenanceRecordDetailView,
    MaintenanceRecordListView,
    StockLevelDetailView,
    StockLevelListView,
    StockMovementListView,
    StockSummaryView,
    SupplierDetailView,
    SupplierListView,
)


urlpatterns = [
    path(
        "categories/",
        AssetCategoryListView.as_view(),
        name="asset-category-list",
    ),
    path(
        "categories/<int:pk>/",
        AssetCategoryDetailView.as_view(),
        name="asset-category-detail",
    ),
    path("suppliers/", SupplierListView.as_view(), name="supplier-list"),
    path(
        "suppliers/<int:pk>/",
        SupplierDetailView.as_view(),
        name="supplier-detail",
    ),
    path("assets/", AssetListView.as_view(), name="asset-list"),
    path(
        "assets/<int:pk>/",
        AssetDetailView.as_view(),
        name="asset-detail",
    ),
    path(
        "assignments/",
        AssetAssignmentListView.as_view(),
        name="asset-assignment-list",
    ),
    path(
        "assignments/<int:pk>/",
        AssetAssignmentDetailView.as_view(),
        name="asset-assignment-detail",
    ),
    path(
        "maintenance/",
        MaintenanceRecordListView.as_view(),
        name="maintenance-list",
    ),
    path(
        "maintenance/<int:pk>/",
        MaintenanceRecordDetailView.as_view(),
        name="maintenance-detail",
    ),
    path(
        "stock/levels/",
        StockLevelListView.as_view(),
        name="stock-level-list",
    ),
    path(
        "stock/levels/<int:pk>/",
        StockLevelDetailView.as_view(),
        name="stock-level-detail",
    ),
    path(
        "stock/movements/",
        StockMovementListView.as_view(),
        name="stock-movement-list",
    ),
    path(
        "stock/summary/",
        StockSummaryView.as_view(),
        name="stock-summary",
    ),
]
