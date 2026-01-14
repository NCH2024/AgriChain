from flask import Flask, render_template, request, redirect, session, url_for, send_file
from database import DatabaseManager
from blockchain import Blockchain
import datetime
import qrcode
import io
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "khoa_bi_mat" # Để dùng được session

db = DatabaseManager()
agri_chain = Blockchain()

# Cấu hình nơi lưu ảnh
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Tự động tạo thư mục nếu chưa có
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Định nghĩa bộ lọc để chuyển timestamp thành ngày tháng năm
@app.template_filter('ctime')
def timectime(s):
    if s is None:
        return ""
    # Chuyển đổi số giây thành ngày tháng năm
    return datetime.datetime.fromtimestamp(int(s)).strftime('%d/%m/%Y %H:%M')

# Tạo QR Code
@app.route('/generate_qr/<batch_code>')
def generate_qr(batch_code):
    # Tạo đường link (Giả sử web em chạy trên localhost)
    # Khi deploy thật thì thay 127.0.0.1 bằng tên miền thật
    link = f"http://127.0.0.1:5000/?search_code={batch_code}"

    img = qrcode.make(link)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# Endpoint để kiểm tra tính toàn vẹn của chuỗi khối
@app.route('/validate_chain')
def validate_chain():
    # Gọi hàm kiểm tra
    ket_qua = agri_chain.kiem_tra_toan_ven()
    return {
        "status": ket_qua['trang_thai'],
        "error_block": ket_qua['block_loi']
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    # TRANG CHỦ: Chỉ có ô tìm kiếm và nút Login
    ket_qua_tra_cuu = None
    if request.method == 'POST' and 'search_code' in request.form:
        code = request.form.get('search_code')
        # Gọi hàm tìm kiếm trong DB
        ket_qua_tra_cuu = db.tim_kiem_theo_ma(code)
    
    return render_template('index.html', ket_qua=ket_qua_tra_cuu)

# Endpoint để khôi phục một block bị lỗi từ bản backup
@app.route('/recover_chain', methods=['POST'])
def recover_chain():
    # Lấy số thứ tự block bị lỗi từ client gửi lên
    data = request.get_json()
    block_index = data.get('block_index')
    
    if block_index is None:
        return {"message": "Không tìm thấy Index"}, 400

    # Gọi hàm trong database để sửa lại
    if db.khoi_phuc_mot_block(block_index):
        return {"message": "Đã khôi phục dữ liệu gốc thành công!", "status": "success"}
    else:
        return {"message": "Không tìm thấy dữ liệu backup!", "status": "error"}

@app.route('/login', methods=['GET', 'POST'])
def login():
    thong_bao = ""
    if request.method == 'POST':
        action = request.form.get('action')
        user = request.form.get('username')
        pwd = request.form.get('password')
        role = request.form.get('role')

        if action == "register":
            if db.tao_tai_khoan(user, pwd, role):
                thong_bao = "Đăng ký thành công! Hãy đăng nhập."
            else:
                thong_bao = "Tài khoản đã tồn tại!"
        
        elif action == "login":
            user_info = db.kiem_tra_dang_nhap(user, pwd)
            if user_info:
                session['user'] = user
                session['role'] = user_info['role']
                return redirect(url_for('dashboard'))
            else:
                thong_bao = "Sai tài khoản hoặc mật khẩu!"

    return render_template('login.html', thong_bao=thong_bao)

@app.route('/logout')
def logout():
    session.clear() # Xóa hết session (tên user, role)
    return redirect(url_for('login'))
    
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = session['user']
    role = session.get('role') # Lấy vai trò ra (farmer hoặc factory)
    
    if request.method == 'POST':
        mode = request.form.get('mode')
        
        # --- PHÂN QUYỀN Ở ĐÂY ---
        # Nếu là Nhà máy mà đòi Tạo mới (create) -> CHẶN NGAY
        if mode == 'create' and role != 'farmer':
            return "<h1>LỖI: Nhà máy không có quyền tạo lô hàng mới! Chỉ được cập nhật.</h1>", 403
        # ------------------------

        batch_code = request.form.get('batch_code')
        action = request.form.get('action')
        
        # Lấy details và xử lý ảnh (giữ nguyên code cũ của em)
        details = request.form.get('details', '') 
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                details = details + f" [Ảnh: {filename}]"
        
        product_type = ""
        if mode == 'create':
            product_type = request.form.get('product_type')
        else:
            # Nếu là cập nhật, ta tạm để trống hoặc lấy từ DB nếu muốn xịn hơn
            product_type = "..." 

        agri_chain.them_block_moi(batch_code, product_type, action, details, user)
        
        return redirect(url_for('dashboard'))

    my_products = db.lay_danh_sach_cua_toi(user)
    
    thong_ke = {}
    for p in my_products:
        loai = p.get('product_type', 'Chưa phân loại')
        if loai in thong_ke:
            thong_ke[loai] += 1
        else:
            thong_ke[loai] = 1
            
    labels = list(thong_ke.keys())
    data = list(thong_ke.values())

    for p in my_products:
        import datetime
        dt_object = datetime.datetime.fromtimestamp(p['timestamp'])
        p['timestamp'] = dt_object.strftime("%d/%m/%Y %H:%M")
    
    # TRẢ VỀ GIAO DIỆN
    # Quan trọng: Truyền biến role sang HTML để ẩn hiện nút
    return render_template('dashboard.html', 
                           user=user, 
                           role=role, # Truyền role sang
                           session=session, 
                           products=my_products,
                           chart_labels=labels,
                           chart_data=data)
    

if __name__ == '__main__':
    # Chạy ứng dụng trên cổng 5000, bật chế độ debug để sửa lỗi
    app.run(debug=True, port=5000)