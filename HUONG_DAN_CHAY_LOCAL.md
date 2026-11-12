# Hướng dẫn chạy Pipeline trên máy cá nhân (có GPU riêng)

Tài liệu này thay thế luồng Google Colab — dùng đúng các script trong `scripts/`,
chạy tuần tự bằng terminal. Không có vấn đề mất dữ liệu do ngắt session như Colab.

---

## Bước 0 — Cài đặt môi trường (chỉ làm 1 lần)

Làm theo `setup/HUONG_DAN_CAI_DAT_GPU.md` (đã có sẵn trong project) — gồm:
kiểm tra driver NVIDIA, tạo virtualenv, cài PyTorch bản CUDA đúng, cài
`requirements.txt`.

Sau khi cài xong, kiểm tra lại:
```bash
python -c "import torch; print('GPU khả dụng:', torch.cuda.is_available())"
```
Phải in ra `True` mới tiếp tục được.

---

## Bước 1 — Chạy toàn bộ pipeline theo đúng thứ tự

Mở terminal, `cd` vào thư mục `dermacare_pipeline/`, kích hoạt virtualenv, rồi
chạy lần lượt (mỗi lệnh cách nhau, chờ lệnh trước xong mới chạy lệnh sau):

```bash
cd dermacare_pipeline
source dermacare_env/bin/activate   # Windows: dermacare_env\Scripts\activate

# --- Giai đoạn A: chuẩn bị dữ liệu ---
python scripts/01_fetch_melasma_images.py
# (Tự tải MultiCaRe -- mất khoảng 10-20 phút tuỳ mạng, ~5GB)

# Tải thủ công ISIC 2018 Task 1 (Input + GroundTruth) từ
# https://challenge.isic-archive.com/data/#2018 hoặc Kaggle,
# đặt các file .zip vào thư mục isic2018_raw/ (tạo thư mục này nếu chưa có)
mkdir -p isic2018_raw
# --> copy/paste các file .zip đã tải vào đây bằng trình quản lý file, rồi:

python scripts/02_prepare_isic_dataset.py
# (Tự động giải nén + xử lý, gộp mọi tập Input+GroundTruth có sẵn)

# --- Giai đoạn B: Giai đoạn 1 (YOLO ROI) ---
mkdir weights   # bỏ qua nếu báo "đã tồn tại"

# Tải model YOLO-face (Windows PowerShell — dùng Invoke-WebRequest, KHÔNG dùng curl -L kiểu Linux):
Invoke-WebRequest -Uri "https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8n.pt" -OutFile "weights/yolov8n-face.pt"
# Kiểm tra đã tải đủ dung lượng (phải ra khoảng 6, không phải một số rất nhỏ):
(Get-Item weights/yolov8n-face.pt).Length / 1MB

# macOS/Linux (dùng curl thật):
# curl -L -o weights/yolov8n-face.pt "https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8n.pt"

python scripts/03_stage1_roi_detection.py duong_dan_anh_mau.jpg
# (Thử nghiệm nhanh trên 1 ảnh mẫu bất kỳ có khuôn mặt, xem thư mục rois_output/)

# --- Đánh giá IoU thật cho Giai đoạn 1 (chạy được trực tiếp, không cần Colab riêng nữa) ---
python scripts/04_evaluate_stage1.py annotate anh_mau_annotate/*.jpg
# (Cửa sổ đồ hoạ sẽ mở lên, vẽ 5 khung theo hướng dẫn trong terminal)
python scripts/04_evaluate_stage1.py evaluate
# (Cần thêm predictions_rois.json -- xem ghi chú cuối script 04)

# --- Giai đoạn B: Giai đoạn 2 (huấn luyện SegFormer) ---
python scripts/05_stage2_train_segformer.py
# (Đây là bước LÂU NHẤT -- tuỳ GPU, có thể mất 30 phút đến vài giờ cho 15 epoch)

python scripts/06_evaluate_stage2.py
# (Tính mIoU, Dice, Precision, Recall -- lưu ra stage2_evaluation_results.txt)

# --- Giai đoạn C: Giai đoạn 3 (MASI) + Demo end-to-end ---
python scripts/08_pipeline_end_to_end.py duong_dan_anh_nam_that.jpg
# (Chạy demo trên ảnh nám thật, ví dụ lấy từ medical_datasets/melasma_dataset/)
```

---

## Ưu điểm khi chạy local so với Colab

- Không mất dữ liệu khi tắt máy/ngủ đông (khác với ổ đĩa tạm `/content/` của Colab)
- Không giới hạn thời gian phiên làm việc (Colab free tier giới hạn ~12 giờ/phiên)
- Bước `04_evaluate_stage1.py annotate` (cần cửa sổ đồ hoạ) chạy được **trực tiếp**,
  không cần phải tải file về máy rồi upload ngược lên như khi dùng Colab
- Toàn bộ file kết quả (`training_log.csv`, `stage2_evaluation_results.txt`,
  `pipeline_demo_output/`) nằm ngay trên máy bạn, dễ quản lý và đưa vào khóa luận

## Lưu ý

- File `weights/`, `medical_datasets/`, `isic2018_raw/`, `processed_isic/`,
  `segformer_melasma_checkpoint/` đều khá nặng (có thể tổng cộng 15-20GB) —
  nên **không** commit các thư mục này lên Git nếu bạn dùng Git để quản lý code
  (thêm vào file `.gitignore`).
- Nếu máy bị tắt/mất điện giữa chừng lúc đang huấn luyện (script 05), chạy lại
  từ đầu script đó — model sẽ huấn luyện lại từ epoch 1 (script hiện chưa hỗ
  trợ resume từ checkpoint dở dang; báo lại nếu bạn cần tính năng này, tôi sẽ
  bổ sung).
