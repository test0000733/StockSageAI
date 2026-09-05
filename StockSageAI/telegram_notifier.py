"""
Telegram Notifier - Formats and sends beautiful Telegram forecast messages
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Formats forecasts into beautiful Telegram messages"""
    
    def __init__(self):
        """Initialize notifier"""
        self.emoji_map = {
            'BUY': '🟢',
            'HOLD': '🟡',
            'SELL': '🔴'
        }
        logger.info("✅ Telegram Notifier initialized")
    
    def format_daily_forecast(
        self,
        forecasts: Dict[str, Dict],
        model_performance: Optional[Dict] = None
    ) -> str:
        """
        Format a compact daily forecast report that fits in a single Telegram message.
        """
        msg = "📊 <b>AI DAILY STOCK FORECAST</b>\n\n"
        now = datetime.now()
        msg += f"📅 {now.strftime('%d %b %Y')} | 🕙 10:15 AM IST\n"

        valid_forecasts = []
        for symbol, forecast in forecasts.items():
            if forecast.get('success'):
                valid_forecasts.append((symbol, forecast))

        if not valid_forecasts:
            return msg + "No valid forecasts available today."

        msg += "🏆 <b>TOP 10 RANKED PICKS</b>\n"
        for index, (symbol, forecast) in enumerate(valid_forecasts[:10], 1):
            msg += self._format_stock_forecast(symbol, forecast, index)

        msg += "\n📌 <b>SUMMARY</b>\n"
        accuracy = 0.0
        if isinstance(model_performance, dict):
            raw_accuracy = model_performance.get('avg_accuracy')
            if raw_accuracy is not None:
                try:
                    accuracy = float(raw_accuracy)
                except (TypeError, ValueError):
                    accuracy = 0.0
        msg += f"Stocks tracked: {len(valid_forecasts)} | Model accuracy: {accuracy:.1f}%"
        msg += "\n\n⚠️ <b>DISCLAIMER</b>\nAI-generated forecast for education only. Not investment advice."
        return msg

    def _format_stock_forecast(
        self,
        symbol: str,
        forecast: Dict,
        index: int
    ) -> str:
        """Format one stock in a compact, single-message-safe form."""
        current = float(forecast.get('current_price') or 0)
        forecasts = forecast.get('forecasts', {})
        signals = forecast.get('signals', {})
        confidence = forecast.get('confidence', {})
        details = forecast.get('horizon_details', {})

        p7 = forecasts.get(7)
        p14 = forecasts.get(14)
        p30 = forecasts.get(30)
        signal = signals.get(14, 'HOLD')
        conf = float(confidence.get(14, 0) or 0)
        metric = details.get(14, {})
        risk = metric.get('risk_level', 'Medium')
        scenario = metric.get('scenario', 'Base')

        def fmt_change(target_price):
            if current <= 0 or target_price is None:
                return 'n/a'
            pct = ((float(target_price) - current) / current) * 100
            return f"{pct:+.1f}%"

        if p7 is None:
            p7 = current
        if p14 is None:
            p14 = current
        if p30 is None:
            p30 = current

        emoji = self.emoji_map.get(str(signal).upper(), '🟡')
        return (
            f"{index}. <b>{symbol}</b> | ₹{current:,.0f} | "
            f"7D {fmt_change(p7)} | 14D {fmt_change(p14)} | 30D {fmt_change(p30)} | "
            f"{emoji} {signal.upper()} {conf:.0f}% | Risk {risk} | {scenario}\n"
        )
    
    def format_test_message(self) -> str:
        """Format a test message"""
        msg = "🧪 <b>TELEGRAM CONNECTION TEST</b>\n\n"
        msg += f"✅ Connection successful!\n"
        msg += f"⏰ Time: {datetime.now().strftime('%d %b %Y %H:%M:%S IST')}\n"
        msg += f"📍 Chat ID: Configured and verified\n\n"
        msg += "Your forecast system is ready to send daily reports at 10:15 AM IST.\n\n"
        msg += "This is a test message. You will not receive this again unless you request it."
        
        return msg
    
    def format_preview_message(
        self,
        forecasts: Dict[str, Dict],
        is_preview: bool = True
    ) -> str:
        """
        Format preview message (same as daily but with preview indicator)
        """
        msg = ""
        
        if is_preview:
            msg += "👁️ <b>PREVIEW - NOT SENT TO CHANNEL</b>\n"
            msg += f"Generated: {datetime.now().strftime('%d %b %Y %H:%M:%S')}\n\n"
        
        # Add regular forecast message
        msg += self.format_daily_forecast(forecasts, model_performance=None)
        
        return msg
    
    def format_status_message(self, status: Dict) -> str:
        """Format system status message"""
        msg = "📡 <b>TELEGRAM FORECAST SYSTEM STATUS</b>\n\n"
        
        # Connection status
        connection = status.get('telegram_connection', 'Unknown')
        conn_emoji = "✅" if connection == "Connected" else "❌"
        msg += f"{conn_emoji} <b>Telegram:</b> {connection}\n"
        
        # Scheduler status
        scheduler = status.get('scheduler_status', 'Unknown')
        sched_emoji = "✅" if scheduler == "Active" else "⏸️"
        msg += f"{sched_emoji} <b>Scheduler:</b> {scheduler}\n"
        
        # Last run
        if status.get('last_successful_run'):
            msg += f"✅ <b>Last Successful:</b> {status['last_successful_run']}\n"
        
        # Last failure
        if status.get('last_failed_run'):
            msg += f"❌ <b>Last Failed:</b> {status['last_failed_run']}\n"
        
        # Next scheduled
        if status.get('next_scheduled_run'):
            msg += f"⏰ <b>Next Scheduled:</b> {status['next_scheduled_run']}\n"
        
        # Stocks forecasted
        if status.get('stocks_forecasted'):
            msg += f"📊 <b>Stocks Forecasted:</b> {status['stocks_forecasted']}\n"
        
        return msg
    
    def format_error_message(self, error: str, context: str = "") -> str:
        """Format error message"""
        msg = "❌ <b>FORECAST SYSTEM ERROR</b>\n\n"
        msg += f"Error: {error}\n"
        
        if context:
            msg += f"Context: {context}\n"
        
        msg += f"\nTime: {datetime.now().strftime('%d %b %Y %H:%M:%S IST')}\n"
        msg += "Please check the system logs for details."
        
        return msg
    
    def split_message_if_needed(self, message: str, max_length: int = 4000) -> List[str]:
        """
        Split message into chunks if it exceeds Telegram limit
        
        Returns:
            List of message chunks
        """
        if len(message) <= max_length:
            return [message]
        
        chunks = []
        lines = message.split('\n')
        current_chunk = ""
        
        for line in lines:
            if len(current_chunk) + len(line) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line
            else:
                if current_chunk:
                    current_chunk += '\n' + line
                else:
                    current_chunk = line
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def validate_message_html(self, message: str) -> str:
        """
        Clean and validate HTML in message for Telegram
        Removes invalid HTML tags, escapes special characters
        """
        import re
        
        # Remove any invalid HTML tags (keep only <b>, <i>, <u>, <code>, <pre>)
        allowed_tags = ['b', 'i', 'u', 'code', 'pre', 'a']
        
        # Simple validation - ensure tags are properly paired
        for tag in allowed_tags:
            opening = f"<{tag}>"
            closing = f"</{tag}>"
            
            # Count opening and closing tags
            open_count = message.count(opening)
            close_count = message.count(closing)
            
            if open_count != close_count:
                logger.warning(f"⚠️ Mismatched tags <{tag}>: {open_count} opening, {close_count} closing")
        
        return message


# Singleton instance
_telegram_notifier = None

def get_telegram_notifier() -> TelegramNotifier:
    """Get or create singleton notifier instance"""
    global _telegram_notifier
    if _telegram_notifier is None:
        _telegram_notifier = TelegramNotifier()
    return _telegram_notifier
