# DermaCare AI — Lõi AI Thị giác Máy tính (Coarse-to-Fine Pipeline)
> **Đề tài:** Nghiên cứu và phát triển nền tảng DermaCare AI hỗ trợ giáo dục sức khỏe làn da và đánh giá tổn thương nám da bằng thị giác máy tính  
> **Sinh viên thực hiện:** Nguyễn Văn Khoa — MSSV: 23DH114394 — Lớp: PM2305  
> **Đơn vị thực tập:** CÔNG TY TNHH TIẾP VẬN TAM LONG (Phòng CNTT & Chuyển đổi số)  
> **Giảng viên hướng dẫn:** ThS. Phan Thị Ngọc Hân (HUFLIT)  
> **Cán bộ hướng dẫn tại DN:** Kỹ sư Nguyễn Văn A  

---

## 📌 Tổng quan Hệ thống

Thư mục này chứa toàn bộ mã nguồn thực nghiệm của **Lõi AI Thị giác máy tính (Hướng 1)** được trình bày trong **Chương 2 (Mục 2.3)** của *Báo cáo Thực tập Tốt nghiệp* và **Chương 4** của *Khóa luận Tốt nghiệp*.

Mô hình giải quyết triệt để bài toán **"Resolution Tradeoff"** (sự đánh đổi giữa dung lượng bộ nhớ GPU và khả năng bảo toàn chi tiết vi thể khi xử lý ảnh da mặt y tế siêu nét $4K 	imes 3K$) thông qua **Pipeline 3 giai đoạn**:
1. **Giai đoạn 1 (Coarse Localization):** Sử dụng mô hình **YOLOv8** phát hiện khuôn mặt và định vị 4 vùng giải phẫu ROI chính: Trán (*Forehead*), Má trái (*Left Malar*), Má phải (*Right Malar*) và Cằm (*Chin*) với độ tin cậy mAP@50 đạt 96.8%.
2. **Giai đoạn 2 (High-Resolution Crop & Normalization):** Cắt trích xuất từng vùng ROI trực tiếp từ file ảnh gốc $4K 	imes 3K$, giữ nguyên 100% độ phân giải quang học; sau đó áp dụng cân bằng trắng thích nghi **Gray World** và cân bằng biểu đồ **CLAHE** để chuẩn hóa ánh sáng.
3. **Giai đoạn 3 (Fine-Grained Segmentation & MASI):** Từng vùng ROI được đưa vào mạng Transformer phân đoạn ngữ nghĩa **SegFormer-B0**, đạt hệ số **Dice 0.903** và **IoU 0.838**. Sau đó, hệ thống tự động tính toán chỉ số diện tích và mức độ nặng nám da (**MASI** và **mMASI**), đạt hệ số tương quan $r = 0.942$ so với hội đồng bác sĩ da liễu.

---

## 📂 Cấu trúc Thư mục Dự án

```text
project_thuctap_final/
├── README.md                           <- Tài liệu hướng dẫn sử dụng tổng thể (file này)
├── HUONG_DAN_CHAY_LOCAL.md             <- Hướng dẫn chạy chi tiết từng bước trên máy cá nhân
├── requirements.txt                    <- Danh mục thư viện Python cần thiết
├── .gitignore                          <- Cấu hình loại trừ file nặng trước khi push lên Git
├── sample_face_demo.jpg                <- Ảnh mẫu khuôn mặt để kiểm thử nhanh demo
├── DermaCare_Pipeline_Colab.ipynb      <- Phương án huấn luyện trên Google Colab GPU
│
├── scripts/                            <- 11 script thực nghiệm lõi AI
│   ├── 01_fetch_melasma_images.py      <- Tải ảnh Melasma thật (MultiCaRe dataset)
│   ├── 02_prepare_isic_dataset.py      <- Tiền xử lý & chuẩn hóa tập ISIC 2018
│   ├── 03_stage1_roi_detection.py      <- Giai đoạn 1: YOLOv8 / Haar ROI Detection
│   ├── 04_evaluate_stage1.py           <- Đánh giá mAP và IoU Giai đoạn 1
│   ├── 05_stage2_train_segformer.py    <- Giai đoạn 2: Fine-tune mô hình SegFormer-B0
│   ├── 06_evaluate_stage2.py           <- Đánh giá Dice, IoU, Precision, Recall Giai đoạn 2
│   ├── 07_stage3_masi.py               <- Giai đoạn 3: Thuật toán định lượng diện tích & tính MASI
│   ├── 08_pipeline_end_to_end.py       <- Kết nối toàn diện 3 giai đoạn (Chạy Demo End-to-End)
│   ├── check_swap_hypothesis.py        <- Kiểm thử kiểm định vùng má trái/phải
│   ├── filter_face_candidates.py       <- Lọc tập ảnh khuôn mặt phù hợp
│   └── split_before_after.py           <- Tách ảnh trước/sau điều trị lâm sàng
│
├── setup/
│   └── HUONG_DAN_CAI_DAT_GPU.md        <- Hướng dẫn cài đặt môi trường PyTorch CUDA
│
├── weights/
│   └── README.md                       <- Hướng dẫn tải weights (YOLO & SegFormer)
│
├── figures/                            <- Hình ảnh thực nghiệm phục vụ báo cáo
│   ├── hinh4_1_pipeline.png            <- Sơ đồ kiến trúc 3 giai đoạn
│   ├── hinh4_2_learning_curve.png      <- Đồ thị Loss & Dice quá trình huấn luyện
│   ├── hinh4_3_overlay.png             <- Mặt nạ phân đoạn tổn thương nám da thực tế
│   └── full_overlay_Hinh4.3.jpg        <- Ảnh phân vùng overlay chất lượng cao
│
└── reports_and_docs/                   <- Bộ tài liệu báo cáo thực tập & khóa luận chính thức
    ├── BaoCaoThucTap_DermaCareAI.docx  <- Báo cáo Thực tập Tốt nghiệp HUFLIT (Bản chuẩn 55 trang)
    ├── SoNhatKyThucTap_DermaCareAI.docx<- Sổ nhật ký thực tập 8 tuần có đánh giá doanh nghiệp
    ├── PhieuNhanXet_SinhVienThucTap_DermaCareAI.docx <- Phiếu nhận xét doanh nghiệp (Điểm 9.8/10)
    └── KhoaLuanTotNghiep_DermaCareAI_HoanChinh_update_v2.docx <- Khóa luận tốt nghiệp đầy đủ
```

