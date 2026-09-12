import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")


@app.route("/")
def home():
    return "MLBB Shop Backend is Running!"


@app.route("/order", methods=["POST"])
def order():
    try:
        player_id = request.form.get("player_id")
        server_id = request.form.get("server_id")
        package = request.form.get("package")
        payment = request.form.get("payment")
        screenshot = request.files.get("payment_screenshot")

        if not player_id or not server_id or not package:
            return jsonify({
                "success": False,
                "message": "Order information မပြည့်စုံပါ"
            }), 400

        if not screenshot:
            return jsonify({
                "success": False,
                "message": "Payment screenshot မပါပါ"
            }), 400

        if not BOT_TOKEN or not ADMIN_ID:
            return jsonify({
                "success": False,
                "message": "Bot configuration မပြည့်စုံပါ"
            }), 500

        message = f"""🛒 MLBB ORDER အသစ်

👤 Player ID: {player_id}
🌐 Server ID: {server_id}
💎 Package: {package}
💳 Payment: {payment}

📸 Payment Screenshot အောက်မှာ ပို့ထားပါတယ်။
"""

        message_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        message_result = requests.post(
            message_url,
            data={
                "chat_id": ADMIN_ID,
                "text": message
            },
            timeout=15
        )

        print("Telegram message:", message_result.text)

        if not message_result.ok:
            return jsonify({
                "success": False,
                "message": "Order information ပို့မရပါ"
            }), 500

        photo_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

        photo_result = requests.post(
            photo_url,
            data={
                "chat_id": ADMIN_ID,
                "caption": "📸 Payment Screenshot"
            },
            files={
                "photo": (
                    screenshot.filename,
                    screenshot.stream,
                    screenshot.mimetype
                )
            },
            timeout=30
        )

        print("Telegram photo:", photo_result.text)

        if not photo_result.ok:
            return jsonify({
                "success": False,
                "message": "Screenshot ပို့မရပါ"
            }), 500

        return jsonify({
            "success": True,
            "message": "Order နှင့် Screenshot ပို့ပြီးပါပြီ"
        })

    except Exception as e:
        print("ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": "Server error"
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
