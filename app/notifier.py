import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.bot = Bot(token=token)
    
    def send_message(self, message: str) -> bool:
        try:
            # Create new event loop for each message
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._async_send(message))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def _async_send(self, message: str) -> bool:
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info("Telegram alert sent successfully")
            return True
        except TelegramError as e:
            logger.error(f"Telegram API error: {e}")
            return False
    
    def format_price_alert(self, old_price: float | None, new_price: float) -> str:
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        if old_price is None:
            return f"""
🔔 <b>MONITORAMENTO INICIADO</b>

Preço atual do curso:
💰 <b>R$ {new_price:.2f}</b>

📚 Tecnologia em Ciência de Dados EAD - UNINTER
⏰ {current_time}
            """
        
        change = new_price - old_price
        change_pct = (change / old_price) * 100 if old_price != 0 else 0
        emoji = "📈" if change > 0 else "📉"
        
        return f"""
{emoji} <b>ALERTA DE MUDANÇA NO PREÇO!</b>

Preço Anterior: R$ {old_price:.2f}
Preço Atual: <b>R$ {new_price:.2f}</b>
Variação: {change:+.2f} ({change_pct:+.1f}%)

📚 Tecnologia em Ciência de Dados EAD - UNINTER
⏰ {current_time}
        """
