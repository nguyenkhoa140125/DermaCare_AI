# Hướng dẫn cài đặt môi trường (chạy trên GPU riêng)

Tài liệu này giải thích chi tiết cách chuẩn bị GPU NVIDIA và môi trường PyTorch CUDA để
chạy pipeline (YOLO ROI Detection + SegFormer Segmentation + MASI). Hướng dẫn cài đặt
ngắn gọn nằm trong `README.md` ở thư mục gốc; đọc tài liệu này khi gặp lỗi GPU/CUDA.

---

## Bước 1 — Kiểm tra GPU và driver NVIDIA

Mở terminal (Command Prompt trên Windows, hoặc Terminal trên Linux/Mac) và chạy:

```bash
nvidia-smi
```

Nếu lệnh này chạy được và hiển thị tên GPU + phiên bản **CUDA Version** ở góc trên
bên phải, driver của bạn đã sẵn sàng. Ghi nhớ số phiên bản CUDA này (ví dụ: 12.1,
12.4...) — sẽ cần ở Bước 3.

Nếu lệnh báo lỗi "not found" hoặc "not recognized": bạn cần cài driver NVIDIA mới
nhất tại https://www.nvidia.com/Download/index.aspx trước, khởi động lại máy, rồi
thử lại lệnh trên.

---

## Bước 2 — Tạo môi trường ảo Python (khuyến nghị Python 3.10 hoặc 3.11)

```bash
python -m venv dermacare_env

# Kích hoạt môi trường ảo:
# Windows (Command Prompt):
dermacare_env\Scripts\activate
# Windows (PowerShell):
dermacare_env\Scripts\Activate.ps1
# Linux / Mac:
source dermacare_env/bin/activate
```

Sau khi kích hoạt, dòng lệnh của bạn sẽ hiện tiền tố `(dermacare_env)`.

---

## Bước 3 — Cài PyTorch bản có hỗ trợ CUDA (QUAN TRỌNG — không cài nhầm bản CPU)

Truy cập https://pytorch.org/get-started/locally/ , chọn đúng phiên bản CUDA khớp
với `nvidia-smi` ở Bước 1, trang web sẽ tự sinh ra lệnh cài đặt chính xác.

Ví dụ tham khảo (CUDA 12.1):

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**Kiểm tra lại ngay sau khi cài** — đây là bước hay bị bỏ sót và gây lỗi khó hiểu
về sau:

```bash
python -c "import torch; print('GPU khả dụng:', torch.cuda.is_available()); print('Tên GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Không tìm thấy')"
```

> Lưu ý: GPU đời cũ (ví dụ dòng GTX 10xx) có thể không được hỗ trợ bởi các bản PyTorch CUDA mới nhất.
> Nếu bản mới báo lỗi hoặc không nhận GPU, dùng bản `cu121` ở lệnh trên.

Nếu dòng "GPU khả dụng" in ra `False`, dừng lại — đừng cài tiếp các bước sau, vì
bản PyTorch bạn cài là bản CPU (rất chậm khi huấn luyện). Quay lại chọn đúng lệnh
theo phiên bản CUDA ở pytorch.org.

---

## Bước 4 — Cài các thư viện còn lại

Chạy từ thư mục gốc của project (thư mục chứa `requirements.txt`):

```bash
cd DermaCare_AI
pip install -r requirements.txt
```

---

## Bước 5 — Kiểm tra nhanh toàn bộ môi trường

```bash
python -c "
import torch, ultralytics, transformers, cv2
print('Torch:', torch.__version__, '| CUDA:', torch.cuda.is_available())
print('Ultralytics OK')
print('Transformers:', transformers.__version__)
print('OpenCV:', cv2.__version__)
"
```

Nếu không có lỗi nào hiện ra, môi trường đã sẵn sàng cho Giai đoạn A-B.

---

## Ghi chú về dung lượng ổ đĩa

Chuẩn bị tối thiểu ~15GB trống:
- Bộ ISIC 2018 Task 1 (ảnh + mask): ~3-4GB
- Metadata + subset MultiCaRe: ~1-2GB
- Model checkpoint SegFormer trong quá trình huấn luyện: ~2-5GB
- Các thư viện Python (torch, transformers...): ~5GB
