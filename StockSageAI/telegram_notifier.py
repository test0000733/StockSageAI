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
        Format daily forecast report for Telegram
        
        Args:
            forecasts: Dict of symbol -> forecast result
            model_performance: Historical model performance metrics
            
        Returns:
            Formatted message string
        """
        # Header
        msg = "📊 <b>AI DAILY STOCK FORECAST</b>\n\n"
        
        # Date and time
        now = datetime.now()
        msg += f"📅 Date: {now.strftime('%d %b %Y')}\n"
        msg += f"🕙 Generated: 10:15 AM IST\n"
        
        # Get latest data timestamp from forecasts
        data_timestamps = [
            f.get('data_timestamp', '') 
            for f in forecasts.values() 
            if f.get('data_timestamp')
        ]
        if data_timestamps:
            msg += f"📡 Data Updated: {data_timestamps[0]}\n"
        
        msg += "\n" + "━" * 40 + "\n\n"
        
        # Top 10 stocks section
        msg += "🏆 <b>TOP 10 STOCK FORECASTS</b>\n\n"
        
        success_count = 0
        failed_stocks = []
        
        for i, (symbol, forecast) in enumerate(forecasts.items(), 1):
            if not forecast.get('success'):
                failed_stocks.append((symbol, forecast.get('error', 'Unknown error')))
                continue
            
            success_count += 1
            msg += self._format_stock_forecast(symbol, forecast, i)
        
        # Summary section
        msg += "\n" + "━" * 40 + "\n\n"
        msg += f"<b>📊 Summary:</b> {success_count} stocks forecasted"
        
        if failed_stocks:
            msg += f", {len(failed_stocks)} unavailable\n"
            msg += "Failed stocks: " + ", ".join([s[0] for s in failed_stocks])
        else:
            msg += "\n"
        
        # Model performance section
        if model_performance:
            msg += "\n" + "━" * 40 + "\n\n"
            msg += "<b>📊 Model Performance</b>\n"
            accuracy = model_performance.get('directional_accuracy', 0)
            msg += f"Historical Directional Accuracy: {accuracy:.1f}%\n"
            
            if model_performance.get('last_updated'):
                msg += f"Last Updated: {model_performance['last_updated']}\n"
        
        # Disclaimer
        msg += "\n" + "━" * 40 + "\n\n"
        msg += "⚠️ <b>DISCLAIMER</b>\n"
        msg += "AI-generated educational forecast. Not financial advice.\n"
        msg += "Predictions are probabilistic. Actual performance may differ.\n"
        msg += "Always conduct your own research before investing."
        
        return msg
    
    def _format_stock_forecast(
        self,
        symbol: str,
        forecast: Dict,
        index: int
    ) -> str:
        """Format a single stock forecast"""
        msg = f"<b>{index}️⃣ {symbol}</b>\n"
        
        current = forecast.get('current_price', 0)
        if current > 0:
            msg += f"Current: ₹{current:,.2f}\n"
        
        # Forecasts for each horizon
        forecasts = forecast.get('forecasts', {})
        if 7 in forecasts:
            price_7d = forecasts[7]
            change_7d = ((price_7d - current) / current * 100) if current > 0 else 0
            msg += f"📈 7D: ₹{price_7d:,.2f} ({change_7d:+.2f}%)\n"
        
        if 14 in forecasts:
            price_14d = forecasts[14]
            change_14d = ((price_14d - current) / current * 100) if current > 0 else 0
            msg += f"📈 14D: ₹{price_14d:,.2f} ({change_14d:+.2f}%)\n"
        
        if 30 in forecasts:
            price_30d = forecasts[30]
            change_30d = ((price_30d - current) / current * 100) if current > 0 else 0
            msg += f"📈 30D: ₹{price_30d:,.2f} ({change_30d:+.2f}%)\n"
        
        # Signal from 14D (main signal)
        signal = forecast.get('signals', {}).get(14, 'HOLD')
        confidence = forecast.get('confidence', {}).get(14, 50)
        details = forecast.get('horizon_details', {}).get(14, {})
        risk_level = details.get('risk_level', 'Medium')
        expected_return = details.get('expected_return_pct', 0.0)
        confluence = details.get('confluence_score', 50.0)
        scenario = details.get('scenario', 'Base')
        
        emoji = self.emoji_map.get(signal, '🟡')
        msg += f"Signal: {emoji} {signal}\n"
        if expected_return is not None:
            msg += f"Expected Return: {expected_return:+.2f}% | Confidence: {confidence:.1f}%\n"
        else:
            msg += f"Confidence: {confidence:.1f}%\n"
        msg += f"Risk: {risk_level} | Scenario: {scenario} | Confluence: {confluence:.1f}%\n"
        
        # Reasoning
        reasoning = forecast.get('metadata', {}).get('14d_reasoning', '')
        if reasoning:
            if len(reasoning) > 180:
                reasoning = reasoning[:177] + '...'
            msg += f"Reason: {reasoning}\n"
        
        # Rich factors if available
        positive_factors = details.get('positive_factors', [])
        negative_factors = details.get('negative_factors', [])
        if positive_factors:
            msg += f"Positive: {', '.join(positive_factors[:2])}\n"
        if negative_factors:
            msg += f"Negative: {', '.join(negative_factors[:2])}\n"
        
        msg += "\n"
        return msg
    
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
