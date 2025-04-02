# report_generator.py
import yfinance as yf
import pandas as pd
from datetime import datetime
from fredapi import Fred
import requests
from bs4 import BeautifulSoup

fred = Fred(api_key="your_fred_api_key")
start_date = "2000-01-01"

ASSET_NAME_MAP = {
    "QQQ": "美國科技股（[QQQ](https://www.etf.com/QQQ)）",
    "TLT": "長期美國公債（[TLT](https://www.etf.com/TLT)）",
    "GLD": "黃金（[GLD](https://www.etf.com/GLD)）",
    "SHY": "短期美國國債（[SHY](https://www.etf.com/SHY)）",
    "LQD": "投資級公司債（[LQD](https://www.etf.com/LQD)）"
}

def fetch_series(name, series_id):
    try:
        return fred.get_series(series_id, observation_start=start_date)
    except Exception as e:
        print(f"❌ 無法下載 {name} ({series_id}): {e}")
        return pd.Series(dtype='float64')

def fetch_macro_data():
    ids = {
        "10Y-2Y 殖利率差": "T10Y2Y",
        "工業生產指數": "INDPRO",
        "失業救濟初領人數": "ICSA",
        "消費者信心指數": "UMCSENT",
        "CPI": "CPIAUCNS",
        "核心CPI": "CPILFESL",
        "聯邦基金利率": "DFEDTARU",
        "美元指數": "DTWEXBGS",
        "聯準會總資產": "WALCL",
        "SOFR": "SOFR",
        "零售銷售": "RSAFS",
        "企業盈餘": "CP",
        "台幣匯率指數": "TWEXMMTH"
    }
    return {key: fetch_series(key, val) for key, val in ids.items()}

def fetch_global_market_data():
    indices = {
        "VIX": "^VIX", "10年期美債殖利率": "^TNX",
        "道瓊工業指數": "^DJI", "標普500指數": "^GSPC", "納斯達克指數": "^IXIC", "費城半導體指數": "^SOX",
        "英國FTSE 100指數": "^FTSE", "德國DAX指數": "^GDAXI", "法國CAC 40指數": "^FCHI",
        "日經225指數": "^N225", "台灣加權指數": "0050.TW", "上證指數": "000001.SS", "香港恆生指數": "^HSI",
        "布蘭特原油": "BZ=F", "黃金期貨": "GC=F", "美元指數": "DX-Y.NYB"
    }
    market_data = {}
    for name, ticker in indices.items():
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            close = data["Close"].iloc[-1]
            open_ = data["Open"].iloc[-1]
            change = (close - open_) / open_ * 100
            market_data[name] = {"收盤價": close, "漲跌幅": change}
    return market_data

def fetch_news():
    news_summary = []
    try:
        response = requests.get("https://tw.stock.yahoo.com", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.select("li.js-stream-content h3")[:5]:
            news_summary.append(item.text.strip())
    except:
        news_summary.append("⚠️ 無法擷取新聞")
    return news_summary

def classify_merrill_clock(ip, cpi):
    ip_trend = ip.pct_change(12).iloc[-1] - ip.pct_change(12).iloc[-2]
    cpi_trend = cpi.pct_change(12).iloc[-1] - cpi.pct_change(12).iloc[-2]
    if ip_trend > 0 and cpi_trend < 0:
        return "復甦期（建議資產：股票型基金）"
    elif ip_trend > 0 and cpi_trend > 0:
        return "成長期（建議資產：原物料、景氣循環類股）"
    elif ip_trend < 0 and cpi_trend > 0:
        return "過熱期（建議資產：黃金、抗通膨債券）"
    elif ip_trend < 0 and cpi_trend < 0:
        return "衰退期（建議資產：公債、短天期債券）"
    return "無法判斷目前階段"

def generate_integrated_report(macro_data, market_data, news):
    report_date = datetime.now().strftime("%Y/%m/%d")
    report = f"【{report_date} 綜合市場與經濟指標報告】\n\n"

    report += "【全球市場風險指標】\n"
    report += f"VIX恐慌指數: {market_data['VIX']['收盤價']:.2f}\n"
    report += f"10年期美債殖利率: {market_data['10年期美債殖利率']['收盤價']:.2f}%\n\n"

    report += "【美股行情】\n"
    for index in ["道瓊工業指數", "標普500指數", "納斯達克指數", "費城半導體指數"]:
        info = market_data[index]
        report += f"{index}: 收盤 {info['收盤價']:.2f}, 漲跌 {info['漲跌幅']:.2f}%\n"

    # 可擴充更多段落，這裡簡化...
    report += "\n【景氣階段判斷（美林時鐘）】\n"
    report += classify_merrill_clock(macro_data["工業生產指數"], macro_data["CPI"]) + "\n"

    report += "\n【財經新聞摘要】\n"
    for i, item in enumerate(news, 1):
        report += f"{i}. {item}\n"

    return report
