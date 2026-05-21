from twilio.rest import Client
import yfinance as yf
import time
from datetime import datetime
import streamlit as st

class PriceAlertManager:
    def __init__(self):
        # Initialize Twilio client
        self.client = Client(st.secrets["twilio_account_sid"], st.secrets["twilio_auth_token"])
        self.alerts = {}
        
    def add_alert(self, symbol, target_price, phone_number, alert_type="both"):
        """
        Add a new price alert
        alert_type: "above", "below", or "both"
        """
        if symbol not in self.alerts:
            self.alerts[symbol] = []
        
        self.alerts[symbol].append({
            "target_price": float(target_price),
            "phone_number": phone_number,
            "alert_type": alert_type,
            "created_at": datetime.now(),
            "triggered": False
        })
        
    def check_alerts(self):
        """Check all active alerts against current prices"""
        for symbol in self.alerts:
            try:
                current_price = yf.Ticker(symbol).info['regularMarketPrice']
                
                for alert in self.alerts[symbol]:
                    if alert["triggered"]:
                        continue
                        
                    target_price = alert["target_price"]
                    alert_type = alert["alert_type"]
                    
                    if (alert_type in ["above", "both"] and current_price >= target_price) or \
                       (alert_type in ["below", "both"] and current_price <= target_price):
                        self.send_alert(
                            alert["phone_number"],
                            symbol,
                            current_price,
                            target_price
                        )
                        alert["triggered"] = True
                        
            except Exception as e:
                st.error(f"Error checking price for {symbol}: {str(e)}")
                
    def send_alert(self, phone_number, symbol, current_price, target_price):
        """Send SMS alert via Twilio"""
        try:
            message = self.client.messages.create(
                body=f"🔔 Price Alert for {symbol}!\n" \
                     f"Current Price: ₹{current_price:,.2f}\n" \
                     f"Target Price: ₹{target_price:,.2f}",
                from_=st.secrets["twilio_phone_number"],
                to=phone_number
            )
            return True
        except Exception as e:
            st.error(f"Error sending alert: {str(e)}")
            return False
