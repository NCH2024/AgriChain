from flask import Flask, jsonify, render_template, request, session, redirect, url_for, send_file
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

def fmt_ts(ts):
    """Chuyển đổi timestamp (số nguyên) sang chuỗi ngày giờ định dạng dd/mm/YYYY HH:MM."""
    try:
        return datetime.datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y %H:%M")
    except:
        return ""


@app.template_filter('ctime')
def timectime(s):
    """Template filter: Định dạng timestamp trong giao diện HTML (Jinja2)."""
    try:
        if s is None:
            return ""
        return datetime.datetime.fromtimestamp(int(s)).strftime('%d/%m/%Y %H:%M')
    except Exception:
        return ""

@app.route('/generate_qr/<batch_code>')
def generate_qr(batch_code):
    """Tạo mã QR code trỏ đến trang truy xuất nguồn gốc (/trace/...) và trả về dưới dạng file ảnh."""
    link = f"{request.host_url}trace/{batch_code}"
    img = qrcode.make(link)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/login')
def login():
    """Hiển thị trang đăng nhập."""
    return render_template('login.html')

@app.route('/api/login_wallet', methods=['POST'])
def api_login_wallet():
    """API xử lý đăng nhập: Kiểm tra ví trong DB, thiết lập session nếu ví hợp lệ."""
    data = request.get_json(force=True)
    wallet_address = data.get('wallet')
    
    # [THÊM LOGIC KIỂM TRA Ở ĐÂY]
    # Tìm xem ví này đã có tài khoản (người dùng) trong DB chưa
    user = db.db.users.find_one({"wallet": wallet_address})
    
    if not user:
        # Nếu không tìm thấy ví trong DB, báo lỗi không cho vào
        return {"ok": False, "error": "Tài khoản không tồn tại. Vui lòng đăng ký!"}, 404

    session['wallet'] = wallet_address
    session['role'] = user.get('role', 'farmer')
    session['username'] = user.get('username')
    
    return {"ok": True}

