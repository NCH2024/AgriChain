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
    """Decorator: Yêu cầu người dùng phải kết nối ví (đăng nhập) mới được truy cập route này."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "wallet" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def _make_nonce_message():
    """Tạo thông điệp ngẫu nhiên (Nonce) để ví ký tên. Giúp chống tấn công phát lại (Replay Attack)."""
    # QUAN TRỌNG: MetaMask sẽ hiển thị chuỗi này cho người dùng đọc trước khi ký.
    # Sử dụng UUID và Token ngẫu nhiên để đảm bảo tính duy nhất mỗi lần đăng nhập.
    return f"AgriChain Login\nNonce: {uuid.uuid4()}\nToken: {secrets.token_hex(16)}"

def register_wallet_routes(app, db):
    """Đăng ký các API routes liên quan đến xác thực ví (Web3 Login)."""
    
    @app.route("/api/nonce", methods=["GET", "POST"])
    def api_nonce():
        """API Bước 1: Tạo chuỗi ngẫu nhiên (Nonce) gửi về Frontend để ví người dùng ký."""
        msg = _make_nonce_message()
        session["login_nonce_message"] = msg # Lưu tạm vào session để đối chiếu ở bước sau
        return jsonify({"message": msg})

    @app.route("/api/verify", methods=["POST"])
    def api_verify():
        """API Bước 2: Xác thực chữ ký (Signature) gửi từ Frontend."""
        data = request.get_json(force=True) or {}
        address = (data.get("address") or "").strip()
        signature = (data.get("signature") or "").strip()

        # 1. Kiểm tra xem server có đang chờ xác thực không (có Nonce trong session không)
        msg = session.get("login_nonce_message")
        if not msg:
            return jsonify({"ok": False, "error": "Missing nonce. Please click Login again."}), 400

        if not address or not signature:
            return jsonify({"ok": False, "error": "Missing address/signature"}), 400

        try:
            # 2. Giải mã chữ ký: Khôi phục địa chỉ ví từ (Message gốc + Chữ ký)
            # Đây là thuật toán mật mã học (Elliptic Curve Recover)
            message = encode_defunct(text=msg)
            recovered = Account.recover_message(message, signature=signature)
        except Exception as e:
            return jsonify({"ok": False, "error": f"Signature verify failed: {str(e)}"}), 400

        # 3. So sánh địa chỉ khôi phục được với địa chỉ ví người dùng gửi lên
        if recovered.lower() != address.lower():
            return jsonify({"ok": False, "error": "Signature does not match wallet"}), 400

        # 4. Nếu chữ ký đúng -> Kiểm tra xem ví này đã đăng ký tài khoản trong DB chưa
        user = db.db[USERS_COL].find_one({"wallet": address.lower()})
        
        # Lưu tạm ví vào session chờ đăng ký (nếu chưa có tài khoản)
        session["wallet_pending"] = address  
        
        if not user:
            # Chưa đăng ký -> Trả về flag để Frontend hiện form nhập Tên & Vai trò
            return jsonify({"ok": True, "need_register": True})

        # 5. Nếu đã đăng ký -> Thiết lập phiên đăng nhập (Session) ngay lập tức
        session["wallet"] = address
        session["role"] = user.get("role", "farmer")
        session["username"] = user.get("username", "Người dùng ẩn danh") # Lấy tên từ DB nạp vào Session
        session.pop("wallet_pending", None) # Xoá biến tạm
        return jsonify({"ok": True, "need_register": False, "role": session["role"]})

    @app.route("/api/register_role", methods=["POST"])
    def api_register_role():
        """API Bước 3: Hoàn tất đăng ký (Lưu Role + Username) cho người dùng mới."""
        data = request.get_json(force=True) or {}
        role = (data.get("role") or "").strip().lower()
        username = (data.get("username") or "").strip() # Lấy username từ request

        if role not in ("farmer", "factory"):
            return jsonify({"ok": False, "error": "Vai trò không hợp lệ"}), 400
        if not username:
            return jsonify({"ok": False, "error": "Tên người dùng không được để trống"}), 400

        # Lấy ví đang chờ đăng ký từ session (đảm bảo đã qua bước verify signature)
        address = session.get("wallet_pending")
        if not address:
            return jsonify({"ok": False, "error": "Phiên làm việc hết hạn. Hãy đăng nhập lại."}), 400

        # Thực hiện lưu (Upsert) thông tin vào MongoDB
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

        # Thiết lập session chính thức sau khi lưu thành công
        session["wallet"] = address
        session["role"] = role
        session["username"] = username # Lưu vào session để dùng toàn trang
        session.pop("wallet_pending", None)

        return jsonify({"ok": True, "role": role})