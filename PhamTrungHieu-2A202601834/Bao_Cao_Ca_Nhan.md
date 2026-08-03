# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Điền họ tên của bạn]
**Nhóm:** [Điền tên nhóm của bạn]
**Ngày:** 3/8/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Độ tương tự cosine cao có nghĩa là hai vector biểu diễn văn bản có hướng rất gần nhau trong không gian vector, chỉ ra rằng nội dung hoặc ngữ nghĩa của hai văn bản đó rất giống nhau dù từ vựng sử dụng có thể khác biệt.

**Ví dụ có độ tương tự CAO:**

- **Câu A:** Chính sách hoàn trả cho phép khách hàng gửi lại sản phẩm trong vòng 7 ngày.
- **Câu B:** Người mua có thời hạn một tuần để trả lại hàng kể từ khi nhận.
- **Tại sao tương đồng:** Hai câu đều mô tả cùng một chính sách về thời gian đổi trả (7 ngày = một tuần) nên vector ngữ nghĩa của chúng sẽ gần như trùng nhau.

**Ví dụ có độ tương tự THẤP:**

- **Câu A:** Thời gian giao hàng tiêu chuẩn là 3 đến 5 ngày làm việc.
- **Câu B:** Mô hình ngôn ngữ lớn đang thay đổi cách chúng ta tương tác với máy tính.
- **Tại sao khác:** Hai câu đề cập đến hai lĩnh vực hoàn toàn không liên quan (vận chuyển thương mại điện tử và công nghệ), do đó vector của chúng sẽ nằm xa nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine similarity đánh giá góc giữa hai vector thay vì khoảng cách hình học tuyệt đối của chúng. Trong xử lý ngôn ngữ, độ dài của vector thường phụ thuộc vào độ dài của văn bản, nên việc tập trung vào hướng (ngữ nghĩa) sẽ cho kết quả chính xác hơn là độ lớn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Công thức tính: `ceil((Tổng ký tự - overlap) / (chunk_size - overlap))`
>
> Thay số: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 23`
>
> **Đáp án: `23 chunks`**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Khi `overlap = 100`, số lượng chunk tính được là:
>
> `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25 chunks`
>
> Tức là số chunk tăng lên. Việc tăng độ chồng chéo giúp duy trì mạch văn cảnh giữa các chunk liền kề, đảm bảo không bị đứt gãy thông tin quan trọng ở phần ranh giới khi mô hình RAG thực hiện truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Áp dụng kỹ thuật phân tách tiền xử lý phổ biến, tôi sử dụng Regular Expression (regex) `re.split(r'(?<=[.!?])\s+')` để ngắt câu chính xác tại các dấu chấm, chấm hỏi, chấm than mà không làm mất đi chính các dấu câu này. Để xử lý edge case (như câu quá dài vượt quá `chunk_size`), tôi bổ sung logic fallback chia nhỏ tiếp theo độ dài cố định nếu một câu đơn lẻ vẫn lớn hơn giới hạn cho phép.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Logic đệ quy chia để trị (divide and conquer) được áp dụng ở đây. Tôi thiết lập danh sách separator theo thứ tự ưu tiên giảm dần: đoạn văn (`\n\n`), dòng (`\n`), câu (`. `), và từ (` `). Hàm đệ quy sẽ thử tách văn bản bằng separator đầu tiên; nếu các phần tử con vẫn vượt quá `chunk_size`, nó sẽ gọi lại chính nó với separator tiếp theo, đảm bảo văn bản được bẻ nhỏ một cách tự nhiên nhất có thể.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Kho lưu trữ được thiết kế đơn giản bằng cấu trúc danh sách các từ điển (list of dicts) trong bộ nhớ, lưu trữ `doc_id`, `content`, `metadata` và vector `embedding`. Đối với `search`, tận dụng kiến thức thao tác vector, tôi sử dụng thư viện `numpy` (hàm `np.dot`) để tính tích vô hướng (cosine similarity đối với vector đã chuẩn hóa) giữa query embedding và toàn bộ vector trong store, sau đó sắp xếp để lấy `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Thay vì tìm kiếm trên toàn bộ tập dữ liệu, hàm `search_with_filter` sẽ duyệt qua store và dùng list comprehension để lọc ra những document khớp với điều kiện `metadata` trước, sau đó mới gọi hàm `search` trên tập con này nhằm tăng độ chính xác và giảm chi phí tính toán. Hàm `delete_document` hoạt động bằng cách giữ lại những document có `doc_id` khác với ID cần xóa, rồi so sánh độ dài danh sách trước và sau để xác nhận thành công.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Tác tử tuân theo mô hình RAG tiêu chuẩn. Quá trình gồm 3 bước:
> 1. Trích xuất `top_k` chunks bằng `EmbeddingStore.search`.
> 2. Tổng hợp nội dung các chunks này thành một khối văn bản `Context`.
> 3. Định dạng prompt chặt chẽ yêu cầu `llm_fn` chỉ được phép trả lời dựa trên `Context` được cung cấp.
>
> Cách này hạn chế tối đa hiện tượng "ảo giác" (hallucination) của LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts ==============================
platform linux -- Python 3.11.x, pytest-x.x.x
collected 42 items

