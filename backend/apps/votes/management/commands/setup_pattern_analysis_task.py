"""
Management command to set up periodic pattern analysis task.
"""

from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule


class Command(BaseCommand):
    help = "Set up periodic pattern analysis task"

    def handle(self, *args, **options):
        # Create interval schedule for hourly execution
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created interval schedule: every {schedule.every} {schedule.period}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Using existing interval schedule: every {schedule.every} {schedule.period}"
                )
            )

        # Create or update periodic task
        task, created = PeriodicTask.objects.get_or_create(
            name="Periodic Vote Pattern Analysis",
            defaults={
                "task": "apps.votes.tasks.periodic_pattern_analysis",
                "interval": schedule,
                "enabled": True,
                "description": "Periodically analyze vote patterns for suspicious activity",
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created periodic task: {task.name}"))
        else:
            # Update existing task
            task.task = "apps.votes.tasks.periodic_pattern_analysis"
            task.interval = schedule
            task.enabled = True
            task.save()
            self.stdout.write(self.style.SUCCESS(f"Updated periodic task: {task.name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nPeriodic pattern analysis task is {'enabled' if task.enabled else 'disabled'}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Task will run every {schedule.every} {schedule.period}"
            )
        )
