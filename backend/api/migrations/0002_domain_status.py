# Generated by Django 5.1.1 on 2024-09-17 10:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain',
            name='status',
            field=models.CharField(default='not_started', max_length=50),
        ),
    ]
