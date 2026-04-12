#!/usr/bin/env python3
"""
Bolt SMS - Complete OTP Bot with Country Name & 2 Buttons (1.5 sec refresh)
"""

import os
import sys
import time
import json
import logging
import re
import asyncio
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# ========== কনফিগারেশন ==========
TELEGRAM_BOT_TOKEN = "8618305528:AAF64PwFIlsw091Hbns8fGQqvwVSW6_4iCY"
GROUP_CHAT_ID = "-1001153782407"
USERNAME = "Sohaib12"
PASSWORD = "mamun1132"
BASE_URL = "http://93.190.143.35"
LOGIN_URL = f"{BASE_URL}/ints/Login"
SMS_PAGE_URL = f"{BASE_URL}/ints/agent/SMSCDRReports"

IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class CompleteOTPBot:
    def __init__(self):
        self.driver = None
        self.logged_in = False
        self.processed_otps = self._load_processed_otps()
        self.total_otps_sent = 0
        self.is_monitoring = True
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.refresh_counter = 0
        
        logger.info("🤖 Complete OTP Bot Initialized")
    
    def _load_processed_otps(self):
        try:
            if os.path.exists('processed_otps.json'):
                with open('processed_otps.json', 'r') as f:
                    data = json.load(f)
                cutoff = datetime.now() - timedelta(hours=24)
                return {k for k, v in data.items() if datetime.fromisoformat(v) > cutoff}
        except:
            pass
        return set()
    
    def _save_processed_otps(self):
        try:
            data = {otp_id: datetime.now().isoformat() for otp_id in self.processed_otps}
            with open('processed_otps.json', 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def get_country_from_phone(self, phone):
        """ফোন নম্বর থেকে কান্ট্রি নাম ও ফ্ল্যাগ বের করে"""
        phone_str = str(phone).strip()
        
        country_codes = {
            '880': ('🇧🇩', 'Bangladesh'),
            '91': ('🇮🇳', 'India'),
            '1': ('🇺🇸', 'USA'),
            '44': ('🇬🇧', 'UK'),
            '61': ('🇦🇺', 'Australia'),
            '86': ('🇨🇳', 'China'),
            '81': ('🇯🇵', 'Japan'),
            '49': ('🇩🇪', 'Germany'),
            '33': ('🇫🇷', 'France'),
            '7': ('🇷🇺', 'Russia'),
            '55': ('🇧🇷', 'Brazil'),
            '92': ('🇵🇰', 'Pakistan'),
            '94': ('🇱🇰', 'Sri Lanka'),
            '977': ('🇳🇵', 'Nepal'),
            '95': ('🇲🇲', 'Myanmar'),
            '966': ('🇸🇦', 'Saudi Arabia'),
            '971': ('🇦🇪', 'UAE'),
            '962': ('🇯🇴', 'Jordan'),
            '965': ('🇰🇼', 'Kuwait'),
            '974': ('🇶🇦', 'Qatar'),
            '968': ('🇴🇲', 'Oman'),
            '20': ('🇪🇬', 'Egypt'),
            '27': ('🇿🇦', 'South Africa'),
            '234': ('🇳🇬', 'Nigeria'),
            '254': ('🇰🇪', 'Kenya'),
            '213': ('🇩🇿', 'Algeria'),
            '212': ('🇲🇦', 'Morocco'),
        }
        
        for code, (flag, name) in country_codes.items():
            if phone_str.startswith(code):
                return f"{flag} {name}"
        
        return "🌍 Unknown"
    
    def setup_browser(self):
        try:
            chrome_options = Options()
            
            if IS_RAILWAY:
                chrome_options.add_argument('--headless=new')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--window-size=1280,720')
                chrome_options.binary_location = "/usr/bin/google-chrome"
                service = Service(executable_path="/usr/local/bin/chromedriver")
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("✅ Browser opened on Railway")
            else:
                chromedriver_path = r"C:\Users\mamun\Desktop\chromedriver.exe"
                chrome_options.add_argument('--start-maximized')
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("✅ Browser opened on Local PC")
            
            return True
        except Exception as e:
            logger.error(f"Browser error: {e}")
            return False
    
    def solve_captcha(self):
        try:
            captcha_text = self.driver.find_element(By.XPATH, "//div[contains(text(), 'What is')]").text
            match = re.search(r'(\d+)\s*\+\s*(\d+)', captcha_text)
            if match:
                result = int(match.group(1)) + int(match.group(2))
                captcha_input = self.driver.find_element(By.NAME, "capt")
                captcha_input.clear()
                captcha_input.send_keys(str(result))
                logger.info(f"✅ Captcha solved: {result}")
                return True
            return False
        except Exception as e:
            logger.error(f"Captcha error: {e}")
            return False
    
    def auto_login(self):
        try:
            logger.info("🔐 Logging in...")
            self.driver.get(LOGIN_URL)
            time.sleep(3)
            
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(USERNAME)
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            
            time.sleep(1)
            self.solve_captcha()
            
            time.sleep(1)
            form = self.driver.find_element(By.TAG_NAME, "form")
            form.submit()
            
            time.sleep(5)
            current_url = self.driver.current_url
            
            if 'agent' in current_url or 'Dashboard' in current_url:
                logger.info("✅ LOGIN SUCCESSFUL!")
                self.logged_in = True
                self.driver.get(SMS_PAGE_URL)
                time.sleep(5)
                logger.info("📱 SMS page loaded")
                return True
            else:
                logger.error("❌ Login failed!")
                return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def extract_otp(self, message):
        """OTP বের করে - ড্যাশ সহ এবং ছাড়া"""
        if not isinstance(message, str):
            message = str(message)
        
        patterns = [
            r'code[:\s]*([\d\-]{5,8})',
            r'OTP[:\s]*([\d\-]{5,8})',
            r'code\s+([\d\-]{5,8})',
            r'verification code[:\s]*([\d\-]{5,8})',
            r'\b([\d\-]{5,8})\b',
            r'\b(\d{4,6})\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def get_platform(self, message):
        """প্ল্যাটফর্ম ডিটেক্ট করে"""
        msg_lower = message.lower()
        
        if 'whatsapp' in msg_lower:
            return "💚 WhatsApp"
        elif 'telegram' in msg_lower:
            return "📨 Telegram"
        elif 'instagram' in msg_lower:
            return "📸 Instagram"
        elif 'facebook' in msg_lower or 'fb' in msg_lower:
            return "📘 Facebook"
        elif 'gmail' in msg_lower or 'google' in msg_lower:
            return "📧 Gmail"
        elif 'binance' in msg_lower or 'crypto' in msg_lower:
            return "📊 Binance"
        elif 'apple' in msg_lower or 'icloud' in msg_lower:
            return "🍎 Apple"
        elif 'microsoft' in msg_lower or 'outlook' in msg_lower:
            return "💻 Microsoft"
        elif 'amazon' in msg_lower:
            return "📦 Amazon"
        elif 'paypal' in msg_lower:
            return "💰 PayPal"
        else:
            return "📱 Other"
    
    def hide_phone(self, phone):
        """ফোন নম্বর হাইড করে"""
        phone_str = str(phone)
        if len(phone_str) >= 8:
            return phone_str[:4] + "****" + phone_str[-4:]
        elif len(phone_str) >= 4:
            return phone_str[:2] + "***" + phone_str[-2:]
        return phone_str
    
    def get_sms(self):
        try:
            rows = self.driver.find_elements(By.XPATH, "//table/tbody/tr")
            if not rows:
                return []
            
            sms_list = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 6:
                    sms_list.append({
                        'time': cols[0].text.strip(),
                        'phone': cols[2].text.strip(),
                        'client': cols[4].text.strip(),
                        'message': cols[5].text.strip()
                    })
            return sms_list
        except Exception as e:
            logger.error(f"Get SMS error: {e}")
            return []
    
    async def send_telegram(self, otp, platform, phone, time_str, is_new=True):
        """টেলিগ্রামে OTP পাঠায় - ২ টা বাটন সহ"""
        try:
            # ২ টা বাটন তৈরি (চ্যানেল + নাম্বারবট)
            keyboard = [[
                InlineKeyboardButton("📢 Main Channel", url="https://t.me/updaterange"),
                InlineKeyboardButton("🤖 Number Bot", url="https://t.me/Updateotpnew_bot")
            ]]
            
            country = self.get_country_from_phone(phone)
            hidden_phone = self.hide_phone(phone)
            
            if is_new:
                title = "🆕 NEW OTP!"
            else:
                title = "📜 Previous OTP"
            
            msg = f"""**{title}**
━━━━━━━━━━━━━━━━━━━━

📅 **Time:** `{time_str}`
📱 **Phone:** `{hidden_phone}`
🌍 **Country:** {country}
{platform}

🔐 **OTP Code:** `{otp}`

━━━━━━━━━━━━━━━━━━━━
🤖 @updaterange"""
            
            await self.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=msg,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False
    
    async def send_all_today_otps(self):
        """আজকের সব OTP পাঠায়"""
        logger.info("📤 Sending today's OTPs...")
        
        sms_list = self.get_sms()
        if not sms_list:
            await self.send_telegram("No OTPs", "📱", "N/A", datetime.now().strftime('%H:%M:%S'), False)
            return
        
        otp_count = 0
        for sms in sms_list:
            otp = self.extract_otp(sms['message'])
            if otp:
                sms_id = f"{sms['time']}_{sms['phone']}_{otp}"
                if sms_id not in self.processed_otps:
                    phone = sms['phone']
                    platform = self.get_platform(sms['message'])
                    
                    if await self.send_telegram(otp, platform, phone, sms['time'], False):
                        self.processed_otps.add(sms_id)
                        otp_count += 1
                        await asyncio.sleep(0.5)
        
        logger.info(f"✅ Sent {otp_count} OTPs")
        self._save_processed_otps()
        
        # স্টার্টআপ কমপ্লিট মেসেজ
        startup_msg = f"""✅ **Startup Complete!**
━━━━━━━━━━━━━━━━━━━━
📊 **Today's OTPs:** {otp_count}
⚡ **Check Interval:** 0.5 seconds
🔄 **Browser Refresh:** Every 1.5 seconds
⏰ **Started:** {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
🤖 @updaterange"""
        
        keyboard = [[
            InlineKeyboardButton("📢 Main Channel", url="https://t.me/updaterange"),
            InlineKeyboardButton("🤖 Number Bot", url="https://t.me/Updateotpnew_bot")
        ]]
        
        await self.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=startup_msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def monitor(self):
        """নতুন OTP মনিটর করে - 1.5 sec রিফ্রেশ"""
        logger.info("🚀 Starting OTP monitor (0.5 sec check, 1.5 sec refresh)...")
        
        await self.send_telegram(f"✅ Bot Started!\n👤 User: {USERNAME}", "📱", "N/A", datetime.now().strftime('%H:%M:%S'), False)
        
        while self.is_monitoring:
            try:
                start_time = time.time()
                
                sms_list = self.get_sms()
                
                if sms_list:
                    for sms in sms_list:
                        otp = self.extract_otp(sms['message'])
                        if otp:
                            sms_id = f"{sms['time']}_{sms['phone']}_{otp}"
                            
                            if sms_id not in self.processed_otps:
                                phone = sms['phone']
                                platform = self.get_platform(sms['message'])
                                
                                logger.info(f"🆕 NEW OTP: {otp} for {phone}")
                                
                                if await self.send_telegram(otp, platform, phone, sms['time'], True):
                                    self.processed_otps.add(sms_id)
                                    self.total_otps_sent += 1
                                    self._save_processed_otps()
                                    await asyncio.sleep(0.5)
                
                # চেক ইন্টারভাল (0.5 সেকেন্ড)
                elapsed = time.time() - start_time
                wait_time = max(0, 0.5 - elapsed)
                await asyncio.sleep(wait_time)
                
                # 1.5 সেকেন্ডে ব্রাউজার রিফ্রেশ (প্রতি 3 বার চেকে)
                self.refresh_counter += 1
                if self.refresh_counter >= 3:  # 3 * 0.5 = 1.5 সেকেন্ড
                    self.driver.refresh()
                    logger.info("🔄 Browser refreshed (1.5 seconds)")
                    self.refresh_counter = 0
                    await asyncio.sleep(1.5)
                    
            except WebDriverException as e:
                logger.error(f"Driver error: {e}")
                logger.info("Reconnecting...")
                try:
                    self.driver.quit()
                    time.sleep(3)
                    self.setup_browser()
                    self.driver.get(SMS_PAGE_URL)
                    await asyncio.sleep(5)
                except:
                    pass
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(1)
    
    async def run(self):
        print("\n" + "="*60)
        print("🤖 COMPLETE OTP BOT")
        print("="*60)
        print(f"📝 Username: {USERNAME}")
        print(f"📱 Telegram: {GROUP_CHAT_ID}")
        print(f"⚡ Check Interval: 0.5 seconds")
        print(f"🔄 Browser Refresh: Every 1.5 seconds")
        print("="*60)
        
        print("\n🔧 Setting up browser...")
        if not self.setup_browser():
            print("❌ Browser setup failed!")
            return
        
        print("\n🔐 Logging in...")
        if not self.auto_login():
            print("❌ Login failed!")
            return
        
        print("\n✅ Login successful!")
        
        print("\n📤 Forwarding today's OTPs...")
        await self.send_all_today_otps()
        
        print("\n" + "="*60)
        print("🚀 Starting OTP Monitor...")
        print("="*60)
        print("⚡ Checking every 0.5 seconds")
        print("🔄 Refreshing every 1.5 seconds")
        print("📱 Only OTP codes will be forwarded")
        print("🌍 Country name will be shown")
        print("💾 Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        await self.monitor()


async def main():
    bot = CompleteOTPBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped!")
        if bot.driver:
            bot.driver.quit()
        print(f"📊 Total OTPs sent: {bot.total_otps_sent}")
        print("👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())