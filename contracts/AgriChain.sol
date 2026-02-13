// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AgriChain {
    
    // 1. Định nghĩa cấu trúc lô hàng (Giống class Block trong file blockchain.py cũ)
    struct LoHang {
        string batch_code;    // Mã lô hàng
        string product_type;  // Loại sản phẩm
        string action;        // Hành động
        string details;       // Chi tiết ( ghi chú)
        uint256 timestamp;    // Thời gian
        address owner;        // Ví của người ghi (Nông dân/Nhà máy)
    }

    // 2. Danh sách lưu trữ (Thay thế MongoDB)
    LoHang[] public danhSachNhatKy;

    // Sự kiện để thông báo ra ngoài (Web bắt được cái này)
    event GhiNhatKyMoi(string indexed batch_code, address indexed owner, uint256 timestamp);

    // 3. Hàm Ghi Nhật Ký (Thay thế hàm them_block_moi trong Python)
    function themNhatKy(
        string memory _batch_code, 
        string memory _product_type, 
        string memory _action, 
        string memory _details
    ) public {
        LoHang memory loMoi = LoHang({
            batch_code: _batch_code,
            product_type: _product_type,
            action: _action,
            details: _details,
            timestamp: block.timestamp, // Lấy giờ của mạng Blockchain
            owner: msg.sender           // Lấy địa chỉ ví người đang bấm nút
        });

        danhSachNhatKy.push(loMoi);
        emit GhiNhatKyMoi(_batch_code, msg.sender, block.timestamp);
    }

    // 4. Hàm lấy tổng số lượng bản ghi
    function laySoLuong() public view returns (uint256) {
        return danhSachNhatKy.length;
    }

    // 5. Hàm lấy chi tiết một bản ghi
    function layThongTin(uint256 _index) public view returns (
        string memory, string memory, string memory, string memory, uint256, address
    ) {
        LoHang memory lo = danhSachNhatKy[_index];
        return (
            lo.batch_code, 
            lo.product_type, 
            lo.action, 
            lo.details, 
            lo.timestamp, 
            lo.owner
        );
    }
}