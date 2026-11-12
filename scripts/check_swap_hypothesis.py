"""Kiem tra gia thuyet hoan doi nhan Ma_trai/Ma_phai bang cach tinh lai IoU
neu hoan doi 2 nhan nay cho tung anh, so sanh voi ket qua goc."""
import json
import sys

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

gt = json.load(open(sys.argv[1]))
pred = json.load(open(sys.argv[2]))

normal_ious, swapped_ious = [], []
for img, gt_boxes in gt.items():
    pred_boxes = pred.get(img, {})
    if "Ma_trai" in gt_boxes and "Ma_phai" in gt_boxes and "Ma_trai" in pred_boxes and "Ma_phai" in pred_boxes:
        normal_ious.append(compute_iou(gt_boxes["Ma_trai"], pred_boxes["Ma_trai"]))
        normal_ious.append(compute_iou(gt_boxes["Ma_phai"], pred_boxes["Ma_phai"]))
        # Neu hoan doi: so gt Ma_trai voi pred Ma_phai va nguoc lai
        swapped_ious.append(compute_iou(gt_boxes["Ma_trai"], pred_boxes["Ma_phai"]))
        swapped_ious.append(compute_iou(gt_boxes["Ma_phai"], pred_boxes["Ma_trai"]))

print(f"mIoU Ma_trai+Ma_phai KHONG hoan doi (nhu hien tai): {sum(normal_ious)/len(normal_ious):.3f}")
print(f"mIoU Ma_trai+Ma_phai NEU hoan doi nhan:              {sum(swapped_ious)/len(swapped_ious):.3f}")
if sum(swapped_ious) > sum(normal_ious):
    print("\n=> XAC NHAN: co hoan doi nhan trai/phai. Can sua lai quy uoc dat ten.")
else:
    print("\n=> KHONG phai do hoan doi nhan -- IoU thap do nguyen nhan khac (vi du: anh")
    print("   khong chuan/goc chup la, ty le hinh hoc chua phu hop voi tap anh nay).")
