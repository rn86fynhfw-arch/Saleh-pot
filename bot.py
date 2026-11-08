import time
import requests
import alpaca_trade_api as tradeapi

# --- 1. إعدادات الحساب والمفاتيح (ضع مفاتيحك التجريبية هنا) ---
API_KEY = "https://authx.alpaca.markets/v1/oauth2/token"
SECRET_KEY = "YOUR_ALPACA_PAPER_SECRET_KEY"
BASE_URL = "https://paper-api.alpaca.markets"  # بيئة الورقي التجريبية

# مفتاح مزود بيانات الخيارات
POLYGON_API_KEY = "YOUR_POLYGON_API_KEY"

api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')

# قائمة الأسهم المستهدفة للمراقبة
WATCH_LIST = ["AAPL", "NVDA", "TSLA", "META", "AMZN", "MSFT"]

def scan_options_flow():
    """رصد صفقات الخيارات الضخمة (Whale Sweeps) وتنفيذ الشراء آلياً"""
    print("🔍 جاري فحص تدفق سيولة عقود الخيارات في السوق الأمريكي...")
    
    for symbol in WATCH_LIST:
        try:
            url = f"https://api.polygon.io/v3/trades/options?ticker=O:{symbol}&limit=20&apiKey={POLYGON_API_KEY}"
            response = requests.get(url)
            
            if response.status_code != 200:
                continue
                
            data = response.json().get('results', [])
            
            for trade in data:
                size = trade.get('size', 0)
                price = trade.get('price', 0.0)
                total_value = size * price * 100
                contract_ticker = trade.get('ticker')
                
                # شرط السيولة الكبرى: صفقة خيارات تتجاوز 50,000 دولار
                if total_value >= 50000:
                    print(f"🚨 [تدفق سيولة / Whale Sweep] على {symbol} | القيمة: ${total_value:,.2f}")
                    
                    # التحقق من عدم تكرار فتح نفس العقد
                    positions = [p.symbol for p in api.list_positions()]
                    if contract_ticker in positions:
                        continue
                    
                    print(f"⚡ [تنفيذ آلي] شراء عقد واحد من: {contract_ticker}")
                    api.submit_order(
                        symbol=contract_ticker,
                        qty=1,
                        side='buy',
                        type='market',
                        time_in_force='gtc'
                    )
                    print(f"✅ تم فتح الصفقة بنجاح على: {contract_ticker}")
                    time.sleep(5)
                    
        except Exception as e:
            print(f"خطأ أثناء فحص خيارات {symbol}: {e}")

def manage_open_positions():
    """إدارة المراكز المفتوحة: بيع 50% عند ربح +50% وإيقاف الخسارة عند -35%"""
    try:
        positions = api.list_positions()
        for p in positions:
            symbol = p.symbol
            qty = int(p.qty)
            avg_entry = float(p.avg_entry_price)
            current_price = float(p.current_price)
            
            profit_pct = ((current_price - avg_entry) / avg_entry) * 100
            
            # هدف الربح +50% (بيع نصف العقود لتأمين رأس المال)
            if profit_pct >= 50.0 and qty >= 2:
                sell_qty = qty // 2
                print(f"🚨 [ربح +50%] بيع جزئي لـ {sell_qty} عقود من {symbol}")
                api.submit_order(symbol=symbol, qty=sell_qty, side='sell', type='market', time_in_force='gtc')
                
            # وقف الخسارة -35% (إغلاق كامل الصفقة)
            elif profit_pct <= -35.0:
                print(f"⚠️ [وقف خسارة -35%] إغلاق كامل الصفقة لـ {symbol}")
                api.close_position(symbol)
                
    except Exception as e:
        print(f"خطأ في إدارة المراكز: {e}")

def run_testing_bot():
    print("--- 🚀 بدء تشغيل بوت التجربة والاختبار الآلي ---")
    
    while True:
        try:
            clock = api.get_clock()
            if not clock.is_open:
                print("السوق الأمريكي مغلق حالياً. البوت في وضع الانتظار...")
                time.sleep(300)
                continue
                
            # 1. فحص السوق واقتناص الفرص
            scan_options_flow()
            
            # 2. إدارة المراكز المفتوحة ومتابعة الأرباح
            manage_open_positions()
            
            print("\nاكتمال دورة الفحص والإدارة. الانتظار للدورة القادمة...\n")
            time.sleep(120)  # فحص كل دقيقتين
            
        except Exception as e:
            print(f"خطأ في الحلقة الرئيسية: {e}")
            time.sleep(30)

if __name__ == "__main__":
    run_testing_bot()
