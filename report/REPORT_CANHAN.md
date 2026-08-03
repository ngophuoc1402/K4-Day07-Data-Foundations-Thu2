# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Ngô Minh Phước
**Nhóm:** [Chờ bạn cập nhật tên nhóm]
**Ngày:** 3/8/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Nghĩa là hai câu có hướng biểu diễn vector gần nhau, nên nội dung hoặc ý nghĩa của chúng khá giống nhau dù cách viết có thể khác.

**Ví dụ có độ tương tự CAO:**
- Câu A: Khách hàng có thể đổi trả sản phẩm trong vòng 7 ngày sau khi nhận hàng.
- Câu B: Người mua được phép hoàn trả hàng trong 7 ngày kể từ ngày nhận.
- Tại sao tương đồng: Hai câu diễn đạt gần như cùng một chính sách đổi trả, chỉ khác cách dùng từ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Chính sách giao hàng quy định thời gian vận chuyển nội thành từ 1 đến 2 ngày.
- Câu B: Trí tuệ nhân tạo đang được ứng dụng trong nhận diện hình ảnh y tế.
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác nhau nên vector ngữ nghĩa sẽ cách xa nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung vào hướng của vector nên phản ánh mức độ giống nhau về ngữ nghĩa tốt hơn, dù độ dài vector có thể khác nhau. Với text embeddings, điều quan trọng thường là nội dung có cùng ý hay không, chứ không phải độ lớn tuyệt đối của vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)`
> Đáp án: `23 chunks`

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi `overlap=100`, số chunk là `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25`, nên số lượng chunk tăng từ 23 lên 25. Ta muốn overlap lớn hơn để giữ lại nhiều ngữ cảnh ở ranh giới giữa hai chunk, giúp giảm nguy cơ mất ý khi truy xuất hoặc trả lời câu hỏi.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])(?:\s+|\n+)` để tách câu tại vị trí ngay sau dấu `.`, `!`, `?` rồi theo sau là khoảng trắng hoặc xuống dòng. Cách này giữ lại dấu câu trong từng sentence và đủ nhanh cho dữ liệu text thông thường. Tôi cũng xử lý edge case như chuỗi rỗng, chuỗi chỉ có khoảng trắng, hoặc sau khi tách không còn câu hợp lệ thì fallback về `text.strip()`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Tôi triển khai theo hướng đệ quy: ưu tiên tách theo `\n\n`, rồi `\n`, rồi `. `, rồi khoảng trắng, cuối cùng mới cắt cứng theo số ký tự nếu không còn separator nào phù hợp. Base case là khi đoạn hiện tại rỗng, đã ngắn hơn hoặc bằng `chunk_size`, hoặc danh sách separator đã hết. Trong quá trình tách, tôi cố gắng gom lại các phần nhỏ vào buffer để chunk tạo ra vẫn tự nhiên và không bị quá vụn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Tôi chuẩn hóa mỗi document thành một record gồm `id`, `doc_id`, `content`, `metadata` và `embedding`, rồi lưu vào danh sách trong bộ nhớ cho luồng mặc định của bài lab. Khi search, tôi embed câu query, tính score bằng dot product giữa query embedding và embedding của từng record, sau đó sắp xếp giảm dần để lấy `top_k`. Cách làm này đơn giản, dễ kiểm thử và đủ rõ ràng để sau này thay bằng backend như ChromaDB.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Với `search_with_filter`, tôi lọc theo metadata trước rồi mới chạy similarity search trên tập record đã thu hẹp để giảm nhiễu và bám sát yêu cầu bài toán. Với `delete_document`, tôi xóa toàn bộ record có `doc_id` tương ứng và so sánh kích thước store trước/sau để trả về `True` hoặc `False`. Cách này giúp hành vi dễ hiểu và cũng phù hợp với các bài test về filter và delete.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Tôi triển khai agent theo flow RAG cơ bản: truy xuất `top_k` chunks liên quan từ `EmbeddingStore`, ghép chúng thành phần context, rồi tạo prompt để gọi `llm_fn`. Prompt gồm phần chỉ dẫn ngắn, phần context và câu hỏi của người dùng. Cách inject này giúp câu trả lời có grounding rõ ràng vào dữ liệu truy xuất được và rất phù hợp cho một knowledge base agent tối giản.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
collected 42 items

42 tests PASSED

