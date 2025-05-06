from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime

from search.models import SearchHistory

class Command(BaseCommand):
    help = 'Cleans up old search history records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete search history older than this many days'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - datetime.timedelta(days=days)
        
        # Count records to be deleted
        count = SearchHistory.objects.filter(created_at__lt=cutoff_date).count()
        
        # Delete old records
        SearchHistory.objects.filter(created_at__lt=cutoff_date).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} search history records older than {days} days')
        )
