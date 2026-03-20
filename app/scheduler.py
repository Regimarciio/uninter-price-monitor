from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
import logging
from datetime import datetime
import pytz
from typing import Callable
import atexit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceScheduler:
    def __init__(self, scrape_interval_minutes: int = 30):
        self.scrape_interval = scrape_interval_minutes
        self.scheduler = BackgroundScheduler(
            executors={
                'default': ThreadPoolExecutor(1)
            },
            timezone=pytz.UTC,
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 60 * 5
            }
        )
        
        # Ensure scheduler shuts down properly
        atexit.register(lambda: self.shutdown())
    
    def start(self, scrape_job: Callable):
        """Start the scheduler with the scraping job"""
        try:
            # Add job with interval trigger
            self.scheduler.add_job(
                func=scrape_job,
                trigger=IntervalTrigger(minutes=self.scrape_interval),
                id='price_scraper',
                name='Check course price',
                replace_existing=True
            )
            
            # Run immediately on start
            self.scheduler.add_job(
                func=scrape_job,
                trigger='date',
                run_date=datetime.now(),
                id='initial_scrape'
            )
            
            self.scheduler.start()
            logger.info(f"Scheduler started. Will check every {self.scrape_interval} minutes")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def shutdown(self):
        """Shutdown the scheduler gracefully"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler shutdown complete")
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        return self.scheduler.get_jobs()