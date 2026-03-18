from django.urls import path
from .views import AdminDashboardOverviewAPIView

urlpatterns = [
    path('dashboard/overview/', AdminDashboardOverviewAPIView.as_view(), name="admin_dashboard_overview"),
]
