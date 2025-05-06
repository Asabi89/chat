from django.core.management.base import BaseCommand
from django.utils import timezone
from stories.models import Story

class Command(BaseCommand):
    help = 'Cleans up expired stories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete expired stories instead of just hiding them',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        expired_stories = Story.objects.filter(expires_at__lt=now, is_hidden=False)
        
        count = expired_stories.count()
        
        if options['delete']:
            # Delete stories that are not in any highlights
            stories_to_delete = expired_stories.filter(in_highlights__isnull=True)
            delete_count = stories_to_delete.count()
            stories_to_delete.delete()
            
            # Hide stories that are in highlights
            stories_to_hide = expired_stories.filter(in_highlights__isnull=False)
            hide_count = stories_to_hide.count()
            stories_to_hide.update(is_hidden=True)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully processed {count} expired stories: '
                    f'{delete_count} deleted, {hide_count} hidden'
                )
            )
        else:
            # Just hide expired stories
            expired_stories.update(is_hidden=True)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully hidden {count} expired stories')
            )
