import hashlib
import json
import time
from database import DatabaseManager 

db = DatabaseManager()

class Block:
    def __init__(self, index, data, previous_hash, nguoi_tao):
        self.index = index
        self.timestamp = time.time()
        self.data = data # Nội dung nhật ký
        self.previous_hash = previous_hash
        self.nguoi_tao = nguoi_tao
        self.hash = self.tinh_ma_bam()

    def tinh_ma_bam(self):
        block_string = json.dumps(self.__dict__, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        # Khởi động lên là kiểm tra DB ngay
        last_block = db.lay_block_cuoi()
        if last_block is None:
            self.tao_khoi_nguyen_thuy()                     

    def tao_khoi_nguyen_thuy(self):
        genesis_block = Block(0, "Khoi tao he thong", "0", "System")
        db.luu_block(genesis_block.__dict__)

    #   CẢI TIẾN CHỨC NĂNG THÊM BLOCK MỚI VỚI NHIỀU TRƯỜNG HƠN
    def them_block_moi(self, batch_code, product_type, action, details, owner):
        last_block = db.lay_block_cuoi()
        
        # Nếu DB chưa có gì thì index = 0, ngược lại thì +1
        new_index = 0 if last_block is None else last_block['index'] + 1
        new_prev_hash = "0" if last_block is None else last_block['hash']
        
        # Tạo cấu trúc data chi tiết
        block_data = {
            "index": new_index,
            "timestamp": time.time(),
            "batch_code": batch_code,       # Mã lô hàng (VD: 12345678)
            "product_type": product_type,   # Loại sản phẩm
            "owner": owner,                 # Người thực hiện
            "action": action,               # Hành động (Gieo, Gặt, Đóng gói)
            "details": details,             # Chi tiết khác
            "previous_hash": new_prev_hash
        }
        
        # Tính hash
        block_string = json.dumps(block_data, sort_keys=True).encode()
        block_hash = hashlib.sha256(block_string).hexdigest()
        
        block_data["hash"] = block_hash
        
        # Lưu DB
        db.luu_block(block_data)
        return True
    
    def lay_chuoi(self):
        return db.lay_toan_bo_chuoi()
    
    # Nâng cấp hàm kiểm tra toàn vẹn chuỗi
    def kiem_tra_toan_ven(self):
        chuoi = db.lay_toan_bo_chuoi()
        ket_qua = {
            "trang_thai": "An toàn",
            "block_loi": None,
            "chi_tiet": ""
        }
        
        for i in range(len(chuoi)):
            block_hien_tai = chuoi[i]
            
            # --- KIỂM TRA 1: Nội dung có khớp với Mã Hash không? (Re-hashing) ---
            # 1. Tạo một bản sao của block để tính toán lại
            block_can_tinh = block_hien_tai.copy()
            
            # 2. Lấy mã hash đang lưu trong DB ra để so sánh sau này
            hash_da_luu = block_can_tinh['hash']
            
            # 3. Xóa trường 'hash' và '_id' đi vì lúc tính hash gốc không có 2 cái này
            del block_can_tinh['hash']
            if '_id' in block_can_tinh:
                del block_can_tinh['_id']
            
            # 4. Tính lại hash từ dữ liệu hiện tại
            # Lưu ý: Phải sort_keys=True y hệt lúc tạo block thì hash mới khớp
            block_string = json.dumps(block_can_tinh, sort_keys=True).encode()
            hash_tinh_lai = hashlib.sha256(block_string).hexdigest()
            
            # 5. So sánh
            if hash_tinh_lai != hash_da_luu:
                ket_qua["trang_thai"] = "Bị thay đổi nội dung"
                ket_qua["block_loi"] = block_hien_tai['index']
                ket_qua["chi_tiet"] = f"Dữ liệu tại Block {block_hien_tai['index']} bị sửa đổi! Hash tính lại không khớp Hash lưu trữ."
                return ket_qua

            # --- KIỂM TRA 2: Mắt xích có bị đứt không? (Previous Hash) ---
            if i > 0:
                block_truoc = chuoi[i-1]
                if block_hien_tai['previous_hash'] != block_truoc['hash']:
                    ket_qua["trang_thai"] = "Bị đứt gãy chuỗi"
                    ket_qua["block_loi"] = block_hien_tai['index']
                    ket_qua["chi_tiet"] = f"Block {block_hien_tai['index']} không liên kết đúng với Block trước đó."
                    return ket_qua
            
        return ket_qua