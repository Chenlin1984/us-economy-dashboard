#@title 美國景氣追蹤
# 美國景氣追蹤完整程式碼（模組化版本 + Colab 優化）
# =============================================
# 每一個區段改寫成可重用函式，支援 Google Colab 終端顯示版本。

# --- 安裝與引入套件 ---
!pip install yfinance fredapi scikit-learn --quiet > log.txt
!apt-get -y install fonts-noto-cjk > log.txt

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from datetime import datetime
from fredapi import Fred
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

rcParams['font.sans-serif'] = ['Noto Sans CJK TC']
rcParams['axes.unicode_minus'] = False

# --- FRED 設定 ---
fred = Fred(api_key="9ff6e83238521e65e71d5be717e2dc27")
start_date = "2000-01-01"

# 🔴 打分用變數
liquidity_score = 0


def fetch_series(name, series_id):
    try:
        return fred.get_series(series_id, observation_start=start_date)
    except Exception as e:
        print(f"❌ 無法下載 {name}（{series_id}）：{e}")
        return pd.Series(dtype='float64')

def fetch_macro_data():
    macro = {
        "10Y-2Y 殖利率差": fetch_series("10Y-2Y 殖利率差", "T10Y2Y"),
        "工業生產指數": fetch_series("工業生產指數", "INDPRO"),
        "失業救濟初領人數": fetch_series("失業救濟初領人數", "ICSA"),
        "消費者信心指數": fetch_series("消費者信心指數", "UMCSENT"),
        "CPI": fetch_series("CPI", "CPIAUCNS"),
        "核心CPI": fetch_series("核心CPI", "CPILFESL"),
        "聯邦基金利率（目標上限）": fetch_series("聯邦基金利率（目標上限）", "DFEDTARU"),
        "美元指數（DXY）": fetch_series("美元指數（DXY）", "DTWEXBGS"),
        "NBER 衰退期間": fetch_series("NBER 衰退期間", "USREC"),
        "聯準會總資產（WALCL）": fetch_series("聯準會總資產", "WALCL"),
        "SOFR": fetch_series("SOFR 利率", "SOFR"),
        "零售銷售": fetch_series("零售銷售", "RSAFS"),
        "企業盈餘(總體)": fetch_series("企業盈餘", "CP"),
        "2年期公債利率": fetch_series("2年期公債利率", "DGS2"),
        "台幣匯率指數": fetch_series("台幣加權匯率指數", "TWEXMMTH")
    }
    return macro

def show_latest_values(data):
    print("\n📌 最新經濟指標總覽")
    for key, series in data.items():
        if not series.empty:
            latest_val = series.dropna().iloc[-1]
            print(f"{key}: 最新值 = {latest_val:.2f}")

def analyze_liquidity(macro_data):
    global liquidity_score
    print("\n💧 流動性判斷雷達：SOFR + WALCL")
    sofr_series = macro_data["SOFR"].dropna()
    walcl = macro_data["聯準會總資產（WALCL）"].dropna()
    allocation = {}

    if not sofr_series.empty and not walcl.empty:
        sofr_trend = sofr_series.iloc[-1] - sofr_series.iloc[-5]
        walcl_trend = walcl.iloc[-1] - walcl.iloc[-5]
        print(f"SOFR 最新值：{sofr_series.iloc[-1]:.2f}，近 5 日變化：{sofr_trend:.4f}")
        print(f"WALCL 最新值：{walcl.iloc[-1]:,.2f}，近 5 週變化：{walcl_trend:,.2f}")

        if sofr_trend < -0.02 and walcl_trend > 0:
            print("✅ 聯準會釋放流動性，市場資金寬鬆")
            allocation = {"QQQ": 0.4, "TLT": 0.3, "GLD": 0.3}
        elif sofr_trend > 0.02 and walcl_trend < 0:
            print("⚠️ 流動性緊縮，保守配置")
            allocation = {"SHY": 0.5, "LQD": 0.3, "GLD": 0.2}
        elif walcl_trend < 0 or sofr_trend > 0:
            print("⚠️ 市場偏緊，建議防禦配置")
            allocation = {"LQD": 0.4, "GLD": 0.3, "TLT": 0.3}
        elif walcl_trend > 0 or sofr_trend < 0:
            print("📈 市場偏鬆，建議積極配置")
            allocation = {"QQQ": 0.5, "GLD": 0.3, "TLT": 0.2}
        else:
            print("➡️ 市場中性，建議均衡配置")
            allocation = {"QQQ": 0.3, "TLT": 0.3, "GLD": 0.2, "LQD": 0.2}

        if walcl_trend > 0:
            print("🟢 聯準會開始擴表：總資產上升 → 偏寬鬆訊號")
        else:
            print("🔴 聯準會未擴表：總資產未增加或下降")
            liquidity_score -= 1

    print("\n💱 美元利率與台幣匯率觀察")
    fed_rate = macro_data["聯邦基金利率（目標上限）"].dropna()
    twd_index = macro_data["台幣匯率指數"].dropna()
    if not fed_rate.empty and not twd_index.empty:
        fed_diff = fed_rate.iloc[-1] - fed_rate.iloc[-5]
        twd_diff = twd_index.iloc[-1] - twd_index.iloc[-5]
        print(f"聯邦基金利率近5期變化：{fed_diff:.2f}")
        print(f"台幣加權匯率指數近5期變化：{twd_diff:.2f}")

        if fed_diff > 0 and twd_diff > 0:
            print("🔴 美元利率上升 & 台幣貶值 → 資金可能外流")
        elif fed_diff < 0 and twd_diff < 0:
            print("🟢 美元利率下降 & 台幣升值 → 資金回流機會")
        else:
            print("⚠️ 匯率與利率變動分歧，需持續觀察")

    print("\n📊 實質利率分析")
    cpi = macro_data["CPI"].pct_change(12).dropna()
    if not fed_rate.empty and not cpi.empty:
        common_index = fed_rate.index.intersection(cpi.index)
        real_rate = fed_rate[common_index] / 100 - cpi[common_index]
        latest_real_rate = real_rate.iloc[-1]
        print(f"實質利率（最新值）= {fed_rate.iloc[-1]:.2f}% - {cpi.iloc[-1]*100:.2f}% = {latest_real_rate*100:.2f}%")
        if latest_real_rate < 0:
            print("🟢 資金成本偏低，有利風險資產與黃金")
        elif latest_real_rate > 0.5:
            print("🔴 資金成本偏高，風險偏好下降")
        else:
            print("🟡 中性利率，市場資金中性")
    else:
        print("❌ 無法計算實質利率（資料不足）")

    return allocation
