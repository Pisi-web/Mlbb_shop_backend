import os
import requests

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# =========================
# ENVIRONMENT VARIABLES
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
G2BULK_API_KEY = os.getenv("G2BULK_API_KEY")

G2BULK_URL = "https://api.g2bulk.com/v1"


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return "MLBB Shop Backend is Running!"


# =========================
# CHECK MLBB PLAYER
# =========================

@app.route("/check-player", methods=["POST"])
def check_player():

    try:

        player_id = request.form.get("player_id", "").strip()
        server_id = request.form.get("server_id", "").strip()

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


        print("G2BULK CHECK STATUS:", response.status_code)
        print("G2BULK CHECK RESPONSE:", response.text)


        if not response.ok:

            return jsonify({
                "success": False,
                "message": "G2Bulk Account Check API Error",
                "api_status": response.status_code
            }), 502


        try:

            data = response.json()

        except Exception:

            return jsonify({
                "success": False,
                "message": "G2Bulk က JSON response မပေးပါ"
            }), 502


        if data.get("valid") == "valid":

            return jsonify({

                "success": True,

                "player_id": player_id,

                "server_id": server_id,

                "name": data.get("name") or "Unknown",

                "message": "Account တွေ့ပါပြီ"

            })


        return jsonify({

            "success": False,

            "message": "Account မတွေ့ပါ"

        }), 404


    except requests.RequestException as e:

        print("G2BULK CONNECTION ERROR:", str(e))

        return jsonify({

            "success": False,

            "message": "G2Bulk API ကို ချိတ်ဆက်လို့မရပါ"

        }), 502


    except Exception as e:

        print("CHECK PLAYER ERROR:", str(e))

        return jsonify({

            "success": False,

            "message": "Server error"

        }), 500


# =========================
# ORDER
# =========================

@app.route("/order", methods=["POST"])
def order():

    try:

        # -------------------------
        # GET FORM DATA
        # -------------------------

        player_id = request.form.get(
            "player_id",
            ""
        ).strip()

        server_id = request.form.get(
            "server_id",
            ""
        ).strip()

        package = request.form.get(
            "package",
            ""
        ).strip()

        payment = request.form.get(
            "payment",
            "KPay"
        ).strip()

        screenshot = request.files.get(
            "payment_screenshot"
        )


        # -------------------------
        # CHECK ORDER DATA
        # -------------------------

        if not player_id:

            return jsonify({
                "success": False,
                "message": "Player ID မပါပါ"
            }), 400


        if not server_id:

            return jsonify({
                "success": False,
                "message": "Server ID မပါပါ"
            }), 400


        if not package:

            return jsonify({
                "success": False,
                "message": "Diamond Package မပါပါ"
            }), 400


        if not screenshot:

            return jsonify({
                "success": False,
                "message": "Payment screenshot မပါပါ"
            }), 400


        # -------------------------
        # CHECK TELEGRAM CONFIG
        # -------------------------

        if not BOT_TOKEN:

            return jsonify({
                "success": False,
                "message": "BOT_TOKEN မတွေ့ပါ"
            }), 500


        if not ADMIN_ID:

            return jsonify({
                "success": False,
                "message": "ADMIN_ID မတွေ့ပါ"
            }), 500


        print("ORDER RECEIVED")
        print("Player ID:", player_id)
        print("Server ID:", server_id)
        print("Package:", package)
        print("Payment:", payment)


        # -------------------------
        # TELEGRAM MESSAGE
        # -------------------------

        message = f"""🛒 MLBB ORDER အသစ်

👤 Player ID: {player_id}
🌐 Server ID: {server_id}
💎 Package: {package}
💳 Payment: {payment}

📸 Payment Screenshot အောက်မှာ ပို့ထားပါတယ်။
"""


        message_url = (
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        )


        message_result = requests.post(

            message_url,

            data={
                "chat_id": ADMIN_ID,
                "text": message
            },

            timeout=20
        )


        print(
            "TELEGRAM MESSAGE STATUS:",
            message_result.status_code
        )

        print(
            "TELEGRAM MESSAGE RESPONSE:",
            message_result.text
        )


        # -------------------------
        # TELEGRAM MESSAGE ERROR
        # -------------------------

        if not message_result.ok:

            return jsonify({

                "success": False,

                "message": "Telegram ကို Order information ပို့မရပါ",

                "telegram_error":
                    message_result.text

            }), 500


        # -------------------------
        # SEND SCREENSHOT
        # -------------------------

        photo_url = (
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        )


        photo_result = requests.post(

            photo_url,

            data={
                "chat_id": ADMIN_ID,
                "caption":
                    f"📸 Payment Screenshot\n"
                    f"👤 Player ID: {player_id}\n"
                    f"🌐 Server ID: {server_id}\n"
                    f"💎 Package: {package}"
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


        print(
            "TELEGRAM PHOTO STATUS:",
            photo_result.status_code
        )

        print(
            "TELEGRAM PHOTO RESPONSE:",
            photo_result.text
        )


        # -------------------------
        # PHOTO ERROR
        # -------------------------

        if not photo_result.ok:

            return jsonify({

                "success": False,

                "message":
                    "Order information ပို့ပြီးပါပြီ၊ "
                    "Screenshot ပို့မရပါ",

                "telegram_error":
                    photo_result.text

            }), 500


        # -------------------------
        # SUCCESS
        # -------------------------

        return jsonify({

            "success": True,

            "message":
                "Order နှင့် Screenshot "
                "ပို့ပြီးပါပြီ"

        })


    except requests.RequestException as e:

        print(
            "TELEGRAM CONNECTION ERROR:",
            str(e)
        )

        return jsonify({

            "success": False,

            "message":
                "Telegram Server နဲ့ ချိတ်ဆက်မရပါ"

        }), 502


    except Exception as e:

        print(
            "ORDER ERROR:",
            str(e)
        )

        return jsonify({

            "success": False,

            "message": "Server error"

        }), 500


# =========================
# RUN
# =========================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            5000
        )
    )

    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

            )
