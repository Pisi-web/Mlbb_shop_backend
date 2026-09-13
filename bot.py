import os
import time
import uuid
import threading
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
# ORDERS
# =========================

orders = {}
orders_lock = threading.Lock()


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return "MLBB Shop Backend is Running!"


# =========================
# CHECK PLAYER
# =========================

@app.route("/check-player", methods=["POST"])
def check_player():

    try:

        player_id = request.form.get(
            "player_id",
            ""
        ).strip()

        server_id = request.form.get(
            "server_id",
            ""
        ).strip()

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

        print(
            "G2BULK CHECK STATUS:",
            response.status_code
        )

        print(
            "G2BULK CHECK RESPONSE:",
            response.text
        )

        if not response.ok:

            return jsonify({
                "success": False,
                "message": "G2Bulk Account Check API Error"
            }), 502

        data = response.json()

        if data.get("valid") == "valid":

            return jsonify({

                "success": True,

                "player_id": player_id,

                "server_id": server_id,

                "name": data.get(
                    "name",
                    "Unknown"
                ),

                "message": "Account တွေ့ပါပြီ"

            })

        return jsonify({

            "success": False,

            "message": "Account မတွေ့ပါ"

        }), 404

    except requests.RequestException as e:

        print(
            "G2BULK CONNECTION ERROR:",
            str(e)
        )

        return jsonify({

            "success": False,

            "message":
                "G2Bulk API ကို ချိတ်ဆက်လို့မရပါ"

        }), 502

    except Exception as e:

        print(
            "CHECK PLAYER ERROR:",
            str(e)
        )

        return jsonify({

            "success": False,

            "message": "Server error"

        }), 500


# =========================
# CREATE ORDER
# =========================

