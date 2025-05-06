from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerError',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=100)),
                ('customer_name', models.CharField(blank=True, max_length=200, null=True)),
                ('account_number', models.CharField(blank=True, max_length=100, null=True)),
                ('amount', models.CharField(blank=True, max_length=100, null=True)),
                ('national_id', models.CharField(blank=True, max_length=100, null=True)),
                ('error_code', models.CharField(max_length=100)),
                ('message', models.TextField()),
                ('line_number', models.CharField(blank=True, max_length=10, null=True)),
                ('is_fixed', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='CleanEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('account_number', models.CharField(max_length=100)),
                ('amount', models.DecimalField(max_digits=15, decimal_places=2)),
                ('national_id', models.CharField(max_length=100)),
                ('customer_code', models.CharField(max_length=100)),
                ('batch_identifier', models.CharField(max_length=100)),
                ('status', models.CharField(max_length=20, default='ok')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('xml_file_name', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name_plural': 'Clean Entries',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BatchHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('batch_identifier', models.CharField(max_length=100, unique=True)),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
                ('resolved_date', models.DateTimeField(null=True, blank=True)),
                ('error_count', models.IntegerField(default=0)),
                ('xml_file', models.FileField(upload_to='xml_uploads/')),
                ('report_file', models.FileField(upload_to='bot_reports/', null=True, blank=True)),
                ('status', models.CharField(max_length=20, choices=[('pending', 'Pending'), ('resolved', 'Resolved')], default='pending')),
                ('filename', models.CharField(max_length=255)),
                ('uploaded_by', models.ForeignKey('auth.User', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Batch Histories',
                'ordering': ['-upload_date'],
            },
        ),
        migrations.CreateModel(
            name='ErrorHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('previous_status', models.CharField(max_length=20)),
                ('new_status', models.CharField(max_length=20)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('changed_by', models.ForeignKey('auth.User', null=True, on_delete=models.SET_NULL)),
                ('error', models.ForeignKey('core.CustomerError', on_delete=models.CASCADE, related_name='history')),
            ],
            options={
                'verbose_name_plural': 'Error Histories',
                'ordering': ['-changed_at'],
            },
        ),
    ]