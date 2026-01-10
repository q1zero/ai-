from django.contrib import admin

# Register your models here.

from .models import VideoProject, VideoScript


@admin.register(VideoProject)
class VideoProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "topic", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("topic__title",)
    ordering = ("-created_at",)


@admin.register(VideoScript)
class VideoScriptAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "created_at", "updated_at")
    search_fields = ("project__topic__title",)
    ordering = ("-created_at",)
