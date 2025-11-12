# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("analytics", "0002_add_auditlog"),
    ]

    operations = [
        migrations.CreateModel(
            name="FingerprintBlock",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "fingerprint",
                    models.CharField(
                        db_index=True,
                        help_text="Blocked browser/device fingerprint hash",
                        max_length=128,
                        unique=True,
                    ),
                ),
                (
                    "reason",
                    models.TextField(
                        help_text="Reason for blocking (e.g., 'Used by multiple users')"
                    ),
                ),
                (
                    "blocked_at",
                    models.DateTimeField(
                        auto_now_add=True, help_text="When the fingerprint was blocked"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether this block is currently active (can be unblocked by admin)",
                    ),
                ),
                (
                    "unblocked_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When the fingerprint was unblocked (if applicable)",
                        null=True,
                    ),
                ),
                (
                    "total_users",
                    models.IntegerField(
                        default=0,
                        help_text="Total number of different users who used this fingerprint before blocking",
                    ),
                ),
                (
                    "total_votes",
                    models.IntegerField(
                        default=0,
                        help_text="Total number of votes from this fingerprint before blocking",
                    ),
                ),
                (
                    "blocked_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="User/admin who blocked this fingerprint (null if auto-blocked)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="blocked_fingerprints",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "first_seen_user",
                    models.ForeignKey(
                        blank=True,
                        help_text="First user who used this fingerprint",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="first_seen_fingerprints",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "unblocked_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="User/admin who unblocked this fingerprint",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="unblocked_fingerprints",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Blocked Fingerprint",
                "verbose_name_plural": "Blocked Fingerprints",
                "ordering": ["-blocked_at"],
            },
        ),
        migrations.AddIndex(
            model_name="fingerprintblock",
            index=models.Index(
                fields=["fingerprint", "is_active"], name="analytics_f_fingerp_7a8b8a_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="fingerprintblock",
            index=models.Index(
                fields=["is_active", "blocked_at"], name="analytics_f_is_acti_8c9d0e_idx"
            ),
        ),
    ]

