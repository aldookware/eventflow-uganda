# Generated by Django 4.2.7 on 2025-07-21 23:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("events", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="organizer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="organized_events",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="venue",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="events",
                to="events.venue",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="venueamenity",
            unique_together={("venue", "amenity_type")},
        ),
        migrations.AlterUniqueTogether(
            name="eventtagging",
            unique_together={("event", "tag")},
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["start_date"], name="events_start_d_6c01fc_idx"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["status"], name="events_status_8890b6_idx"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["category"], name="events_categor_fd16be_idx"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["venue"], name="events_venue_i_ccbf24_idx"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(
                fields=["is_featured"], name="events_is_feat_6aef59_idx"
            ),
        ),
    ]
