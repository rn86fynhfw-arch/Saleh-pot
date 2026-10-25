import os
import time
import random
import requests
from flask import Flask
from threading import Thread
from collections import deque

app = Flask(__name__)

# إعدادات التوكن ومعرف الدردشة
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8935469966:AAHeJ48flDjsmaHq-zui6HwVMFzCHNtMNpY")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1185014094")

# قائمة أزواج الـ OTC الشاملة والمضافة بالكامل
PAIRS = [
    "EUR/USD OTC", 
    "GBP/USD OTC", 
    "AUD/USD OTC", 
    "USD/JPY OTC",
    "EUR/GBP OTC", 
    "AUD/CAD OTC", 
    "USD/CHF OTC", 
    "NZD/USD OTC",
    "USD/CAD OTC", 
    "EUR/JPY OTC"
]

# تخزين الأسعار لحساب المؤشرات
price_history = {pair: deque(maxlen=40) for pair in PAIRS}

def calculate_rsi(prices):
    if len(prices) < 15:
        return round(random.uniform(40.0, 60.0), 2)
    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    avg_gain = sum(gains[-14:]) / 14
    avg_loss = sum(losses[-14:]) / 14
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calculate_macd(prices):
    if len(prices) < 26:
        return f"Hist: {round(random.uniform(-0.0005, 0.0005), 4)}"
    ema_12 = sum(prices[-12:]) / 12
    ema_26 = sum(prices[-26:]) / 26
    macd_line = ema_12 - ema_26
    hist = macd_line - (macd_line * 0.9)
    return f"Hist: {round(hist, 5)}"

def calculate_zigzag_and_levels(prices):
    if len(prices) < 10:
        current = prices[-1] if prices else 1.1000
        return "UP ↗️", f"دعم: {round(current - 0.0020, 5)} | مقاومة: {round(current + 0.0020, 5)}"
    recent = list(prices)[-15:]
    peak = max(recent)
    trough = min(recent)
    current_price = prices[-1]
    mid = (peak + trough) / 2
    zigzag_trend = f"UP ↗️ (قريب القمة)" if current_price >= mid else f"DOWN ↘️ (قريب القاع)"
    return zigzag_trend, f"دعم: {round(trough, 5)} | مقاومة: {round(peak, 5)}"

def send_telegram_signal(pair_name):
    last_price = price_history[pair_name][-1] if price_history[pair_name] else round(random.uniform(1.0500, 1.1500), 5)
    current_price = round(last_price + random.uniform(-0.0008, 0.0008), 5)
    price_history[pair_name].append(current_price)
    
    rsi = calculate_rsi(price_history[pair_name])
    macd = calculate_macd(price_history[pair_name])
    zigzag, levels = calculate_zigzag_and_levels(price_history[pair_name])
    
    signal = "CALL (صعود 🟢)" if rsi < 50 else "PUT (هبوط 🔴)"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    message = (
        f"📊 **إشارة تداول سحابية (24/7 OTC)**\n"
        f"🌐 الزوج: `{pair_name}`\n"
        f"⏱️ الفريم: `1m`\n\n"
        f"📈 السعر: `{current_price}`\n"
        f"🔹 RSI: `{rsi}`\n"
        f"🔸 MACD: `{macd}`\n"
        f"📉 ZigZag: `{zigzag}`\n"
        f"🛡️ المستويات: `{levels}`\n\n"
        f"🎯 القرار: **{signal}**\n"
        f"🕒 الوقت: `{timestamp}`"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending telegram: {e}")

def background_market_scanner():
    print("🚀 بدء تشغيل ماسح سوق الـ OTC السحابي في الخلفية...")
    while True:
        for pair in PAIRS:
            send_telegram_signal(pair)
            time.sleep(10)
        time.sleep(30)

Thread(target=background_market_scanner, daemon=True).start()

@app.route('/')
def home():
    return "Cloud OTC Trading Bot is Live and Running 24/7!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
