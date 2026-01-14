import requests
import json

# 1. Định nghĩa địa chỉ Server (phải đảm bảo app.py đang chạy)
url_mine = "http://127.0.0.1:5000/mine_block"
url_get = "http://127.0.0.1:5000/get_chain"

# 2. Chuẩn bị dữ liệu mẫu (Giả lập hành động của nông dân)
data_mau = {
    "data": {
        "nong_dan": "Bac Ba Phi",
        "hanh_dong": "Bon phan huu co",
        "ghi_chu": "Phan vi sinh nhap khau"
    }
}

# 3. Gửi yêu cầu POST (Ghi vào sổ)
print("--- ĐANG GỬI DỮ LIỆU LÊN SERVER ---")
response = requests.post(url_mine, json=data_mau)

if response.status_code == 201:
    print("THÀNH CÔNG! Server trả về:", response.json()['message'])
else:
    print("THẤT BẠI! Lỗi:", response.text)

# 4. Kiểm tra lại xem chuỗi đã dài ra chưa (Đọc sổ)
print("\n--- KIỂM TRA LẠI SỔ CÁI ---")
response_chain = requests.get(url_get)
chain_data = response_chain.json()
print(f"Độ dài hiện tại của chuỗi: {chain_data['length']} Blocks")
print("Block mới nhất:", chain_data['chain'][-1]['data'])