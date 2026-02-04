import json
import time
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor, as_completed # Import thư viện xử lý song song
from config import CRONOS_RPC, CONTRACT_ADDRESS

CONTRACT_ABI =  [
    {
      "anonymous": False,
      "inputs": [{"indexed": True,"internalType": "string","name": "batch_code","type": "string"},{"indexed": True,"internalType": "address","name": "owner","type": "address"},{"indexed": False,"internalType": "uint256","name": "timestamp","type": "uint256"}],
      "name": "GhiNhatKyMoi",
      "type": "event"
    },
    {
      "inputs": [{"internalType": "uint256","name": "","type": "uint256"}],
      "name": "danhSachNhatKy",
      "outputs": [{"internalType": "string","name": "batch_code","type": "string"},{"internalType": "string","name": "product_type","type": "string"},{"internalType": "string","name": "action","type": "string"},{"internalType": "string","name": "details","type": "string"},{"internalType": "uint256","name": "timestamp","type": "uint256"},{"internalType": "address","name": "owner","type": "address"}],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "laySoLuong",
      "outputs": [{"internalType": "uint256","name": "","type": "uint256"}],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "uint256","name": "_index","type": "uint256"}],
      "name": "layThongTin",
      "outputs": [{"internalType": "string","name": "","type": "string"},{"internalType": "string","name": "","type": "string"},{"internalType": "string","name": "","type": "string"},{"internalType": "string","name": "","type": "string"},{"internalType": "uint256","name": "","type": "uint256"},{"internalType": "address","name": "","type": "address"}],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "string","name": "_batch_code","type": "string"},{"internalType": "string","name": "_product_type","type": "string"},{"internalType": "string","name": "_action","type": "string"},{"internalType": "string","name": "_details","type": "string"}],
      "name": "themNhatKy",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    }
]

# Khởi tạo kết nối
w3 = Web3(Web3.HTTPProvider(CRONOS_RPC))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# Hàm phụ trợ để gọi trong thread
def call_lay_thong_tin(index):
    try:
        data = contract.functions.layThongTin(index).call()
        return {
            "index": index, # Giữ index để sort lại sau
            "batch_code": data[0],
            "product_type": data[1],
            "action": data[2],
            "details": data[3],
            "timestamp": data[4],
            "owner": data[5]
        }
    except Exception as e:
        print(f"Lỗi tại index {index}: {e}")
        return None

def lay_danh_sach_blockchain():
    try:
        # 1. Lấy tổng số lượng (Vẫn phải chờ cái này)
        so_luong = contract.functions.laySoLuong().call()
        if so_luong == 0:
            return []

        ket_qua = []
        
        # 2. Sử dụng ThreadPoolExecutor để gọi song song
        # max_workers=10 nghĩa là gửi 10 request cùng lúc
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Tạo danh sách các tác vụ cần làm (Lấy từ mới nhất về cũ nhất)
            futures = [executor.submit(call_lay_thong_tin, i) for i in range(so_luong - 1, -1, -1)]
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    ket_qua.append(result)
        
        # 3. Sắp xếp lại kết quả theo thứ tự (vì chạy song song có thể cái sau xong trước cái trước)
        # Chúng ta muốn mới nhất (index cao nhất) lên đầu, hoặc dựa vào timestamp
        ket_qua.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return ket_qua
    except Exception as e:
        print(f"❌ Lỗi đọc Blockchain: {e}")
        return []

def tim_kiem_blockchain(search_code):
    try:
        # Vì hàm lay_danh_sach_blockchain giờ đã nhanh, ta có thể tái sử dụng
        all_data = lay_danh_sach_blockchain()
        return [item for item in all_data if item["batch_code"] == search_code]
    except Exception:
        return []