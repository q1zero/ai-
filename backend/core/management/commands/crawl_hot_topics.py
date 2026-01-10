from django.core.management.base import BaseCommand

from core.models import HotTopic
from core.utils.crawler import fetch_douyin_hot, fetch_weibo_hot, fetch_zhihu_hot

class Command(BaseCommand):
    help = 'Crawl hot topics from Weibo, Douyin and Zhihu'

    def handle(self, *args, **options):
        self.stdout.write('Starting crawler...')

        # Weibo
        self.stdout.write('Fetching Weibo hot topics...')
        weibo_items = fetch_weibo_hot()
        count_weibo = 0
        for item in weibo_items:
            obj, created = HotTopic.objects.update_or_create(
                title=item.title,
                platform=HotTopic.PlatformChoices.WEIBO,
                defaults={
                    'hot_value': item.hot_value,
                    'created_at': item.fetched_at, 
                    # Note: update_or_create won't update created_at if it exists unless we put it in defaults. 
                    # But created_at is auto_now_add=True usually. Let's check model.
                    # Model: created_at = models.DateTimeField(auto_now_add=True)
                    # auto_now_add only sets on creation.
                    # We might want to update a 'updated_at' field if we had one, or just ignore.
                    # But for now, we just ensure it exists.
                }
            )
            if created:
                count_weibo += 1
        self.stdout.write(f'Saved {count_weibo} new Weibo topics.')

        # Douyin
        self.stdout.write('Fetching Douyin hot topics...')
        douyin_items = fetch_douyin_hot()
        count_douyin = 0
        for item in douyin_items:
            obj, created = HotTopic.objects.update_or_create(
                title=item.title,
                platform=HotTopic.PlatformChoices.DOUYIN,
                defaults={
                    'hot_value': item.hot_value,
                    # 'created_at': item.fetched_at 
                }
            )
            if created:
                count_douyin += 1
        self.stdout.write(f'Saved {count_douyin} new Douyin topics.')

        # Zhihu
        self.stdout.write('Fetching Zhihu hot topics...')
        zhihu_items = fetch_zhihu_hot()
        count_zhihu = 0
        for item in zhihu_items:
            obj, created = HotTopic.objects.update_or_create(
                title=item.title,
                platform=HotTopic.PlatformChoices.ZHIHU,
                defaults={
                    'hot_value': item.hot_value,
                }
            )
            if created:
                count_zhihu += 1
        self.stdout.write(f'Saved {count_zhihu} new Zhihu topics.')

        self.stdout.write(self.style.SUCCESS('Crawler finished successfully.'))
