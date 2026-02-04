from flask import Flask, render_template, request, session, redirect, url_for, send_file
from database import DatabaseManager
from wallet_auth import register_wallet_routes, require_wallet
from config import CRONOS_TESTNET_EXPLORER
import web3_connect
import datetime
import qrcode
import io
import os 
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = "nch2024@AgriChainSecretKey" 

# Cấu hình Cloudinary
cloudinary.config(
    cloud_name = "dkvckvi5y",
    api_key = "265113723281414",
    api_secret = "GNvV5vKorCPiiRPyIc1soaXJ-JY"
)

db = DatabaseManager()
register_wallet_routes(app, db)

@app.template_filter('ctime')
def timectime(s):
    try:
        if s is None:
            return ""
        return datetime.datetime.fromtimestamp(int(s)).strftime('%d/%m/%Y %H:%M')
    except Exception:
        return ""

@app.route('/generate_qr/<batch_code>')
def generate_qr(batch_code):
    link = f"{request.host_url}trace/{batch_code}"
    img = qrcode.make(link)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/api/login_wallet', methods=['POST'])
def api_login_wallet():
    data = request.get_json(force=True)
    wallet_address = data.get('wallet')
    
    if not wallet_address:
        return {"ok": False, "error": "Địa chỉ ví không hợp lệ"}, 400
    
    session['wallet'] = wallet_address
    if 'role' not in session:
        session['role'] = 'farmer' 
    
    print(f"✅ Đã đăng nhập ví: {wallet_address}")
    return {"ok": True}

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@require_wallet
def dashboard():
    wallet = session.get("wallet")
    role = session.get("role")

    all_chain = web3_connect.lay_danh_sach_blockchain() or []
    my_products = [p for p in all_chain if str(p.get("owner","")).lower() == str(wallet).lower()]

    for p in my_products:
        try:
            ts = int(p.get("timestamp", 0) or 0)
            p["timestamp_fmt"] = datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
        except Exception:
            p["timestamp_fmt"] = ""

    thong_ke = {}
    for p in my_products:
        loai = p.get('product_type', 'Chưa xác định')
        thong_ke[loai] = thong_ke.get(loai, 0) + 1
    labels = list(thong_ke.keys())
    data = list(thong_ke.values())

    return render_template(
        'dashboard.html',
        wallet=wallet,
        role=role,
        session=session,
        products=my_products,
        chart_labels=labels,
        chart_data=data,
        contract_address=getattr(web3_connect, "CONTRACT_ADDRESS", ""),
        contract_abi=getattr(web3_connect, "CONTRACT_ABI", []),
        explorer_base=CRONOS_TESTNET_EXPLORER
    )

@app.route("/api/tx_record", methods=["POST"])
@require_wallet
def api_tx_record():
    data = request.get_json(force=True)
    wallet = session["wallet"]

    if data.get("wallet", "").lower() != wallet.lower():
        return {"ok": False, "error": "Wallet mismatch"}, 403

    db.db.user_txs.insert_one({
        "wallet": wallet,
        "batch_code": data.get("batch_code"),
        "tx_hash": data.get("tx_hash"),
        "action": data.get("action", ""),
        "image_id": data.get("image_id"), 
        "timestamp": int(data.get("timestamp", 0) or 0),
        "contract": getattr(web3_connect, "CONTRACT_ADDRESS", ""),
        "saved_at": datetime.datetime.utcnow()
    })
    return {"ok": True}

@app.route("/products")
@require_wallet
def products():
    wallet = session["wallet"]
    batch_codes = db.db.user_txs.find({"wallet": wallet}).distinct("batch_code")
    all_chain = web3_connect.lay_danh_sach_blockchain() or []

    latest = []
    for code in batch_codes:
        items = [x for x in all_chain if x.get("batch_code") == code]
        if items:
            p = items[0]
            try:
                ts = int(p.get("timestamp", 0) or 0)
                p["timestamp_fmt"] = datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
            except Exception:
                p["timestamp_fmt"] = ""
            latest.append(p)

    return render_template("products.html", wallet=wallet, products=latest)

@app.route("/products/<batch_code>")
@require_wallet
def product_detail(batch_code):
    wallet = session["wallet"]
    owned = db.db.user_txs.find_one({"wallet": wallet, "batch_code": batch_code})
    if not owned:
        return "Forbidden", 403

    # 1. Lấy lịch sử Blockchain (Sắp xếp Cũ -> Mới)
    history = web3_connect.tim_kiem_blockchain(batch_code) or []
    try:
        history = sorted(history, key=lambda x: int(x.get("timestamp", 0) or 0))
    except Exception:
        pass

    # 2. Lấy Transaction Local để map (Lấy hết, không cần điều kiện có ảnh)
    local_txs = list(db.db.user_txs.find({"batch_code": batch_code}))

    # 3. Vòng lặp ghép thông tin (Ảnh + Tx Hash)
    for h in history:
        try:
            ts = int(h.get("timestamp", 0) or 0)
            h["timestamp_fmt"] = datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
            
            h_action = h.get("action", "").strip()
            
            found_img = None
            found_tx = None
            found_index = -1
            
            # Tìm trong local_txs xem có cái nào khớp Action không
            for i, tx in enumerate(local_txs):
                tx_action = tx.get("action", "").strip()
                if tx_action == h_action:
                    found_img = tx.get("image_id")
                    found_tx = tx.get("tx_hash") # Lấy thêm Tx Hash
                    found_index = i
                    break 
            
            # Gắn dữ liệu tìm được vào h
            if found_index != -1:
                if found_img:
                    h["image_id"] = found_img
                if found_tx:
                    h["tx_hash"] = found_tx # Gắn Hash vào đây
                
                # Xoá để không trùng lặp
                local_txs.pop(found_index)
                
        except Exception as e:
            print("Lỗi map dữ liệu:", e)
            h["timestamp_fmt"] = ""

    # Danh sách Tx bên phải (Vẫn giữ để hiển thị list raw nếu cần)
    txs = list(db.db.user_txs.find(
        {"wallet": wallet, "batch_code": batch_code},
        {"_id": 0}
    ).sort("timestamp", -1))

    return render_template(
        "product_detail.html",
        wallet=wallet,
        batch_code=batch_code,
        history=history,
        txs=txs,
        explorer_base=CRONOS_TESTNET_EXPLORER,
        contract_address=getattr(web3_connect, "CONTRACT_ADDRESS", "")
    )