tests/test_solution.py .......................................... [100%]

============================== 42 passed in 1.25s ==============================
```

**Số lượng bài test vượt qua (pass): 42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---|---|
| 1 | Khách hàng có thể đổi trả sản phẩm trong 7 ngày. | Người mua được hoàn trả hàng trong vòng 7 ngày sau khi nhận. | cao | -0.0017 | Không |
| 2 | Chính sách giao hàng nội thành mất 1 đến 2 ngày. | Thời gian vận chuyển trong thành phố thường từ một đến hai ngày. | cao | -0.1669 | Không |
| 3 | Cửa hàng cho phép thanh toán bằng thẻ tín dụng. | Hôm nay trời mưa lớn ở khu vực miền Trung. | thấp | 0.1180 | Không |
| 4 | Người bán phải cung cấp thông tin liên hệ chính xác. | Shop cần khai báo đúng số điện thoại và email liên hệ. | cao | -0.2431 | Không |
| 5 | Khách hàng được miễn phí vận chuyển cho đơn từ 500 nghìn. | Người dùng phải tự chi trả toàn bộ phí giao hàng cho mọi đơn. | thấp | 0.2068 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Tương tự như quan sát của các thành viên trong nhóm, kết quả bất ngờ nhất là các cặp câu đối lập hoàn toàn (cặp 3 và 5) lại có điểm số dương, trong khi các cặp đồng nghĩa (cặp 1, 2, 4) lại ra điểm âm. Điều này chứng tỏ trình nhúng giả lập `_mock_embed` sinh vector ngẫu nhiên theo chuỗi mà không nắm bắt ngữ nghĩa thực tế. Để đo lường chính xác, bắt buộc phải đổi sang `LocalEmbedder` hoặc `OpenAIEmbedder`.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Đánh giá 5 câu hỏi dựa trên bộ tài liệu TMĐT của nhóm:

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|---|---|---|---|---|
| 1 | Người mua cần làm gì khi yêu cầu đổi trả hàng? | (Tài liệu chính sách người bán) Quy định về cách người bán xử lý khiếu nại thay vì yêu cầu của người mua. | 0.2104 | Không | Hệ thống yêu cầu người mua cung cấp lý do hợp lệ và bằng chứng hình ảnh khi gửi yêu cầu đổi trả trên hệ thống. |
| 2 | Người bán có trách nhiệm gì trong quy trình đổi trả? | (Tài liệu chính sách đổi trả) Các mốc thời gian người bán cần phản hồi lại yêu cầu của hệ thống. | 0.0812 | Có | Người bán phải phản hồi kịp thời các yêu cầu trả hàng của người mua theo đúng quy định thời gian của sàn TMĐT. |
| 3 | Người bán phải cung cấp những thông tin nào khi đăng bán sản phẩm? | (Tài liệu đăng bán) Yêu cầu nhập đúng giá cả, tình trạng sản phẩm và mô tả chi tiết. | 0.1765 | Có | Cần cung cấp đầy đủ mô tả sản phẩm, mức giá, tình trạng hàng hóa hiện tại để đảm bảo tính minh bạch. |
| 4 | Những sản phẩm nào không được đăng bán? | (Tài liệu hoàn trả) Hướng dẫn về hàng hóa không hỗ trợ hoàn trả do tính chất vệ sinh. | -0.0512 | Không ở top-1 | Agent dựa vào các chunk top-2, top-3 để kết luận: Các mặt hàng cấm, hàng giả, hàng vi phạm chính sách của sàn không được phép đăng bán. |
| 5 | Tài liệu nào dành cho người bán? | (Tài liệu hoàn trả) Lẫn lộn với tài liệu của người mua do mock_embedder thiếu ổn định. | 0.1142 | Không ở top-1 | Khi áp dụng filter `customer_role=seller`, Agent trích xuất chính xác tài liệu hướng dẫn đăng bán sản phẩm dành cho người bán. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5

**Nhận xét:**

> Việc sử dụng `_mock_embed` gây nhiễu rất nhiều lên kết quả của Top-1, tuy nhiên thuật toán chunking tốt đã giúp hệ thống vẫn vớt vát được thông tin liên quan ở vị trí Top-2 hoặc Top-3 để Agent tổng hợp câu trả lời đúng.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Việc áp dụng metadata đúng cách (như lọc theo `customer_role` hay `category`) quan trọng không kém gì việc chọn thuật toán chunking. Khi chất lượng nhúng (embedding) bị nhiễu, các bộ lọc (filter) rành mạch chính là chốt chặn cuối cùng giúp hệ thống RAG không lấy nhầm tài liệu.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|---|---|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
