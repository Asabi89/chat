from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, F
import datetime

from search.models import Hashtag, TrendingHashtag, PostHashtag, ReelHashtag

class Command(BaseCommand):
    help = 'Updates trending hashtags data'

    def handle(self, *args, **options):
        # Get today's date
        today = timezone.now().date()
        yesterday = timezone.now() - datetime.timedelta(days=1)
        
        # Get all hashtags
        hashtags = Hashtag.objects.all()
        
        self.stdout.write(f"Updating trending data for {hashtags.count()} hashtags...")
        
        # Process each hashtag
        for hashtag in hashtags:
            # Get 24h post count
            post_count = PostHashtag.objects.filter(
                hashtag=hashtag,
                created_at__gte=yesterday
            ).count()
            
            reel_count = ReelHashtag.objects.filter(
                hashtag=hashtag,
                created_at__gte=yesterday
            ).count()
            
            # Skip if no activity
            if post_count == 0 and reel_count == 0:
                continue
            
            # Get or create trending record
            trending, created = TrendingHashtag.objects.get_or_create(
                hashtag=hashtag,
                date=today
            )
            
            # Update trending record
            trending.post_count_24h = post_count + reel_count
            
            # Calculate engagement score
            # Formula: post_count_24h * 1.0 + view_count_24h * 0.1
            trending.engagement_score = (post_count + reel_count) * 1.0 + trending.view_count_24h * 0.1
            
            trending.save()
        
        self.stdout.write(self.style.SUCCESS('Successfully updated trending hashtags'))
