# Generated by Django 5.1.5 on 2025-01-23 22:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auths', '0003_customuser_full_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='github_score',
            field=models.IntegerField(default=0),
        ),
    ]