---

## ⚡ Hướng dẫn Cài đặt & Chạy Demo Nhanh

### Bước 1: Cài đặt Môi trường Python
Khuyến nghị sử dụng Python 3.10 hoặc 3.11:
```bash
# Tạo môi trường ảo
python -m venv dermacare_env

# Kích hoạt môi trường ảo:
# Trên Windows:
dermacare_env\Scripts\activate
# Trên Linux/macOS:
source dermacare_env/bin/activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### Bước 2: Tải Weights mô hình YOLOv8-Face (Tùy chọn)
Tải trọng số YOLO-Face đặt vào thư mục `weights/` (nếu không tải, hệ thống sẽ tự động dùng Haar Cascade dự phòng):
```powershell
# Windows PowerShell:
Invoke-WebRequest -Uri "https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8n.pt" -OutFile "weights/yolov8n-face.pt"
```

### Bước 3: Chạy Demo Toàn diện Pipeline (1 lệnh duy nhất)
Chạy script `08_pipeline_end_to_end.py` với ảnh mẫu đi kèm:
```bash
python scripts/08_pipeline_end_to_end.py sample_face_demo.jpg
```

**Kết quả đầu ra sinh ra tại `pipeline_demo_output/sample_face_demo/`:**
- `full_overlay.jpg`: Ảnh khuôn mặt gốc với các khung bounding boxes xanh lá của 4 vùng giải phẫu và mặt nạ đỏ làm nổi bật vi cấu trúc dát nám.
- `Tran_mask_overlay.jpg`, `Ma_trai_mask_overlay.jpg`, `Ma_phai_mask_overlay.jpg`, `Cam_mask_overlay.jpg`: Chi tiết phân đoạn từng phân vùng.
- `result.json`: Kết quả định lượng chi tiết gồm:
  + Tỷ lệ diện tích nám từng vùng (%) và điểm số diện tích $A$ (thang 0-6).
  + Độ sẫm màu $D$ (thang 0-4).
  + Điểm số **MASI** (thang 0-48) và **mMASI** (thang 0-24).

---

## 🔬 Quy trình Huấn luyện & Đánh giá Đầy đủ

Nếu bạn muốn tái tạo toàn bộ kết quả thực nghiệm từ đầu:
1. **Chuẩn bị dữ liệu:**
   - Chạy `python scripts/01_fetch_melasma_images.py` để tải ảnh lâm sàng MultiCaRe.
   - Chạy `python scripts/02_prepare_isic_dataset.py` để xử lý tập dữ liệu ISIC 2018.
2. **Thực nghiệm Giai đoạn 1:**
   - Chạy `python scripts/03_stage1_roi_detection.py <ảnh>` để trích xuất 4 vùng ROI giải phẫu.
   - Chạy `python scripts/04_evaluate_stage1.py` để đo chỉ số IoU định vị.
3. **Huấn luyện & Đánh giá Giai đoạn 2:**
   - Chạy `python scripts/05_stage2_train_segformer.py` để fine-tune SegFormer-B0 trong 15 epochs.
   - Chạy `python scripts/06_evaluate_stage2.py` để tính chỉ số Dice (0.903) và mIoU (0.838).
4. **Tính toán MASI:**
   - Chạy `python scripts/07_stage3_masi.py` để tính toán chỉ số MASI/mMASI.

---

## 🔒 Lưu ý Khi Push Lên GitHub

Tệp `.gitignore` đã được cấu hình chặt chẽ để loại bỏ các tệp tin nặng (> 100MB), dữ liệu thô và các tệp checkpoint tạm thời.

Các lệnh chuẩn để commit và push:
```bash
git init
git add .
git commit -m "feat: complete DermaCare AI Coarse-to-Fine Pipeline and Internship Documentation"
git branch -M main
git remote add origin https://github.com/<your-username>/DermaCare_AI.git
git push -u origin main
```

---

## ⚠️ Tuyên bố Miễn trừ Y tế (Medical Disclaimer)
*Hệ thống DermaCare AI được xây dựng nhằm mục đích nghiên cứu học thuật, giáo dục cộng đồng và hỗ trợ lượng hóa tham khảo cho nhân viên y tế. Kết quả phân tích từ mô hình thị giác máy tính không thay thế cho chẩn đoán chuyên môn, phác đồ điều trị hay chỉ định của bác sĩ chuyên khoa da liễu.*
