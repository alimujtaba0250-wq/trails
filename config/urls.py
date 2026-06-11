# Root URL configuration — register app-level urlconfs here

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.trails.urls", namespace="trails")),
]
