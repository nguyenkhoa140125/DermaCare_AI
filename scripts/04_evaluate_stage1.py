"""
Script: 04_evaluate_stage1.py
Muc dich: (a) Cong cu don gian de TU GAN NHAN TAY khung ROI chuan tren mot
tap nho anh mat (~20-30 anh), va (b) tinh IoU THAT giua ROI do model du
doan (script 03) so voi nhan tay -- day la SO LIEU DINH LUONG THAT cho
Giai doan 1 trong khoa luan (khong can cong cu ngoai nhu CVAT/Roboflow).

QUAN TRONG -- CHE DO 'annotate' CHI CHAY DUOC TREN MAY CA NHAN (KHONG chay
duoc tren Google Colab), vi no can mo cua so do hoa (cv2.imshow) va bat thao
tac chuot -- Colab la moi truong server, khong co man hinh hien thi. Neu ban
dang dung Colab: hay tai script nay + vai anh mau ve MAY CA NHAN, chay che do
'annotate' o do, roi upload file ground_truth_rois.json ket qua len lai
Colab/Google Drive de dung cho che do 'evaluate' (che do nay tinh toan thuan
tuy, chay binh thuong tren Colab).

CACH DUNG:

  Buoc 1 -- Tu gan nhan tay (CHAY TREN MAY CA NHAN, ve 5 khung bang chuot):
      python 04_evaluate_stage1.py annotate anh_mau/*.jpg

      Huong dan thao tac khi cua so hien len:
        - Keo chuot de ve khung cho tung vung, theo dung thu tu duoc in ra
          terminal (Tran -> Ma_trai -> Ma_phai -> Mui -> Cam)
        - Nhan 'n' (hoac Enter) de xac nhan khung vua ve, qua vung/anh tiep theo
        - Nhan 'x' de bo qua RIENG VUNG hien tai (dung khi vung nay khong hien
          dien/khong quan sat duoc trong anh, vd goc chup nghieng che khuat --
          CAC VUNG KHAC da ve dung trong CUNG anh nay VAN duoc giu lai)
        - Nhan 's' de BO QUA CA ANH HIEN TAI, bao gom CA CAC VUNG DA VE TRUOC DO
          trong anh nay cung bi huy (dung khi CA ANH khong phai anh mat -- vd
          anh soi da phong dai, mo hoc, bieu do...)
        - Nhan 'q' de dung han chuong trinh (nhung gi da luu truoc do van giu)
        - Chay lai lenh nay nhieu lan voi tap anh khac nhau se TU DONG BO QUA
          anh da gan nhan roi, chi hoi cac anh moi -- khong lo lam lai tu dau

  Buoc 2 -- Chay du doan cua model (script 03) tren cung tap anh do, luu
            ket qua vao predictions.json (xem huong dan cuoi file).

  Buoc 3 -- Tinh IoU that:
      python 04_evaluate_stage1.py evaluate
"""

import json
import sys
from pathlib import Path
import cv2

GT_PATH = Path("ground_truth_rois.json")
PRED_PATH = Path("predictions_rois.json")
REGION_ORDER = ["Tran", "Ma_trai", "Ma_phai", "Mui", "Cam"]


class SkipImageSignal(Exception):
    """Duoc nem ra khi nguoi dung nhan 's' de bo qua NGUYEN CA ANH hien tai
    (vd anh khong phai anh khuon mat -- soi da, mo hoc, bieu do...). Moi vung
    da ve truoc do trong anh nay (neu co) se KHONG duoc luu."""
    pass


class SkipRegionSignal(Exception):
    """Duoc nem ra khi nguoi dung nhan 'x' de bo qua RIENG VUNG hien tai (vd
    goc chup nghieng khien vung nay khong hien dien/khong quan sat duoc),
    trong khi VAN GIU LAI cac vung khac da ve dung cho anh nay."""
    pass


