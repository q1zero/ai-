from django.contrib import admin

# Register your models here.

from .models import HotTopic


@admin.register(HotTopic)
class HotTopicAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "platform", "hot_value", "is_used", "created_at")
    list_filter = ("platform", "is_used")
    search_fields = ("title", "summary")
    ordering = ("-created_at",)
