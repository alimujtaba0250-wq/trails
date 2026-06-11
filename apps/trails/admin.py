from django.contrib import admin
from .models import Region, Trail, TrailPhoto, Waypoint


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class TrailPhotoInline(admin.TabularInline):
    model = TrailPhoto
    extra = 0
    readonly_fields = ("wikiloc_photo_id", "url", "alt_text", "order")


class WaypointInline(admin.TabularInline):
    model = Waypoint
    extra = 0
    readonly_fields = ("wikiloc_wp_id", "name", "latitude", "longitude", "elevation_ft", "order")


@admin.register(Trail)
class TrailAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "wikiloc_id",
        "region",
        "difficulty",
        "trail_type",
        "distance_mi",
        "trail_rank",
        "rating",
        "scraped_at",
    )
    list_filter = ("region", "difficulty", "trail_type", "activity")
    search_fields = ("title", "author_name", "near")
    readonly_fields = ("wikiloc_id", "scraped_at", "updated_at", "slug")
    prepopulated_fields = {}
    ordering = ("-trail_rank", "-scraped_at")
    inlines = [TrailPhotoInline, WaypointInline]
    view_on_site = False  # no public URL registered yet; prevents NoReverseMatch 500


@admin.register(TrailPhoto)
class TrailPhotoAdmin(admin.ModelAdmin):
    list_display = ("wikiloc_photo_id", "trail", "order", "url")
    list_filter = ("trail__region",)
    search_fields = ("trail__title", "alt_text")


@admin.register(Waypoint)
class WaypointAdmin(admin.ModelAdmin):
    list_display = ("name", "trail", "wikiloc_wp_id", "latitude", "longitude", "elevation_ft", "order")
    search_fields = ("name", "trail__title")
