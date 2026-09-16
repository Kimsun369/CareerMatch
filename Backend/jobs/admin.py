from django.contrib import admin

from .models import Job, SavedJob, UserPreference


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "organization",
        "country",
        "job_type",
        "field",
        "is_active",
        "closing_date",
        "published_date",
        "source",
    )
    list_filter = ("is_active", "job_type", "field", "source", "country")
    search_fields = ("title", "organization", "description", "country")
    readonly_fields = ("source", "source_id", "source_name", "source_url", "created_at", "updated_at")
    date_hierarchy = "published_date"
    list_per_page = 50

    fieldsets = (
        ("Core", {
            "fields": ("title", "organization", "location", "country"),
        }),
        ("Classification", {
            "fields": ("job_type", "field", "is_active"),
        }),
        ("Description", {
            "fields": ("description", "skills"),
            "classes": ("collapse",),
        }),
        ("Dates", {
            "fields": ("published_date", "closing_date"),
        }),
        ("Source", {
            "fields": ("source", "source_id", "source_name", "source_url"),
        }),
        ("Metadata", {
            "fields": ("raw_metadata", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "location_type", "country", "onboarding_completed", "updated_at")
    list_filter = ("location_type", "onboarding_completed")
    readonly_fields = ("created_at", "updated_at")


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__telegram_id", "user__username", "job__title")
    readonly_fields = ("created_at",)
