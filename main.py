from flask import Flask
from dashboard import run_dashboard

app = Flask(__name__)

@app.route("/")
def home():
    result = run_dashboard()
    return result

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