@app.route("/order", methods=["POST"])
def create_order():

    try:

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
        # CHECK DATA
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
                "message":
                    "Payment screenshot မပါပါ"
            }), 400

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

        # -------------------------
        # CREATE ORDER ID
        # -------------------------

        order_id = str(
            uuid.uuid4()
        )[:8].upper()

        with orders_lock:

            orders[order_id] = {

                "status": "pending",

                "player_id": player_id,

                "server_id": server_id,

                "package": package

            }

        print(
            "=============================="
        )

        print(
            "ORDER RECEIVED:",
            order_id
        )

        print(
            "Player ID:",
            player_id
        )

        print(
            "Server ID:",
            server_id
        )

        print(
            "Package:",
            package
        )

        # -------------------------
        # TELEGRAM MESSAGE
        # -------------------------

        message = f"""🛒 MLBB ORDER အသစ်

🆔 Order ID: {order_id}

👤 Player ID: {player_id}
🌐 Server ID: {server_id}
💎 Package: {package}
💳 Payment: {payment}

⏳ Customer ကို 1–15 မိနစ်ခန့် စောင့်ဆိုင်းပေးရန် ပြောထားပါတယ်။

Top Up ပြီးသွားရင် ဒီ Bot ထဲမှာ

done

လို့ပို့ပါ။
"""

        message_url = (
            f"https://api.telegram.org/"
            f"bot{BOT_TOKEN}/sendMessage"
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

        if not message_result.ok:

            with orders_lock:
                orders.pop(
                    order_id,
                    None
                )

            return jsonify({

                "success": False,

                "message":
                    "Telegram ကို Order information ပို့မရပါ",

                "telegram_error":
                    message_result.text

            }), 500

        # -------------------------
        # SEND SCREENSHOT
        # -------------------------

        photo_url = (
            f"https://api.telegram.org/"
            f"bot{BOT_TOKEN}/sendPhoto"
        )

        photo_result = requests.post(

            photo_url,

            data={

                "chat_id": ADMIN_ID,

                "caption":
                    f"""📸 Payment Screenshot

🆔 Order ID: {order_id}

👤 Player ID: {player_id}
🌐 Server ID: {server_id}
💎 Package: {package}
"""

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

        if not photo_result.ok:

            return jsonify({

                "success": False,

                "message":
                    "Order ပို့ပြီးပါပြီ၊ Screenshot ပို့မရပါ",

                "telegram_error":
                    photo_result.text

            }), 500

        # -------------------------
        # SUCCESS
        # -------------------------

        return jsonify({

            "success": True,

            "order_id": order_id,

            "status": "pending",

            "message":
                "Order လက်ခံပြီးပါပြီ"

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
# ORDER STATUS
# =========================

@app.route(
    "/order-status/<order_id>",
    methods=["GET"]
)
def order_status(order_id):

    with orders_lock:

        order = orders.get(
            order_id
        )

    if not order:

        return jsonify({

            "success": False,

            "message": "Order မတွေ့ပါ"

        }), 404

    return jsonify({

        "success": True,

        "order_id": order_id,

        "status":
            order["status"]

    })


# =========================
# TELEGRAM LISTENER
# =========================

def telegram_listener():

    print(
        "Telegram listener started"
    )

    offset = None

    # Remove webhook

    try:

        requests.get(

            f"https://api.telegram.org/"
            f"bot{BOT_TOKEN}/deleteWebhook",

            params={
                "drop_pending_updates": False
            },

            timeout=10

        )

        print(
            "Telegram webhook removed"
        )

    except Exception as e:

        print(
            "Webhook error:",
            str(e)
        )

    # -------------------------
    # LISTEN
    # -------------------------

    while True:

        try:

            params = {
                "timeout": 20
            }

            if offset is not None:

                params["offset"] = offset

            response = requests.get(

                f"https://api.telegram.org/"
                f"bot{BOT_TOKEN}/getUpdates",

                params=params,

                timeout=30

            )

            data = response.json()

            if not data.get("ok"):

                print(
                    "Telegram getUpdates error:",
                    data
                )

                time.sleep(5)

                continue

            for update in data.get(
                "result",
                []
            ):

                offset = (
                    update["update_id"]
                    + 1
                )

                message = update.get(
                    "message"
                )

                if not message:
                    continue

                chat = message.get(
                    "chat",
                    {}
                )

                chat_id = str(
                    chat.get(
                        "id",
                        ""
                    )
                )

                text = message.get(
                    "text",
                    ""
                ).strip().lower()

                # Only ADMIN can use done

                if chat_id != str(
                    ADMIN_ID
                ):
                    continue

                # -------------------------
                # DONE
                # -------------------------

                if text == "done":

                    done_order_id = None

                    with orders_lock:

                        pending_orders = [

                            oid

                            for oid,
                            order_data
                            in orders.items()

                            if order_data[
                                "status"
                            ] == "pending"

                        ]

                        if pending_orders:

                            done_order_id = (
                                pending_orders[0]
                            )

                            orders[
                                done_order_id
                            ][
                                "status"
                            ] = "done"

                    if done_order_id:

                        print(
                            "ORDER DONE:",
                            done_order_id
                        )

                        requests.post(

                            f"https://api.telegram.org/"
                            f"bot{BOT_TOKEN}/sendMessage",

                            data={

                                "chat_id":
                                    ADMIN_ID,

                                "text":
                                    f"""✅ Order Done

🆔 Order ID:
{done_order_id}

Customer website မှာ
အောင်မြင်ပါပြီ 🎉
လို့ ပြောင်းသွားပါမယ်။
"""

                            },

                            timeout=10

                        )

                    else:

                        requests.post(

                            f"https://api.telegram.org/"
                            f"bot{BOT_TOKEN}/sendMessage",

                            data={

                                "chat_id":
                                    ADMIN_ID,

                                "text":
                                    "❌ Pending Order မရှိပါ။"

                            },

                            timeout=10

                        )

        except Exception as e:

            print(
                "TELEGRAM LISTENER ERROR:",
                str(e)
            )

            time.sleep(5)


# =========================
# START TELEGRAM
# =========================

if BOT_TOKEN:

    thread = threading.Thread(

        target=telegram_listener,

        daemon=True

    )

    thread.start()

else:

    print(
        "BOT_TOKEN မရှိပါ။"
    )


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
