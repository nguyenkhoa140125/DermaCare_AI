"""
Script: 03_stage1_roi_detection.py
Muc dich: GIAI DOAN 1 cua pipeline Huong 1 -- dinh vi khung khuon mat bang
YOLO (pretrained tren tap WIDERFace), sau do suy luan hinh hoc ra 5 vung
giai phau hay bi Nam: Tran, Ma trai, Ma phai, Mui, Cam.

CACH LAY MODEL YOLO-FACE (da xac minh nguon hoat dong, tai file .pt, dat vao
thu muc weights/):
    https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8n.pt
    (repo Bingsu/adetailer, huan luyen tren bo chuan WIDER FACE, giay phep
    Apache-2.0, dang duoc dung rong rai boi cong cu ADetailer)
    -> luu thanh weights/yolov8n-face.pt

Neu CHUA co file weights nay, script se TU DONG dung phuong an du phong
(OpenCV Haar Cascade -- da co san trong opencv-python, khong can tai them gi)
de pipeline luon chay duoc ngay, khong bi gian doan.

QUAN TRONG: Ty le hinh hoc (FOREHEAD_RATIO, CHEEK_RATIO...) ben duoi la uoc
luong dua tren ty le khuon mat co dien (rule of thirds/fifths) thuong dung
trong tai lieu da lieu/phau thuat tham my. Ban NEN kiem tra/hieu chinh lai
cac ty le nay bang tap anh da tu gan nhan tay (xem script 04_evaluate_stage1.py).
"""

from dataclasses import dataclass
from pathlib import Path
import cv2
import numpy as np

WEIGHTS_PATH = Path("weights/yolov8n-face.pt")

# Ty le hinh hoc uoc luong tung vung so voi khung mat (x1,y1,x2,y2)
FOREHEAD_TOP = 0.05      # bat dau tu 5% duoi dinh dau (tranh vung toc)
FOREHEAD_BOTTOM = 0.30
MIDFACE_BOTTOM = 0.68     # het vung mui/ma
CHIN_BOTTOM = 0.98
CHEEK_INNER = 0.38        # bien trong cua ma (gan mui)
CHEEK_OUTER = 0.90        # bien ngoai cua ma
NOSE_LEFT = 0.38
NOSE_RIGHT = 0.62
CHIN_LEFT = 0.30
CHIN_RIGHT = 0.70


@dataclass
class ROI:
    name: str
    box: tuple  # (x1, y1, x2, y2) toa do tuyet doi tren anh goc


class FaceDetector:
    """Wrapper: uu tien YOLO-face pretrained, tu dong fallback sang Haar Cascade."""

    def __init__(self):
        self.mode = None
        if WEIGHTS_PATH.exists():
            from ultralytics import YOLO
            self.model = YOLO(str(WEIGHTS_PATH))
            self.mode = "yolo"
            print(f"[FaceDetector] Dang dung YOLO-face: {WEIGHTS_PATH}")
        else:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.model = cv2.CascadeClassifier(cascade_path)
            self.mode = "haar_fallback"
            print(f"[FaceDetector] CANH BAO: khong tim thay {WEIGHTS_PATH}.")
            print("   Dang dung phuong an du phong Haar Cascade (do chinh xac thap hon YOLO).")
            print("   -> Tai yolov8n-face.pt tu link trong docstring de dung YOLO that.")

    def detect(self, image_bgr: np.ndarray):
        """Tra ve bounding box (x1,y1,x2,y2) cua khuon mat lon nhat trong anh,
        hoac None neu khong tim thay."""
        if self.mode == "yolo":
            results = self.model.predict(image_bgr, verbose=False)
            boxes = results[0].boxes
            if len(boxes) == 0:
                return None
            # chon box co confidence cao nhat
            best_idx = boxes.conf.argmax().item()
            x1, y1, x2, y2 = boxes.xyxy[best_idx].tolist()
            return int(x1), int(y1), int(x2), int(y2)
        else:
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            faces = self.model.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            if len(faces) == 0:
                return None
            # chon khuon mat co dien tich lon nhat
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            return int(x), int(y), int(x + w), int(y + h)


