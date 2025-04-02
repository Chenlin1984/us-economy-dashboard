# 美國景氣追蹤完整程式碼（Flask + Render 版本）
# =============================================
# 將主流程包裝為 Web API 形式，讓 Render 可從網址呼叫

# --- 安裝與引入套件 ---
# 注意：Render 平台會自動根據 requirements.txt 安裝套件，不需要 !pip 或 !apt-get

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from datetime import datetime
from fredapi import Fred
from flask import Flask

rcParams['font.sans-serif'] = ['Noto Sans CJK TC']
rcParams['axes.unicode_minus'] = False

# --- FRED 設定 ---
fred = Fred(api_key="9ff6e83238521e65e71d5be717e2dc27")
start_date = "2000-01-01"

# 🔴 打分用變數
liquidity_score = 0

app = Flask(__name__)

# ========================
# 功能模組
# ========================

def fetch_series(name, series_id):
    try:
        return fred.get_series(series_id, observation_start=start_date)
    except Exception as e:
        print(f"❌ 無法下載 {name}（{series_id}）：{e}")
        return pd.Series(dtype='float64')

def fetch_macro_data():
    macro_data = {
        "10Y-2Y 殖利率差": fetch_series("10Y-2Y 殖利率差", "T10Y2Y"),
        "工業生產指數": fetch_series("工業生產指數", "INDPRO"),
        "失業救濟初領人數": fetch_series("失業救濟初領人數", "ICSA"),
        "消費者信心指數": fetch_series("消費者信心指數", "UMCSENT"),
        "CPI": fetch_series("CPI", "CPIAUCNS"),
        "核心CPI": fetch_series("核心CPI", "CPILFESL"),
        "聯邦基金利率（目標上限）": fetch_series("聯邦基金利率", "DFEDTARU"),
        "美元指數（DXY）": fetch_series("美元指數", "DTWEXBGS"),
        "NBER 衰退期間": fetch_series("NBER 衰退期間", "USREC"),
        "聯準會總資產（WALCL）": fetch_series("聯準會總資產", "WALCL"),
        "SOFR": fetch_series("SOFR 利率", "SOFR"),
        "零售銷售": fetch_series("零售銷售", "RSAFS"),
        "企業盈餘(總體)": fetch_series("企業盈餘", "CP"),
        "2年期公債利率": fetch_series("2年期公債利率", "DGS2"),
        "VIX 恐慌指數": yf.download("^VIX", start=start_date)["Close"]
    }
    return macro_data

def show_latest_values(data):
    print("\n📌 最新經濟指標總覽")
    for key, series in data.items():
        if not series.empty:
            latest_val = series.dropna().iloc[-1]
            print(f"{key}: 最新值 = {latest_val:.2f}")

def evaluate_economic_risk(data):
    print("\n🚦 經濟衰退預警（紅燈打分系統）")
    score = 0
    reasons = []

    if data['消費者信心指數'].iloc[-1] < 70:
        score -= 1
        reasons.append("消費信心過低")

    if data['10Y-2Y 殖利率差'].iloc[-1] < 0:
        score -= 1
        reasons.append("殖利率倒掛")

    if data['工業生產指數'].pct_change().iloc[-1] < 0:
        score -= 1
        reasons.append("工業生產轉弱")

    if data['失業救濟初領人數'].iloc[-1] > 300000:
        score -= 1
        reasons.append("初領失業人數偏高")

    if data['核心CPI'].pct_change(12).dropna().iloc[-1] > 0.03:
        score -= 1
        reasons.append("核心通膨壓力仍高")

    if data['美元指數（DXY）'].iloc[-1] > 120:
        score -= 1
        reasons.append("美元偏強")

    if data['零售銷售'].pct_change().dropna().iloc[-1] < 0:
        score -= 1
        reasons.append("零售銷售轉弱")

    if data['企業盈餘(總體)'].pct_change(4).dropna().iloc[-1] < 0:
        score -= 1
        reasons.append("企業盈餘年減")

    if data['聯準會總資產（WALCL）'].iloc[-1] < data['聯準會總資產（WALCL）'].iloc[-5]:
        score -= 1
        reasons.append("聯準會未擴表")

    if data['VIX 恐慌指數'].dropna().iloc[-1] > 25:
        score -= 1
        reasons.append("VIX 恐慌指數過高")

    if score <= -5:
        level = "🔴 景氣紅燈（高風險）"
    elif score <= -3:
        level = "🟠 景氣偏弱"
    elif score <= -1:
        level = "🟡 景氣不穩"
    else:
        level = "🟢 景氣穩定"

    print(f"{level}｜打分 = {score}")
    if reasons:
        print("⚠️ 因素：" + "、".join(reasons))

def analyze_liquidity(data):
    print("\n💧 流動性判斷雷達：SOFR + WALCL")
    sofr = data['SOFR'].dropna()
    walcl = data['聯準會總資產（WALCL）'].dropna()
    if sofr.empty or walcl.empty:
        print("❌ 缺少 SOFR 或 WALCL 資料")
        return
    sofr_diff = sofr.iloc[-1] - sofr.iloc[-5]
    walcl_diff = walcl.iloc[-1] - walcl.iloc[-5]
    print(f"SOFR 最新值：{sofr.iloc[-1]:.2f}，近 5 日變化：{sofr_diff:.4f}")
    print(f"WALCL 最新值：{walcl.iloc[-1]:,.2f}，近 5 週變化：{walcl_diff:,.2f}")

    if sofr_diff > 0.02 and walcl_diff < 0:
        print("⚠️ 流動性緊縮，保守配置")
    elif sofr_diff < -0.02 and walcl_diff > 0:
        print("✅ 流動性寬鬆，偏多配置")
    else:
        print("📊 中性狀態，維持均衡配置")

# ========================
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
