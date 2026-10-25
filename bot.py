from flask import Flask, request
import os
import requests

app = Flask(__name__)

# استدعاء التوكن والـ Chat ID من متغيرات البيئة أو وضعها مباشرة
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8935469966:AAHeJ48flDjsmaHq-zui6HwVMFzCHNtMNpY")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1185014094")

# قائمة أزواج الـ OTC المعتمدة في السيرفر
SUPPORTED_OTC_PAIRS = [
    "EUR/USD OTC", "GBP/USD OTC", "AUD/USD OTC", "USD/JPY OTC",
    "EUR/GBP OTC", "AUD/CAD OTC", "USD/CHF OTC", "NZD/USD OTC",
    "USD/CAD OTC", "EUR/JPY OTC"
]

@app.route('/')
def home():
    return "Bot Server is Alive and Running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    # التحقق مما إذا كان الطلب مجرد إشارة إيقاظ (Ping) لكي لا ينام السيرفر
    if data.get("ping") == "keep_alive":
        return {"status": "awake"}, 200

    # استخراج البيانات المرسلة من سكربت بايثون المحلي
    pair = data.get("pair", "Unknown Pair")
    signal = data.get("signal", "N/A")
    price = data.get("price", "N/A")
    timeframe = data.get("timeframe", "1m")
    rsi = data.get("rsi", "N/A")
    macd = data.get("macd", "N/A")
    zigzag = data.get("zigzag", "N/A")
    volume = data.get("volume", "N/A")
    supply_demand = data.get("supply_demand", "N/A")
    timestamp = data.get("timestamp", "")

    # التأكد أن الزوج ضمن القائمة المدعومة
    pair_status = f"🌐 الزوج: `{pair}` (OTC معتمد 🔥)" if pair in SUPPORTED_OTC_PAIRS else f"🌐 الزوج: `{pair}`"

    # صياغة رسالة تيليجرام باحترافية وتنسيق جميل
    message = (
        f"📊 **إشارة تداول تلقائية**\n"
        f"{pair_status}\n"
        f"⏱️ الفريم: `{timeframe}`\n\n"
        f"📈 السعر الحالي: `{price}`\n"
        f"🔹 مؤشر RSI: `{rsi}`\n"
        f"🔸 مؤشر MACD: `{macd}`\n"
        f"📉 مؤشر ودعم ZigZag: `{zigzag}`\n"
        f"📊 السيولة: `{volume}`\n"
        f"🛡️ المستويات:\n`{supply_demand}`\n\n"
        f"🎯 القرار: **{signal}**\n"
        f"🕒 الوقت: `{timestamp}`"
    )

    # إرسال الرسالة إلى بوت تيليجرام
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return {"status": "success"}, 200
        else:
            return {"status": "telegram_error", "details": response.text}, 400
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
