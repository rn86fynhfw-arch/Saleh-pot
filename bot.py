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

# القائمة الموسعة لمراقبة أزواج الـ OTC على مدار 24/7
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


# وظيفة جلب أو محاكاة بيانات الأسعار والفوليوم
def get_market_data(pair):
  np.random.seed(int(time.time() * 1000) % 10000)
  base_price = 1.1000
  prices = base_price + np.random.normal(0, 0.0004, 120).cumsum()
  volumes = np.random.randint(100, 1000, 120)
  df = pd.DataFrame({"close": prices, "volume": volumes})
  return df


# حساب المؤشرات الفنية المتقدمة
def calculate_indicators(df):
  # 1. المتوسطات الأسية (EMA 10, 20, 50, 100)
  df["EMA_10"] = df["close"].ewm(span=10, adjust=False).mean()
  df["EMA_20"] = df["close"].ewm(span=20, adjust=False).mean()
  df["EMA_50"] = df["close"].ewm(span=50, adjust=False).mean()
  df["EMA_100"] = df["close"].ewm(span=100, adjust=False).mean()

  # 2. مؤشر RSI (14)
  delta = df["close"].diff()
  gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
  rs = gain / loss
  df["RSI"] = 100 - (100 / (1 + rs))

  # 3. مؤشر MACD
  exp1 = df["close"].ewm(span=12, adjust=False).mean()
  exp2 = df["close"].ewm(span=26, adjust=False).mean()
  df["MACD"] = exp1 - exp2
  df["MACD_Signal"] = df["close"].ewm(span=9, adjust=False).mean()

  # 4. مؤشر CCI (Commodity Channel Index)
  tp = df["close"]
  sma_tp = tp.rolling(window=20).mean()
  mad = tp.rolling(window=20).apply(lambda x: np.fabs(x - x.mean()).mean())
  df["CCI"] = (tp - sma_tp) / (0.015 * mad)

  # 5. مؤشر Volume (متوسط الحجم)
  df["Volume_SMA"] = df["volume"].rolling(window=20).mean()

  return df


# محرك التحليل الاستراتيجي الشامل
def analyze_market_engine(pair):
  print(f"جاري فحص الزوج بكل المؤشرات: {pair}")
  df = get_market_data(pair)
  df = calculate_indicators(df)

  if len(df) < 110:
    return

  curr = df.iloc[-1]
  prev = df.iloc[-2]

  close_p = curr["close"]
  rsi = curr["RSI"]
  cci = curr["CCI"]
  macd = curr["MACD"]
  macd_sig = curr["MACD_Signal"]
  vol = curr["volume"]
  vol_avg = curr["Volume_SMA"]

  ema10 = curr["EMA_10"]
  ema20 = curr["EMA_20"]
  ema50 = curr["EMA_50"]
  ema100 = curr["EMA_100"]

  # شروط إشارة صعودية قوية (CALL) تقاطع EMA مع مؤشرات الزخم والسيولة
  is_bullish_trend = ema10 > ema20 > ema50
  is_bearish_trend = ema10 < ema20 < ema50

  if (
      is_bullish_trend
      and rsi < 45
      and cci < -100
      and macd > macd_sig
      and vol > vol_avg
  ):
    signal_msg = (
        f"🚀 **إشارة شراء صعودية قوية (CALL) - OTC**\n"
        f"📊 الزوج: `{pair}`\n"
        f"📈 التقاطع الإيجابي: `EMA 10/20/50`\n"
        f"📉 مؤشر RSI: `{rsi:.2f}` | CCI: `{cci:.2f}`\n"
        f"🌊 الماكد والسيولة: `إيجابية وفوليوم مرتفع`\n"
        f"💰 السعر: `{close_p:.5f}` | الفريم: `{TIMEFRAME}`"
    )
    print(signal_msg)
    send_telegram_alert(signal_msg)

  # شروط إشارة هبوطية قوية (PUT)
  elif (
      is_bearish_trend
      and rsi > 55
      and cci > 100
      and macd < macd_sig
      and vol > vol_avg
  ):
    signal_msg = (
        f"🔻 **إشارة بيع هبوطية قوية (PUT) - OTC**\n"
        f"📊 الزوج: `{pair}`\n"
        f"📉 الاتجاه الهابط: `EMA 10/20/50`\n"
        f"📈 مؤشر RSI: `{rsi:.2f}` | CCI: `{cci:.2f}`\n"
        f"🌊 الماكد والسيولة: `سلبية وفوليوم مرتفع`\n"
        f"💰 السعر: `{close_p:.5f}` | الفريم: `{TIMEFRAME}`"
    )
    print(signal_msg)
    send_telegram_alert(signal_msg)


# إعداد خادم Flask Keep-Alive
app = Flask(__name__)


@app.route("/")
def home():
  return "I am alive! Multi-Indicator Bot is running 24/7!"


def trading_loop():
  print("🚀 بدء تفعيل بوت المؤشرات المتقدمة (RSI, MACD, CCI, EMAs, Volume)")
  send_telegram_alert(
      "🚀 تم تفعيل بوت التداول الذكي بالمؤشرات المتقدمة بنجاح!"
  )
  while True:
    for pair in TARGET_PAIRS:
      try:
        analyze_market_engine(pair)
      except Exception as e:
        print(f"خطأ في فحص {pair}: {e}")
      time.sleep(3)
    time.sleep(25)


if __name__ == "__main__":
  t_bot = threading.Thread(target=trading_loop)
  t_bot.daemon = True
  t_bot.start()

  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)
