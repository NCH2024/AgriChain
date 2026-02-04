# 📖 Hệ thống Truy xuất nguồn gốc Nông sản Sạch - AgriChain

**Đề tài:** SỔ NHẬT KÝ NÔNG SẢN SẠCH (Ứng dụng Blockchain)

---

*   **Lớp:** 22TIN-TT
*   **Giảng viên:** Võ Thanh Vinh
*   **Nhóm:** 4
*   **Thành viên:** Nguyễn Chánh Hiệp, Nguyễn Chí Thanh, Tiêu Quang Thịnh

---

## 📝 MÔ TẢ ĐỀ TÀI

### 1. Vấn đề thực tế

Người tiêu dùng hiện nay rất lo sợ về vấn đề thực phẩm bẩn. Các tem nhãn dán trên rau củ trong siêu thị có thể bị làm giả hoặc thay đổi thông tin một cách dễ dàng. Do đó, khách hàng thiếu một công cụ đáng tin cậy để kiểm chứng lịch sử thật sự của một sản phẩm, từ lúc gieo hạt đến khi lên kệ.

### 2. Giải pháp: AgriChain

Xây dựng một ứng dụng phi tập trung (DApp) sử dụng công nghệ **Blockchain (Cronos Testnet)** để lưu trữ nhật ký canh tác.

*   **Khác biệt:** Thay vì chỉ mô phỏng bằng cơ sở dữ liệu thông thường, hệ thống sử dụng **Smart Contract (Hợp đồng thông minh)** để ghi lại dữ liệu lên mạng lưới Blockchain thực tế.
*   **Điểm mấu chốt:** Dữ liệu một khi đã được ghi vào Blockchain sẽ **không thể sửa đổi hay xóa bỏ (Immutability)**. Người tiêu dùng có thể kiểm tra mã giao dịch (Tx Hash) trực tiếp trên Blockchain Explorer để xác thực tính toàn vẹn.

## 🔄 QUY TRÌNH HOẠT ĐỘNG

Vòng đời của một nông sản sẽ được ghi lại và truy xuất như sau:

1.  **Đăng nhập & Xác thực:**
    *   Nông dân đăng nhập vào hệ thống thông qua **Ví điện tử (Metamask/Web3 Wallet)**. Địa chỉ ví đóng vai trò là định danh duy nhất của người sản xuất.

2.  **Ghi nhật ký canh tác (Giao dịch Blockchain):**
    *   Mỗi khi thực hiện một công việc (Gieo trồng, Bón phân, Thu hoạch), nông dân nhập thông tin và tải ảnh minh chứng.
    *   **Ảnh:** Được upload lên **Cloudinary** để tối ưu lưu trữ.
    *   **Dữ liệu:** Thông tin lô hàng, hành động, và thời gian được gửi lên **Smart Contract** trên mạng **Cronos Testnet**.
    *   Hệ thống lưu trữ Hash giao dịch và liên kết ảnh vào MongoDB để phục vụ hiển thị nhanh.

3.  **Tạo mã QR định danh:**
    *   Mỗi lô hàng (`batch_code`) sẽ được hệ thống tạo một mã QR duy nhất.
    *   Mã QR này chứa đường dẫn đến trang truy xuất nguồn gốc công khai (`/trace/<batch_code>`).

4.  **Người tiêu dùng kiểm tra:**
    *   Khách hàng quét mã QR trên sản phẩm.
    *   Hệ thống tự động truy vấn dữ liệu trực tiếp từ **Blockchain** (để lấy thông tin xác thực) và kết hợp với hình ảnh từ cơ sở dữ liệu để hiển thị toàn bộ lịch sử canh tác.

## 🛠️ KIẾN TRÚC HỆ THỐNG & CÔNG NGHỆ (TECH STACK)

Hệ thống được xây dựng dựa trên kiến trúc hiện đại kết hợp giữa Web2 và Web3:

*   **Tầng Blockchain (Web3 Layer)**:
    *   **Mạng lưới:** Cronos Testnet (EVM Compatible).
    *   **Smart Contract:** Viết bằng ngôn ngữ **Solidity**. Chịu trách nhiệm lưu trữ các bản ghi nhật ký bất biến.
    *   **Giao tiếp:** Sử dụng thư viện `Web3.py` để kết nối Backend với Blockchain Node (RPC).

*   **Tầng Backend (Application Layer - `Flask`)**:
    *   Xây dựng bằng **Python Flask**.
    *   Xử lý logic nghiệp vụ, xác thực ví, upload ảnh lên Cloudinary.
    *   Đóng vai trò cầu nối (Middleware) giữa người dùng và Blockchain.

*   **Tầng Dữ liệu (Database Layer)**:
    *   **MongoDB:** Lưu trữ thông tin người dùng, metadata của ảnh, và cache lịch sử giao dịch (Transaction Hash) để tăng tốc độ truy vấn.
    *   **Cloudinary:** Lưu trữ hình ảnh minh chứng hoạt động canh tác chất lượng cao.

*   **Tầng Hiển thị (Frontend)**:
    *   HTML5, CSS3 (Glassmorphism UI), JavaScript.
    *   Tích hợp hiển thị dữ liệu minh bạch từ Blockchain.

## 🧱 CẤU TRÚC DỮ LIỆU TRÊN SMART CONTRACT

Dữ liệu trên Blockchain không lưu dưới dạng JSON thông thường mà được định nghĩa bằng `Struct` trong Solidity để tối ưu hóa chi phí (Gas fee) và đảm bảo tính chặt chẽ:

```solidity
struct LoHang {
    string batch_code;    // Mã lô hàng (Ví dụ: RAU-001)
    string product_type;  // Loại sản phẩm (Ví dụ: Cải bẹ xanh)
    string action;        // Hành động (Ví dụ: Bón phân)
    string details;       // Chi tiết ghi chú
    uint256 timestamp;    // Thời gian ghi nhận (Lấy từ thời gian thực của Block)
    address owner;        // Địa chỉ ví của người thực hiện (Định danh người nông dân)
}
```

## 🚀 TÍNH NĂNG CHÍNH

1.  **Quản lý nhật ký (Dashboard):** Xem thống kê các hoạt động, biểu đồ tỷ lệ loại sản phẩm.
2.  **Truy xuất nguồn gốc (Traceability):** Giao diện Timeline hiển thị lịch sử từ mới đến cũ, kết hợp dữ liệu từ Blockchain và hình ảnh thực tế.
3.  **Minh bạch thông tin:** Hiển thị rõ ràng Transaction Hash (Mã giao dịch) và liên kết đến Blockchain Explorer để người dùng tự kiểm chứng.
4.  **Upload ảnh:** Tích hợp API Cloudinary để lưu trữ ảnh chất lượng cao.

---
*Dự án được phát triển cho môn học Công nghệ Chuỗi khối (Blockchain Technology).*