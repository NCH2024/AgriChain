import json
import time
import hashlib

class Block:
    # Đây là cái khuôn để đúc ra các Khối (Block)
    def __init__(self, index, data, previous_hash):
        self.index = index
        self.timestamp = time.time() # Lấy thời gian hiện tại
        self.data = data # Dữ liệu nông sản (ví dụ: "Tưới nước")
        self.previous_hash = previous_hash # Mã băm của khối đứng trước nó
        self.hash = self.tinh_ma_bam() # Tự tính mã băm cho chính nó ngay khi được tạo

    def tinh_ma_bam(self):
        # Hàm này giống như việc "đóng dấu niêm phong"
        # 1. Gom tất cả thông tin của khối lại thành một chuỗi văn bản
        chuoi_du_lieu = json.dumps(self.__dict__, sort_keys=True)
        
        # 2. Băm chuỗi văn bản đó thành một dãy ký tự loằng ngoằng (SHA256)
        # Ví dụ: từ "hello" -> băm thành "2cf24dba5fb0..."
        ma_bam = hashlib.sha256(chuoi_du_lieu.encode()).hexdigest()
        return ma_bam
    
class Blockchain:
    def __init__(self):
        # Đây là cái kho chứa tất cả các khối
        self.chain = [] 
        # Ngay khi khởi động, phải tạo ra khối đầu tiên (Khối Nguyên Thủy)
        self.tao_khoi_khoi_nguyen()

    def tao_khoi_khoi_nguyen(self):
        # Khối đầu tiên luôn đặc biệt: Index = 0, Previous Hash = "0"
        genesis_block = Block(0, "Nhat ky bat dau", "0")
        self.chain.append(genesis_block)

    def lay_khoi_cuoi_cung(self):
        # Lấy ra khối mới nhất vừa được thêm vào
        return self.chain[-1]

    def them_khoi_moi(self, data):
        # Bước 1: Lấy khối cuối cùng hiện tại để lấy dấu vân tay (Hash) của nó
        khoi_truoc = self.lay_khoi_cuoi_cung()
        
        # Bước 2: Tạo khối mới
        # Index tăng lên 1, Previous Hash chính là Hash của khối trước
        khoi_moi = Block(khoi_truoc.index + 1, data, khoi_truoc.hash)
        
        # Bước 3: Đưa khối mới vào chuỗi
        self.chain.append(khoi_moi)
        
# --- PHẦN CHẠY THỬ (TEST) ---
if __name__ == "__main__":
    # 1. Khởi tạo hệ thống
    print("Đang khởi tạo Blockchain...")
    nong_san_chain = Blockchain()

    # 2. Thêm dữ liệu giả lập
    print("Đang thêm dữ liệu...")
    nong_san_chain.them_khoi_moi("Nong dan A gieo hat")
    nong_san_chain.them_khoi_moi("Nong dan A tuoi nuoc")
    nong_san_chain.them_khoi_moi("Nong dan A bon phan")

    # 3. In kết quả ra màn hình
    print("\n--- KẾT QUẢ SỔ CÁI ---")
    for block in nong_san_chain.chain:
        print(f"Block #{block.index}")
        print(f"Timestamp: {block.timestamp}")
        print(f"Data: {block.data}")
        print(f"Hash: {block.hash}")
        print(f"Previous Hash: {block.previous_hash}")
        print("-" * 20)