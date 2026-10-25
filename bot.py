import os
import requests
from flask import Flask, request, jsonify

# ==================== الإعدادات الأساسية ====================
TELE_TOKEN = "8935469966:AAHeJ48flDjsmaHq-zui6HwVMFzCHNtMNpY"
CHAT_ID = "1185014094"

app = Flask(__name__)


@app.route("/")
def home():
  return "I am alive! Webhook Bot for Pocket Option OTC is running 24/7!"


# نقطة استقبال الـ Webhook من منصتك أو شارت التحليل (Endpoint)
@app.route("/webhook", methods=["POST"])
def webhook():
  try:
    data = request.json
    if not data:
      return jsonify({"status": "error", "message": "No data received"}), 400

    # استخراج البيانات المرسلة من التنبيه
    pair = data.get("pair", "EUR/USD OTC")
    signal_type = data.get(
        "signal", "CALL"
    )  # CALL (صعود) أو PUT (هبوط)
    price = data.get("price", "0.00000")
    level = data.get("level", "0.00000")
    rsi = data.get("rsi", "0.00")
    cci = data.get("cci", "0.00")
    timeframe = data.get("timeframe", "1m")

    # تنسيق رسالة التيليجرام باحترافية ودقة تامة
    if signal_type.upper() == "CALL":
      icon_signal = "📈 الإشارة: `CALL (صعود من دعم ZigZag 🟢)`"
      title_emoji = "🎯 **إشارة شراء حية مؤكدة (OTC)!**"
    else:
      icon_signal = "📉 الإشارة: `PUT (هبوط من مقاومة ZigZag 🔴)`"
      title_emoji = "🎯 **إشارة بيع حية مؤكدة (OTC)!**"

    message = (
        f"{title_emoji}\n\n"
        f"🔹 الزوج: `{pair}`\n"
        f"{icon_signal}\n"
        f"📍 المنطقة: `{level}`\n"
        f"⏱️ الفريم: `{timeframe}`\n"
        f"📊 السعر الحالي: `{price}`\n"
        f"🔸 RSI: `{rsi}` | CCI: `{cci}`"
    )

    # إرسال الرسالة إلى تيليجرام
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=10)

    return jsonify({"status": "success", "message": "Signal sent successfully"}), 200

  except Exception as e:
    print(f"خطأ في معالجة الـ Webhook: {e}")
    return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)
