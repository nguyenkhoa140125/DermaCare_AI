# Hướng dẫn tải Weights cho Mô hình AI

Thư mục này chứa trọng số (weights) của các mô hình dùng trong pipeline.

## 1. Mô hình YOLOv8-Face (Giai đoạn 1 - Định vị khuôn mặt & ROI)
- **File:** `yolov8n-face.pt` (đặt trong thư mục `weights/` này)
- **Nguồn tải:** [HuggingFace - Bingsu/adetailer](https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8n.pt)
- **Lệnh tải nhanh trên Windows PowerShell** (chạy từ thư mục gốc project):
  ```powershell
  Invoke-WebRequest -Uri "https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8n.pt" -OutFile "weights/yolov8n-face.pt"
  ```
- **Lệnh tải trên Linux / macOS:**
  ```bash
  curl -L -o weights/yolov8n-face.pt "https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8n.pt"
  ```
- **Lưu ý:** Nếu chưa có file này, hệ thống tự động dùng bộ lọc **OpenCV Haar Cascade** làm phương án dự phòng, không gây lỗi (độ chính xác thấp hơn).

## 2. Mô hình SegFormer-B0 (Giai đoạn 2 - Phân vùng nám da)
- **Mô hình nền:** `nvidia/segformer-b0-finetuned-ade-512-512`. Thư viện `transformers` tự tải trọng số pretrained này từ HuggingFace Hub về cache khi bạn huấn luyện.
- **Repo không kèm checkpoint đã huấn luyện.** Bạn cần tự chạy `scripts/05_stage2_train_segformer.py` để fine-tune trên dữ liệu nám da. Checkpoint tốt nhất được lưu tại `segformer_melasma_checkpoint/best_model` (thư mục này nằm ở thư mục gốc project, không nằm trong `weights/`).
- **Cảnh báo:** Nếu chạy `scripts/08_pipeline_end_to_end.py` khi chưa có checkpoint, script **không báo lỗi** mà dùng mô hình nền chưa được huấn luyện cho nám da. Kết quả phân vùng và điểm MASI khi đó **không có giá trị**. Hãy chắc chắn terminal in dòng `[Model] Nạp checkpoint fine-tuned từ: ...`.
- Luôn chạy các script từ **thư mục gốc project**, vì đường dẫn checkpoint là đường dẫn tương đối.
