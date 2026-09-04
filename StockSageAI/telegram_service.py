"""
Telegram Service - Handles secure Telegram API communication
Production-ready Telegram bot integration for daily stock forecasts
"""

import os
import logging
import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
import time

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TelegramService:
    """Secure Telegram API wrapper for forecast notifications"""
    
    def __init__(self):
        """Initialize Telegram service with credentials from environment"""
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        # Validate credentials
        if not self.bot_token or not self.chat_id:
            logger.error("❌ Telegram credentials not configured in .env file")
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        
        logger.info("✅ Telegram Service initialized")
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> Tuple[bool, Optional[str]]:
        """
        Send a message to Telegram chat with retry logic
        
        Args:
            text: Message text
            parse_mode: HTML or Markdown
            
        Returns:
            Tuple of (success: bool, message_id: Optional[str])
        """
        if not text or len(text.strip()) == 0:
            logger.error("❌ Cannot send empty message")
            return False, None
        
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/sendMessage",
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get('ok'):
                    message_id = data.get('result', {}).get('message_id')
                    logger.info(f"✅ Message sent successfully (ID: {message_id})")
                    return True, str(message_id)
                else:
                    error = data.get('description', 'Unknown error')
                    logger.error(f"❌ Telegram API error: {error}")
                    return False, None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️ Timeout on attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"🌐 Connection error on attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
            except requests.exceptions.HTTPError as e:
                if response.status_code == 400:
                    logger.error(f"❌ Bad request (400): Invalid chat ID or message format")
                    return False, None
                elif response.status_code == 401:
                    logger.error(f"❌ Unauthorized (401): Invalid bot token")
                    return False, None
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get('Retry-After', 5))
                    logger.warning(f"⚠️ Rate limited. Waiting {retry_after}s...")
                    if attempt < self.max_retries - 1:
                        time.sleep(retry_after)
                else:
                    logger.error(f"❌ HTTP error {response.status_code}: {str(e)}")
                    return False, None
                    
            except json.JSONDecodeError:
                logger.error("❌ Invalid JSON response from Telegram API")
                return False, None
                
            except Exception as e:
                logger.error(f"❌ Unexpected error: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        logger.error(f"❌ Failed to send message after {self.max_retries} attempts")
        return False, None
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test Telegram connection status
        
        Returns:
            Tuple of (is_connected: bool, status_message: str)
        """
        try:
            response = requests.get(
                f"{self.base_url}/getMe",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('ok'):
                bot_name = data.get('result', {}).get('username', 'Unknown')
                msg = f"✅ Connected to bot @{bot_name}"
                logger.info(msg)
                return True, msg
            else:
                msg = f"❌ Bot authentication failed: {data.get('description')}"
                logger.error(msg)
                return False, msg
                
        except requests.exceptions.Timeout:
            msg = "❌ Connection timeout - Telegram API is slow or unreachable"
            logger.error(msg)
            return False, msg
            
        except requests.exceptions.ConnectionError:
            msg = "❌ Cannot connect to Telegram API - check internet connection"
            logger.error(msg)
            return False, msg
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                msg = "❌ Invalid bot token"
            else:
                msg = f"❌ HTTP Error {e.response.status_code}"
            logger.error(msg)
            return False, msg
            
        except Exception as e:
            msg = f"❌ Unexpected error: {str(e)}"
            logger.error(msg)
            return False, msg
    
    def validate_chat_id(self) -> bool:
        """Check if chat ID is accessible"""
        try:
            response = requests.get(
                f"{self.base_url}/getChat",
                params={"chat_id": self.chat_id},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('ok'):
                logger.info(f"✅ Chat ID {self.chat_id} is valid")
                return True
            else:
                logger.error(f"❌ Chat ID validation failed: {data.get('description')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error validating chat ID: {str(e)}")
            return False
    
    def send_long_message(self, text: str, chunk_size: int = 4000) -> Tuple[bool, List[Optional[str]]]:
        """
        Send long message by splitting into chunks (Telegram limit: 4096 chars)
        
        Args:
            text: Long message text
            chunk_size: Characters per chunk
            
        Returns:
            Tuple of (all_sent: bool, message_ids: List[str])
        """
        if len(text) <= chunk_size:
            return self.send_message(text)
        
        message_ids = []
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        for i, chunk in enumerate(chunks, 1):
            success, msg_id = self.send_message(chunk)
            if not success:
                logger.error(f"❌ Failed to send chunk {i}/{len(chunks)}")
                return False, message_ids
            message_ids.append(msg_id)
            
            # Small delay between chunks to avoid rate limiting
            if i < len(chunks):
                time.sleep(0.5)
        
        logger.info(f"✅ Successfully sent {len(chunks)} message chunks")
        return True, message_ids
    
    def delete_message(self, message_id: str) -> bool:
        """Delete a previously sent message"""
        try:
            response = requests.post(
                f"{self.base_url}/deleteMessage",
                json={"chat_id": self.chat_id, "message_id": message_id},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('ok'):
                logger.info(f"✅ Message {message_id} deleted")
                return True
            else:
                logger.error(f"❌ Failed to delete message: {data.get('description')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting message: {str(e)}")
            return False
    
    def get_chat_info(self) -> Optional[Dict]:
        """Get information about the chat"""
        try:
            response = requests.get(
                f"{self.base_url}/getChat",
                params={"chat_id": self.chat_id},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('ok'):
                return data.get('result')
            else:
                logger.error(f"❌ Failed to get chat info: {data.get('description')}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting chat info: {str(e)}")
            return None


# Singleton instance
_telegram_service = None

def get_telegram_service() -> TelegramService:
    """Get or create singleton Telegram service instance"""
    global _telegram_service
    if _telegram_service is None:
        try:
            _telegram_service = TelegramService()
        except ValueError as e:
            logger.error(f"Failed to initialize Telegram service: {e}")
            return None
    return _telegram_service