# ---------------------------------------------------------------------------
# CHE DO 1: TU GAN NHAN TAY
# ---------------------------------------------------------------------------
def annotate(image_paths):
    ground_truth = {}
    if GT_PATH.exists():
        ground_truth = json.loads(GT_PATH.read_text(encoding="utf-8"))

    skipped_bad_images = []
    for img_path in image_paths:
        img_path = str(img_path)

        if img_path in ground_truth:
            print(f"[Bo qua] Da gan nhan truoc do: {img_path}")
            continue

        image = cv2.imread(img_path)
        if image is None:
            print(f"[!] Bo qua, khong doc duoc: {img_path}")
            continue

        boxes = {}
        try:
            for region_name in REGION_ORDER:
                print(f"\n>>> Anh: {img_path} | Ve khung cho vung: {region_name}")
                print("    (Keo chuot trai de ve khung, tha chuot de xac nhan)")
                print("    Phim tat: 'n'=xac nhan | 'x'=vung nay KHONG hien dien"
                      " (giu lai cac vung khac) | 's'=BO QUA CA ANH | 'q'=dung han")
                try:
                    box = _draw_single_box(image.copy(), region_name)
                except SkipRegionSignal:
                    print(f"    -> Da bo qua rieng vung '{region_name}' (khong hien dien trong anh).")
                    continue
                if box is not None:
                    boxes[region_name] = list(box)
        except SkipImageSignal:
            print(f"[Da bo qua] Anh khong hop le (khong phai anh mat?): {img_path}")
            skipped_bad_images.append(img_path)
            cv2.destroyAllWindows()
            continue

        if not boxes:
            print(f"[!] Khong co vung nao hop le cho {img_path}, khong luu anh nay.")
            continue

        ground_truth[img_path] = boxes
        GT_PATH.write_text(json.dumps(ground_truth, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] Da luu nhan cho {img_path} ({len(boxes)}/5 vung) -> {GT_PATH}")

    cv2.destroyAllWindows()
    print(f"\nHOAN TAT. Da gan nhan tong cong {len(ground_truth)} anh (tich luy) trong {GT_PATH}.")
    if skipped_bad_images:
        print(f"Da bo qua {len(skipped_bad_images)} anh khong hop le (nhan 's'):")
        for p in skipped_bad_images:
            print(f"    - {p}")


def _draw_single_box(image, window_title):
    state = {"start": None, "box": None, "drawing": False}

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            state["start"] = (x, y)
            state["drawing"] = True
        elif event == cv2.EVENT_MOUSEMOVE and state["drawing"]:
            disp = image.copy()
            cv2.rectangle(disp, state["start"], (x, y), (0, 255, 0), 2)
            cv2.imshow(window_title, disp)
        elif event == cv2.EVENT_LBUTTONUP:
            state["drawing"] = False
            x1, y1 = state["start"]
            state["box"] = (min(x1, x), min(y1, y), max(x1, x), max(y1, y))

    cv2.namedWindow(window_title)
    cv2.setMouseCallback(window_title, on_mouse)
    cv2.imshow(window_title, image)

    while True:
        key = cv2.waitKey(20) & 0xFF
        if key == ord("n") or key == 13:  # 'n' hoac Enter -> xac nhan xong khung nay
            break
        if key == ord("x"):  # 'x' -> bo qua RIENG vung nay, giu lai cac vung khac
            cv2.destroyWindow(window_title)
            raise SkipRegionSignal()
        if key == ord("s"):  # 's' -> bo qua nguyen anh nay, khong luu gi ca
            cv2.destroyWindow(window_title)
            raise SkipImageSignal()
        if key == ord("q"):
            cv2.destroyWindow(window_title)
            sys.exit("Da dung theo yeu cau nguoi dung (q).")

    cv2.destroyWindow(window_title)
    return state["box"]


# ---------------------------------------------------------------------------
# CHE DO 2: TINH IoU THAT
# ---------------------------------------------------------------------------
def compute_iou(box_a, box_b):
    xa1, ya1, xa2, ya2 = box_a
    xb1, yb1, xb2, yb2 = box_b

    inter_x1, inter_y1 = max(xa1, xb1), max(ya1, yb1)
    inter_x2, inter_y2 = min(xa2, xb2), min(ya2, yb2)
    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)

    area_a = (xa2 - xa1) * (ya2 - ya1)
    area_b = (xb2 - xb1) * (yb2 - yb1)
    union = area_a + area_b - inter_area
    return inter_area / union if union > 0 else 0.0


def evaluate():
    assert GT_PATH.exists(), f"Chua co {GT_PATH} -- chay 'annotate' truoc."
    assert PRED_PATH.exists(), (
        f"Chua co {PRED_PATH}. Ban can tu chay script 03 tren cung tap anh va luu "
        f"ket qua ROI vao file JSON cung cau truc nhu {GT_PATH}, dat ten {PRED_PATH}."
    )

    ground_truth = json.loads(GT_PATH.read_text(encoding="utf-8"))
    predictions = json.loads(PRED_PATH.read_text(encoding="utf-8"))

    per_region_ious = {r: [] for r in REGION_ORDER}
    for img_path, gt_boxes in ground_truth.items():
        pred_boxes = predictions.get(img_path, {})
        for region in REGION_ORDER:
            if region in gt_boxes and region in pred_boxes:
                iou = compute_iou(gt_boxes[region], pred_boxes[region])
                per_region_ious[region].append(iou)

    print("\n=== KET QUA DANH GIA GIAI DOAN 1 (IoU that, tinh tren tap tu gan nhan) ===")
    all_ious = []
    for region, ious in per_region_ious.items():
        if ious:
            mean_iou = sum(ious) / len(ious)
            all_ious.extend(ious)
            print(f"  {region:10s}: mean IoU = {mean_iou:.3f}  (n={len(ious)} anh)")
        else:
            print(f"  {region:10s}: khong co du lieu")

    if all_ious:
        print(f"\n  TRUNG BINH TOAN BO (mIoU): {sum(all_ious) / len(all_ious):.3f}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("annotate", "evaluate"):
        print("Cach dung:")
        print("  python 04_evaluate_stage1.py annotate anh1.jpg anh2.jpg ...")
        print("  python 04_evaluate_stage1.py evaluate")
        sys.exit(1)

    if sys.argv[1] == "annotate":
        annotate(sys.argv[2:])
    else:
        evaluate()
