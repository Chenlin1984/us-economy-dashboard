from flask import Flask
from dashboard import run_dashboard
import os


app = Flask(__name__)

@app.route("/")
def home():
    result = run_dashboard()
    return result

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
