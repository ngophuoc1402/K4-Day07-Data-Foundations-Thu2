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
| 1 | Chính sách trả hàng và hoàn tiền | https://help.shopee.vn/portal/4/article/77251 | 3.298 | `customer_role=both`, `category=returns` |
| 2 | Chính sách vận chuyển Shopee | https://help.shopee.vn/portal/4/article/77250 | 3.305 | `customer_role=both`, `category=shipping` |
| 3 | Điều kiện sử dụng mã miễn phí vận chuyển | https://help.shopee.vn/portal/4/article/79606 | 1.379 | `customer_role=buyer`, `category=shipping_promo` |
| 4 | Quy định về đăng bán sản phẩm | https://help.shopee.vn/portal/4/article/77246 | 2.119 | `customer_role=seller`, `category=listing` |
| 5 | Chính sách cấm/hạn chế sản phẩm | https://help.shopee.vn/portal/4/article/77247 | 1.363 | `customer_role=seller`, `category=prohibited_products` |

Hai file starter dùng `example.com` đã được chuyển sang `data/starter_examples/`, nên mọi cách ingest trực tiếp `data/k4_ecommerce/` đều nhận đúng 5 tài liệu chung. Danh sách nguồn có thể kiểm tra trong `data/k4_ecommerce/sources.csv`.

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
| `document_version` | string | `published-2024-08-14`, `not-stated` | Ngày/phiên bản nguồn công bố; không dùng ngày thu thập thay thế |

---

## 2. Thiết kế chiến lược (Strategy Design) — 15 điểm

### Baseline với `chunk_size=200`

Kết quả từ `ChunkingStrategyComparator().compare()`:

| Tài liệu | Chiến lược | Số chunk | Độ dài TB | Nhận xét |
|----------|------------|----------|------------|----------|
| Trả hàng/hoàn tiền | FixedSize | 22 | 198 | Ổn định nhưng cắt giữa danh sách |
| Trả hàng/hoàn tiền | Sentence | 14 | 234 | Giữ ranh giới câu nhưng có chunk dài |
| Trả hàng/hoàn tiền | Recursive | 24 | 136 | Tôn trọng đoạn nhưng dễ phân mảnh |
| Vận chuyển | FixedSize | 22 | 198 | Có thể cắt giữa điều khoản |
| Vận chuyển | Sentence | 19 | 172 | Rõ nghĩa nhưng độ dài không đều |
| Vận chuyển | Recursive | 26 | 125 | Chia chi tiết theo cấu trúc |
| Mã freeship | FixedSize | 9 | 198 | Phù hợp baseline tài liệu ngắn |
| Mã freeship | Sentence | 7 | 196 | Giữ trọn các điều kiện gần nhau |
| Mã freeship | Recursive | 11 | 124 | Chia tự nhiên theo mục và đoạn |
| Quy định đăng bán | FixedSize | 14 | 198 | Baseline ổn định |
| Quy định đăng bán | Sentence | 5 | 421 | Câu dài làm chunk vượt 200 ký tự |
| Quy định đăng bán | Recursive | 17 | 123 | Giữ được ranh giới mục |
| Sản phẩm cấm/hạn chế | FixedSize | 9 | 196 | Có thể cắt giữa danh sách |
| Sản phẩm cấm/hạn chế | Sentence | 4 | 339 | Ít chunk nhưng khá dài |
| Sản phẩm cấm/hạn chế | Recursive | 14 | 96 | Nhiều chunk ngắn |

### Chiến lược từng thành viên

**Ngô Minh Phước — RecursiveChunker**

- Cấu hình: `RecursiveChunker(chunk_size=700)`.
- Lý do: policy có nhiều heading, đoạn và danh sách; recursive ưu tiên ranh giới cấu trúc trước khi cắt cứng.
- Kết quả benchmark sau khi làm sạch corpus: **8/10**, tạo **23 chunks**.

**Nguyễn Xuân Quân — SentenceChunker**

- Cấu hình: `SentenceChunker(max_sentences_per_chunk=3)`.
- Lý do: mỗi câu policy thường biểu diễn một quy tắc; nhóm ba câu giữ đủ ngữ cảnh mà không tạo chunk quá dài.
- Kết quả benchmark sau khi làm sạch corpus: **7/10**, tạo **49 chunks**.

**Phạm Trung Hiếu — FixedSizeChunker**

- Cấu hình: `FixedSizeChunker(chunk_size=500, overlap=100)`.
- Lý do: làm baseline có overlap 20%, giảm mất ngữ cảnh tại biên chunk.
- Kết quả benchmark sau khi làm sạch corpus: **9/10**, tạo **31 chunks**.

### So sánh

| Thành viên | Chiến lược | Điểm /10 | Điểm mạnh | Điểm yếu |
|------------|------------|----------|-----------|----------|
| Ngô Minh Phước | Recursive (700) | 8 | Q3-Q5 có đủ căn cứ | Q1 và Q2 thiếu độ phủ gold answer |
| Nguyễn Xuân Quân | Sentence (3 câu) | 7 | Q3-Q4 giữ trọn câu trả lời | Top-3 thiếu nhiều ý ở Q1, Q2 và Q5 |
| Phạm Trung Hiếu | FixedSize (500/100) | 9 | Độ phủ tốt nhất; Q1 và Q3-Q5 đủ ý | Q2 chỉ đứng top-2 |

