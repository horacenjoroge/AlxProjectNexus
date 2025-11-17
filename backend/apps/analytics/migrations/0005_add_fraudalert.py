"""
Migration for FraudAlert model.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('analytics', '0004_add_ip_reputation_models'),
        ('polls', '0002_add_poll_fields_and_rename_choice'),
        ('votes', '0002_update_vote_and_add_voteattempt'),
    ]

    operations = [
        migrations.CreateModel(
            name='FraudAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address of suspicious vote', null=True)),
                ('reasons', models.TextField(help_text='Comma-separated list of fraud detection reasons')),
                ('risk_score', models.IntegerField(help_text='Risk score (0-100) indicating severity of fraud')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When fraud was detected')),
                ('poll', models.ForeignKey(help_text='Poll where fraud was detected', on_delete=django.db.models.deletion.CASCADE, related_name='fraud_alerts', to='polls.poll')),
                ('user', models.ForeignKey(blank=True, help_text='User who made the suspicious vote', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fraud_alerts', to=settings.AUTH_USER_MODEL)),
                ('vote', models.ForeignKey(help_text='Vote that triggered the fraud alert', on_delete=django.db.models.deletion.CASCADE, related_name='fraud_alerts', to='votes.vote')),
            ],
            options={
                'verbose_name': 'Fraud Alert',
                'verbose_name_plural': 'Fraud Alerts',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='fraudalert',
            index=models.Index(fields=['poll', 'created_at'], name='analytics_fraudalert_poll_created_idx'),
        ),
        migrations.AddIndex(
            model_name='fraudalert',
            index=models.Index(fields=['user', 'created_at'], name='analytics_fraudalert_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='fraudalert',
            index=models.Index(fields=['ip_address', 'created_at'], name='analytics_fraudalert_ip_created_idx'),
        ),
        migrations.AddIndex(
            model_name='fraudalert',
            index=models.Index(fields=['risk_score', 'created_at'], name='analytics_fraudalert_risk_created_idx'),
        ),
    ]

