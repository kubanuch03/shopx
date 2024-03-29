# Generated by Django 5.0.3 on 2024-03-27 16:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "app_support_service",
            "0002_supportserviceroom_supportservicemessage_and_more",
        ),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="supportserviceroom",
            name="admin",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="admin_rooms",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