`FixedSizeChunker` tốt nhất trong lượt chạy đã làm sạch với 9/10. Kết quả được tạo lại bằng `python3 scripts/run_group_benchmark.py`; script dùng lexical hashing có chuẩn hóa tiếng Việt và kiểm tra độ phủ của toàn bộ các ý bắt buộc trong gold answer. Đây là điểm retrieval/evidence coverage; nhóm không trình bày nó như điểm đánh giá tự động câu trả lời do LLM sinh ra.

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

Với mỗi câu hỏi, script lấy top-3, kiểm tra đúng `doc_id`, rồi đo xem hợp các chunk đã truy xuất có bao phủ **tất cả** ý bắt buộc của gold answer hay không. Các cụm từ đồng nghĩa được khai báo theo từng nhóm yêu cầu, thay vì chỉ cần khớp một từ khóa bất kỳ:

- **2 điểm:** chunk liên quan ở top-1 và hợp top-3 bao phủ đủ toàn bộ gold answer.
- **1 điểm:** top-3 có chunk liên quan nhưng chunk đúng không ở top-1 hoặc bằng chứng chưa đủ mọi ý.
- **0 điểm:** top-3 không chứa chunk mang thông tin cần thiết.

Script in thêm `gold_coverage=x/y` để việc chấm có thể kiểm tra lại. Câu trả lời tóm tắt trong báo cáo là phần đọc và tổng hợp thủ công từ các chunk đã in; không phải output từ một LLM production.

| # | Chiến lược tốt nhất | Chunk đúng trong top-3? | Nhận xét |
|---|---------------------|--------------------------|----------|
| 1 | FixedSize | Có, top-1 | Hợp top-3 bao phủ đủ 8/8 nhóm trường hợp |
| 2 | FixedSize | Có, top-2 | Một chunk chứa đủ 15 ngày và ngoại lệ 24 giờ |
| 3 | Cả ba | Có, top-1 | Từ khóa COD/chuyển khoản có tính phân biệt cao |
| 4 | Cả ba | Có, top-1 | Bằng chứng bao phủ kiểm tra bao bì và từ chối nhận hàng |
| 5 | FixedSize/Recursive + metadata filter | Có, top-1 | Hợp top-3 bao phủ đủ 6/6 yêu cầu thông tin |

Metadata filter hữu ích nhất ở Q5: `customer_role=seller` loại ba tài liệu buyer/both và chỉ tìm trong hai chính sách dành cho người bán. Đánh đổi là filter quá chặt có thể bỏ tài liệu `both`, vì vậy chỉ áp dụng khi vai trò trong câu hỏi đã rõ. Với cách chấm nghiêm ngặt trên, ba chiến lược lần lượt đạt FixedSize 9/10, Sentence 7/10 và Recursive 8/10.

### Failure analysis

Q1 là failure case rõ nhất của SentenceChunker: dù chunk liên quan đứng top-1, hợp top-3 chỉ bao phủ 3/8 nhóm trường hợp trong gold answer. Q2 cũng chỉ bao phủ 1/2 mốc thời gian. Nguyên nhân là danh sách và ngoại lệ bị tách thành nhiều sentence chunks nhưng lexical top-3 ưu tiên các đoạn lặp lại từ trong query. Cách cải thiện là chunk theo heading/section hoặc tăng số câu mỗi chunk, rồi kiểm tra lại bằng embedding đa ngôn ngữ thật.

---

## 4. Demo & Bài học nhóm — 5 điểm

### Kịch bản demo

1. Giới thiệu 5 tài liệu và metadata `customer_role`, `category`, `source_url`.
2. Chạy `python3 scripts/run_group_benchmark.py` để hiển thị thứ hạng, độ phủ gold answer và các điểm 9/10, 7/10, 8/10.
3. Dùng Q4 minh họa SentenceChunker giữ trọn câu trả lời.
4. Dùng Q5 minh họa metadata filtering dành cho seller.
5. Trình bày failure case Q2 và hướng cải thiện.

### Bài học

- Fixed-size có overlap đạt điểm cao nhất trong lượt chạy hiện tại vì top-3 bao phủ tốt các danh sách dài.
- Recursive giữ cấu trúc tốt nhưng cần điều chỉnh kích thước cho danh sách dài.
- Fixed-size hữu ích làm baseline nhưng overlap không loại bỏ hoàn toàn việc cắt giữa câu.
- Metadata filter tăng precision cấp tài liệu; chunking vẫn quyết định đáp án đứng top-1 hay top-3.
- Mock embedding chỉ phù hợp unit test. Lượt benchmark này dùng lexical hashing để tái lập offline; khi demo có đủ dependency, nhóm ưu tiên kiểm tra thêm bằng embedding đa ngôn ngữ thật.

### Nếu làm lại

Nhóm đã loại phần ghi chú benchmark khỏi corpus. Bước tiếp theo là thêm metadata `section`, thử chunker theo heading và chạy `paraphrase-multilingual-MiniLM-L12-v2` khi môi trường có `sentence-transformers`.

---

## Tự đánh giá

| Tiêu chí | Điểm |
|----------|------|
| Lựa chọn tài liệu | 10 / 10 |
| Thiết kế chiến lược | 14 / 15 |
| Chất lượng truy xuất | 9 / 10 |
| Demo | 5 / 5 |
| **Tổng** | **38 / 40** |
