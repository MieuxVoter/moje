# Generated by Django 2.0.3 on 2018-04-07 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0007_auto_20180407_1039'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='state',
            field=models.CharField(choices=[('ST', 'En cours'), ('DR', 'Brouillon'), ('OV', 'Terminée')], default='DR', max_length=2),
        ),
    ]
