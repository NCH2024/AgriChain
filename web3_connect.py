import json
import time
from web3 import Web3

# --- CẤU HÌNH KẾT NỐI (Em điền thông tin vào đây) ---
CRONOS_RPC = "https://evm-t3.cronos.org"
CONTRACT_ADDRESS = "0x8C3449A80f4A6BB197A35D46F402eE1A3473FFe1"
MY_WALLET_ADDRESS = "0x8d97B8068B83B7F494140593fbaF5586FEE056ae"
MY_PRIVATE_KEY = "ab282bc97ae0af877f9113c089667be52ecd906dbad435f705ed97aac1013110"

# ABI em vừa gửi (Thầy đã dán sẵn vào đây cho em)
CONTRACT_ABI = [
	{
		"anonymous": False,
		"inputs": [
			{"indexed": True, "internalType": "string", "name": "batch_code", "type": "string"},
			{"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
			{"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
		],
		"name": "GhiNhatKyMoi",
		"type": "event"
	},
	{
		"inputs": [
			{"internalType": "string", "name": "_batch_code", "type": "string"},
			{"internalType": "string", "name": "_product_type", "type": "string"},
			{"internalType": "string", "name": "_action", "type": "string"},
			{"internalType": "string", "name": "_details", "type": "string"}
		],
		"name": "themNhatKy",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "laySoLuong",
		"outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [{"internalType": "uint256", "name": "_index", "type": "uint256"}],
		"name": "layThongTin",
		"outputs": [
			{"internalType": "string", "name": "", "type": "string"},
			{"internalType": "string", "name": "", "type": "string"},
			{"internalType": "string", "name": "", "type": "string"},
			{"internalType": "string", "name": "", "type": "string"},
			{"internalType": "uint256", "name": "", "type": "uint256"},
			{"internalType": "address", "name": "", "type": "address"}
		],
		"stateMutability": "view",
		"type": "function"
	}
]

# Khởi tạo kết nối
w3 = Web3(Web3.HTTPProvider(CRONOS_RPC))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

def ghi_block_moi(batch_code, product_type, action, details):
    """Hàm này thay thế cho agri_chain.them_block_moi"""
    try:
        # 1. Tạo giao dịch
        tx = contract.functions.themNhatKy(
            batch_code, product_type, action, details
        ).build_transaction({
            'chainId': 338, # ID mạng Cronos Testnet
            'gas': 500000,  # Giới hạn Gas
            'gasPrice': w3.to_wei('10000', 'gwei'),
            'nonce': w3.eth.get_transaction_count(MY_WALLET_ADDRESS),
        })

        # 2. Ký giao dịch
        signed_tx = w3.eth.account.sign_transaction(tx, MY_PRIVATE_KEY)

        # 3. Gửi lên mạng
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # 4. Đợi xác nhận (Block)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Đã ghi thành công! Hash: {w3.to_hex(tx_hash)}")
        return True
    except Exception as e:
        print(f"❌ Lỗi ghi Blockchain: {e}")
        return False

def lay_danh_sach_blockchain():
    """Hàm này thay thế cho db.lay_danh_sach_cua_toi"""
    try:
        so_luong = contract.functions.laySoLuong().call()
        ket_qua = []
        
        # Duyệt ngược từ cuối về đầu để lấy cái mới nhất trước
        for i in range(so_luong - 1, -1, -1):
            # Gọi hàm layThongTin từ Smart Contract
            data = contract.functions.layThongTin(i).call()
            # data trả về: (batch_code, product_type, action, details, timestamp, owner)
            
            ket_qua.append({
                "batch_code": data[0],
                "product_type": data[1],
                "action": data[2],
                "details": data[3],
                "timestamp": data[4],
                "owner": data[5]
            })
        return ket_qua
    except Exception as e:
        print(f"❌ Lỗi đọc Blockchain: {e}")
        return []

def tim_kiem_blockchain(search_code):
    """Hàm tìm kiếm theo mã lô hàng"""
    try:
        all_data = lay_danh_sach_blockchain()
        # Lọc ra những block có mã trùng khớp
        ket_qua = [item for item in all_data if item['batch_code'] == search_code]
        return ket_qua
    except Exception as e:
        return []