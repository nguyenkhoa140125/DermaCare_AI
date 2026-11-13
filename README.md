# DermaCare AI — Lõi AI Thị giác Máy tính (Coarse-to-Fine Pipeline)

> **Đề tài:** Nghiên cứu và phát triển nền tảng DermaCare AI hỗ trợ giáo dục sức khỏe làn da và đánh giá tổn thương nám da bằng thị giác máy tính
> **Sinh viên thực hiện:** Nguyễn Văn Khoa — MSSV: 23DH114394 — Lớp: PM2305
> **Giảng viên hướng dẫn:** ThS. Phan Thị Ngọc Hân (HUFLIT)

> ⚠️ **Lưu ý quan trọng:** Repo **không kèm checkpoint SegFormer đã huấn luyện**. Bạn cần tự tải dữ liệu và huấn luyện mô hình (mục 6) trước khi chạy demo (mục 7). Cần khoảng **15–20GB** ổ cứng trống, thời gian huấn luyện từ **30 phút đến vài giờ** tùy GPU.

---

## Mục lục

1. [Giới thiệu](#1-giới-thiệu)
2. [Kết quả tham khảo](#2-kết-quả-tham-khảo)
3. [Yêu cầu hệ thống](#3-yêu-cầu-hệ-thống)
4. [Cấu trúc thư mục](#4-cấu-trúc-thư-mục)
5. [Cài đặt](#5-cài-đặt)
6. [Chuẩn bị dữ liệu và huấn luyện](#6-chuẩn-bị-dữ-liệu-và-huấn-luyện)
7. [Chạy demo](#7-chạy-demo)
8. [Đọc kết quả đầu ra](#8-đọc-kết-quả-đầu-ra)
9. [Xử lý lỗi thường gặp](#9-xử-lý-lỗi-thường-gặp)
10. [Tuyên bố miễn trừ y tế](#10-tuyên-bố-miễn-trừ-y-tế)

---

## 1. Giới thiệu

Repo chứa mã nguồn thực nghiệm của **Lõi AI Thị giác máy tính (Hướng 1)** trong đề tài DermaCare AI. Hệ thống đánh giá mức độ nám da (melasma) trên ảnh khuôn mặt độ phân giải cao (~4K × 3K) bằng **pipeline 3 giai đoạn**, giải quyết bài toán đánh đổi giữa dung lượng GPU và việc giữ chi tiết vi thể của da:

| Giai đoạn | Nhiệm vụ | Mô hình / kỹ thuật |
|---|---|---|
| 1 — Coarse Localization | Phát hiện khuôn mặt, định vị 4 vùng ROI: Trán, Má trái, Má phải, Cằm | YOLOv8-Face (dự phòng: Haar Cascade) |
| 2 — Crop & Normalization | Cắt ROI trực tiếp từ ảnh gốc (giữ nguyên độ phân giải), chuẩn hóa ánh sáng | Gray World + CLAHE |
| 3 — Fine Segmentation & MASI | Phân đoạn vùng nám, tính diện tích và điểm MASI / mMASI | SegFormer-B0 |

## 2. Kết quả tham khảo

Kết quả đạt được trong đề tài (kết quả của bạn khi tự huấn luyện có thể chênh lệch nhẹ do dữ liệu và ngẫu nhiên):

| Chỉ số | Giá trị |
|---|---|
| mAP@50 (Giai đoạn 1) | 96.8% |
| Dice (Giai đoạn 3) | 0.903 |
| IoU (Giai đoạn 3) | 0.838 |
| Tương quan MASI so với hội đồng bác sĩ da liễu | r = 0.942 |

## 3. Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|---|---|
| Hệ điều hành | Windows 10/11, Linux hoặc macOS |
| Python | 3.10 hoặc 3.11 |
| GPU (khuyến nghị) | NVIDIA, ≥ 4GB VRAM (đã chạy thử trên GTX 1050 Ti 4GB) + driver mới |
| Ổ cứng trống | ~15–20GB (dữ liệu + checkpoint) |
| Mạng | Cần khi cài thư viện, tải weights và tải dữ liệu (~5GB) |

> Huấn luyện (script 05) cần GPU mới chạy trong thời gian hợp lý. Chạy bằng CPU được nhưng rất chậm.

## 4. Cấu trúc thư mục

```
DermaCare_AI/
├── README.md                        <- Tài liệu này
├── requirements.txt                 <- Thư viện Python
├── .gitignore
├── sample_face_demo.jpg             <- Ảnh mẫu để chạy demo
│
├── scripts/                         <- Mã nguồn pipeline
│   ├── 01_fetch_melasma_images.py   <- Tải ảnh melasma (MultiCaRe)
│   ├── 02_prepare_isic_dataset.py   <- Tiền xử lý ISIC 2018
│   ├── 03_stage1_roi_detection.py   <- Giai đoạn 1: phát hiện ROI
│   ├── 04_evaluate_stage1.py        <- Đánh giá Giai đoạn 1 (IoU)
│   ├── 05_stage2_train_segformer.py <- Huấn luyện SegFormer-B0
│   ├── 06_evaluate_stage2.py        <- Đánh giá Dice / IoU / Precision / Recall
│   ├── 07_stage3_masi.py            <- Tính MASI / mMASI
│   └── 08_pipeline_end_to_end.py    <- Chạy toàn bộ 3 giai đoạn
│
├── setup/                           <- Hướng dẫn cài PyTorch CUDA
├── weights/                         <- Nơi đặt YOLOv8-Face (tải ở mục 5)
└── figures/                         <- Hình minh họa kết quả
```

Các thư mục sau **được sinh ra khi chạy script** (không có sẵn trong repo): `medical_datasets/`, `isic2018_raw/`, `processed_isic/`, `segformer_melasma_checkpoint/`, `rois_output/`, `pipeline_demo_output/`.

## 5. Cài đặt

### Bước 1 — Tải project về

```bash
git clone https://github.com/nguyenkhoa140125/DermaCare_AI.git
cd DermaCare_AI
```

### Bước 2 — Tạo môi trường ảo

**Windows (PowerShell):**

```powershell
python -m venv dermacare_env
dermacare_env\Scripts\activate
```

> Nếu PowerShell báo lỗi không cho chạy script, chạy một lần: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**Linux / macOS:**

```bash
python3 -m venv dermacare_env
source dermacare_env/bin/activate
```

### Bước 3 — Cài PyTorch (có GPU)

Cài PyTorch bản CUDA **trước** khi cài các thư viện còn lại:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Nếu không có GPU NVIDIA, bỏ qua bước này (bước 4 sẽ tự cài bản CPU).

### Bước 4 — Cài các thư viện còn lại

```bash
pip install -r requirements.txt
```

### Bước 5 — Kiểm tra GPU

```bash
python -c "import torch; print('GPU khả dụng:', torch.cuda.is_available())"
```

In `True` là GPU đã sẵn sàng. Nếu in `False`, xem [mục 9](#9-xử-lý-lỗi-thường-gặp) hoặc `setup/HUONG_DAN_CAI_DAT_GPU.md`.

### Bước 6 — Tải weights YOLOv8-Face

**Windows (PowerShell):**

```powershell
mkdir weights -Force
Invoke-WebRequest -Uri "https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8n.pt" -OutFile "weights/yolov8n-face.pt"
(Get-Item weights/yolov8n-face.pt).Length / 1MB
```

Kết quả dòng cuối phải khoảng **6** (MB). Nếu ra số rất nhỏ nghĩa là tải lỗi, hãy tải lại.

**Linux / macOS:**

```bash
mkdir -p weights
curl -L -o weights/yolov8n-face.pt "https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8n.pt"
ls -lh weights/yolov8n-face.pt
```

> Nếu không có file này, hệ thống tự dùng Haar Cascade dự phòng (độ chính xác thấp hơn).

## 6. Chuẩn bị dữ liệu và huấn luyện

Chạy **lần lượt** từng lệnh, chờ lệnh trước xong mới chạy lệnh sau. Chạy từ thư mục gốc của project, với môi trường ảo đã kích hoạt.

### Giai đoạn A — Chuẩn bị dữ liệu

**A1. Tải ảnh melasma (tự động, ~5GB, khoảng 10–20 phút):**

```bash
python scripts/01_fetch_melasma_images.py
```

**A2. Tải thủ công ISIC 2018 Task 1** (cả *Input* và *GroundTruth*) từ [ISIC Challenge](https://challenge.isic-archive.com/data/#2018) hoặc Kaggle. Tạo thư mục rồi đặt các file `.zip` đã tải vào đó:

```bash
mkdir isic2018_raw
```

**A3. Xử lý ISIC (tự động giải nén và gộp):**

```bash
python scripts/02_prepare_isic_dataset.py
```

### Giai đoạn B — Kiểm tra Giai đoạn 1 (phát hiện ROI)

Thử nhanh trên một ảnh bất kỳ có khuôn mặt (kết quả nằm trong `rois_output/`):

```bash
python scripts/03_stage1_roi_detection.py sample_face_demo.jpg
```

Đánh giá IoU định vị ROI (**tùy chọn**). Bước `annotate` mở cửa sổ đồ họa để bạn vẽ 5 khung theo hướng dẫn trong terminal:

```bash
python scripts/04_evaluate_stage1.py annotate anh_mau_annotate/*.jpg
python scripts/04_evaluate_stage1.py evaluate
```

> Bước `evaluate` cần file `predictions_rois.json`, xem ghi chú ở cuối script 04.

### Giai đoạn C — Huấn luyện SegFormer-B0 (bắt buộc)

```bash
python scripts/05_stage2_train_segformer.py
```

- Đây là bước lâu nhất: 15 epoch, từ 30 phút đến vài giờ tùy GPU.
- Checkpoint được lưu vào `segformer_melasma_checkpoint/`, log huấn luyện lưu trong `training_log.csv`.
- Script **chưa hỗ trợ resume**: nếu bị ngắt giữa chừng, phải chạy lại từ epoch 1.

Đánh giá mô hình sau huấn luyện (kết quả lưu vào `stage2_evaluation_results.txt`):

```bash
python scripts/06_evaluate_stage2.py
```

### Giai đoạn D — Tính MASI

```bash
python scripts/07_stage3_masi.py
```

## 7. Chạy demo

Chỉ chạy được **sau khi hoàn thành Giai đoạn C** (đã có checkpoint SegFormer).

```bash
python scripts/08_pipeline_end_to_end.py sample_face_demo.jpg
```

Muốn chạy trên ảnh của bạn, thay `sample_face_demo.jpg` bằng đường dẫn tới ảnh khuôn mặt (nên chụp chính diện, đủ sáng):

```bash
python scripts/08_pipeline_end_to_end.py duong_dan/toi/anh_cua_ban.jpg
```

Kết quả nằm tại `pipeline_demo_output/<tên_ảnh>/` (xem mục 8).

## 8. Đọc kết quả đầu ra

Sau khi chạy script 08, thư mục `pipeline_demo_output/<tên_ảnh>/` chứa:

| File | Nội dung |
|---|---|
| `full_overlay.jpg` | Ảnh gốc kèm khung 4 vùng ROI (xanh lá) và mặt nạ nám (đỏ) |
| `Tran_mask_overlay.jpg` | Phân đoạn vùng Trán |
| `Ma_trai_mask_overlay.jpg` | Phân đoạn vùng Má trái |
| `Ma_phai_mask_overlay.jpg` | Phân đoạn vùng Má phải |
| `Cam_mask_overlay.jpg` | Phân đoạn vùng Cằm |
| `result.json` | Kết quả định lượng (bảng dưới) |

Nội dung `result.json`:

| Đại lượng | Ý nghĩa | Thang |
|---|---|---|
| Tỷ lệ diện tích nám (%) | Phần trăm vùng da bị nám trong từng ROI | 0–100% |
| Điểm diện tích **A** | Mức độ diện tích nám theo từng vùng | 0–6 |
| Độ sẫm màu **D** | Mức độ sẫm màu của nám | 0–4 |
| **MASI** | Chỉ số mức độ nặng nám da | 0–48 |
| **mMASI** | Phiên bản MASI hiệu chỉnh | 0–24 |

## 9. Xử lý lỗi thường gặp

| Lỗi | Cách xử lý |
|---|---|
| `torch.cuda.is_available()` trả về `False` | Cập nhật driver NVIDIA, cài lại PyTorch theo bước 3 mục 5; xem thêm `setup/HUONG_DAN_CAI_DAT_GPU.md` |
| `CUDA out of memory` khi huấn luyện | Giảm batch size trong script 05, đóng các chương trình đang dùng GPU |
| Script 08 báo không tìm thấy checkpoint | Chưa huấn luyện xong, hãy chạy script 05 trước (mục 6, Giai đoạn C) |
| PowerShell không kích hoạt được môi trường ảo | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| File `yolov8n-face.pt` quá nhỏ (vài KB) | Tải lỗi, xóa file và tải lại theo bước 6 mục 5; trên PowerShell không dùng `curl -L` |
| Demo không tìm thấy khuôn mặt | Dùng ảnh chính diện, đủ sáng, khuôn mặt rõ nét |
| Máy tắt giữa lúc huấn luyện | Chạy lại script 05 từ đầu (chưa hỗ trợ resume) |

## 10. Tuyên bố miễn trừ y tế

*DermaCare AI được xây dựng cho mục đích nghiên cứu học thuật, giáo dục cộng đồng và hỗ trợ lượng hóa tham khảo cho nhân viên y tế. Kết quả phân tích từ mô hình không thay thế chẩn đoán chuyên môn, phác đồ điều trị hay chỉ định của bác sĩ chuyên khoa da liễu.*
