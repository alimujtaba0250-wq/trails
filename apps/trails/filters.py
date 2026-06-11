# django-filter FilterSet classes for Trail and Region queryset filtering go here

import django_filters
from .models import Trail, Region


class RegionFilter(django_filters.FilterSet):
    class Meta:
        model = Region
        fields = []


class TrailFilter(django_filters.FilterSet):
    class Meta:
        model = Trail
        fields = []
