"""
Script: 05_stage2_train_segformer.py
Muc dich: GIAI DOAN 2 cua pipeline Huong 1 -- fine-tune SegFormer (mo hinh
segmentation dang Transformer) tren bo du lieu ISIC 2018 (da qua tien xu ly
o script 02) de hoc phan vung tổn thuong da dang pixel-level.

Day la mo hinh duoc HUAN LUYEN THAT, co checkpoint that, co so lieu danh gia
that (xem script 06) -- dung lam thanh phan "lo AI" chinh cho Chuong 4 khoa
luan. Luu y: huan luyen tren ISIC (anh soi da, ton thuong khu tru) nhu mot
proxy dataset do THIEU du lieu Nam da co gan nhan public (da neu ro trong
Chuong 4.5 la han che phuong phap).

CHAY TREN GOOGLE COLAB: nho chon Runtime > Change runtime type > GPU truoc
khi chay script nay, neu khong se rat cham.
"""

from pathlib import Path
import os
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor
from tqdm import tqdm

DATA_DIR = Path("processed_isic")
OUTPUT_DIR = Path("segformer_melasma_checkpoint")
MODEL_NAME = "nvidia/segformer-b0-finetuned-ade-512-512"  # backbone pretrained nhe, phu hop fine-tune

NUM_EPOCHS = 15
BATCH_SIZE = 2  # giam tu 4 xuong 2 -- phu hop GPU VRAM thap (vd GTX 1050 Ti 4GB)
LEARNING_RATE = 6e-5
NUM_LABELS = 2  # 0 = nen (background/da thuong), 1 = vung ton thuong/sac to
GRADIENT_ACCUMULATION_STEPS = 2  # bu lai cho batch size nho: batch "hieu qua" = 2*2 = 4


def warn_if_not_on_drive():
    """Canh bao neu dang chay trong o dia tam cua Colab (/content/, ngoai
    Google Drive) -- checkpoint huan luyen se bi XOA neu runtime bi ngat.
    Day la buoc TON NHIEU THOI GIAN NHAT trong toan bo pipeline, nen kiem
    tra ky truoc khi bat dau huan luyen."""
    cwd = os.getcwd()
    is_colab = os.path.exists("/content")
    if is_colab and "/drive/MyDrive" not in cwd:
        print("=" * 70)
        print("CANH BAO QUAN TRONG: ban dang KHONG chay trong Google Drive!")
        print(f"    Thu muc hien tai: {cwd}")
        print("    Checkpoint huan luyen (co the mat vai gio de tao ra) se")
        print("    bi XOA neu Colab runtime bi ngat/restart giua chung.")
        print("    -> Chay lai cell 'Ket noi Google Drive' (mount + %cd) truoc.")
        print("=" * 70)
        response = input("Van tiep tuc chay du sao (khong khuyen nghi)? (y/N): ")
        if response.strip().lower() != "y":
            raise SystemExit("Da dung lai. Chay lai cell mount Google Drive truoc.")


class LesionSegDataset(Dataset):
    def __init__(self, split_dir: Path, processor: SegformerImageProcessor):
        self.image_dir = split_dir / "images"
        self.mask_dir = split_dir / "masks"
        self.image_files = sorted(self.image_dir.glob("*.jpg"))
        self.processor = processor

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        img_path = self.image_files[idx]
        mask_path = self.mask_dir / f"{img_path.stem}.png"

        image = Image.open(img_path).convert("RGB")
        mask = Image.open(mask_path).convert("L")
        mask_arr = (np.array(mask) > 127).astype(np.int64)  # {0, 1}

        encoded = self.processor(image, mask_arr, return_tensors="pt")
        return {
            "pixel_values": encoded["pixel_values"].squeeze(0),
            "labels": encoded["labels"].squeeze(0),
        }


def main():
    warn_if_not_on_drive()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f">>> Thiet bi su dung: {device}")
    if device.type == "cpu":
        print("    CANH BAO: dang chay tren CPU, se rat cham. Kiem tra lai da cai dung ban")
        print("    PyTorch co ho tro CUDA chua (xem HUONG_DAN_CAI_DAT_GPU.md).")
    else:
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"    GPU: {torch.cuda.get_device_name(0)} ({vram_gb:.1f} GB VRAM)")
        if vram_gb < 6:
            print(f"    LUU Y: VRAM thap ({vram_gb:.1f}GB) -- neu gap loi 'CUDA out of")
            print(f"    memory', giam them BATCH_SIZE xuong 1 hoac giam IMG_SIZE trong")
            print(f"    script 02_prepare_isic_dataset.py (vd 512 -> 384) roi xu ly lai du lieu.")

    processor = SegformerImageProcessor(do_reduce_labels=False)
    train_ds = LesionSegDataset(DATA_DIR / "train", processor)
    val_ds = LesionSegDataset(DATA_DIR / "val", processor)
    print(f">>> Train: {len(train_ds)} anh | Val: {len(val_ds)} anh")

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    model = SegformerForSemanticSegmentation.from_pretrained(
        MODEL_NAME,
        num_labels=NUM_LABELS,
        ignore_mismatched_sizes=True,
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)

    best_val_loss = float("inf")
    OUTPUT_DIR.mkdir(exist_ok=True)
    log_path = OUTPUT_DIR / "training_log.csv"
    # Xoa log cu neu co (tranh lap dong header/du lieu tu lan chay do dang truoc)
    log_path.write_text("epoch,train_loss,val_loss\n", encoding="utf-8")

    for epoch in range(1, NUM_EPOCHS + 1):
        model.train()
        train_loss = 0.0
        optimizer.zero_grad()
        for step, batch in enumerate(tqdm(train_loader, desc=f"Epoch {epoch}/{NUM_EPOCHS} [train]")):
            pixel_values = batch["pixel_values"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(pixel_values=pixel_values, labels=labels)
            loss = outputs.loss / GRADIENT_ACCUMULATION_STEPS

            loss.backward()
            if (step + 1) % GRADIENT_ACCUMULATION_STEPS == 0:
                optimizer.step()
                optimizer.zero_grad()
            train_loss += loss.item() * GRADIENT_ACCUMULATION_STEPS

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in tqdm(val_loader, desc=f"Epoch {epoch}/{NUM_EPOCHS} [val]"):
                pixel_values = batch["pixel_values"].to(device)
                labels = batch["labels"].to(device)
                outputs = model(pixel_values=pixel_values, labels=labels)
                val_loss += outputs.loss.item()

        avg_train = train_loss / len(train_loader)
        avg_val = val_loss / len(val_loader)
        print(f"[Epoch {epoch}] train_loss={avg_train:.4f}  val_loss={avg_val:.4f}")

        # Luu log ra file de dua vao bao cao (bieu do Log Loss giong Figure 8 trong bai bao tham khao)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{epoch},{avg_train:.6f},{avg_val:.6f}\n")

        if avg_val < best_val_loss:
            best_val_loss = avg_val
            model.save_pretrained(OUTPUT_DIR / "best_model")
            processor.save_pretrained(OUTPUT_DIR / "best_model")
            print(f"  -> Luu checkpoint tot nhat (val_loss={avg_val:.4f}) tai {OUTPUT_DIR / 'best_model'}")

    print(f"\nHOAN TAT huan luyen. Checkpoint tot nhat: {OUTPUT_DIR / 'best_model'}")
    print(f"Log huan luyen day du: {OUTPUT_DIR / 'training_log.csv'} (dung ve bieu do Chuong 4)")


if __name__ == "__main__":
    main()
