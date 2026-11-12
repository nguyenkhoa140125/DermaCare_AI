# Hướng dẫn tải Weights cho Mô hình AI

Để chạy pipeline với độ chính xác cao nhất, bạn cần tải file trọng số (weights) và đặt vào thư mục `weights/` này:

## 1. Mô hình YOLOv8-Face (Giai đoạn 1 - Định vị khuôn mặt & ROI)
- **File:** `yolov8n-face.pt`
- **Nguồn tải:** [HuggingFace - Bingsu/adetailer](https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8n.pt)
- **Lệnh tải nhanh trên Windows PowerShell:**
  ```powershell
  Invoke-WebRequest -Uri "https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8n.pt" -OutFile "weights/yolov8n-face.pt"
  ```
- **Lưu ý:** Nếu chưa có file này, hệ thống sẽ tự động dùng bộ lọc **OpenCV Haar Cascade** tích hợp sẵn làm phương án dự phòng mà không gây lỗi.

## 2. Mô hình SegFormer-B0 (Giai đoạn 2 - Phân vùng nám da)
- **Tên mô hình:** `nvidia/segformer-b0-finetuned-ade-512-512`
- **Cơ chế:** Thư viện `transformers` sẽ tự động tải trọng số pretrained từ HuggingFace Hub về cache khi bạn chạy `08_pipeline_end_to_end.py` lần đầu tiên.
- Khi bạn huấn luyện xong với dữ liệu riêng qua script `05_stage2_train_segformer.py`, checkpoint tốt nhất sẽ được tự động lưu vào thư mục `segformer_melasma_checkpoint/best_model`.
