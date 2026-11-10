from rest_framework import serializers

from .models import Job, UserPreference


class JobSerializer(serializers.ModelSerializer):
    """Serialiser for Job model instances.

    Exposes ``match_score`` and ``match_reason`` when a job has been run
    through the recommendation engine (the view annotates the instance with
    ``_match_score`` / ``_match_reason``), otherwise those fields are null.

    ``is_saved`` is populated when the view passes a ``saved_ids`` set in the
    serialiser context.

    ``source`` is mapped to the human-readable ``source_name`` field.
    ``url`` is an alias for ``source_url`` so the frontend can use either name.
    """

    match_score = serializers.SerializerMethodField()
    match_reason = serializers.SerializerMethodField()
    match_factors = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    # Expose source_name as 'source' for frontend compatibility.
    source = serializers.CharField(source="source_name", read_only=True)
    # Expose source_url as 'url' as well (the frontend types reference both).
    url = serializers.CharField(source="source_url", read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "organization",
            "location",
            "country",
            "job_type",
            "field",
            "description",
            "skills",
            "closing_date",
            "published_date",
            "source",
            "source_url",
            "url",
            "match_score",
            "match_reason",
            "match_factors",
            "is_saved",
        ]

    def get_match_score(self, obj) -> int | None:
        """Populated by the recommendations view; null on regular job listings."""
        return getattr(obj, "_match_score", None)

    def get_match_reason(self, obj) -> str | None:
        return getattr(obj, "_match_reason", None)

    def get_match_factors(self, obj) -> list[dict[str, str]] | None:
        return getattr(obj, "_match_factors", None)

    def get_is_saved(self, obj) -> bool | None:
        saved_ids = self.context.get("saved_ids")
        if saved_ids is None:
            return None
        return obj.id in saved_ids


class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serialiser for UserPreference instances."""

    class Meta:
        model = UserPreference
        fields = [
            "job_types",
            "fields",
            "location_type",
            "country",
            "onboarding_completed",
        ]
        read_only_fields = ["onboarding_completed"]

    def validate_job_types(self, value):
        # Valid codes mirror JOB_TYPE_CHOICES in models.py
        valid = {"full_time", "part_time", "internship", "freelance"}
        bad = [v for v in value if v not in valid]
        if bad:
            raise serializers.ValidationError(
                f"Invalid job_types: {bad}. "
                f"Valid values: {sorted(valid)}"
            )
        return value

    def validate_fields(self, value):
        valid = {
            "hotel_tourism", "tech_it", "marketing_sales", "health_ngo",
            "finance_banking", "education_teaching", "construction_engineering",
            "logistics_supply_chain", "any",
        }
        bad = [v for v in value if v not in valid]
        if bad:
            raise serializers.ValidationError(
                f"Invalid fields: {bad}. Valid values: {sorted(valid)}"
            )
        return value

    def validate(self, attrs):
        location_type = attrs.get("location_type")
        country = attrs.get("country")
        if location_type == "abroad" and not country:
            raise serializers.ValidationError(
                {"country": "A country is required when location_type is 'abroad'."}
            )
        return attrs
