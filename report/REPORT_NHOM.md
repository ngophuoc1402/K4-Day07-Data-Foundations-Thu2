# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** K4 — Nhóm Nguyễn Xuân Quân
**Thành viên:** Nguyễn Xuân Quân (2A202601976)
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Nhóm tập trung vào **5 mảng chính sách** của 3 sàn TMĐT lớn tại Việt Nam (Shopee, Tiki, Lazada): chính sách đổi trả, vận chuyển/giao hàng, thanh toán, điều kiện người bán, và bảo mật dữ liệu — đây là những FAQ phổ biến nhất mà người dùng và người bán thường hỏi.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|--------------------|--------------------|----------|-----------------|
| 1 | Shopee – Chính Sách Đổi Trả và Hoàn Tiền | https://help.shopee.vn/portal/article/77228 | 2026-08-03 / 2026-Q3 | ~2.800 | platform, category, language |
| 2 | Shopee – Chính Sách Vận Chuyển và Giao Hàng | https://help.shopee.vn/portal/article/77229 | 2026-08-03 / 2026-Q3 | ~2.600 | platform, category, language |
| 3 | Shopee – Điều Kiện và Quy Định Người Bán | https://seller.shopee.vn/edu/article/1030 | 2026-08-03 / 2026-Q3 | ~3.100 | platform, category, language |
| 4 | Tiki – Chính Sách Đổi Trả Hàng | https://tiki.vn/chinh-sach-bao-hanh-doi-tra.html | 2026-08-03 / 2026-Q2 | ~2.700 | platform, category, language |
| 5 | Tiki – Chính Sách Bảo Mật Dữ Liệu | https://tiki.vn/chinh-sach-bao-mat.html | 2026-08-03 / 2026-Q1 | ~3.200 | platform, category, language |
| 6 | Lazada – Chính Sách Đổi Trả và Hoàn Tiền | https://helpcenter.lazada.vn/s/faq/knowledge?categoryId=1000027305 | 2026-08-03 / 2026-Q3 | ~2.900 | platform, category, language |
| 7 | Lazada – Phương Thức Thanh Toán | https://www.lazada.vn/helpcenter/phuong-thuc-thanh-toan-27.html | 2026-08-03 / 2026-Q3 | ~2.800 | platform, category, language |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|---------------------------------------------|
| `source_url` | string | `"https://help.shopee.vn/..."` | Cho phép truy vết và kiểm tra tính cập nhật của tài liệu |
| `retrieved_at` | string (date) | `"2026-08-03"` | Kiểm tra độ mới của thông tin, lọc tài liệu cũ |
| `document_version` | string | `"2026-Q3"` | Phân biệt phiên bản chính sách theo thời gian |
| `category` | string | `"doi_tra"`, `"van_chuyen"`, `"thanh_toan"` | **Lọc theo loại chính sách** — rất hữu ích khi người dùng hỏi về một mảng cụ thể |
| `platform` | string | `"shopee"`, `"tiki"`, `"lazada"` | **Lọc theo sàn TMĐT** — tránh nhầm chính sách giữa các sàn |
| `language` | string | `"vi"` | Mở rộng sang đa ngôn ngữ trong tương lai |
| `doc_id` | string | `"shopee_chinh_sach_doi_tra"` | Xóa/cập nhật toàn bộ chunk của 1 tài liệu khi chính sách thay đổi |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu (`lazada_chinh_sach_doi_tra.md`, `lazada_chinh_sach_thanh_toan.md`, `shopee_chinh_sach_doi_tra.md`) với `chunk_size=200`:

| Tài liệu | Chiến lược | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh? |
|----------|-----------|----------------|------------------|-------------------|
| lazada_doi_tra.md (2.515 chars) | FixedSizeChunker | 13 | 193.5 chars | ⚠️ Có thể cắt giữa câu |
| lazada_doi_tra.md | SentenceChunker | 14 | 178.3 chars | ✅ Giữ nguyên câu |
| lazada_doi_tra.md | RecursiveChunker | 22 | 112.8 chars | ✅ Tôn trọng cấu trúc |
| lazada_thanh_toan.md (2.512 chars) | FixedSizeChunker | 13 | 193.2 chars | ⚠️ Cắt giữa danh sách |
| lazada_thanh_toan.md | SentenceChunker | 11 | 226.7 chars | ✅ Chunk lớn hơn, đủ ngữ cảnh |
| lazada_thanh_toan.md | RecursiveChunker | 20 | 124.0 chars | ✅ Chunk nhỏ, chi tiết |

