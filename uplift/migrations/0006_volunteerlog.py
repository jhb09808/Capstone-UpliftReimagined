# Generated by Django 4.2.16 on 2024-12-07 18:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("uplift", "0005_inventoryitem_category_inventoryitem_notes"),
    ]

    operations = [
        migrations.CreateModel(
            name="VolunteerLog",
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
                ("date", models.DateField()),
                ("activity", models.CharField(max_length=255)),
                ("hours", models.DecimalField(decimal_places=2, max_digits=5)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]