Tất cả các phần chính đều đã vượt qua kiểm thử, gồm:
FixedSizeChunker, SentenceChunker, RecursiveChunker,
compute_similarity, ChunkingStrategyComparator,
EmbeddingStore và KnowledgeBaseAgent.
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khách hàng có thể đổi trả sản phẩm trong 7 ngày. | Người mua được hoàn trả hàng trong vòng 7 ngày sau khi nhận. | cao | -0.0017 | Không |
| 2 | Chính sách giao hàng nội thành mất 1 đến 2 ngày. | Thời gian vận chuyển trong thành phố thường từ một đến hai ngày. | cao | -0.1669 | Không |
| 3 | Cửa hàng cho phép thanh toán bằng thẻ tín dụng. | Hôm nay trời mưa lớn ở khu vực miền Trung. | thấp | 0.1180 | Không |
| 4 | Người bán phải cung cấp thông tin liên hệ chính xác. | Shop cần khai báo đúng số điện thoại và email liên hệ. | cao | -0.2431 | Không |
| 5 | Khách hàng được miễn phí vận chuyển cho đơn từ 500 nghìn. | Người dùng phải tự chi trả toàn bộ phí giao hàng cho mọi đơn. | thấp | 0.2068 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điều bất ngờ nhất là các cặp câu rất gần nghĩa như cặp 1, 2 và 4 lại cho điểm thấp hoặc âm, trong khi một số cặp khác nghĩa lại cho điểm dương. Điều này cho thấy tôi đang dùng `_mock_embed`, tức là embedding giả lập phục vụ unit test chứ không phản ánh ngữ nghĩa thật. Vì vậy, để đánh giá chất lượng retrieval hoặc so sánh chiến lược chunking một cách nghiêm túc, cần dùng local embedder hoặc OpenAI embedder thay cho mock.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chưa có bộ benchmark chính thức của nhóm tại thời điểm viết báo cáo, nên tôi chạy **benchmark cá nhân tạm thời** trên bộ dữ liệu khởi động trong `data/k4_ecommerce/` để tự kiểm tra chất lượng truy xuất của mã nguồn `src`. Các kết quả dưới đây hữu ích để đánh giá hiện trạng pipeline, nhưng vẫn cần được thay bằng 5 câu hỏi chung của nhóm khi hoàn thiện phần nhóm.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua cần làm gì khi yêu cầu đổi trả hàng? | Chunk từ tài liệu `k4-seller-listing`; top-1 bị nhiễu và không trả lời trực tiếp yêu cầu đổi trả của người mua | 0.1929 | Không | Người mua cần gửi yêu cầu đổi trả trong thời hạn được nêu trên trang sản phẩm hoặc chính sách của sàn và kèm bằng chứng phù hợp nếu hàng bị lỗi hoặc không đúng mô tả. |
| 2 | Người bán có trách nhiệm gì trong quy trình đổi trả? | Chunk từ tài liệu `k4-returns-policy`; có chứa thông tin liên quan đến trách nhiệm phản hồi của người bán | 0.0680 | Có | Người bán có trách nhiệm phản hồi theo quy trình của sàn trong quá trình đổi trả. |
| 3 | Người bán phải cung cấp những thông tin nào khi đăng bán sản phẩm? | Chunk từ tài liệu `k4-seller-listing`; nêu rõ giá, mô tả và tình trạng hàng | 0.1948 | Có | Người bán phải cung cấp thông tin sản phẩm chính xác, bao gồm giá, mô tả và tình trạng hàng. |
| 4 | Những sản phẩm nào không được đăng bán? | Top-1 bị lệch sang tài liệu `k4-returns-policy`, nhưng trong top-3 vẫn có chunk thuộc `k4-seller-listing` liên quan đến hàng bị hạn chế hoặc bị cấm | -0.0121 | Không ở top-1 | Các sản phẩm bị hạn chế hoặc bị cấm không được đăng bán. |
| 5 | Tài liệu nào dành cho người bán? | Top-1 bị nhiễu từ `k4-returns-policy`; khi lọc metadata `customer_role=seller`, kết quả đúng là `k4-seller-listing` | 0.1396 | Không ở top-1 | Tài liệu dành cho người bán là quy định đăng bán, có metadata `customer_role` là `seller`. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5
> Nhận xét: với `_mock_embed`, retrieval vẫn khá nhiễu dù nhiều câu hỏi còn tìm thấy thông tin đúng trong top-3. Điều này phù hợp với cảnh báo trong README rằng mock embedding chỉ nên dùng cho unit test, không nên dùng để kết luận chất lượng retrieval.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Điều tôi thấy hữu ích nhất là chiến lược dữ liệu và metadata thường ảnh hưởng đến retrieval nhiều không kém bản thân thuật toán chunking. Khi tài liệu có `source_url`, `category`, `language`, `customer_role` hoặc `document_version` rõ ràng, việc lọc và kiểm chứng câu trả lời trở nên dễ hơn nhiều. Tôi cũng học được rằng không nên kết luận chất lượng chiến lược chỉ từ unit test, mà cần benchmark trên bộ tài liệu thật với embedder ngữ nghĩa phù hợp.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **57 / 60** |
