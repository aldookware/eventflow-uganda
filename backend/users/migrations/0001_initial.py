# Generated by Django 4.2.7 on 2025-07-21 23:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
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
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                ("email", models.EmailField(max_length=254, unique=True)),
                (
                    "phone",
                    models.CharField(blank=True, max_length=20, null=True, unique=True),
                ),
                ("first_name", models.CharField(max_length=30)),
                ("last_name", models.CharField(max_length=30)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("user", "User"),
                            ("organizer", "Organizer"),
                            ("admin", "Admin"),
                        ],
                        default="user",
                        max_length=10,
                    ),
                ),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                (
                    "gender",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("male", "Male"),
                            ("female", "Female"),
                            ("other", "Other"),
                            ("prefer_not_to_say", "Prefer not to say"),
                        ],
                        max_length=20,
                        null=True,
                    ),
                ),
                (
                    "profile_image",
                    models.ImageField(blank=True, null=True, upload_to="profiles/"),
                ),
                ("city", models.CharField(blank=True, max_length=100, null=True)),
                ("country", models.CharField(default="Uganda", max_length=100)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("is_verified", models.BooleanField(default=False)),
                ("phone_verified", models.BooleanField(default=False)),
                ("email_verified", models.BooleanField(default=False)),
                (
                    "date_joined",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("last_login", models.DateTimeField(blank=True, null=True)),
                ("preferred_language", models.CharField(default="en", max_length=10)),
                ("preferred_currency", models.CharField(default="UGX", max_length=10)),
                ("marketing_consent", models.BooleanField(default=False)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "db_table": "users",
            },
        ),
        migrations.CreateModel(
            name="OTPVerification",
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
                ("otp_code", models.CharField(max_length=6)),
                ("phone_number", models.CharField(max_length=20)),
                (
                    "purpose",
                    models.CharField(
                        choices=[
                            ("registration", "Registration"),
                            ("login", "Login"),
                            ("password_reset", "Password Reset"),
                            ("phone_verification", "Phone Verification"),
                        ],
                        max_length=20,
                    ),
                ),
                ("is_used", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="otp_verifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "otp_verifications",
            },
        ),
        migrations.CreateModel(
            name="UserDevice",
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
                ("device_id", models.CharField(max_length=255)),
                (
                    "device_name",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "platform",
                    models.CharField(
                        choices=[
                            ("ios", "iOS"),
                            ("android", "Android"),
                            ("web", "Web"),
                        ],
                        max_length=20,
                    ),
                ),
                ("fcm_token", models.TextField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="devices",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "user_devices",
                "unique_together": {("user", "device_id")},
            },
        ),
    ]