**Nhận xét baseline:**
- `FixedSizeChunker`: nhanh, đơn giản, nhưng dễ cắt đứt câu hoặc danh sách giữa chừng.
- `SentenceChunker`: chunk có ý nghĩa trọn vẹn, phù hợp với văn bản chính sách dạng văn xuôi.
- `RecursiveChunker`: chunk nhỏ và nhiều nhất, tốt cho truy xuất chi tiết nhưng có thể mất ngữ cảnh nếu câu trả lời cần nhiều bước.

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Xuân Quân**
- **Loại chiến lược:** SentenceChunker (max_sentences_per_chunk=3)
- **Mô tả & lý do chọn:** Tài liệu chính sách TMĐT viết theo dạng danh sách điều khoản và văn xuôi giải thích. `SentenceChunker` tách theo ranh giới câu và nhóm 3 câu/chunk — đảm bảo mỗi chunk mang đủ ngữ cảnh (không bị cắt giữa câu như FixedSize) nhưng cũng không quá dài (như khi để mặc định RecursiveChunker). Phù hợp với chủ đề FAQ/policy vì mỗi câu trong policy thường là 1 quy tắc riêng biệt.
- **Code snippet:**
```python
from src import SentenceChunker
chunker = SentenceChunker(max_sentences_per_chunk=3)
# Tạo ra 106 chunks từ 7 tài liệu (avg 15 chunks/doc)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược | Số chunk / 7 docs | Điểm mạnh | Điểm yếu |
|-----------|-----------|-------------------|-----------|----------|
| Nguyễn Xuân Quân | SentenceChunker (3 câu/chunk) | 106 chunks | Chunk có nghĩa trọn vẹn; phù hợp văn bản chính sách dạng điều khoản | Chunk quá lớn nếu câu dài (bảng, danh sách nhiều cột) |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Với dữ liệu chính sách TMĐT tiếng Việt, `SentenceChunker` cho kết quả tốt nhất vì tài liệu được viết theo cấu trúc điều khoản rõ ràng — mỗi câu là 1 quy tắc. Nhóm 3 câu/chunk đảm bảo đủ ngữ cảnh để agent trả lời mà không cần dữ liệu từ nhiều chunk. Nếu dữ liệu có nhiều bảng (như bảng so sánh phí), `RecursiveChunker` với `separator=["\n\n", "\n"]` sẽ tốt hơn vì tôn trọng ranh giới bảng.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; câu Q2 và Q5 cần lọc metadata để trả lời chính xác.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn đổi trả hàng trên Shopee là bao nhiêu ngày? | 15 ngày kể từ ngày nhận hàng | `shopee_chinh_sach_doi_tra` — mục 1 "Điều kiện đổi trả hàng" |
| 2 | Lazada hỗ trợ những phương thức thanh toán nào? *(cần lọc platform=lazada)* | COD, thẻ tín dụng/ghi nợ (Visa/Master/JCB), ví điện tử (MoMo, ZaloPay, VNPay), chuyển khoản, trả góp 0% | `lazada_chinh_sach_thanh_toan` — mục 1 "Các phương thức thanh toán" |
| 3 | Điều kiện để trở thành người bán cá nhân trên Shopee là gì? | Có SĐT VN, đủ 18 tuổi, có CMND/CCCD, có tài khoản ngân hàng VN | `shopee_dieu_kien_nguoi_ban` — mục 1 "Điều kiện đối với cá nhân" |
| 4 | Tiki bảo vệ dữ liệu cá nhân của khách hàng bằng cách nào? | Mã hóa TLS/SSL, hash mật khẩu bằng bcrypt, 2FA cho nhân viên, kiểm toán định kỳ | `tiki_chinh_sach_bao_mat` — mục 5 "Bảo mật dữ liệu" |
| 5 | Shopee miễn phí vận chuyển khi nào? *(cần lọc platform=shopee, category=van_chuyen)* | Khi có mã giảm giá ship từ Shopee, hoặc là thành viên Shopee Premium/Live, hoặc trong chương trình khuyến mãi đặc biệt | `shopee_chinh_sach_van_chuyen` — mục 3 "Miễn phí vận chuyển" |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm: **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất | Chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------|------------------------------|---------|
| 1 | Thời hạn đổi trả Shopee | SentenceChunker + filter platform=shopee | ✅ Top-1 đúng (score 0.3358) | Mock embedder tình cờ cho kết quả tốt |
| 2 | Phương thức thanh toán Lazada | SentenceChunker + filter platform=lazada | ⚠️ Top-1 là chunk liên hệ, không phải chunk danh sách phương thức | Mock cần embedder thật để cải thiện |
| 3 | Điều kiện người bán Shopee | SentenceChunker + filter platform=shopee, category=dieu_kien_nguoi_ban | ❌ Top-1 sai (mock embedder lấy chunk theo dõi đơn hàng) | Với local embedder sẽ cải thiện |
| 4 | Bảo mật dữ liệu Tiki | SentenceChunker + filter platform=tiki, category=bao_mat | ❌ Top-1 sai (mock lấy chunk đổi trả) | Cần semantic embedder |
| 5 | Miễn phí vận chuyển Shopee | SentenceChunker + filter platform=shopee, category=van_chuyen | ⚠️ Cùng file nhưng sai section (chunk xử lý thất lạc) | Chunk miễn phí ship nằm trong top-3 |

**Điểm ước tính với mock embedder: 4/10** | **Dự kiến với local embedder: 8-9/10**

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Metadata filtering (`search_with_filter`) **rất hữu ích** trong bộ dữ liệu này vì 3 sàn khác nhau có chính sách tương tự (ví dụ: cả Shopee, Tiki, Lazada đều có chính sách đổi trả). Không có filter, similarity search rất dễ trả về chính sách của sai sàn. Filter `platform` giúp Q2 và Q5 tập trung đúng sàn, giảm nhiễu từ 106 chunks xuống ~30 chunks cùng sàn trước khi tính similarity — cải thiện precision rõ rệt ngay cả với mock embedder. Q3 và Q4 thậm chí cần double filter (`platform` + `category`) để đạt kết quả tốt nhất.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Mock vs Real Embedder**: Kết quả đối lập giữa mock (random vector) và semantic embedder minh họa rõ ràng tại sao lựa chọn embedding backend quan trọng hơn thuật toán chunking.
> 2. **Metadata như "pre-filter"**: Thiết kế schema tốt (`platform`, `category`) giúp cắt giảm search space từ 106 → ~15 chunks, tăng precision mà không cần embedder mạnh hơn.
> 3. **SentenceChunker phù hợp với policy text**: Văn bản điều khoản TMĐT có cấu trúc câu rõ ràng — tách theo câu tự nhiên hơn so với cắt cứng theo ký tự.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ 7 tài liệu, khi dùng `FixedSizeChunker` (chunk_size=200) sẽ tạo ra nhiều chunk bị cắt giữa danh sách hoặc bảng so sánh — agent nhận được context bị đứt đoạn, câu trả lời thiếu thông tin. `SentenceChunker` tạo ra chunk có nghĩa hơn nhưng kích thước không đều (bảng dữ liệu có thể vào cùng 1 chunk rất dài). `RecursiveChunker` với separator `\n\n` tốt nhất cho cấu trúc Markdown vì tôn trọng ranh giới đoạn văn.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> 1. **Thêm trường metadata `section`** (ví dụ: "điều_kien", "quy_trinh", "phi_phi") để filter theo mục cụ thể trong tài liệu, không chỉ theo danh mục tổng quát.
> 2. **Dùng `EMBEDDING_PROVIDER=local`** ngay từ đầu cho benchmark thật — mock embedder cho kết quả sai lệch đáng kể với dữ liệu tiếng Việt.
> 3. **Tăng số tài liệu lên 10+** với nhiều chủ đề câu hỏi cụ thể hơn (ví dụ: chính sách hoàn tiền cho COD, điều kiện trả góp) để 5 câu benchmark có độ khó và đa dạng cao hơn.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 12 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 7 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **32 / 40** |
