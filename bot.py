<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Candle Scan</title>
  <style>
    * {
      box-sizing: border-box;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    body {
      margin: 0;
      padding: 12px;
      background: #0d1117;
      color: #f0f6fc;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
    }
    .box {
      width: 100%;
      max-width: 320px;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 14px;
      padding: 12px;
    }
    .top {
      display: flex;
      gap: 8px;
      margin-bottom: 10px;
    }
    select {
      flex: 1;
      background: #0d1117;
      color: #f0f6fc;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 8px;
      font-size: 13px;
      outline: none;
    }
    button {
      background: #238636;
      color: #fff;
      border: none;
      border-radius: 8px;
      padding: 8px 16px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
    }
    button:disabled {
      opacity: 0.5;
    }
    .candles {
      display: flex;
      align-items: flex-end;
      justify-content: center;
      gap: 5px;
      height: 34px;
      margin-bottom: 10px;
      background: #0d1117;
      border-radius: 8px;
      padding: 4px;
    }
    .c {
      width: 6px;
      border-radius: 2px;
      background: #30363d;
      transition: height 0.15s, background 0.15s;
    }
    .result {
      background: #0d1117;
      border: 1px solid #30363d;
      border-radius: 10px;
      padding: 12px;
      min-height: 76px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
    }
    .sig {
      font-size: 18px;
      font-weight: 800;
      margin-bottom: 4px;
    }
    .buy { color: #3fb950; }
    .sell { color: #f85149; }
    .wait { color: #d29922; }
    .sub {
      font-size: 12px;
      color: #8b949e;
    }
  </style>
</head>
<body>
  <div class="box">
    <div class="top">
      <select id="pair">
        <option value="AUD/USD OTC">AUD/USD OTC</option>
        <option value="EUR/USD OTC">EUR/USD OTC</option>
        <option value="GBP/USD OTC">GBP/USD OTC</option>
        <option value="USD/JPY OTC">USD/JPY OTC</option>
        <option value="AUD/CAD OTC">AUD/CAD OTC</option>
      </select>
      <button id="btn" onclick="scan()">SCAN</button>
    </div>

    <div class="candles" id="candles">
      <div class="c" style="height:14px"></div>
      <div class="c" style="height:22px"></div>
      <div class="c" style="height:18px"></div>
      <div class="c" style="height:28px"></div>
      <div class="c" style="height:20px"></div>
      <div class="c" style="height:25px"></div>
    </div>

    <div class="result" id="res">
      <div class="sub">اضغط SCAN لفحص الشموع</div>
    </div>
  </div>

  <script>
    function getCandles(n = 20) {
      let arr = [], p = 1.085;
      for (let i = 0; i < n; i++) {
        let d = (Math.random() - 0.5) * 0.002;
        let o = p, c = o + d;
        let h = Math.max(o, c) + Math.random() * 0.0012;
        let l = Math.min(o, c) - Math.random() * 0.0012;
        arr.push({ o, h, l, c });
        p = c;
      }
      return arr;
    }

    function drawCandles(arr) {
      const els = document.querySelectorAll(".c");
      const last = arr.slice(-els.length);
      els.forEach((el, i) => {
        const x = last[i];
        el.style.height = Math.min(28, Math.max(8, Math.abs(x.c - x.o) * 14000)) + "px";
        el.style.background = x.c >= x.o ? "#3fb950" : "#f85149";
      });
    }

    function analyze(arr) {
      const last = arr[arr.length - 1];
      const body = Math.abs(last.c - last.o);
      const upper = last.h - Math.max(last.o, last.c);
      const lower = Math.min(last.o, last.c) - last.l;

      let gains = 0, losses = 0;
      for (let i = arr.length - 14; i < arr.length; i++) {
        let diff = arr[i].c - arr[i - 1].c;
        if (diff >= 0) gains += diff; else losses -= diff;
      }
      const rsi = losses === 0 ? 100 : 100 - (100 / (1 + (gains / 14) / (losses / 14)));

      if ((lower > body * 1.5 && last.c >= last.o) || rsi < 32) {
        return { t: "BUY", cls: "buy", txt: "🟢 BUY (صعود)", sub: "ارتداد شمعة / تشبع بيعي" };
      }
      if ((upper > body * 1.5 && last.c <= last.o) || rsi > 68) {
        return { t: "SELL", cls: "sell", txt: "🔴 SELL (هبوط)", sub: "رفض شمعة / تشبع شرائي" };
      }
      return { t: "WAIT", cls: "wait", txt: "🟡 NO SIGNAL", sub: "لا توجد إشارة واضحة" };
    }

    function scan() {
      const btn = document.getElementById("btn");
      const res = document.getElementById("res");
      const pair = document.getElementById("pair").value;
      btn.disabled = true;
      res.innerHTML = `<div class="sub">جاري مسح ${pair}...</div>`;

      let ticks = 0;
      const timer = setInterval(() => {
        ticks++;
        const temp = getCandles(20);
        drawCandles(temp);
        if (ticks >= 5) {
          clearInterval(timer);
          const out = analyze(temp);
          res.innerHTML = `<div class="sig ${out.cls}">${out.txt}</div><div class="sub">${pair} — ${out.sub}</div>`;
          btn.disabled = false;
        }
      }, 120);
    }
  </script>
</body>
</html>
