
# main.py
from datetime import datetime
from dashboard import fetch_macro_data, show_latest_values, analyze_liquidity, evaluate_economic_risk

print(f"🇺🇸 美國景氣追蹤儀表板 (Colab/Render 終端版) - {datetime.now().strftime('%Y-%m-%d')}")
macro_data = fetch_macro_data()
show_latest_values(macro_data)
analyze_liquidity(macro_data)
evaluate_economic_risk(macro_data)
