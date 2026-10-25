import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# إعدادات بوت تيليجرام (تأكد من إضافتها في Environment Variables على Render)
TELEGRAM_BOT_TOKEN = os.environ.get("8935469966:AAHeJ48flDjsmaHq-zui6HwVMFzCHNtMNpY", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.environ.get("1185014094", "YOUR_CHAT_ID_HERE")


@app.route("/")
def home():
  return "I am alive! Webhook Bot for Pocket Option OTC is running 24/7!"


# --- دوال حساب المؤشرات المتقدمة (ZigZag, MACD, Volume, Supply/Demand) ---


def calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9):
  if len(prices) < slow_period + signal_period:
    return 0.0, 0.0

  def ema(data, period):
    multiplier = 2 / (period + 1)
    ema_vals = [sum(data[:period]) / period]
    for price in data[period:]:
      ema_vals.append((price - ema_vals[-1]) * multiplier + ema_vals[-1])
    return ema_vals

  # حساب مبسط لـ MACD Line والـ Signal Line
  fast_ema = ema(prices, fast_period)
  slow_ema = ema(prices, slow_period)
  min_len = min(len(fast_ema), len(slow_ema))

  macd_line = [
      f - s for f, s in zip(fast_ema[-min_len:], slow_ema[-min_len:])
  ]
  if len(macd_line) < signal_period:
    return round(macd_line[-1], 5), 0.0

  signal_line = ema(macd_line, signal_period)
  return round(macd_line[-1], 5), round(signal_line[-1], 5)


def detect_zigzag_and_levels(highs, lows, closes):
  """تقدير مبسط لحركة الزجزاج ومناطق العرض والطلب (الدعم والمقاومة اللحظية)"""
  if not highs or not lows:
    return "غير متوفر", "دعم/مقاومة قريبة"

  recent_high = max(highs[-10:])
  recent_low = min(lows[-10:])

  # تحديد اتجاه الزجزاج التقريبي بناءً على القمم والقيعان الأخيرة
  zigzag_trend = (
      "صاعد ↗️" if closes[-1] > closes[-5] else "هابط ↘️"
  )
  supply_demand = (
      f"طلب: {round(recent_low, 5)} | عرض: {round(recent_high, 5)}"
  )

  return zigzag_trend, supply_demand


@app.route("/webhook", methods=["POST"])
def webhook():
  try:
    data = request.json
    if not data:
      return jsonify({"status": "error", "message": "No data received"}), 400

    # استقبال البيانات الأساسية
    pair = data.get("pair", "EUR/USD OTC")
    signal = data.get("signal", "CALL")
    price = data.get("price", "N/A")
    timeframe = data.get("timeframe", "1m")
    timestamp = data.get("timestamp", "")

    # استقبال أو حساب المؤشرات المتقدمة (MACD, Volume, ZigZag, Supply/Demand)
    volume = data.get("volume", "عالي / طبيعي")
    
    # إذا تم إرسال تاريخ أسعار، نحسب MACD والزجزاج برمجياً، أو نستقبلها جاهزة
    raw_prices = data.get("prices", [])
    raw_highs = data.get("highs", [])
    raw_lows = data.get("lows", [])

    if raw_prices and len(raw_prices) > 30:
      macd_val, signal_val = calculate_macd(raw_prices)
      macd_str = f"MACD: {macd_val} | Signal: {signal_val}"
    else:
      macd_str = data.get("macd", "مستقر (متوافق مع الاتجاه)")

    if raw_highs and raw_lows and raw_prices:
      zigzag_trend, supply_demand = detect_zigzag_and_levels(
          raw_highs, raw_lows, raw_prices
      )
    else:
      zigzag_trend = data.get("zigzag", "اتجاه لحظي نشط")
      supply_demand = data.get("supply_demand", "مناطق قوية قيد الاختبار")

    # صياغة رسالة تيليجرام تفصيلية واحترافية
    message = (
        f"🚨 **تنبيه إشارة تداول احترافية** 🚨\n\n"
        f"📊 **الزوج:** {pair}\n"
        f"⏱ **الفريم:** {timeframe}\n"
        f"🎯 **الإتجاه:** {signal}\n"
        f"💰 **السعر الحالي:** {price}\n\n"
        f"📈 **مؤشر MACD:** {macd_str}\n"
        f"📉 **مؤشر الزجزاج (ZigZag):** {zigzag_trend}\n"
        f"📦 **حجم التداول (Volume):** {volume}\n"
        f"🛡 **مناطق العرض والطلب:** {supply_demand}\n\n"
        f"⏰ **الوقت:** {timestamp}"
    )

    # إرسال الرسالة إلى تيليجرام
    send_to_telegram(message)

    return jsonify({"status": "success", "message": "Signal sent with indicators"}), 200

  except Exception as e:
    return jsonify({"status": "error", "message": str(e)}), 500


def send_to_telegram(text):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": text,
      "parse_mode": "Markdown",
  }
  try:
    requests.post(url, json=payload, timeout=5)
  except Exception as e:
    print(f"Error sending to telegram: {e}")


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
