import os
import requests
from flask import Flask, jsonify
import numpy as np
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# إعدادات بوت تليجرام
TELEGRAM_BOT_TOKEN = os.environ.get("8935469966:AAHeJ48flDjsmaHq-zui6HwVMFzCHNtMNpY", "ضع_التوكن_هنا")
TELEGRAM_CHAT_ID = os.environ.get("1185014094", "ضع_الآيدي_هنا")

# قائمة أزواج OTC للخيارات الثنائية
OTC_PAIRS = [
    "EUR/USD OTC",
    "GBP/USD OTC",
    "AUD/USD OTC",
    "USD/CAD OTC",
    "USD/JPY OTC",
    "EUR/GBP OTC",
    "AUD/CAD OTC",
    "AED/CNY OTC"
]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def fetch_pair_data(pair_name):
    """
    محاكاة جلب حركة الأسعار والحجم لفريم الدقيقة لزوج محدد.
    (توليد بيانات حركية تقريبية تتفاعل مع المؤشرات)
    """
    np.random.seed()
    base_price = 1.0850 if "USD" in pair_name else 100.0
    # إنشاء حركة 30 شمعة
    price_changes = np.random.normal(0, 0.0002, 35)
    prices = list(np.cumsum(price_changes) + base_price)
    volumes = list(np.random.randint(100, 500, size=35))
    return prices, volumes

# حساب RSI
def calculate_rsi(prices, period=14):
    df = pd.DataFrame({'price': prices})
    delta = df['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# حساب MACD
def calculate_macd(prices, slow=26, fast=12, signal=9):
    df = pd.DataFrame({'price': prices})
    exp1 = df['price'].ewm(span=fast, adjust=False).mean()
    exp2 = df['price'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line
    return macd.iloc[-1], signal_line.iloc[-1], hist.iloc[-1]

# تحديد اتجاه ZigZag
def detect_zigzag(prices):
    if len(prices) < 5:
        return "NEUTRAL"
    last_few = prices[-5:]
    if last_few[-1] > last_few[-2] > last_few[-3]:
        return "UP"
    elif last_few[-1] < last_few[-2] < last_few[-3]:
        return "DOWN"
    return "NEUTRAL"

def auto_scan_and_analyze():
    """فحص جميع أزواج OTC تلقائياً على فريم الدقيقة"""
    for pair in OTC_PAIRS:
        prices, volumes = fetch_pair_data(pair)
        
        rsi = calculate_rsi(prices)
        macd, signal_line, hist = calculate_macd(prices)
        zigzag = detect_zigzag(prices)
        
        vol_avg = np.mean(volumes[-10:]) if len(volumes) >= 10 else 1
        current_vol = volumes[-1] if len(volumes) > 0 else 1
        high_volume = current_vol > (vol_avg * 1.1)

        # تحديد وجود فرصة صعود أو هبوط
        signal_result = None
        if rsi < 48 and hist > 0 and zigzag == "UP":
            signal_result = "🚀 صعود (CALL)"
        elif rsi > 52 and hist < 0 and zigzag == "DOWN":
            signal_result = "🔻 هبوط (PUT)"

        # إرسال الرسالة إلى التلجرام فور اكتشاف فرصة
        if signal_result:
            message = (
                f"📊 *إشارة تداول تلقائية (OTC)*\n"
                f"🌐 الزوج: `{pair}`\n"
                f"⏱️ الفريم: 1 دقيقة\n\n"
                f"• RSI: `{rsi:.2f}`\n"
                f"• MACD Hist: `{hist:.4f}`\n"
                f"• ZigZag: `{zigzag}`\n"
                f"• Volume: `{'مرتفع 🟢' if high_volume else 'عادي ⚪'}`\n\n"
                f"🎯 *القرار:* {signal_result}"
            )
            send_telegram_message(message)

# تشغيل الفحص التلقائي في الخلفية كل دقيقة
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(auto_scan_and_analyze, 'interval', minutes=1)
scheduler.start()

@app.route('/')
def home():
    return "Automated OTC Signal Bot is active and scanning markets every minute!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
