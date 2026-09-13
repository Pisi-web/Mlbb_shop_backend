import os
import requests

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# =========================
# Environment Variables
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
G2BULK_API_KEY = os.getenv("G2BULK_API_KEY")

G2BULK_URL = "https://api.g2bulk.com/v1"


# =========================
# Home
# =========================

@app.route("/")
def home():
    return "MLBB Shop Backend is Running!"


# =========================
# Check MLBB Player
# =========================

@app.route("/check-player", methods=["POST"])
def check_player():
    try:
        player_id = request.form.get("player_id")
        server_id = request.form.get("server_id")

        if not player_id or not server_id:
            return jsonify({
                "success": False,
                "message": "Player ID နဲ့ Server ID ထည့်ပါ"
            }), 400

        if not G2BULK_API_KEY:
            return jsonify({
                "success": False,
                "message": "G2BULK_API_KEY မတွေ့ပါ"
            }), 500

        # G2Bulk API request
        response = requests.post(
            f"{G2BULK_URL}/games/checkPlayerId",
            headers={
                "X-API-Key": G2BULK_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "game": "mlbb",
                "user_id": player_id,
                "server_id": server_id
            },
            timeout=20
        )

        print("G2Bulk Check:", response.text)

        # API error
        if not response.ok:
            return jsonify({
                "success": False,
                "message": "Account စစ်လို့မရပါ",
                "api_status": response.status_code
            }), 502

        data = response.json()

        # Valid account
        if data.get("valid") == "valid":
            return jsonify({
                "success": True,
                "player_id": player_id,
                "server_id": server_id,
                "name": data.get("name"),
                "message": "Account တွေ့ပါပြီ"
            })

        # Invalid account
        return jsonify({
            "success": False,
            "message": "Account မတွေ့ပါ"
        }), 404

    except requests.RequestException as e:
        print("G2Bulk connection error:", str(e))

        return jsonify({
            "success": False,
            "message": "G2Bulk API ကို ချိတ်ဆက်လို့မရပါ"
        }), 502

    except Exception as e:
        print("ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": "Server error"
        }), 500


# =========================
# Order
# =========================

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

        # Send order information to Telegram
        message_url = (
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        )

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

        # Send payment screenshot
        photo_url = (
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        )

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


# =========================
# Run
# =========================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
