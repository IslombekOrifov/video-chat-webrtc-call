# Generated by Django 3.2.5 on 2023-12-15 15:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_activeuser'),
    ]

    operations = [
        migrations.AddField(
            model_name='activeuser',
            name='is_lawyer',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='activeuser',
            name='is_translator',
            field=models.BooleanField(default=False),
        ),
    ]
