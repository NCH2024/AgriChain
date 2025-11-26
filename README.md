# 📖 Hệ thống Truy xuất nguồn gốc Nông sản Sạch - AgriChain

**Đề tài:** SỔ NHẬT KÝ NÔNG SẢN SẠCH

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

Xây dựng một ứng dụng web mô phỏng công nghệ **Blockchain** để lưu trữ nhật ký canh tác.

*   **Ví dụ:** Mỗi khi người nông dân thực hiện một công việc (tưới nước, bón phân, thu hoạch), hành động đó sẽ được ghi lại, đóng gói thành một **"Khối" (Block)** và thêm vào chuỗi.
*   **Điểm mấu chốt:** Một khi đã được ghi vào chuỗi, thông tin đó vĩnh viễn **không thể sửa đổi hay xóa bỏ**. Đây chính là tính chất **Bất biến (Immutability)** của công nghệ Blockchain, đảm bảo tính minh bạch và đáng tin cậy của dữ liệu.

## 🔄 QUY TRÌNH HOẠT ĐỘNG

Vòng đời của một nông sản sẽ được ghi lại theo từng giai đoạn như sau:

1.  **Giai đoạn 1: Gieo trồng (Genesis Block)**
    *   Nông dân tạo ra bản ghi đầu tiên (khối nguyên thủy) của chuỗi.
    *   *Ví dụ: "Gieo hạt giống Cải bẹ xanh, Lô đất A, Ngày 01/10/2023".*

2.  **Giai đoạn 2: Chăm sóc (Tạo các Block mới)**
    *   Mỗi hành động chăm sóc sẽ tạo ra một khối mới, được liên kết với khối trước đó.
    *   *Ví dụ: Ngày 05/10, nông dân ghi "Tưới nước sạch" -> Tạo Block mới.*
    *   *Ví dụ: Ngày 15/10, nông dân ghi "Bón phân hữu cơ" -> Tạo Block mới.*

3.  **Giai đoạn 3: Thu hoạch & Phân phối**
    *   Hành động thu hoạch và bàn giao cho đơn vị vận chuyển cũng được ghi lại.
    *   *Ví dụ: Ngày 30/10/2023, nông dân ghi "Đã thu hoạch, chuyển cho xe tải" -> Tạo Block mới.*

4.  **Giai đoạn 4: Người tiêu dùng kiểm tra**
    *   Tại siêu thị, khách hàng quét mã QR hoặc nhập mã lô hàng trên ứng dụng web.
    *   Hệ thống sẽ hiển thị toàn bộ lịch sử của sản phẩm từ Giai đoạn 1 đến 3, giúp khách hàng có đầy đủ thông tin để đánh giá sản phẩm có "sạch" hay không.

## 🛠️ KIẾN TRÚC HỆ THỐNG & CÔNG NGHỆ (TECH STACK)

Hệ thống được xây dựng dựa trên kiến trúc 3 tầng đơn giản:

*   **Tầng Dữ liệu (Blockchain Core - `Python`)**:
    *   Sử dụng một `List` trong Python để mô phỏng chuỗi các `Block`.
    *   Mỗi `Block` là một đối tượng chứa các thông tin: `Index`, `Timestamp`, `Data` (dữ liệu giao dịch), `Hash` (mã băm của khối hiện tại), và `Previous Hash` (mã băm của khối trước đó).
    *   Các khối được móc xích với nhau thông qua `Previous Hash`, đảm bảo tính toàn vẹn của chuỗi.

*   **Tầng Giao tiếp (Backend API - `Flask`)**:
    *   Sử dụng thư viện Flask của Python để xây dựng các API endpoint.
    *   API đóng vai trò là "cổng giao tiếp", nhận yêu cầu từ giao diện người dùng (Frontend) và tương tác với lõi Blockchain (thêm khối mới, truy vấn chuỗi).

*   **Tầng Hiển thị (Frontend - `HTML/CSS`)**:
    *   Giao diện web đơn giản được xây dựng bằng HTML và CSS.
    *   **Trang cho Nông dân:** Cung cấp form nhập liệu để ghi lại các hoạt động canh tác.
    *   **Trang cho Khách hàng:** Cung cấp ô tìm kiếm để tra cứu lịch sử nông sản theo mã.

## 🧱 CẤU TRÚC DỮ LIỆU CỦA MỘT BLOCK

Mỗi khối trong chuỗi sẽ có cấu trúc dữ liệu dạng JSON như sau:

```json
{
    "index": 1,
    "timestamp": 1672531200,
    "data": "Gieo hạt giống Cải bẹ xanh, Lô đất A",
    "previous_hash": "0",
    "hash": "a1b2c3d4e5f6..."
}
```

Trong đó, `previous_hash` chính là "sợi dây xích" kết nối khối này với khối trước đó. Nếu ai đó cố tình sửa đổi dữ liệu của một khối trong quá khứ, mã băm sẽ thay đổi, làm cho "sợi dây xích" này bị "đứt" và chuỗi sẽ không còn hợp lệ.