@app.route("/trace/<batch_code>")
def trace_public(batch_code):
    # 1. Lấy lịch sử từ Blockchain
    history = web3_connect.tim_kiem_blockchain(batch_code) or []
    try:
        history = sorted(history, key=lambda x: int(x.get("timestamp", 0) or 0))
    except Exception:
        pass
    
    # 2. Lấy dữ liệu từ Database (bao gồm cả Ảnh và Tx Hash)
    # Lọc lấy các bản ghi có action để ghép
    local_txs = list(db.db.user_txs.find({"batch_code": batch_code}))

    # 3. Vòng lặp ghép thông tin (Ảnh + Tx Hash)
    for h in history:
        try:
            ts = int(h.get("timestamp", 0) or 0)
            h["timestamp_fmt"] = datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
            
            # Chuẩn hoá tên hành động để so sánh
            h_action = h.get("action", "").strip()
            
            found_img = None
            found_tx = None # Biến để chứa Hash tìm thấy
            found_index = -1
            
            # Tìm trong local_txs xem có cái nào khớp Action không
            for i, tx in enumerate(local_txs):
                tx_action = tx.get("action", "").strip()
                
                # Logic ghép: Nếu trùng tên hành động
                if tx_action == h_action:
                    found_img = tx.get("image_id")
                    found_tx = tx.get("tx_hash") # Lấy thêm Tx Hash
                    found_index = i
                    break 
            
            # Nếu tìm thấy thì gắn vào h
            if found_index != -1:
                if found_img:
                    h["image_id"] = found_img
                if found_tx:
                    h["tx_hash"] = found_tx # Gắn Tx Hash vào để HTML dùng
                
                # Xoá khỏi danh sách để không dùng lại (tránh trùng lặp)
                local_txs.pop(found_index)
                
        except Exception as e:
            print(f"Lỗi ghép dữ liệu: {e}")
            h["timestamp_fmt"] = ""
            
    return render_template(
        "product_detail_public.html",
        batch_code=batch_code,
        history=history,
        explorer_base=CRONOS_TESTNET_EXPLORER,
        contract_address=getattr(web3_connect, "CONTRACT_ADDRESS", "")
    )

@app.route('/api/upload_image', methods=['POST'])
def api_upload_image():
    if 'image' not in request.files:
        return {"ok": False, "error": "Không có file ảnh"}, 400
    file = request.files['image']
    if file.filename == '':
        return {"ok": False, "error": "Chưa chọn file"}, 400
    try:
        upload_result = cloudinary.uploader.upload(file)
        url = upload_result.get("secure_url")
        public_id = upload_result.get("public_id")
        wallet = session.get("wallet", "unknown") 
        image_id = db.luu_anh(url, public_id, file.filename, wallet)
        return {"ok": True, "url": url, "image_id": image_id}
    except Exception as e:
        print("Lỗi upload:", e)
        return {"ok": False, "error": str(e)}, 500

@app.route('/image/<image_id>')
def get_image_redirect(image_id):
    img = db.lay_anh(image_id)
    if img and 'url' in img:
        return redirect(img['url'])
    else:
        return "Ảnh không tồn tại", 404

@app.route('/contact')
def contact():
    return render_template('contact.html')

# --- ĐÂY LÀ HÀM INDEX DUY NHẤT (ĐÃ GỘP TÍNH NĂNG SLIDESHOW) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    # 1. Logic tìm kiếm
    ket_qua_tra_cuu = None
    if request.method == 'POST':
        code = (request.form.get('search_code') or '').strip()
        if code:
            ket_qua_tra_cuu = web3_connect.tim_kiem_blockchain(code)
            for item in ket_qua_tra_cuu:
                item["image_id"] = db.lay_anh_dai_dien(item["batch_code"])

    # 2. Logic danh sách sản phẩm
    all_chain = web3_connect.lay_danh_sach_blockchain() or []
    latest_map = {}
    for item in all_chain:
        code = item.get("batch_code")
        if not code: continue
        if code not in latest_map:
            try:
                ts = int(item.get("timestamp", 0) or 0)
                item["timestamp_fmt"] = datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
            except Exception:
                item["timestamp_fmt"] = ""
            latest_map[code] = item
    products = list(latest_map.values())
    for p in products:
        p["image_id"] = db.lay_anh_dai_dien(p["batch_code"])

    # 3. Logic Slideshow
    slideshow_images = []
    try:
        slideshow_dir = os.path.join(app.static_folder, 'slideshow')
        if os.path.exists(slideshow_dir):
            slideshow_images = [
                f for f in os.listdir(slideshow_dir) 
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
            ]
            slideshow_images.sort()
    except Exception as e:
        print(f"Lỗi đọc slideshow: {e}")

    return render_template('index.html', 
                           ket_qua=ket_qua_tra_cuu, 
                           products=products, 
                           slideshow_images=slideshow_images)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)