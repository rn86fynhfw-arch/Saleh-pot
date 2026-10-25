import os
import threading
import time
import numpy as np
import pandas as pd
import requests
from flask import Flask

# ==================== الإعدادات الأساسية ====================
TELEGRAM_BOT_TOKEN = "8935469966:AAHeJ48flDjsmaHq-zui6HwVMFzCHNtMNpY"
TELEGRAM_CHAT_ID = "1185014094"

# القائمة الموسعة للمراقبة 24/7 قائمة أزواج الـ OTC
TARGET_PAIRS = [
    "EUR/USD OTC",
    "GBP/USD OTC",
    "AUD/USD OTC",
    "EUR/JPY OTC",
    "GBP/JPY OTC",
    "AUD/CAD OTC",
    "USD/CHF OTC",
    "NZD/USD OTC",
    "AED/CNY OTC",
]

TIMEFRAME = "1m"


# وظيفة إرسال تنبيهات تيليجرام
def send_telegram_alert(message):
  try:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    requests.post(url, json=payload, timeout=10)
  except Exception as e:
    print(f"خطأ في إرسال التيليجرام: {e}")


# محرك التحليل الأساسي
def analyze_market_engine(pair):
  # هنا كود التحليل الفني والمنطق الخاص بك
  print(f"جاري فحص الزوج: {pair}")


# إعداد خادم Flask Keep-Alive
app = Flask(__name__)


@app.route("/")
def home():
  return "I am alive! Bot is running 24/7!"


def trading_loop():
  print("🚀 بدء تفعيل بوت إشارات الأزوج المباشرة")
  send_telegram_alert("🚀 تفعيل بوت إشارات الأزوج المباشرة")
  while True:
    for pair in TARGET_PAIRS:
      try:
        analyze_market_engine(pair)
      except Exception:
        pass
      time.sleep(3)
    time.sleep(45)


if __name__ == "__main__":
  # 1. تشغيل بوت التداول في الخلفية عبر Thread مستقل
  t_bot = threading.Thread(target=trading_loop)
  t_bot.daemon = True
  t_bot.start()

  # 2. تشغيل خادم Flask Keep-Alive في الخيط الرئيسي لمنصة Render
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)
