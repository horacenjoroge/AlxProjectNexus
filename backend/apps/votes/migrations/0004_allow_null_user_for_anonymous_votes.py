"""
Migration to allow null users in Vote model for anonymous voting.

This migration:
1. Makes the user field nullable (null=True, blank=True)
2. Removes the unique_together constraint on (user, poll)
3. Adds a partial unique constraint that only applies when user is not null
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('votes', '0003_rename_votes_vote_poll_id_voter_t_idx_votes_vote_poll_id_6f9005_idx_and_more'),
    ]

    operations = [
        # Step 1: Make user field nullable
        migrations.AlterField(
            model_name='vote',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='votes',
                to='auth.user',
                null=True,
                blank=True
            ),
        ),
        # Step 2: Remove the old unique_together constraint
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set(),
        ),
        # Step 3: Add partial unique constraint for authenticated users only
        migrations.AddConstraint(
            model_name='vote',
            constraint=models.UniqueConstraint(
                fields=['user', 'poll'],
                condition=models.Q(user__isnull=False),
                name='unique_user_poll'
            ),
        ),
    ]

