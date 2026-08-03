# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** K4 — Thứ 2
**Thành viên:**
- Ngô Minh Phước — 2A202601576
- Nguyễn Xuân Quân — 2A202601976
- Phạm Trung Hiếu — 2A202601834

**Ngày:** 2026-08-03

> Báo cáo này dùng chung một corpus, một bộ 5 benchmark queries và ba chiến lược chunking. Phần cá nhân của từng thành viên được lưu trong thư mục mang tên thành viên tại repository root.

---

## 1. Lựa chọn tài liệu (Document Set Quality) — 10 điểm

### Phạm vi

Nhóm tập trung vào chính sách thương mại điện tử và hỗ trợ khách hàng của Shopee: trả hàng/hoàn tiền, vận chuyển, mã miễn phí vận chuyển, quy định đăng bán và sản phẩm cấm/hạn chế. Tất cả tài liệu benchmark nằm trong `data/k4_ecommerce/`.

### Danh sách tài liệu

| # | Tài liệu | Nguồn chính thức | Số ký tự | Metadata chính |
|---|----------|------------------|-----------|----------------|
| 1 | Chính sách trả hàng và hoàn tiền | https://help.shopee.vn/portal/4/article/77251 | 3.846 | `customer_role=both`, `category=returns` |
| 2 | Chính sách vận chuyển Shopee | https://help.shopee.vn/portal/4/article/77250 | 3.937 | `customer_role=both`, `category=shipping` |
| 3 | Điều kiện sử dụng mã miễn phí vận chuyển | https://help.shopee.vn/portal/4/article/79606 | 1.910 | `customer_role=buyer`, `category=shipping_promo` |
| 4 | Quy định về đăng bán sản phẩm | https://help.shopee.vn/portal/4/article/77246 | 2.390 | `customer_role=seller`, `category=listing` |
| 5 | Chính sách cấm/hạn chế sản phẩm | https://help.shopee.vn/portal/4/article/77247 | 1.646 | `customer_role=seller`, `category=prohibited_products` |

Hai file starter dùng `example.com` vẫn được giữ theo cấu trúc ban đầu của đề nhưng bị loại khỏi corpus benchmark. Danh sách nguồn có thể kiểm tra trong `data/k4_ecommerce/sources.csv`.

### Quản trị dữ liệu

- [x] Corpus gồm 5 nguồn công khai từ Shopee Help Center.
- [x] Không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `doc_id`, `source_url`, `retrieved_at` và `document_version`.
- [x] Mỗi tài liệu có `customer_role`, `category` và `language` phục vụ filtering.

### Metadata schema

| Trường | Kiểu | Ví dụ | Mục đích |
|--------|------|-------|----------|
| `doc_id` | string | `shopee-returns-refund-policy` | Truy vết, cập nhật hoặc xóa tài liệu gốc |
| `customer_role` | string | `buyer`, `seller`, `both` | Lọc chính sách theo vai trò người dùng |
| `category` | string | `returns`, `shipping`, `listing` | Thu hẹp kết quả theo chủ đề |
| `language` | string | `vi` | Hỗ trợ corpus đa ngôn ngữ về sau |
| `source_url` | string | URL Help Center | Kiểm chứng nguồn câu trả lời |
| `retrieved_at` | date string | `2026-08-03` | Theo dõi ngày thu thập |
| `document_version` | string | `help-center-2026-08-03` | Theo dõi phiên bản chính sách |

---

## 2. Thiết kế chiến lược (Strategy Design) — 15 điểm

### Baseline với `chunk_size=200`

Kết quả từ `ChunkingStrategyComparator().compare()`:

| Tài liệu | Chiến lược | Số chunk | Độ dài TB | Nhận xét |
|----------|------------|----------|------------|----------|
| Trả hàng/hoàn tiền | FixedSize | 26 | 196 | Ổn định nhưng cắt giữa danh sách |
| Trả hàng/hoàn tiền | Sentence | 25 | 152 | Dễ đọc, giữ ranh giới câu |
| Trả hàng/hoàn tiền | Recursive | 28 | 135 | Tôn trọng đoạn nhưng dễ phân mảnh |
| Vận chuyển | FixedSize | 26 | 199 | Có thể cắt giữa điều khoản |
| Vận chuyển | Sentence | 34 | 114 | Rõ nghĩa nhưng có nhiều chunk ngắn |
| Vận chuyển | Recursive | 31 | 125 | Cân bằng giữa đoạn và chi tiết |
| Mã freeship | FixedSize | 13 | 193 | Phù hợp baseline tài liệu ngắn |
| Mã freeship | Sentence | 15 | 126 | Truy xuất tốt từng điều kiện |
| Mã freeship | Recursive | 15 | 125 | Chia tự nhiên theo mục và đoạn |

