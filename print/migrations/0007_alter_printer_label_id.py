# Generated by Django 5.0.6 on 2024-09-13 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("print", "0006_rename_zpl_label_zpl_text"),
    ]

    operations = [
        migrations.AlterField(
            model_name="printer",
            name="Label_ID",
            field=models.CharField(max_length=12),
        ),
    ]
