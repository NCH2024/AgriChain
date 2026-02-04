import json
import time
from web3 import Web3
from config import CRONOS_RPC, CONTRACT_ADDRESS
# # --- CẤU HÌNH KẾT NỐI (Em điền thông tin vào đây) ---
# CRONOS_RPC = "https://evm-t3.cronos.org"
# CONTRACT_ADDRESS = "0x1228BC01B160D2da1932dc378C9c8689F002a9b7"
# MY_WALLET_ADDRESS = "0xFc85EAd4152bD8Bb80cddAFc4ef74Fa980dEDEC6"
# MY_PRIVATE_KEY = "338e8da0a17ab973746addb3f42894da5937f5d009a949aae5bde681aa8e07e0"

# ABI em vừa gửi (Thầy đã dán sẵn vào đây cho em)
CONTRACT_ABI =  [
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "string",
          "name": "batch_code",
          "type": "string"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "owner",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "timestamp",
          "type": "uint256"
        }
      ],
      "name": "GhiNhatKyMoi",
      "type": "event"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "name": "danhSachNhatKy",
      "outputs": [
        {
          "internalType": "string",
          "name": "batch_code",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "product_type",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "action",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "details",
          "type": "string"
        },
        {
          "internalType": "uint256",
          "name": "timestamp",
          "type": "uint256"
        },
        {
          "internalType": "address",
          "name": "owner",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "laySoLuong",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "_index",
          "type": "uint256"
        }
      ],
      "name": "layThongTin",
      "outputs": [
        {
          "internalType": "string",
          "name": "",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "",
          "type": "string"
        },
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        },
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "string",
          "name": "_batch_code",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "_product_type",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "_action",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "_details",
          "type": "string"
        }
      ],
      "name": "themNhatKy",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    }
  ]

# Khởi tạo kết nối
w3 = Web3(Web3.HTTPProvider(CRONOS_RPC))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

def lay_danh_sach_blockchain():
    try:
        so_luong = contract.functions.laySoLuong().call()
        ket_qua = []
        for i in range(so_luong - 1, -1, -1):
            data = contract.functions.layThongTin(i).call()
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
    try:
        all_data = lay_danh_sach_blockchain()
        return [item for item in all_data if item["batch_code"] == search_code]
    except Exception:
        return []