### Chiến lược từng thành viên

**Ngô Minh Phước — RecursiveChunker**

- Cấu hình: `RecursiveChunker(chunk_size=700)`.
- Lý do: policy có nhiều heading, đoạn và danh sách; recursive ưu tiên ranh giới cấu trúc trước khi cắt cứng.
- Kết quả benchmark: **7/10**, tạo **24 chunks**.

**Nguyễn Xuân Quân — SentenceChunker**

- Cấu hình: `SentenceChunker(max_sentences_per_chunk=3)`.
- Lý do: mỗi câu policy thường biểu diễn một quy tắc; nhóm ba câu giữ đủ ngữ cảnh mà không tạo chunk quá dài.
- Kết quả benchmark: **8/10**, tạo **59 chunks**.

**Phạm Trung Hiếu — FixedSizeChunker**

- Cấu hình: `FixedSizeChunker(chunk_size=500, overlap=100)`.
- Lý do: làm baseline có overlap 20%, giảm mất ngữ cảnh tại biên chunk.
- Kết quả benchmark: **7/10**, tạo **32 chunks**.

### So sánh

| Thành viên | Chiến lược | Điểm /10 | Điểm mạnh | Điểm yếu |
|------------|------------|----------|-----------|----------|
| Ngô Minh Phước | Recursive (700) | 7 | Giữ cấu trúc đoạn, Q2-Q4 tốt | Danh sách dài ở Q1 bị phân tách |
| Nguyễn Xuân Quân | Sentence (3 câu) | 8 | Tốt nhất tổng thể; Q1, Q3, Q4 ở top-1 | Heading ngắn gây nhiễu Q2; Q5 ở top-3 |
| Phạm Trung Hiếu | FixedSize (500/100) | 7 | Baseline ổn định, overlap giữ ngữ cảnh | Có thể cắt giữa câu; Q2/Q4 ở top-3 |

`SentenceChunker` tốt nhất trong lượt chạy này với 8/10. Kết quả được tạo lại bằng `python3 scripts/run_group_benchmark.py`; script dùng lexical hashing có chuẩn hóa tiếng Việt để benchmark offline, thay vì mock embedding ngẫu nhiên. Điểm này là kết quả đánh giá retrieval kết hợp với kiểm tra thủ công câu trả lời dựa trên context, không phải metric sinh tự động bởi một LLM-as-judge.

---

## 3. Benchmark & Chất lượng truy xuất — 10 điểm

### Năm câu hỏi và gold answers

| # | Query | Gold answer | Tài liệu/section chứa đáp án |
|---|-------|-------------|------------------------------|
| 1 | Người mua có thể yêu cầu trả hàng/hoàn tiền trong những trường hợp nào? | Không nhận/thiếu hàng, hàng giả, lỗi hoặc hư hại, giao sai, khác mô tả, hết hạn, người bán đồng ý, hoặc Trả hàng COM hợp lệ. | `shopee-returns-refund-policy`, mục các trường hợp yêu cầu |
| 2 | Thời hạn gửi yêu cầu trả hàng/hoàn tiền là bao lâu? | Thông thường 15 ngày từ khi giao thành công; thực phẩm tươi sống/đông lạnh là 24 giờ. | `shopee-returns-refund-policy`, mục thời hạn |
| 3 | Đơn COD/chuyển khoản cần điều kiện gì để nhận hoàn tiền? | Phải liên kết tài khoản Shopee với tài khoản ngân hàng hoặc ví hợp lệ như ShopeePay. | `shopee-returns-refund-policy`, mục hoàn tiền COD |
| 4 | Người mua nên làm gì khi bao bì bị rách, móp méo, vỡ hoặc ướt? | Kiểm tra bao bì và nên từ chối nhận hàng. | `shopee-shipping-policy`, mục khuyến cáo vận chuyển |
| 5 | Với `customer_role=seller`, quy định đăng bán yêu cầu thông tin sản phẩm thế nào? | Tiêu đề, hình ảnh, giá, mô tả phải thống nhất, chính xác, đúng quy định và không gây nhầm lẫn. | `shopee-seller-listing-policy`, mục yêu cầu thông tin |

### Kết quả chung

### Phương pháp chấm

