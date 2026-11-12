"""
Script: 08_pipeline_end_to_end.py
Muc dich: NOI TOAN BO 3 GIAI DOAN cua Huong 1 thanh mot pipeline hoan chinh:

    Anh khuon mat day du
        -> [Giai doan 1] YOLO/Haar dinh vi mat + suy luan 5 vung ROI (giu
           nguyen do phan giai goc)
        -> [Giai doan 2] SegFormer da fine-tune phan vung ton thuong tren
           tung ROI
        -> [Giai doan 3] Tinh MASI/mMASI tu ket qua phan vung
        -> Xuat: anh minh hoa (ROI + mask chong len anh goc) + file JSON
           ket qua diem so -- day la dau ra dung de chup man hinh/dua vao
           Chuong 4 khoa luan.

CHAY:
    python 08_pipeline_end_to_end.py duong_dan_anh.jpg
"""

import json
import sys
from pathlib import Path
import cv2
import numpy as np
import torch
from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor


class NpEncoder(json.JSONEncoder):
    """Lop bao ve du phong: tu dong chuyen doi moi kieu du lieu NumPy con sot
    lai (float32, int64, ndarray...) sang kieu Python thuan truoc khi ghi
    JSON, dam bao khong bao gio gap lai loi 'not JSON serializable'."""
    def default(self, obj):
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


sys.path.append(str(Path(__file__).parent))
from importlib import import_module

_stage1 = import_module("03_stage1_roi_detection")
_stage3 = import_module("07_stage3_masi")

FaceDetector = _stage1.FaceDetector
derive_anatomical_rois = _stage1.derive_anatomical_rois
crop_roi = _stage1.crop_roi
analyze_region = _stage3.analyze_region
compute_masi = _stage3.compute_masi

CHECKPOINT_DIR = Path("segformer_melasma_checkpoint/best_model")
OUTPUT_DIR = Path("pipeline_demo_output")


def segment_roi(image_bgr, model, processor, device):
    """Chay SegFormer da fine-tune tren mot anh ROI, tra ve mask nhi phan
    {0,1} CUNG KICH THUOC voi anh ROI dau vao (upsample lai sau khi model
    du doan o do phan giai co dinh cua no)."""
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    inputs = processor(images=image_rgb, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits

    upsampled = torch.nn.functional.interpolate(
        logits, size=image_bgr.shape[:2], mode="bilinear", align_corners=False
    )
    mask = upsampled.argmax(dim=1)[0].cpu().numpy().astype(np.uint8)
    return mask


def run_pipeline(image_path: str):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if CHECKPOINT_DIR.exists():
        print(f"[Model] Nạp checkpoint fine-tuned từ: {CHECKPOINT_DIR}")
        processor = SegformerImageProcessor.from_pretrained(CHECKPOINT_DIR)
        model = SegformerForSemanticSegmentation.from_pretrained(CHECKPOINT_DIR).to(device)
    else:
        print(f"[Model] Chưa tìm thấy checkpoint tại '{CHECKPOINT_DIR}'.")
        print("        Đang nạp mô hình pretrained mặc định 'nvidia/segformer-b0-finetuned-ade-512-512' từ HuggingFace...")
        print("        (Để có kết quả phân vùng nám chuẩn theo dữ liệu riêng, hãy chạy script 05_stage2_train_segformer.py trước).")
        pretrained_name = "nvidia/segformer-b0-finetuned-ade-512-512"
        processor = SegformerImageProcessor.from_pretrained(pretrained_name)
        model = SegformerForSemanticSegmentation.from_pretrained(
            pretrained_name, num_labels=2, ignore_mismatched_sizes=True
        ).to(device)
    model.eval()

    detector = FaceDetector()

    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Khong doc duoc anh: {image_path}")

    print(">>> Giai doan 1: dinh vi khuon mat + suy luan vung ROI...")
    face_box = detector.detect(image)
    if face_box is None:
        print("[!] Khong phat hien duoc khuon mat. Dung lai.")
        return
    rois = derive_anatomical_rois(face_box)

    out_path = OUTPUT_DIR / Path(image_path).stem
    out_path.mkdir(parents=True, exist_ok=True)

    region_results = {}
    overlay = image.copy()

    print(">>> Giai doan 2: phan vung ton thuong tren tung ROI...")
    for roi in rois:
        crop = crop_roi(image, roi)
        if crop.size == 0:
            continue

        mask = segment_roi(crop, model, processor, device)
        region_results[roi.name] = analyze_region(crop, mask)

        x1, y1, x2, y2 = roi.box
        colored_mask = np.zeros_like(crop)
        colored_mask[mask == 1] = (0, 0, 255)
        blended = cv2.addWeighted(crop, 0.7, colored_mask, 0.3, 0)
        overlay[y1:y2, x1:x2] = blended
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 1)

        cv2.imwrite(str(out_path / f"{roi.name}_mask_overlay.jpg"), blended)

    print(">>> Giai doan 3: tinh chi so MASI/mMASI...")
    masi_result = compute_masi(region_results)

    cv2.imwrite(str(out_path / "full_overlay.jpg"), overlay)
    with open(out_path / "result.json", "w", encoding="utf-8") as f:
        json.dump(
            {"per_region_analysis": region_results, "masi_result": masi_result},
            f, ensure_ascii=False, indent=2, cls=NpEncoder,
        )

    print(f"\n=== KET QUA CUOI CUNG ({image_path}) ===")
    for region, data in region_results.items():
        print(f"  {region:10s}: dien tich={data['area_pct']}%  A={data['A']}  D={data['D']}")
    print(f"\n  MASI  = {masi_result['MASI']}  (thang ly thuyet 0-48)")
    print(f"  mMASI = {masi_result['mMASI']}  (thang ly thuyet 0-24, khong dung Homogeneity)")
    print(f"\nAnh + JSON ket qua da luu tai: {out_path}")
    print("-> Dung anh 'full_overlay.jpg' va noi dung 'result.json' de chup man hinh")
    print("   dua vao Chuong 4 khoa luan (minh hoa dau ra thuc te cua pipeline).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cach dung: python 08_pipeline_end_to_end.py <duong_dan_anh.jpg>")
        sys.exit(1)
    run_pipeline(sys.argv[1])
