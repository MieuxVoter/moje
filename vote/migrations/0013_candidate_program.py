# Generated by Django 2.0.3 on 2018-04-14 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0012_organisation_site'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='program',
            field=models.TextField(default=''),
        ),
    ]