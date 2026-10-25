import os
import requests
from flask import Flask, jsonify, request
import numpy as np
import pandas as pd

app = Flask(__name__)

# إعدادات بوت تليجرام (يمكنك تعديلها هنا مباشرة أو تركها تسحب من متغيرات بيئة Render)
TELEGRAM_BOT_TOKEN = os.environ.get("8935469966:AAHeJ48flDjsmaHq-zui6HwVMFzCHNtMNpY", "ضع_التوكن_هنا")
TELEGRAM_CHAT_ID = os.environ.get("1185014094", "ضع_الآيدي_هنا")

# قائمة أزواج العملات (OTC) المضافة مسبقاً
OTC_PAIRS = [
    "EUR/USD OTC",
    "GBP/USD OTC",
    "AUD/USD OTC",
    "USD/CAD OTC",
    "USD/JPY OTC",
    "EUR/GBP OTC",
    "AUD/CAD OTC",
    "AED/CNY OTC",
]


def send_telegram_message(message):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
  try:
    response = requests.post(url, json=payload)
    return response.json()
  except Exception as e:
    print(f"Error sending message: {e}")
    return None


@app.route("/")
def home():
  return (
      "Bot is active and running! Supported OTC Pairs:"
      f" {', '.join(OTC_PAIRS)}"
  )


# حساب مؤشر RSI
def calculate_rsi(prices, period=14):
  df = pd.DataFrame({"price": prices})
  delta = df["price"].diff()
  gain = delta.where(delta > 0, 0).rolling(window=period).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
  rs = gain / loss
  rsi = 100 - (100 / (1 + rs))
  return rsi.iloc[-1]


# حساب مؤشر MACD
def calculate_macd(prices, slow=26, fast=12, signal=9):
  df = pd.DataFrame({"price": prices})
  exp1 = df["price"].ewm(span=fast, adjust=False).mean()
  exp2 = df["price"].ewm(span=slow, adjust=False).mean()
  macd = exp1 - exp2
  signal_line = macd.ewm(span=signal, adjust=False).mean()
  hist = macd - signal_line
  return macd.iloc[-1], signal_line.iloc[-1], hist.iloc[-1]


# تحديد اتجاه ZigZag المبسط
def detect_zigzag(prices):
  if len(prices) < 5:
    return "NEUTRAL"
  last_few = prices[-5:]
  if last_few[-1] > last_few[-2] > last_few[-3]:
    return "UP"
  elif last_few[-1] < last_few[-2] < last_few[-3]:
    return "DOWN"
  return "NEUTRAL"


@app.route("/analyze", methods=["POST"])
def analyze():
  data = request.json
  pair = data.get("pair", "EUR/USD OTC")

  # التحقق من أن الزوج ضمن القائمة المعتمدة
  if pair not in OTC_PAIRS:
    # يمكنك السماح به أو وضعه كافتراضي
    pass

  prices = data.get("prices", [])
  volumes = data.get("volumes", [])

  if len(prices) < 30:
    return (
        jsonify({
            "status": "error",
            "message": "البيانات أقل من 30 شمعة",
        }),
        400,
    )

  rsi = calculate_rsi(prices)
  macd, signal_line, hist = calculate_macd(prices)
  zigzag = detect_zigzag(prices)

  vol_avg = np.mean(volumes[-10:]) if len(volumes) >= 10 else 1
  current_vol = volumes[-1] if len(volumes) > 0 else 1
  high_volume = current_vol > (vol_avg * 1.2)

  # منطق الإشارة بناءً على المؤشرات
  signal_result = "لا توجد فرصة ⏳"
  if rsi < 45 and hist > 0 and zigzag == "UP":
    signal_result = "🚀 صعود (CALL)"
  elif rsi > 55 and hist < 0 and zigzag == "DOWN":
    signal_result = "🔻 هبوط (PUT)"

  message = (
      f"📊 *تحليل فريم الدقيقة (OTC)*\n"
      f"🌐 الزوج: `{pair}`\n\n"
      f"• RSI: `{rsi:.2f}`\n"
      f"• MACD Hist: `{hist:.4f}`\n"
      f"• ZigZag: `{zigzag}`\n"
      f"• Volume: `{'مرتفع 🟢' if high_volume else 'عادي ⚪'}`\n\n"
      f"🎯 *النتيجة:* {signal_result}"
  )

  send_telegram_message(message)
  return jsonify({"status": "success", "pair": pair, "signal": signal_result})


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
