# Generated by Django 5.1.5 on 2025-01-22 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_team_decision'),
    ]

    operations = [
        migrations.AddField(
            model_name='hackathon',
            name='banner',
            field=models.ImageField(blank=True, null=True, upload_to='hackathon_banners/'),
        ),
        migrations.AddField(
            model_name='hackathon',
            name='social_links',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='hackathon',
            name='theme',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='hackathon',
            name='website',
            field=models.URLField(blank=True, null=True),
        ),
    ]
