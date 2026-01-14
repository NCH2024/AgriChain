import pymongo 
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Thay mật khẩu của các bạn vào
CONNECTION_STRING = "mongodb+srv://admin:AgriChain2025TeamWork@agrichain.6kdxkpt.mongodb.net/?appName=AgriChain"

class DatabaseManager:
    def __init__(self):
        self.client = pymongo.MongoClient(CONNECTION_STRING)
        self.db = self.client["AgriChainDB"] # Tên cơ sở dữ liệu 
        
    def tao_tai_khoan(self, username, password, role):
        if self.db.users.find_one({"username": username}):
            return False
        
        
        # AgriChainDB.users
        # BĂM MẬT KHẨU TRƯỚC KHI LƯU
        hashed_password = generate_password_hash(password) 
        
        user = {
            "username": username,
            "password": hashed_password, # Lưu cái đã băm
            "role": role,
            "created_at": datetime.now()
        }
        self.db.users.insert_one(user)
        return True

    def kiem_tra_dang_nhap(self, username, password):
        user = self.db.users.find_one({"username": username})
        if user:
            # So sánh mật khẩu người dùng nhập với mật khẩu đã băm trong DB
            if check_password_hash(user['password'], password):
                return user
        return None
    
    # Nâng cấp hàm lưu block (để lưu cả bản backup)

    def luu_block(self, block_data):
        # Lưu vào chuỗi chính (để hiển thị)
        self.db.blockchain.insert_one(block_data.copy())
        
        # Lưu vào chuỗi dự phòng (để khôi phục sau này)
        # Lưu ý: Cần xóa _id đi để MongoDB tự tạo _id mới cho bên backup, tránh trùng lặp
        backup_data = block_data.copy()
        if '_id' in backup_data:
            del backup_data['_id']
        self.db.blockchain_backup.insert_one(backup_data)
        
    # Nâng cấp hàm khôi phục một block từ bản backup    
        
    def khoi_phuc_mot_block(self, index_can_sua):
        # Tìm block gốc trong kho dự phòng
        block_chuan = self.db.blockchain_backup.find_one({"index": index_can_sua}, {"_id": 0})
        
        if block_chuan:
            # Xóa block rác/bị hack ở chuỗi chính
            self.db.blockchain.delete_one({"index": index_can_sua})
            
            # Chèn lại block chuẩn vào
            self.db.blockchain.insert_one(block_chuan)
            return True
        return False

    def lay_toan_bo_chuoi(self):
        # Lấy dữ liệu, bỏ trường _id đi để đỡ lỗi
        return list(self.db.blockchain.find({}, {"_id": 0}).sort("index", 1))

    def lay_block_cuoi(self):
        return self.db.blockchain.find_one({}, {"_id": 0}, sort=[("index", -1)])
    
    
    # CẢI TIẾN CHỨC NĂNG TÌM KIẾM VÀ LẤY DANH SÁCH V2   

    def tim_kiem_theo_ma(self, batch_code):
        # Hàm này dùng cho Khách hàng tra cứu
        # Lấy tất cả block có batch_code trùng khớp
        return list(self.db.blockchain.find({"batch_code": batch_code}, {"_id": 0}).sort("index", 1))

    def lay_danh_sach_cua_toi(self, username):
        # Hàm này dùng cho Dashboard
        # Lấy danh sách các lô hàng mà user này từng tác động
        # Dùng distinct để lấy danh sách mã code duy nhất, không trùng lặp
        ds_ma_code = self.db.blockchain.find({"owner": username}).distinct("batch_code")
        
        ket_qua = []
        for code in ds_ma_code:
            # Với mỗi mã code, lấy thông tin mới nhất để hiển thị trạng thái hiện tại
            last_info = self.db.blockchain.find_one(
                {"batch_code": code}, 
                {"_id": 0}, 
                sort=[("index", -1)]
            )
            ket_qua.append(last_info)
        return ket_qua
