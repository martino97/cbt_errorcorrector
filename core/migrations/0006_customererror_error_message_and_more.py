# Generated by Django 5.2 on 2025-05-09 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_customererror_phone_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customererror',
            name='error_message',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customererror',
            name='full_error_code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customererror',
            name='loan_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
    ]
