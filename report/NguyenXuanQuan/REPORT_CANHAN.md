# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Xuân Quân
**Mã số sinh viên:** 2A202601976
**Nhóm:** K4
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Khi hai đoạn văn bản có độ tương tự cosine cao (gần 1.0), điều đó có nghĩa là hai vector đại diện cho chúng chỉ về cùng một hướng trong không gian embedding — tức là hai văn bản có nội dung/ý nghĩa rất gần nhau. Đây là dấu hiệu mô hình embedding đã "hiểu" rằng hai câu nói về cùng một khái niệm, dù từ ngữ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: `"Chính sách hoàn tiền trong 7 ngày kể từ khi nhận hàng."`
- Câu B: `"Khách hàng được hoàn lại tiền nếu trả hàng trong vòng 7 ngày."`
- Tại sao tương đồng: Cả hai câu đều diễn đạt cùng một quy định về chính sách hoàn tiền với thời gian 7 ngày, dù cách diễn đạt khác nhau. Một embedding tốt sẽ ánh xạ chúng tới vùng gần nhau trong không gian vector.

**Ví dụ có độ tương tự THẤP:**
- Câu A: `"Thời tiết hôm nay nắng đẹp và mát mẻ."`
- Câu B: `"Điều kiện đăng ký tài khoản người bán trên Tiki."`
- Tại sao khác: Hai câu này thuộc hai miền hoàn toàn khác nhau — một câu nói về thời tiết, câu kia về thương mại điện tử. Vector embedding của chúng sẽ trỏ theo hai hướng rất khác nhau, cho điểm cosine gần 0 hoặc âm.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng bởi độ dài (magnitude) của vector — một văn bản dài sẽ có vector có magnitude lớn hơn, dẫn đến khoảng cách lớn dù nội dung tương tự. Cosine similarity chỉ quan tâm đến **góc** giữa hai vector (hướng), bỏ qua độ lớn, nên phù hợp hơn để so sánh ý nghĩa ngữ nghĩa bất kể độ dài văn bản.

---

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> **Phép tính:**
> ```
> step = chunk_size - overlap = 500 - 50 = 450
> số_chunk = ceil((10000 - overlap) / step)
>           = ceil((10000 - 50) / 450)
>           = ceil(9950 / 450)
>           = ceil(22.11)
>           = 23 chunks
> ```
> **Đáp án: 23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> ```
> step = 500 - 100 = 400
> số_chunk = ceil((10000 - 100) / 400) = ceil(9900/400) = ceil(24.75) = 25 chunks
> ```
> Tăng overlap từ 50 → 100 làm tăng số chunks từ 23 → 25. Ta muốn overlap nhiều hơn vì nó giúp **giữ nguyên ngữ cảnh ở ranh giới giữa các chunk** — tránh trường hợp một câu quan trọng bị cắt đôi khiến cả hai chunk đều thiếu ngữ cảnh để trả lời câu hỏi.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của tôi khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng `re.split(r'(?<=[.!?])\s+|(?<=\.)\n', text)` để tách câu — pattern này sử dụng **lookbehind** để tách tại vị trí **sau** dấu câu kết thúc (`.`, `!`, `?`), đảm bảo dấu câu vẫn nằm ở cuối câu trước chứ không bị tách ra riêng. Sau đó nhóm các câu thành chunk theo `max_sentences_per_chunk` bằng cách dùng `range(0, len(sentences), max_sentences_per_chunk)` và join bằng dấu cách. Edge case được xử lý: chuỗi rỗng trả về `[]`, câu sau khi strip mà rỗng thì bỏ qua.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động theo nguyên tắc **ưu tiên separator có độ ưu tiên cao nhất**: nếu text đã ngắn hơn `chunk_size` thì trả về ngay (base case). Nếu không, tìm separator đầu tiên trong list có trong text, split text theo separator đó, rồi **gộp các phần nhỏ lại thành chunk** chừng nào tổng độ dài còn trong giới hạn. Nếu một phần riêng lẻ vẫn vượt quá `chunk_size`, gọi đệ quy `_split` với danh sách separator còn lại. Separator `""` là fallback cuối cùng: chia theo từng ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ in-memory bằng `list[dict]`, mỗi record có 3 trường: `content`, `embedding` (kết quả của `embedding_fn(doc.content)`), và `metadata` (dict gốc + thêm `doc_id`). Khi search, embed query → tính dot product với mọi record (dùng hàm `_dot` đã có sẵn từ `chunking.py`) → sắp xếp giảm dần theo score → cắt top_k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` **filter trước, search sau**: lọc `self._store` lấy các record mà `metadata` match tất cả key-value trong `metadata_filter`, rồi mới chạy similarity search trên tập đã lọc. `delete_document` dùng list comprehension để giữ lại tất cả record **không** có `metadata["doc_id"] == doc_id`, so sánh độ dài trước/sau để biết có xóa được không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Cấu trúc prompt theo dạng `"Context:\n[Chunk 1]: ...\n[Chunk 2]: ...\n\nQuestion: ...\nAnswer:"`. Mỗi chunk được đánh số rõ ràng (`[Chunk i]`) để LLM có thể tham chiếu. Context được inject bằng cách join các kết quả top-k từ `store.search()`, bảo đảm ngữ cảnh phong phú nhất có thể trước khi gọi `llm_fn(prompt)`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/nguyen-xuan-quan/vinai/labs/Day072A202601976_NguyenXuanQuan
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================== 42 passed in 0.04s ==============================
```