Với mỗi câu hỏi, script lấy top-3 và xác định chunk liên quan bằng `doc_id` cùng các cụm từ kiểm chứng trong gold answer. Nhóm sau đó đọc context để kiểm tra câu trả lời tóm tắt:

- **2 điểm:** chunk liên quan ở top-1 và context đủ để trả lời đúng gold answer.
- **1 điểm:** chunk liên quan chỉ ở top-2/top-3 nhưng context vẫn đủ căn cứ.
- **0 điểm:** top-3 không chứa chunk mang thông tin cần thiết.

Script hiện tái lập phần retrieval và thứ hạng; câu trả lời trong báo cáo là phần tổng hợp được nhóm kiểm tra thủ công từ đúng các chunk đã in ra. Nhóm không tuyên bố đây là output từ một LLM production.

| # | Chiến lược tốt nhất | Chunk đúng trong top-3? | Nhận xét |
|---|---------------------|--------------------------|----------|
| 1 | Sentence | Có, top-1 | Các chunk tiếp theo bổ sung phần còn lại của danh sách |
| 2 | Recursive | Có, top-1 | Giữ 15 ngày và 24 giờ trong cùng ngữ cảnh |
| 3 | Cả ba | Có, top-1 | Từ khóa COD/chuyển khoản có tính phân biệt cao |
| 4 | Sentence/Recursive | Có, top-1 | Chunk giữ trọn hành động từ chối nhận hàng |
| 5 | Cả ba + metadata filter | Có, top-2 hoặc top-3 | Filter đúng tài liệu seller nhưng phần phạm vi vẫn gây nhiễu |

Metadata filter hữu ích nhất ở Q5: `customer_role=seller` loại ba tài liệu buyer/both và chỉ tìm trong hai chính sách dành cho người bán. Đánh đổi là filter quá chặt có thể bỏ tài liệu `both`, vì vậy chỉ áp dụng khi vai trò trong câu hỏi đã rõ. Với cách chấm trên, ba chiến lược lần lượt đạt FixedSize 7/10, Sentence 8/10 và Recursive 7/10.

### Failure analysis

Q2 là failure case rõ nhất của SentenceChunker: chunk ghi chú chỉ chứa cụm “thời hạn gửi yêu cầu” đứng top-1, còn chunk có đáp án 15 ngày và 24 giờ đứng top-2. Nguyên nhân là lexical retrieval ưu tiên trùng từ và phần ghi chú benchmark lặp lại heading. Cách cải thiện là loại ghi chú trước ingest, chunk theo heading/section và chạy lại với embedding đa ngôn ngữ thật.

---

## 4. Demo & Bài học nhóm — 5 điểm

### Kịch bản demo

1. Giới thiệu 5 tài liệu và metadata `customer_role`, `category`, `source_url`.
2. Chạy `python3 scripts/run_group_benchmark.py` để hiển thị thứ hạng retrieval và các điểm 7/10, 8/10, 7/10.
3. Dùng Q4 minh họa SentenceChunker giữ trọn câu trả lời.
4. Dùng Q5 minh họa metadata filtering dành cho seller.
5. Trình bày failure case Q2 và hướng cải thiện.

### Bài học

- Chunk theo câu phù hợp nhất với corpus policy hiện tại, nhưng heading/bullet ngắn vẫn có thể tạo nhiễu.
- Recursive giữ cấu trúc tốt nhưng cần điều chỉnh kích thước cho danh sách dài.
- Fixed-size hữu ích làm baseline nhưng overlap không loại bỏ hoàn toàn việc cắt giữa câu.
- Metadata filter tăng precision cấp tài liệu; chunking vẫn quyết định đáp án đứng top-1 hay top-3.
- Mock embedding chỉ phù hợp unit test. Lượt benchmark này dùng lexical hashing để tái lập offline; khi demo có đủ dependency, nhóm ưu tiên kiểm tra thêm bằng embedding đa ngôn ngữ thật.

### Nếu làm lại

Nhóm sẽ loại phần ghi chú trước ingest, thêm metadata `section`, thử chunker theo heading và chạy `paraphrase-multilingual-MiniLM-L12-v2` khi môi trường có `sentence-transformers`.

---

## Tự đánh giá

| Tiêu chí | Điểm |
|----------|------|
| Lựa chọn tài liệu | 10 / 10 |
| Thiết kế chiến lược | 14 / 15 |
| Chất lượng truy xuất | 8 / 10 |
| Demo | 5 / 5 |
| **Tổng** | **37 / 40** |
