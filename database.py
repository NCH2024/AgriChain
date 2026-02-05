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
    
    
    def luu_anh(self, url, public_id, filename, upload_by):
        """Lưu metadata của ảnh vào MongoDB"""
        img_doc = {
            "url": url,
            "public_id": public_id,
            "filename": filename,
            "upload_by": upload_by,
            "created_at": datetime.now()
        }
        # Insert vào collection 'images'
        result = self.db.images.insert_one(img_doc)
        return str(result.inserted_id) # Trả về ID dạng chuỗi

    def lay_anh(self, image_id):
        """Lấy link ảnh dựa vào ID"""
        from bson.objectid import ObjectId
        try:
            return self.db.images.find_one({"_id": ObjectId(image_id)})
        except Exception:
            return None
        
    def lay_anh_dai_dien(self, batch_code):
        # Tìm trong lịch sử giao dịch (user_txs) xem có dòng nào chứa image_id không
        # Sắp xếp lấy cái mới nhất (descending)
        record = self.db.user_txs.find_one(
            {"batch_code": batch_code, "image_id": {"$exists": True, "$ne": None}},
            sort=[("timestamp", -1)]
        )
        if record:
            return record.get("image_id")
        return None

    def xoa_tai_khoan(self, username):
        """Xoá tài khoản người dùng khỏi bộ sưu tập users trên MongoDB"""
        try:
            # Tìm và xoá bản ghi có username khớp
            result = self.db.users.delete_one({"username": username})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Lỗi khi xoá tài khoản: {e}")
            return False