**Số lượng bài test vượt qua (pass): 42 / 42** ✅

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> ⚠️ **Lưu ý quan trọng:** Kết quả dưới đây được tính với **Mock Embedder** — embedder giả lập sinh vector xác định nhưng gần như ngẫu nhiên theo chuỗi ký tự, **không phản ánh chất lượng ngữ nghĩa**. Điểm thực tế thấp/âm với cặp câu ngữ nghĩa tương đồng là bình thường với mock embedder.

| Cặp | Câu A | Câu B | Dự đoán (ngữ nghĩa) | Điểm thực tế (mock) | Nhận xét |
|-----|-------|-------|---------------------|---------------------|----------|
| 1 | "Chính sách đổi trả hàng trong 30 ngày." | "Bạn có thể trả lại sản phẩm trong vòng 30 ngày kể từ ngày mua." | Cao | **0.1664** | Mock: dương nhưng thấp |
| 2 | "Phí vận chuyển miễn phí cho đơn hàng trên 300k." | "Đơn hàng dưới 200k phải trả phí ship." | Thấp-Trung | **-0.1968** | Mock: âm — cùng chủ đề nhưng nội dung đối lập |
| 3 | "Shopee hỗ trợ thanh toán bằng ví MoMo." | "Bạn có thể thanh toán qua thẻ Visa hoặc MasterCard." | Cao | **0.2579** | Mock: cao nhất trong 5 cặp |
| 4 | "Trời hôm nay rất đẹp và nắng." | "Chính sách bảo mật dữ liệu khách hàng của Lazada." | Thấp | **-0.1144** | Mock: âm — đúng hướng dự đoán |
| 5 | "Điều kiện trở thành người bán trên Tiki." | "Yêu cầu đăng ký tài khoản người bán trên Tiki." | Cao | **-0.0687** | Mock: âm dù ngữ nghĩa rất tương đồng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **Cặp 5**: hai câu có ngữ nghĩa gần như giống hệt nhau (đều nói về điều kiện/yêu cầu trở thành người bán trên Tiki) nhưng mock embedder lại cho điểm **âm (-0.0687)**. Điều này chứng minh rõ ràng rằng mock embedder hoạt động dựa trên hash MD5 của chuỗi ký tự, không "hiểu" ngữ nghĩa. Ngược lại, một embedder thực sự (như `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) sẽ ánh xạ cả hai câu về cùng vùng trong không gian vector và cho điểm gần 1.0 — đây chính là lý do tại sao Giai đoạn 2 yêu cầu dùng `EMBEDDING_PROVIDER=local`.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

**Chiến lược cá nhân:** `SentenceChunker(max_sentences_per_chunk=3)` — chia theo ranh giới câu, nhóm 3 câu/chunk.  
**Bộ dữ liệu:** 7 tài liệu chính sách TMĐT (Shopee, Tiki, Lazada) → **106 chunks**.  
**Embedder:** Mock embedder (vector hash-based, không phản ánh ngữ nghĩa — dùng cho unit test).  
**Lọc metadata:** Có dùng `search_with_filter(metadata_filter={"platform": platform})` để giới hạn theo sàn.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|--------------------------|
| 1 | Thời hạn đổi trả hàng trên Shopee là bao nhiêu ngày? | "Chính Sách Đổi Trả và Hoàn Tiền – Shopee... Người mua có thể yêu cầu đổi trả trong 15 ngày..." | 0.3358 | ✅ Có (top-1 đúng tài liệu Shopee đổi trả) | Dựa trên thông tin chính sách đổi trả Shopee... |
| 2 | Lazada hỗ trợ những phương thức thanh toán nào? | "Liên hệ hỗ trợ thanh toán — Chat: helpcenter.lazada.vn..." | 0.1851 | ⚠️ Một phần (chunk hỗ trợ, không phải chunk liệt kê phương thức) | Dựa trên thông tin liên hệ Lazada... |
| 3 | Điều kiện để trở thành người bán trên Shopee là gì? | "Theo dõi đơn hàng — Người mua có thể theo dõi..." | 0.2305 | ❌ Không (mock embedder lấy sai chunk) | Dựa trên thông tin theo dõi đơn hàng... |
| 4 | Tiki bảo vệ dữ liệu cá nhân khách hàng như thế nào? | "Chọn sản phẩm và lý do đổi/trả, đính kèm hình ảnh..." | 0.2536 | ❌ Không (mock lấy chunk đổi trả thay vì bảo mật) | Dựa trên thông tin bảo mật Lazada... |
| 5 | Shopee miễn phí vận chuyển khi nào? | "Người mua cần: Báo cáo trong vòng 7 ngày kể từ ngày giao hàng..." | 0.1760 | ⚠️ Một phần (cùng file vận chuyển nhưng sai section) | Dựa trên thông tin đơn hàng bị thất lạc... |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3:** 3 / 5 *(top-1 đúng cho Q1; Q2, Q5 có chunk liên quan trong top-3)*

**Phân tích kết quả:**
> Mock embedder sinh vector ngẫu nhiên theo hash chuỗi ký tự — kết quả retrieval không phản ánh ngữ nghĩa. Q3 và Q4 bị truy xuất sai hoàn toàn vì mock không "hiểu" sự khác biệt giữa "điều kiện người bán" và "theo dõi đơn hàng". Với `EMBEDDING_PROVIDER=local` (sentence-transformers), kết quả dự kiến sẽ đạt 5/5 vì model đa ngữ hiểu ngữ nghĩa tiếng Việt. Đây là minh chứng rõ nhất cho việc tại sao **chọn đúng embedding backend** quan trọng hơn thuật toán chunking trong pipeline RAG.

**Điều hay nhất học được từ thực nghiệm này:**
> Metadata filtering (`search_with_filter`) giúp cải thiện đáng kể precision ngay cả với mock embedder — lọc theo `platform` đã loại bỏ nhiều nhiễu trước khi tính similarity. Khi nhóm so sánh chiến lược trong Giai đoạn 2, việc thiết kế metadata schema tốt (có `category`, `platform`, `language`) sẽ là yếu tố tạo ra sự khác biệt lớn giữa các thành viên.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |
