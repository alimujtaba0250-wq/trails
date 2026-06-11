from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView
from rest_framework import viewsets

from .models import Region, Trail
from .serializers import RegionSerializer, TrailSerializer


# ------------------------------------------------------------------ #
# Template views — serve the Stitch-designed HTML pages
# ------------------------------------------------------------------ #

class HomeView(ListView):
    model = Trail
    template_name = "home.html"
    context_object_name = "featured_trails"
    queryset = Trail.objects.select_related("region").order_by("-trail_rank")[:3]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["regions"] = Region.objects.all()
        return ctx


class TrailListView(ListView):
    model = Trail
    template_name = "trail_list.html"
    context_object_name = "trails"
    paginate_by = 24

    def get_queryset(self):
        qs = Trail.objects.select_related("region").order_by("-trail_rank")
        q = self.request.GET.get("q", "").strip()
        region = self.request.GET.get("region", "").strip()
        difficulty = self.request.GET.get("difficulty", "").strip()
        trail_type = self.request.GET.get("trail_type", "").strip()
        if q:
            qs = qs.filter(title__icontains=q)
        if region:
            qs = qs.filter(region__slug=region)
        if difficulty:
            qs = qs.filter(difficulty__iexact=difficulty)
        if trail_type:
            qs = qs.filter(trail_type__icontains=trail_type)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["regions"] = Region.objects.all()
        return ctx


class TrailDetailView(DetailView):
    model = Trail
    template_name = "trail_detail.html"
    context_object_name = "trail"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Trail.objects.select_related("region").prefetch_related("photos", "waypoints")


# ------------------------------------------------------------------ #
# DRF ViewSets — JSON API endpoints
# ------------------------------------------------------------------ #

class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class TrailViewSet(viewsets.ModelViewSet):
    queryset = Trail.objects.select_related("region").order_by("-trail_rank")
    serializer_class = TrailSerializer
