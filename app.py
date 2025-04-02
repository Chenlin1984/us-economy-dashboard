from flask import Flask, Response
from report_generator import fetch_macro_data, fetch_global_market_data, fetch_news, generate_integrated_report

app = Flask(__name__)

@app.route("/report")
def serve_report():
    macro_data = fetch_macro_data()
    market_data = fetch_global_market_data()
    news_summary = fetch_news()
    report = generate_integrated_report(macro_data, market_data, news_summary)
    return Response(report, mimetype='text/plain')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
