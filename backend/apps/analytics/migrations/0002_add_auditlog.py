# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method', models.CharField(help_text='HTTP method (GET, POST, etc.)', max_length=10)),
                ('path', models.CharField(help_text='Request path', max_length=500)),
                ('query_params', models.TextField(blank=True, help_text='Query parameters as JSON string', null=True)),
                ('request_body', models.TextField(blank=True, help_text='Request body (truncated to 1000 chars)', null=True)),
                ('status_code', models.IntegerField(help_text='HTTP response status code')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=500)),
                ('request_id', models.CharField(blank=True, db_index=True, help_text='Request ID for tracing', max_length=64)),
                ('response_time', models.FloatField(help_text='Response time in seconds')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', 'created_at'], name='analytics_au_user_id_created_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['ip_address', 'created_at'], name='analytics_au_ip_addr_created_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['request_id'], name='analytics_au_request_id_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['method', 'path', 'created_at'], name='analytics_au_method_path_created_idx'),
        ),
    ]

