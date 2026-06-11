from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Region(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "trails"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Trail(models.Model):
    wikiloc_id = models.IntegerField(unique=True, db_index=True)
    title = models.CharField(max_length=500)
    slug = models.SlugField(unique=True, max_length=550, db_index=True)
    region = models.ForeignKey(
        Region,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="trails",
        db_index=True,
    )
    near = models.CharField(max_length=300, blank=True)
    activity = models.CharField(max_length=100, default="Hiking")
    difficulty = models.CharField(max_length=50, blank=True)
    trail_type = models.CharField(max_length=50, blank=True)

    distance_mi = models.FloatField(null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)

    elevation_gain_ft = models.IntegerField(null=True, blank=True)
    elevation_gain_m = models.IntegerField(null=True, blank=True)
    elevation_loss_ft = models.IntegerField(null=True, blank=True)
    elevation_max_ft = models.IntegerField(null=True, blank=True)
    elevation_min_ft = models.IntegerField(null=True, blank=True)

    trail_rank = models.IntegerField(null=True, blank=True, db_index=True)
    rating = models.FloatField(null=True, blank=True)

    moving_time = models.CharField(max_length=100, blank=True)
    total_time = models.CharField(max_length=100, blank=True)
    coordinates_count = models.IntegerField(null=True, blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    description = models.TextField(blank=True)
    author_name = models.CharField(max_length=200, blank=True)
    author_wikiloc_id = models.CharField(max_length=50, blank=True)
    thumbnail_url = models.URLField(blank=True)
    source_url = models.URLField()

    recorded_date = models.CharField(max_length=100, blank=True)
    uploaded_date = models.DateField(null=True, blank=True)

    views_count = models.IntegerField(null=True, blank=True)
    downloads_count = models.IntegerField(null=True, blank=True)

    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "trails"
        ordering = ["-trail_rank", "-scraped_at"]
        indexes = [
            models.Index(fields=["wikiloc_id"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["region"]),
            models.Index(fields=["trail_rank"]),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        try:
            return reverse("trails:trail-detail", kwargs={"slug": self.slug})
        except Exception:
            return self.source_url or "#"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{self.wikiloc_id}")
        super().save(*args, **kwargs)


class TrailPhoto(models.Model):
    trail = models.ForeignKey(Trail, related_name="photos", on_delete=models.CASCADE)
    wikiloc_photo_id = models.IntegerField()
    url = models.URLField()
    alt_text = models.CharField(max_length=500, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        app_label = "trails"
        ordering = ["order"]

    def __str__(self) -> str:
        return f"Photo {self.wikiloc_photo_id} for {self.trail}"


class Waypoint(models.Model):
    trail = models.ForeignKey(Trail, related_name="waypoints", on_delete=models.CASCADE)
    wikiloc_wp_id = models.IntegerField()
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation_ft = models.IntegerField(null=True, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        app_label = "trails"
        ordering = ["order"]

    def __str__(self) -> str:
        return f"{self.name} ({self.trail})"