def evaluate_economic_risk(macro_data):
    print("\n🚨 經濟衰退預警評估")

    score = 0
    warnings = []

    if macro_data["10Y-2Y 殖利率差"].iloc[-1] < 0:
        score -= 1
        warnings.append("殖利率倒掛")

    if macro_data["消費者信心指數"].iloc[-1] < 70:
        score -= 1
        warnings.append("消費者信心低")

    if macro_data["工業生產指數"].pct_change().iloc[-1] < 0:
        score -= 1
        warnings.append("工業生產轉弱")

    if macro_data["失業救濟初領人數"].iloc[-1] > 300000:
        score -= 1
        warnings.append("失業救濟高於 30 萬")

    if macro_data["零售銷售"].pct_change().iloc[-1] < 0:
        score -= 1
        warnings.append("零售銷售月減")

    if macro_data["企業盈餘(總體)"].pct_change(4).iloc[-1] < 0:
        score -= 1
        warnings.append("企業盈餘年減")

    if macro_data["核心CPI"].pct_change(12).iloc[-1] > 0.03:
        score -= 1
        warnings.append("核心CPI > 3%")

    if macro_data["美元指數（DXY）"].iloc[-1] > 120:
        score -= 1
        warnings.append("美元偏強")

    print(f"🔎 經濟紅燈評分：{score} 分")
    if warnings:
        print("⚠️ 異常指標：", "、".join(warnings))

    # 打分解釋
    if score <= -5:
        print("🔴 景氣紅燈：高衰退風險")
    elif score <= -3:
        print("🟠 景氣偏弱：中度風險")
    elif score <= -1:
        print("🟡 景氣不穩：需留意")
    else:
        print("🟢 景氣穩定：無明顯衰退訊號")
def classify_merrill_clock(ip_series, cpi_series):
    ip_yoy = ip_series.pct_change(12)
    cpi_yoy = cpi_series.pct_change(12)
    if len(ip_yoy.dropna()) < 2 or len(cpi_yoy.dropna()) < 2:
        return "資料不足", (None, None)

    ip_trend = "上升" if ip_yoy.iloc[-1] > ip_yoy.iloc[-2] else "下降"
    cpi_trend = "上升" if cpi_yoy.iloc[-1] > cpi_yoy.iloc[-2] else "下降"

    if ip_trend == "上升" and cpi_trend == "下降":
        return "復甦期（建議：股票）", (1, 0)
    elif ip_trend == "上升" and cpi_trend == "上升":
        return "成長期（建議：原物料）", (1, 1)
    elif ip_trend == "下降" and cpi_trend == "上升":
        return "過熱期（建議：黃金、通膨債）", (0, 1)
    elif ip_trend == "下降" and cpi_trend == "下降":
        return "衰退期（建議：公債）", (0, 0)
    else:
        return "資料混亂，無法判斷", (None, None)


def generate_summary(macro_data, score, allocation):
    print("\n🧾 ChatGPT 風格月報摘要")
    ip = macro_data["工業生產指數"]
    cpi = macro_data["CPI"]
    fed = macro_data["聯邦基金利率（目標上限）"].dropna()
    cpi_yoy = cpi.pct_change(12).dropna()
    common_index = fed.index.intersection(cpi_yoy.index)
    real_rate = fed[common_index]/100 - cpi_yoy[common_index]
    latest_real = real_rate.iloc[-1]
    phase, _ = classify_merrill_clock(ip, cpi)
    print(f"1️⃣ 景氣階段：{phase}")
    print(f"2️⃣ CPI YoY: {cpi_yoy.iloc[-1]*100:.2f}%；實質利率: {latest_real*100:.2f}%")
    print(f"3️⃣ 經濟紅燈評分：{score}")
    print("4️⃣ 建議資產配置：")
    for asset, ratio in allocation.items():
        print(f"   - {asset}: {ratio*100:.1f}%")

# 主功能模組
# ========================
def run_dashboard():
    print("🇺🇸 美國景氣追蹤儀表板 (Render 版)")
    macro_data = fetch_macro_data()
    show_latest_values(macro_data)
    analyze_liquidity(macro_data)
    evaluate_economic_risk(macro_data)

# ========================
# Web Service 入口
# ========================
@app.route("/")
def home():
    run_dashboard()
    return "✅ 美國景氣追蹤儀表板已執行完成"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
