# main.py
from dashboard import app

# ✅ Render 會從這裡啟動 Web Service
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(__import__('os').environ.get("PORT", 10000)))
