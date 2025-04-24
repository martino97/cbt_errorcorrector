import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20250422_2232'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='customererror',
            name='customer_details',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AlterField(
            model_name='customererror',
            name='customer_details_json',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customererror',
            name='uploaded_by',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='uploaded_errors',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