def derive_anatomical_rois(face_box: tuple) -> list:
    """Suy luan 5 vung ROI (Tran, Ma trai, Ma phai, Mui, Cam) tu khung khuon mat,
    dua tren ty le hinh hoc dinh nghia o dau file."""
    x1, y1, x2, y2 = face_box
    w = x2 - x1
    h = y2 - y1

    def pt(px, py):
        return int(x1 + px * w), int(y1 + py * h)

    rois = [
        ROI("Tran", (*pt(0.10, FOREHEAD_TOP), *pt(0.90, FOREHEAD_BOTTOM))),
        ROI("Ma_trai", (*pt(1 - CHEEK_OUTER, FOREHEAD_BOTTOM), *pt(1 - CHEEK_INNER, MIDFACE_BOTTOM))),
        ROI("Ma_phai", (*pt(CHEEK_INNER, FOREHEAD_BOTTOM), *pt(CHEEK_OUTER, MIDFACE_BOTTOM))),
        ROI("Mui", (*pt(NOSE_LEFT, FOREHEAD_BOTTOM), *pt(NOSE_RIGHT, MIDFACE_BOTTOM))),
        ROI("Cam", (*pt(CHIN_LEFT, MIDFACE_BOTTOM), *pt(CHIN_RIGHT, CHIN_BOTTOM))),
    ]
    return rois


def crop_roi(image_bgr: np.ndarray, roi: ROI) -> np.ndarray:
    """Cat vung ROI, GIU NGUYEN do phan giai goc (khong resize) -- dung tinh
    than giai quyet 'resolution tradeoff' cua Huong 1."""
    x1, y1, x2, y2 = roi.box
    h_img, w_img = image_bgr.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w_img, x2), min(h_img, y2)
    return image_bgr[y1:y2, x1:x2]


def process_image(image_path: str, detector: FaceDetector, out_dir: str = "rois_output"):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Khong doc duoc anh: {image_path}")

    face_box = detector.detect(image)
    if face_box is None:
        print(f"[!] Khong phat hien khuon mat trong: {image_path}")
        return None

    rois = derive_anatomical_rois(face_box)

    out_path = Path(out_dir) / Path(image_path).stem
    out_path.mkdir(parents=True, exist_ok=True)

    for roi in rois:
        crop = crop_roi(image, roi)
        if crop.size == 0:
            continue
        cv2.imwrite(str(out_path / f"{roi.name}.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, 100])

    # Anh minh hoa: ve khung ROI len anh goc (dung cho bao cao khoa luan)
    vis = image.copy()
    for roi in rois:
        x1, y1, x2, y2 = roi.box
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(vis, roi.name, (x1, max(0, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.imwrite(str(out_path / "visualization.jpg"), vis)

    print(f"[OK] {image_path} -> {out_path} ({len(rois)} vung ROI)")
    return rois


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Cach dung: python 03_stage1_roi_detection.py <duong_dan_anh.jpg> [...]")
        sys.exit(1)

    detector = FaceDetector()

    pred_path = Path("predictions_rois.json")
    predictions = {}
    if pred_path.exists():
        try:
            predictions = json.loads(pred_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    for img_path in sys.argv[1:]:
        try:
            rois = process_image(img_path, detector)
        except FileNotFoundError as e:
            print(f"[!] Bo qua (khong doc duoc, co the da bi xoa/di chuyen): {img_path}")
            continue
        if rois is not None:
            predictions[img_path] = {roi.name: list(roi.box) for roi in rois}

    pred_path.write_text(json.dumps(predictions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[HOAN TAT] Da luu toa do du doan vao file: {pred_path} ({len(predictions)} anh)")
