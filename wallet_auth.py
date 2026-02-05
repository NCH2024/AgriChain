from datetime import datetime
from functools import wraps
from flask import app, request, session, redirect, url_for, jsonify
from eth_account.messages import encode_defunct
from eth_account import Account
import secrets
import uuid

# Collection name in MongoDB: wallet_users (wallet -> role)
USERS_COL = "wallet_users"

def require_wallet(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "wallet" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def _make_nonce_message():
    # IMPORTANT: MetaMask will display this message; keep it ASCII/UTF-8 printable
    # Use UUID + random token
    return f"AgriChain Login\nNonce: {uuid.uuid4()}\nToken: {secrets.token_hex(16)}"

def register_wallet_routes(app, db):
    @app.route("/api/nonce", methods=["GET", "POST"])
    def api_nonce():
        msg = _make_nonce_message()
        session["login_nonce_message"] = msg
        return jsonify({"message": msg})

    @app.route("/api/verify", methods=["POST"])
    def api_verify():
        data = request.get_json(force=True) or {}
        address = (data.get("address") or "").strip()
        signature = (data.get("signature") or "").strip()

        msg = session.get("login_nonce_message")
        if not msg:
            return jsonify({"ok": False, "error": "Missing nonce. Please click Login again."}), 400

        if not address or not signature:
            return jsonify({"ok": False, "error": "Missing address/signature"}), 400

        try:
            message = encode_defunct(text=msg)
            recovered = Account.recover_message(message, signature=signature)
        except Exception as e:
            return jsonify({"ok": False, "error": f"Signature verify failed: {str(e)}"}), 400

        if recovered.lower() != address.lower():
            return jsonify({"ok": False, "error": "Signature does not match wallet"}), 400

        # Signed OK -> check registration
        user = db.db[USERS_COL].find_one({"wallet": address.lower()})
        session["wallet_pending"] = address  # for register_role
        if not user:
            # Not registered yet
            return jsonify({"ok": True, "need_register": True})

        # Registered -> set session wallet + role
        # Nếu ví đã được đăng ký trước đó
        session["wallet"] = address
        session["role"] = user.get("role", "farmer")
        session["username"] = user.get("username", "Người dùng ẩn danh") # Lấy tên từ DB nạp vào Session
        session.pop("wallet_pending", None)
        return jsonify({"ok": True, "need_register": False, "role": session["role"]})

    @app.route("/api/register_role", methods=["POST"])
    def api_register_role():
        data = request.get_json(force=True) or {}
        role = (data.get("role") or "").strip().lower()
        username = (data.get("username") or "").strip() # Lấy username từ request

        if role not in ("farmer", "factory"):
            return jsonify({"ok": False, "error": "Vai trò không hợp lệ"}), 400
        if not username:
            return jsonify({"ok": False, "error": "Tên người dùng không được để trống"}), 400

        address = session.get("wallet_pending")
        if not address:
            return jsonify({"ok": False, "error": "Phiên làm việc hết hạn. Hãy đăng nhập lại."}), 400

        # Lưu cả wallet, role và username vào database
        db.db[USERS_COL].update_one(
            {"wallet": address.lower()},
            {"$set": {
                "wallet": address.lower(), 
                "role": role, 
                "username": username,
                "created_at": datetime.now() # Thêm ngày tham gia cho Profile
            }},
            upsert=True
        )

        session["wallet"] = address
        session["role"] = role
        session["username"] = username # Lưu vào session để dùng toàn trang
        session.pop("wallet_pending", None)

        return jsonify({"ok": True, "role": role})