@app.route('/logout')
def logout():
    """Đăng xuất: Xóa session và chuyển hướng về trang login."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@require_wallet
def dashboard():
    """Trang Dashboard: Lấy dữ liệu từ Blockchain, lọc theo ví người dùng và hiển thị thống kê biểu đồ."""
    wallet = session.get("wallet")
    role = session.get("role")

    all_chain = web3_connect.lay_danh_sach_blockchain() or []
    my_products = [p for p in all_chain if str(p.get("owner","")).lower() == str(wallet).lower()]

    # Vòng lặp xử lý hiển thị thời gian cho từng sản phẩm
    for p in my_products:
        try:
            ts = int(p.get("timestamp", 0) or 0)
            p["timestamp_fmt"] = datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
        except Exception:
            p["timestamp_fmt"] = ""

    # Tính toán thống kê số lượng theo loại sản phẩm để vẽ biểu đồ
    thong_ke = {}
    for p in my_products:
        loai = p.get('product_type', 'Chưa xác định')
        # Nếu chưa có trong dict thì gán 0, sau đó cộng thêm 1
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
    """API lưu metadata giao dịch (Hash, Ảnh, Action) vào MongoDB sau khi ghi thành công lên Blockchain."""
    data = request.get_json(force=True)
    wallet = session["wallet"]

    # Đảm bảo có đầy đủ thông tin trước khi lưu
    db.db.user_txs.insert_one({
        "wallet": wallet,
        "batch_code": data.get("batch_code"),
        "product_type": data.get("product_type"), 
        "tx_hash": data.get("tx_hash"),
        "action": data.get("action", ""),
        "image_id": data.get("image_id"), 
        "timestamp": int(data.get("timestamp", 0) or 0),
        "saved_at": datetime.datetime.utcnow()
    })
    return {"ok": True}

@app.route("/products")
@require_wallet
def products():
    """Hiển thị danh sách các lô hàng (sản phẩm) của người dùng, gom nhóm theo mã lô (batch_code)."""
    wallet = session["wallet"]

    pipeline = [
        {"$match": {"wallet": wallet}},
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$batch_code",
            "batch_code": {"$first": "$batch_code"},
            "product_type": {"$first": "$product_type"},
            "image_id": {"$first": "$image_id"},
            "action": {"$first": "$action"},
            "timestamp": {"$first": "$timestamp"}
        }}
    ]

    products = list(db.db.user_txs.aggregate(pipeline))
    for p in products:
        p["timestamp_fmt"] = fmt_ts(p.get("timestamp"))
        p["product_type"] = p.get("product_type") or "Chưa xác định"

    return render_template("products.html", products=products)

@app.route("/products/<batch_code>")
@require_wallet
def product_detail(batch_code):
    """Chi tiết lô hàng (Admin/Owner): Kết hợp dữ liệu bất biến từ Blockchain với hình ảnh/hash từ MongoDB."""
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

    # 3. Vòng lặp ghép thông tin (Ảnh + Tx Hash) từ DB vào dữ liệu Blockchain
    # Logic: Blockchain giữ sự thật (Action, Time), DB giữ bằng chứng phụ (Ảnh, Hash)
    for h in history:
        try:
            # Format lại thời gian hiển thị
            ts = int(h.get("timestamp", 0) or 0)
            h["timestamp_fmt"] = datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
            
            h_action = h.get("action", "").strip()
            
            found_img = None
            found_tx = None
            found_index = -1
            
            # Tìm trong local_txs xem có bản ghi nào khớp Action không
            # (Duyệt qua danh sách local để tìm action tương ứng)
            for i, tx in enumerate(local_txs):
                tx_action = tx.get("action", "").strip()
                if tx_action == h_action:
                    found_img = tx.get("image_id")
                    found_tx = tx.get("tx_hash") # Lấy thêm Tx Hash
                    found_index = i
                    break 
            
            # Nếu tìm thấy dữ liệu khớp trong DB Local
            if found_index != -1:
                if found_img:
                    h["image_id"] = found_img # Gán ảnh vào record blockchain để hiển thị
                if found_tx:
                    h["tx_hash"] = found_tx # Gắn Hash vào đây
                
                # Xoá bản ghi đã tìm thấy khỏi danh sách local để không dùng lại cho vòng lặp sau
                # (Tránh trường hợp 2 hành động giống tên nhau bị map sai)
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
    """Trang truy xuất công khai (Public): Cho phép người tiêu dùng xem lịch sử lô hàng mà không cần đăng nhập."""
    # 1. Lấy lịch sử từ Blockchain
    history = web3_connect.tim_kiem_blockchain(batch_code) or []
    try:
        history = sorted(history, key=lambda x: int(x.get("timestamp", 0) or 0))
    except Exception:
        pass
    
    # 2. Lấy dữ liệu từ Database (bao gồm cả Ảnh và Tx Hash)
    # Lọc lấy các bản ghi có action để ghép
    local_txs = list(db.db.user_txs.find({"batch_code": batch_code}))

    # 3. Vòng lặp ghép thông tin (Ảnh + Tx Hash) tương tự như hàm product_detail
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
    """API Upload ảnh lên Cloudinary và lưu thông tin tham chiếu vào MongoDB."""
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
    """Chuyển hướng (Redirect) từ ID ảnh nội bộ sang URL thực tế trên Cloudinary."""
    img = db.lay_anh(image_id)
    if img and 'url' in img:
        return redirect(img['url'])
    else:
        return "Ảnh không tồn tại", 404

@app.route('/contact')
def contact():
    """Hiển thị trang liên hệ."""
    return render_template('contact.html')

# --- ĐÂY LÀ HÀM INDEX DUY NHẤT (ĐÃ GỘP TÍNH NĂNG SLIDESHOW) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    """Trang chủ: Xử lý tìm kiếm mã lô trên Blockchain và hiển thị danh sách sản phẩm mới nhất từ DB."""
    # 1. Logic tìm kiếm (Chỉ chạy khi người dùng bấm nút tìm - Nên giữ Blockchain để chính xác nhất)
    ket_qua_tra_cuu = None
    if request.method == 'POST':
        code = (request.form.get('search_code') or '').strip()
        if code:
            ket_qua_tra_cuu = web3_connect.tim_kiem_blockchain(code)
            for item in ket_qua_tra_cuu:
                item["image_id"] = db.lay_anh_dai_dien(item["batch_code"])

    # 2. Logic danh sách sản phẩm (TỐI ƯU: Lấy từ MongoDB thay vì Blockchain)
    # Thay vì gọi web3_connect, ta lấy từ collection user_txs
    raw_products = list(db.db.user_txs.find().sort("timestamp", -1).limit(100)) 
    
    # Lọc lấy các lô hàng duy nhất (tránh hiện 1 lô nhiều lần nếu có nhiều hành động update)
    # Sử dụng Dictionary để chỉ giữ lại bản ghi mới nhất của mỗi batch_code
    latest_map = {}
    for p in raw_products:
        code = p.get("batch_code")
        # Nếu mã lô chưa có trong map thì thêm vào (vì đã sort timestamp giảm dần nên gặp đầu tiên là mới nhất)
        if code and code not in latest_map:
            try:
                ts = int(p.get("timestamp", 0) or 0)
                p["timestamp_fmt"] = datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
            except Exception:
                p["timestamp_fmt"] = ""
            latest_map[code] = p
            
    products = list(latest_map.values())

    # 3. Logic Slideshow (Giữ nguyên)
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
    
@app.route('/profile')
def profile():
    """Trang hồ sơ cá nhân: Hiển thị thông tin user và số lượng giao dịch đã thực hiện."""
    # 1. Kiểm tra xem người dùng đã đăng nhập (kết nối ví) chưa
    if 'wallet' not in session:
        return redirect(url_for('login'))
    
    # 2. Lấy thông tin người dùng từ MongoDB
    # Chúng ta tìm theo username đã lưu trong session lúc đăng nhập
    user_data = db.db.users.find_one({"username": session.get('username')})
    
    # 3. Tính toán số lượng giao dịch của ví này để hiển thị cho oai
    tx_count = db.db.user_txs.count_documents({"wallet": session.get('wallet')})
    
    return render_template('profile.html', user=user_data, tx_count=tx_count)

@app.route('/api/delete_account', methods=['POST'])
def delete_account():
    """API xóa tài khoản người dùng hiện tại khỏi hệ thống."""
    if 'username' not in session:
        return jsonify({"ok": False, "msg": "Bạn chưa đăng nhập!"})
    
    username = session['username']
    
    # Gọi hàm xoá từ DatabaseManager
    if db.xoa_tai_khoan(username):
        session.clear() # Xoá sạch phiên đăng nhập
        return jsonify({"ok": True, "msg": "Tài khoản của bạn đã được xoá thành công."})
    else:
        return jsonify({"ok": False, "msg": "Có lỗi xảy ra khi xoá tài khoản."})
    
@app.route("/api/sync_blockchain", methods=["POST"])
@require_wallet
def sync_blockchain():
    """API đồng bộ dữ liệu: Kéo dữ liệu từ Blockchain về MongoDB nếu local bị thiếu hoặc sai lệch."""
    wallet = session["wallet"]

    chain_data = web3_connect.lay_danh_sach_blockchain() or []
    mongo_data = list(db.db.user_txs.find({"wallet": wallet}))

    # Tạo map để tra cứu nhanh (O(1)) thay vì dùng vòng lặp lồng nhau (O(n^2))
    # Key là sự kết hợp của batch_code + action + timestamp để đảm bảo tính duy nhất
    mongo_map = {}
    for m in mongo_data:
        key = f"{m.get('batch_code')}|{m.get('action')}|{m.get('timestamp')}"
        mongo_map[key] = m

    stats = {
        "added": 0,
        "updated": 0,
        "checked": len(chain_data)
    }

    # Duyệt qua từng bản ghi trên Blockchain để so sánh với DB Local
    for c in chain_data:
        batch = c.get("batch_code")
        action = c.get("action")
        ts = int(c.get("timestamp", 0) or 0)

        # Tạo key tương ứng để tra cứu trong mongo_map
        key = f"{batch}|{action}|{ts}"

        if key not in mongo_map:
            # 👉 Case 1: Blockchain có – MongoDB không có
            # Hành động: Insert bổ sung vào MongoDB để đồng bộ
            db.db.user_txs.insert_one({
                "wallet": wallet,
                "batch_code": batch,
                "product_type": c.get("product_type"),
                "action": action,
                "timestamp": ts,
                "tx_hash": c.get("tx_hash", ""),
                "image_id": None, # Blockchain không lưu ảnh, nên để None
                "synced_from_chain": True,
                "saved_at": datetime.datetime.utcnow()
            })
            stats["added"] += 1
        else:
            # Nếu đã có, kiểm tra xem dữ liệu có bị lệch không
            m = mongo_map[key]
            need_update = False
            update_fields = {}

            # 👉 Case 2: DB thiếu product_type (do phiên bản cũ chưa lưu)
            if not m.get("product_type") and c.get("product_type"):
                update_fields["product_type"] = c.get("product_type")
                need_update = True

            # 👉 Case 3: sai timestamp (hiếm gặp, nhưng check cho chắc)
            if int(m.get("timestamp", 0)) != ts:
                update_fields["timestamp"] = ts
                need_update = True

            if need_update:
                db.db.user_txs.update_one(
                    {"_id": m["_id"]},
                    {"$set": update_fields}
                )
                stats["updated"] += 1

    return {
        "ok": True,
        "result": stats
    }


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)