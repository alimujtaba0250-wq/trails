from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HomeView, RegionViewSet, TrailDetailView, TrailListView, TrailViewSet

app_name = "trails"

router = DefaultRouter()
router.register(r"trails", TrailViewSet, basename="trail-api")
router.register(r"regions", RegionViewSet, basename="region-api")

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("trails/", TrailListView.as_view(), name="trail-list"),
    path("trails/<slug:slug>/", TrailDetailView.as_view(), name="trail-detail"),
    path("api/", include(router.urls)),
]
