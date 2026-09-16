# Generated migration — adds default to UserPreference.location_type and
# adds a country index to Job.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        # Add default='cambodia' to location_type so new UserPreference
        # instances have a safe value before the user completes onboarding.
        migrations.AlterField(
            model_name="userpreference",
            name="location_type",
            field=models.CharField(
                choices=[("cambodia", "Cambodia"), ("abroad", "Abroad")],
                default="cambodia",
                max_length=16,
            ),
        ),
        # Add country index to Job for faster location filtering.
        migrations.AddIndex(
            model_name="job",
            index=models.Index(fields=["is_active", "country"], name="jobs_job_is_acti_country_idx"),
        ),
    ]

