from flask import Flask, render_template, request, redirect, session, url_for, send_file
from database import DatabaseManager
from wallet_auth import register_wallet_routes, require_wallet
from config import CRONOS_TESTNET_EXPLORER
import web3_connect
import datetime
import qrcode
import io

app = Flask(__name__)
app.secret_key = "khoa_bi_mat"

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

@app.route('/', methods=['GET', 'POST'])
def index():
    # Tra cứu theo mã lô (giữ UI tìm kiếm như cũ)
    ket_qua_tra_cuu = None
    if request.method == 'POST':
        code = (request.form.get('search_code') or '').strip()
        if code:
            ket_qua_tra_cuu = web3_connect.tim_kiem_blockchain(code)

    # Danh sách tất cả lô hàng (mỗi batch_code lấy bản mới nhất)
    all_chain = web3_connect.lay_danh_sach_blockchain() or []
    latest_map = {}
    for item in all_chain:
        code = item.get("batch_code")
        if not code:
            continue
        if code not in latest_map:
            try:
                ts = int(item.get("timestamp", 0) or 0)
                item["timestamp_fmt"] = datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
            except Exception:
                item["timestamp_fmt"] = ""
            latest_map[code] = item
    products = list(latest_map.values())

    return render_template('index.html', ket_qua=ket_qua_tra_cuu, products=products)

@app.route('/login')
def login():
    return render_template('login.html')

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
    # Trang chi tiết PRIVATE: chỉ xem được lô thuộc ví đã lưu tx
    wallet = session["wallet"]
    owned = db.db.user_txs.find_one({"wallet": wallet, "batch_code": batch_code})
    if not owned:
        return "Forbidden", 403

    history = web3_connect.tim_kiem_blockchain(batch_code) or []
    try:
        history = sorted(history, key=lambda x: int(x.get("timestamp", 0) or 0))
    except Exception:
        pass

    for h in history:
        try:
            ts = int(h.get("timestamp", 0) or 0)
            h["timestamp_fmt"] = datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
        except Exception:
            h["timestamp_fmt"] = ""

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
    history = web3_connect.tim_kiem_blockchain(batch_code) or []
    try:
        history = sorted(history, key=lambda x: int(x.get("timestamp", 0) or 0))
    except Exception:
        pass
    for h in history:
        try:
            ts = int(h.get("timestamp", 0) or 0)
            h["timestamp_fmt"] = datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
        except Exception:
            h["timestamp_fmt"] = ""
    return render_template(
        "product_detail_public.html",
        batch_code=batch_code,
        history=history,
        explorer_base=CRONOS_TESTNET_EXPLORER,
        contract_address=getattr(web3_connect, "CONTRACT_ADDRESS", "")
    )

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
