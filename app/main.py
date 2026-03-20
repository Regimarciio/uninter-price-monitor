#!/usr/bin/env python3
import os
import sys
import logging
import signal
import time
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from scraper import UninterScraper
from notifier import TelegramNotifier
from scheduler import PriceScheduler

# Try to load .env from multiple possible locations
env_paths = [
    Path('/app/.env'),  # Docker path
    Path('/home/server/uninter-price-monitor/.env'),  # Absolute path
    Path.cwd() / '.env',  # Current working directory
    Path(__file__).parent.parent / '.env',  # Parent of app directory
]

env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"Loaded .env from: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    # Try current directory as last resort
    load_dotenv()
    print("Tried to load .env from current directory")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class PriceMonitor:
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.uninter_url = os.getenv('UNINTER_URL')
        self.scrape_interval = int(os.getenv('SCRAPE_INTERVAL_MINUTES', 30))
        
        # Debug: print environment variables (without exposing full token)
        logger.info("Checking environment variables:")
        logger.info(f"TELEGRAM_BOT_TOKEN: {'Set' if self.telegram_token else 'Not set'}")
        logger.info(f"TELEGRAM_CHAT_ID: {self.telegram_chat_id}")
        logger.info(f"UNINTER_URL: {self.uninter_url}")
        logger.info(f"SCRAPE_INTERVAL: {self.scrape_interval}")
        
        if not all([self.telegram_token, self.telegram_chat_id, self.uninter_url]):
            logger.error("Missing required environment variables!")
            logger.error("Please check your .env file and ensure it contains:")
            logger.error("  TELEGRAM_BOT_TOKEN=your_token")
            logger.error("  TELEGRAM_CHAT_ID=your_chat_id")
            logger.error("  UNINTER_URL=https://www.uninter.com/curso/tecnologia-em-ciencia-de-dados-ead")
            sys.exit(1)
        
        # Initialize components
        self.db = DatabaseManager()
        self.scraper = UninterScraper(self.uninter_url)
        self.notifier = TelegramNotifier(self.telegram_token, self.telegram_chat_id)
        self.scheduler = PriceScheduler(self.scrape_interval)
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def check_price(self):
        """Main function to check price and handle changes"""
        logger.info("=" * 50)
        logger.info(f"Price check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Get current price
            price, source = self.scraper.get_price()
            
            if price is None:
                logger.error("Failed to retrieve price")
                return
            
            logger.info(f"Current price: R$ {price:.2f} (source: {source})")
            
            # Check if price changed
            changed, old_price = self.db.price_changed(price)
            
            if changed:
                logger.info(f"Price change detected! Old: {old_price}, New: {price}")
                
                # Save new price
                self.db.save_price(price)
                
                # Send alert
                message = self.notifier.format_price_alert(old_price, price)
                self.notifier.send_message(message)
                
                # Log price history
                history = self.db.get_price_history(3)
                logger.info("Recent price history:")
                for record in history:
                    logger.info(f"  {record['timestamp']}: R$ {record['price']:.2f}")
            else:
                logger.info("Price unchanged")
                
        except Exception as e:
            logger.error(f"Error during price check: {e}", exc_info=True)
        
        logger.info("=" * 50)
    
    def run(self):
        """Start the monitoring service"""
        logger.info("=" * 50)
        logger.info("UNINTER COURSE PRICE MONITOR")
        logger.info(f"URL: {self.uninter_url}")
        logger.info(f"Check interval: {self.scrape_interval} minutes")
        logger.info("=" * 50)
        
        # Send startup notification
        startup_msg = f"""
🚀 <b>MONITOR DE PREÇOS INICIADO</b>

Curso: Tecnologia em Ciência de Dados EAD
Instituição: UNINTER
Frequência: A cada {self.scrape_interval} minutos

Aguardando mudanças de preço...
        """
        self.notifier.send_message(startup_msg)
        
        # Start scheduler
        self.scheduler.start(self.check_price)
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.shutdown()
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.running = False
        self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down...")
        self.scheduler.shutdown()
        self.notifier.send_message("🛑 Monitor de Preços Encerrado")
        sys.exit(0)

def main():
    """Entry point"""
    monitor = PriceMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
