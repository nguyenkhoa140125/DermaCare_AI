"""
Script: 06_evaluate_stage2.py
Muc dich: Tinh cac chi so danh gia THAT cho model SegFormer da huan luyen o
script 05 -- mIoU, Dice score, Precision, Recall tren tap validation cua
ISIC. Day la SO LIEU DINH LUONG chinh dua vao Chuong 4 khoa luan (tuong tu
cach bai bao tham khao trinh bay Confusion Matrix / Precision-Recall / F1).
"""

from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor
from tqdm import tqdm

import sys
sys.path.append(str(Path(__file__).parent))
from importlib import import_module

_stage2 = import_module("05_stage2_train_segformer".replace("-", "_"))
LesionSegDataset = _stage2.LesionSegDataset

DATA_DIR = Path("processed_isic")
CHECKPOINT_DIR = Path("segformer_melasma_checkpoint/best_model")


def compute_metrics(pred_mask: np.ndarray, gt_mask: np.ndarray):
    """pred_mask, gt_mask: mang nhi phan {0,1} cung kich thuoc."""
    tp = np.logical_and(pred_mask == 1, gt_mask == 1).sum()
    fp = np.logical_and(pred_mask == 1, gt_mask == 0).sum()
    fn = np.logical_and(pred_mask == 0, gt_mask == 1).sum()
    tn = np.logical_and(pred_mask == 0, gt_mask == 0).sum()

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    dice = (2 * tp) / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0.0
    iou = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0

    return {"precision": precision, "recall": recall, "dice": dice, "iou": iou}


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    assert CHECKPOINT_DIR.exists(), f"Khong tim thay checkpoint tai {CHECKPOINT_DIR}. Chay script 05 truoc."

    processor = SegformerImageProcessor.from_pretrained(CHECKPOINT_DIR)
    model = SegformerForSemanticSegmentation.from_pretrained(CHECKPOINT_DIR).to(device)
    model.eval()

    val_ds = LesionSegDataset(DATA_DIR / "val", processor)
    val_loader = DataLoader(val_ds, batch_size=1, shuffle=False)

    all_metrics = []
    with torch.no_grad():
        for batch in tqdm(val_loader, desc="Danh gia"):
            pixel_values = batch["pixel_values"].to(device)
            labels = batch["labels"].numpy()[0]

            outputs = model(pixel_values=pixel_values)
            logits = outputs.logits  # (1, num_labels, H, W)
            upsampled = torch.nn.functional.interpolate(
                logits, size=labels.shape, mode="bilinear", align_corners=False
            )
            pred_mask = upsampled.argmax(dim=1)[0].cpu().numpy()

            all_metrics.append(compute_metrics(pred_mask, labels))

    print(f"\n=== KET QUA DANH GIA GIAI DOAN 2 (tren {len(all_metrics)} anh validation ISIC) ===")
    for key in ["precision", "recall", "dice", "iou"]:
        values = [m[key] for m in all_metrics]
        print(f"  {key.capitalize():10s}: mean = {np.mean(values):.4f}  (std = {np.std(values):.4f})")

    # Luu ra file de trich dan trong bao cao
    with open("stage2_evaluation_results.txt", "w", encoding="utf-8") as f:
        f.write("Ket qua danh gia Giai doan 2 (SegFormer fine-tuned tren ISIC 2018)\n")
        f.write(f"So anh validation: {len(all_metrics)}\n\n")
        for key in ["precision", "recall", "dice", "iou"]:
            values = [m[key] for m in all_metrics]
            f.write(f"{key}: mean={np.mean(values):.4f}, std={np.std(values):.4f}\n")
    print("\nDa luu ket qua vao stage2_evaluation_results.txt")


if __name__ == "__main__":
    main()
