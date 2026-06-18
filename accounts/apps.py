from django.apps import AppConfig
import os
import logging
from django.core.management import call_command

logger = logging.getLogger(__name__)

def fetch_videos_job():
    logger.info("Running scheduled fetch_youtube_videos job...")
    try:
        call_command('fetch_youtube_videos')
    except Exception as e:
        logger.error(f"Error in fetch_youtube_videos job: {e}")


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        import accounts.signals  # noqa: F401
        
        # Start APScheduler only once in dev mode
        if os.environ.get('RUN_MAIN', None) == 'true' or not os.environ.get('RUN_MAIN'):
            from apscheduler.schedulers.background import BackgroundScheduler
            
            scheduler = BackgroundScheduler()
            try:
                # Gece 12 (00:00) ve Öğlen 12 (12:00) için zamanlandı
                scheduler.add_job(
                    fetch_videos_job,
                    trigger="cron",
                    hour="0,12",
                    minute="0",
                    id="fetch_youtube_videos_job",
                    max_instances=1,
                    replace_existing=True,
                )
                
                scheduler.start()
                logger.info("YouTube video fetch scheduler started! (00:00 and 12:00)")
            except Exception as e:
                logger.error(f"Failed to start APScheduler: {e}")
