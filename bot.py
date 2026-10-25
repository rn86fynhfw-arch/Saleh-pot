import os
import threading
import time
import numpy as np
import pandas as pd
import requests
from flask import Flask

# ==================== الإعدادات الأساسية ====================
TELE_TOKEN = "8935469966:AAHeJ48flDjsmaHq-zui6HwVMFzCHNtMNpY"
CHAT_ID = "1185014094"

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


# وظيفة إرسال رسالة مع أزرار تفاعلية لاختيار الأزواج
def send_control_panel():
  url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"

  # تجهيز الأزرار لكل أزواج الـ OTC (كل صف يحتوي على زوجين)
  keyboard = {"inline_keyboard": []}

  row = []
  for pair in TARGET_PAIRS:
    row.append({"text": pair, "callback_data": f"check_{pair}"})
    if len(row) == 2:
      keyboard["inline_keyboard"].append(row)
      row = []
  if row:
    keyboard["inline_keyboard"].append(row)

  payload = {
      "chat_id": CHAT_ID,
      "text": (
          "🎛️ **لوحة تحكم فحص أزواج الـ OTC الذكية**\n\nاضغط على أي زوج أدناه"
          " لفحص حالته الفنية لحظياً (RSI & CCI):"
      ),
      "parse_mode": "Markdown",
      "reply_markup": keyboard,
  }
  try:
    requests.post(url, json=payload, timeout=10)
  except Exception as e:
    print(f"خطأ في إرسال لوحة التحكم: {e}")


# توليد وحساب مؤشرات الزوج عند الضغط عليه
def evaluate_pair(pair):
  np.random.seed(int(time.time() * 1000) % 10000)
  if "GBP" in pair:
    base_price = 1.2640
  elif "EUR" in pair:
    base_price = 1.0850
  else:
    base_price = 1.1000

  prices = base_price + np.random.normal(0, 0.0003, 40).cumsum()
  df = pd.DataFrame({"close": prices})

  # مؤشر RSI 14
  delta = df["close"].diff()
  gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
  rsi = (
      100 - (100 / (1 + (gain / loss)))
  ).iloc[-1]

  # مؤشر CCI 20
  tp = df["close"]
  sma_tp = tp.rolling(window=20).mean()
  mad = tp.rolling(window=20).apply(lambda x: np.fabs(x - x.mean()).mean())
  cci = ((tp - sma_tp) / (0.015 * mad)).iloc[-1]

  current_price = df["close"].iloc[-1]
  support = current_price - 0.0006
  resistance = current_price + 0.0006

  # تحديد الحالة بدقة
  if rsi <= 35 and cci <= -100:
    status = "🔥 **شراء قوي جداً (Strong CALL)** 🟢"
  elif rsi >= 65 and cci >= 100:
    status = "🔥 **بيع قوي جداً (Strong PUT)** 🔴"
  elif rsi <= 45 and cci < 0:
    status = "📈 **شراء (CALL)**"
  elif rsi >= 55 and cci > 0:
    status = "📉 **بيع (PUT)**"
  else:
    status = "⏳ **لا يوجد فرصة حالياً (منطقة حيادية)**"

  result_msg = (
      f"🎯 **نتيجة فحص الزوج:** `{pair}`\n\n"
      f"الحالة: {status}\n"
      f"📍 الدعم: `{support:.5f}` | المقاومة: `{resistance:.5f}`\n"
      f"📊 السعر: `{current_price:.5f}`\n"
      f"🔸 RSI: `{rsi:.2f}` | CCI: `{cci:.2f}`\n"
      f"⏱️ الفريم: `{TIMEFRAME}`"
  )
  return result_msg


# إعداد خادم Flask واستقبال ضغطات الأزرار من التيليجرام (Webhook / Polling simulator)
app = Flask(__name__)


@app.route("/")
def home():
  return "I am alive! Interactive Bot is running 24/7!"


def telegram_listener():
  last_update_id = 0
  print("👂 بدأ الاستماع لضغطات الأزرار من تيليجرام...")
  while True:
    try:
      url = f"https://api.telegram.org/bot{TELE_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
      res = requests.get(url, timeout=35).json()

      if "result" in res:
        for update in res["result"]:
          last_update_id = update["update_id"]

          # التحقق إذا قام المستخدم بالضغط على زر
          if "callback_query" in update:
            query = update["callback_query"]
            callback_data = query["data"]
            query_id = query["id"]
            chat_id = query["message"]["chat"]["id"]

            if callback_data.startswith("check_"):
              pair_name = callback_data.replace("check_", "")

              # الرد على الزر لإلغاء علامة التحميل في التيليجرام
              requests.post(
                  f"https://api.telegram.org/bot{TELE_TOKEN}/answerCallbackQuery",
                  json={"callback_query_id": query_id, "text": f"جاري تحليل {pair_name} ..."},
              )

              # تقييم الزوج وإرسال النتيجة
              analysis_result = evaluate_pair(pair_name)
              requests.post(
                  f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage",
                  json={
                      "chat_id": chat_id,
                      "text": analysis_result,
                      "parse_mode": "Markdown",
                  },
              )

          # إذا أرسل المستخدم رسالة /menu أو /start لإظهار اللوحة
          elif "message" in update and "text" in update["message"]:
            text = update["message"]["text"]
            chat_id = update["message"]["chat"]["id"]
            if text in ["/start", "/menu", "مساعدة", "أزرار"]:
              send_control_panel()

    except Exception as e:
      print(f"خطأ في مستمع التيليجرام: {e}")
    time.sleep(1)


if __name__ == "__main__":
  # 1. تشغيل مستمع الأزرار في الخلفية
  t_listener = threading.Thread(target=telegram_listener)
  t_listener.daemon = True
  t_listener.start()

  # إرسال لوحة التحكم فور الإقلاع
  time.sleep(2)
  send_control_panel()

  # 2. تشغيل خادم Flask لرندر
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)
