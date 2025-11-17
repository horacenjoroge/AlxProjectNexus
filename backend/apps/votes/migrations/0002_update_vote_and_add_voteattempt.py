# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('polls', '0002_add_poll_fields_and_rename_choice'),
        ('votes', '0001_initial'),
    ]

    operations = [
        # Note: option field already created correctly in 0001_initial with polls.polloption
        # No need to rename or alter the field
        # Add new fields to Vote
        migrations.AddField(
            model_name='vote',
            name='voter_token',
            field=models.CharField(db_index=True, help_text='Token for anonymous/guest voting', max_length=64),
        ),
        migrations.AddField(
            model_name='vote',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, db_index=True, help_text='IP address of voter', null=True),
        ),
        migrations.AddField(
            model_name='vote',
            name='user_agent',
            field=models.TextField(blank=True, help_text='User agent string'),
        ),
        migrations.AddField(
            model_name='vote',
            name='fingerprint',
            field=models.CharField(blank=True, db_index=True, help_text='Browser/device fingerprint', max_length=128),
        ),
        migrations.AddField(
            model_name='vote',
            name='is_valid',
            field=models.BooleanField(db_index=True, default=True, help_text='Whether this vote is valid (False if fraud detected)'),
        ),
        migrations.AddField(
            model_name='vote',
            name='fraud_reasons',
            field=models.TextField(blank=True, help_text='Comma-separated list of fraud detection reasons (if is_valid=False)'),
        ),
        migrations.AddField(
            model_name='vote',
            name='risk_score',
            field=models.IntegerField(default=0, help_text='Risk score (0-100) from fraud detection'),
        ),
        # Remove old indexes
        migrations.RemoveIndex(
            model_name='vote',
            name='votes_vote_user_id_poll_id_idx',
        ),
        migrations.RemoveIndex(
            model_name='vote',
            name='votes_vote_poll_id_created_idx',
        ),
        # Add new indexes to Vote
        migrations.AddIndex(
            model_name='vote',
            index=models.Index(fields=['poll', 'voter_token'], name='votes_vote_poll_id_voter_t_idx'),
        ),
        migrations.AddIndex(
            model_name='vote',
            index=models.Index(fields=['idempotency_key'], name='votes_vote_idempotency_idx'),
        ),
        migrations.AddIndex(
            model_name='vote',
            index=models.Index(fields=['ip_address', 'created_at'], name='votes_vote_ip_addr_created_idx'),
        ),
        migrations.AddIndex(
            model_name='vote',
            index=models.Index(fields=['user', 'poll'], name='votes_vote_user_id_poll_id_idx'),
        ),
        migrations.AddIndex(
            model_name='vote',
            index=models.Index(fields=['poll', 'created_at'], name='votes_vote_poll_id_created_idx'),
        ),
        migrations.AddIndex(
            model_name='vote',
            index=models.Index(fields=['fingerprint', 'created_at'], name='votes_vote_fingerprint_created_idx'),
        ),
        migrations.AddIndex(
            model_name='vote',
            index=models.Index(fields=['is_valid', 'poll'], name='votes_vote_is_valid_poll_idx'),
        ),
        # Create VoteAttempt model
        migrations.CreateModel(
            name='VoteAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('voter_token', models.CharField(blank=True, db_index=True, help_text='Token for anonymous/guest voting', max_length=64)),
                ('idempotency_key', models.CharField(db_index=True, help_text='Idempotency key used in attempt', max_length=64)),
                ('ip_address', models.GenericIPAddressField(blank=True, db_index=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('fingerprint', models.CharField(blank=True, db_index=True, max_length=128)),
                ('success', models.BooleanField(default=False, help_text='Whether the vote attempt was successful')),
                ('error_message', models.TextField(blank=True, help_text='Error message if attempt failed')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('option', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vote_attempts', to='polls.polloption')),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vote_attempts', to='polls.poll')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vote_attempts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        # Add indexes to VoteAttempt
        migrations.AddIndex(
            model_name='voteattempt',
            index=models.Index(fields=['poll', 'voter_token'], name='votes_voteattempt_poll_voter_idx'),
        ),
        migrations.AddIndex(
            model_name='voteattempt',
            index=models.Index(fields=['idempotency_key'], name='votes_voteattempt_idempotency_idx'),
        ),
        migrations.AddIndex(
            model_name='voteattempt',
            index=models.Index(fields=['ip_address', 'created_at'], name='votes_voteattempt_ip_created_idx'),
        ),
        migrations.AddIndex(
            model_name='voteattempt',
            index=models.Index(fields=['success', 'created_at'], name='votes_voteattempt_success_created_idx'),
        ),
        migrations.AddIndex(
            model_name='voteattempt',
            index=models.Index(fields=['poll', 'created_at'], name='votes_voteattempt_poll_created_idx'),
        ),
    ]

