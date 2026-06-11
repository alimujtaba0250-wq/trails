# DRF serializers for Trail and Region models go here

from rest_framework import serializers
from .models import Trail, Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = "__all__"


class TrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trail
        fields = "__all__"
