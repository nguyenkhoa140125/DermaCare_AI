"""
Script: 02_prepare_isic_dataset.py
Muc dich: Tien xu ly bo du lieu ISIC 2018 Task 1 (Lesion Boundary Segmentation)
de chuan bi huan luyen SegFormer o Giai doan 2.

YEU CAU TRUOC KHI CHAY:
1. Tai thu cong tu ISIC/Kaggle, dat cac file .zip vao isic2018_raw/ -- CHAP
   NHAN BAT KY TO HOP nao trong: Training/Validation/Test Input + GroundTruth
   (khong bat buoc phai co du ca 3 tap -- script se TU DONG GOM TAT CA cap
   Input+GroundTruth co san lai voi nhau, roi TU CHIA train/val theo ty le
   rieng, thay vi bat buoc theo dung quy uoc split cua ISIC challenge goc).
2. Script se TU DONG giai nen moi file .zip tim thay trong isic2018_raw/.

GHI CHU CHO KHOA LUAN: neu ban dung ca 3 tap con (Training/Validation/Test)
gop lai va tu chia train/val rieng, can neu ro trong Chuong 4.5 rang cach
chia nay KHAC voi quy uoc split chinh thuc cua ISIC 2018 Challenge (chi anh
huong ve mat "chuan hoa de so sanh voi leaderboard challenge", KHONG anh
huong tinh hop le cua so lieu huan luyen/danh gia rieng cua khoa luan).

Script se: resize anh + mask ve cung kich thuoc, chuan hoa mask ve {0,255},
chia train/val (85/15), luu vao thu muc processed_isic/ san sang cho buoc
huan luyen.
"""

import os
import shutil
import random
import zipfile
from datetime import datetime
from pathlib import Path
import numpy as np
from PIL import Image
from tqdm import tqdm

RAW_DIR = Path("isic2018_raw")

OUT_DIR = Path("processed_isic")
IMG_SIZE = 512
VAL_RATIO = 0.15
SEED = 42


def warn_if_not_on_drive():
    """Canh bao neu dang chay trong o dia tam cua Colab (/content/, ngoai
    Google Drive) -- du lieu se bi XOA neu runtime bi ngat/khoi dong lai."""
    cwd = os.getcwd()
    is_colab = os.path.exists("/content")
    if is_colab and "/drive/MyDrive" not in cwd:
        print("=" * 70)
        print("CANH BAO QUAN TRONG: ban dang KHONG chay trong Google Drive!")
        print(f"    Thu muc hien tai: {cwd}")
        print("    -> Chay lai cell 'Ket noi Google Drive' (mount + %cd) truoc.")
        print("=" * 70)
        response = input("Van tiep tuc chay du sao (khong khuyen nghi)? (y/N): ")
        if response.strip().lower() != "y":
            raise SystemExit("Da dung lai. Chay lai cell mount Google Drive truoc.")


def auto_extract_all_zips(root: Path):
    """Tu dong giai nen MOI file .zip tim thay truc tiep trong root (khong
    can biet truoc ten chinh xac cua tung file). LUON giai nen vao 1 thu muc
    con co dinh dat theo ten file zip (root/ten_zip/...) -- BAT KE cau truc
    ben trong zip co san san mot thu muc bao ngoai hay khong (co zip tu tao
    thu muc con trung ten, co zip lai giai nen thang cac file roi vao goc,
    tuy nha cung cap dong goi khac nhau). Cach nay dam bao vi tri sau cung
    luon nhat quan, du dinh dang zip dau vao co the khac nhau."""
    zip_files = list(root.glob("*.zip"))
    if not zip_files:
        return
    print(f">>> Tim thay {len(zip_files)} file .zip, dang giai nen...")
    for zip_path in zip_files:
        target_dir = root / zip_path.stem
        if target_dir.exists() and any(target_dir.iterdir()):
            print(f"    {zip_path.name}: da giai nen truoc do, bo qua.")
            continue
        print(f"    Giai nen {zip_path.name} -> {target_dir.name}/...")
        target_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(target_dir)


def find_dir(root: Path, keywords: list, required_ext: str) -> Path:
    """Tu dong do tim thu muc con co ten khop voi TAT CA tu khoa (khong phan
    biet hoa/thuong) VA thuc su chua file dinh dang required_ext ngay ben
    trong no -- tranh chon nham thu muc cha rong."""
    candidates = [p for p in root.rglob("*") if p.is_dir()]
    matched_with_files = []
    for cand in candidates:
        name_lower = cand.name.lower()
        if all(kw.lower() in name_lower for kw in keywords):
            file_count = len(list(cand.glob(f"*{required_ext}")))
            if file_count > 0:
                matched_with_files.append((cand, file_count))
    if not matched_with_files:
        return None
    matched_with_files.sort(key=lambda x: x[1], reverse=True)
    return matched_with_files[0][0]


def resolve_isic_pairs():
    """Tim TAT CA cap (thu muc anh, thu muc mask) co san cho tung split
    (Training/Validation/Test) -- CHI lay split nao co DU CA HAI (Input va
    GroundTruth), roi tra ve danh sach cac cap tim duoc de gop chung lai."""
    pairs = []
    split_counts = {}
    for split in ["training", "validation", "test"]:
        image_dir = find_dir(RAW_DIR, ["task1", split, "input"], ".jpg")
        mask_dir = find_dir(RAW_DIR, ["task1", split, "groundtruth"], ".png")
        if image_dir and mask_dir:
            n = len(list(image_dir.glob("*.jpg")))
            print(f">>> Tim thay du cap Input+GroundTruth cho tap '{split}': {n} anh")
            pairs.append((image_dir, mask_dir))
            split_counts[split] = n
        else:
            status = []
            if not image_dir:
                status.append("thieu Input")
            if not mask_dir:
                status.append("thieu GroundTruth")
            print(f"    Tap '{split}': {', '.join(status)} -- bo qua tap nay.")
            split_counts[split] = None

    if not pairs:
        print(f"\n>>> KHONG TIM DUOC cap Input+GroundTruth nao hop le. "
              f"Cau truc thuc te trong {RAW_DIR.resolve()}:")
        for p in sorted(RAW_DIR.rglob("*")):
            if p.is_dir():
                print(f"    [DIR]  {p}")
        raise FileNotFoundError(
            "Khong tim thay du lieu ISIC hop le. Xem danh sach thu muc o tren, "
            "gui lai cho Claude de duoc ho tro neu can."
        )
    return pairs, split_counts


def resize_pair(img_path: Path, mask_path: Path, size: int):
    img = Image.open(img_path).convert("RGB").resize((size, size), Image.BILINEAR)
    mask = Image.open(mask_path).convert("L").resize((size, size), Image.NEAREST)
    mask_arr = (np.array(mask) > 127).astype(np.uint8) * 255
    return img, Image.fromarray(mask_arr)


def main():
    warn_if_not_on_drive()

    # Xoa sach OUT_DIR truoc khi xu ly, tranh lan du lieu cu tu lan chay
    # truoc (vd neu isic2018_raw thay doi giua cac lan chay, du lieu cu se
    # khong tu bien mat neu khong xoa thu cong -- day chinh la nguyen nhan
    # gay sai lech so lieu da gap phai truoc do).
    if OUT_DIR.exists():
        print(f">>> Xoa du lieu da xu ly cu tai {OUT_DIR} truoc khi lam lai tu dau...")
        shutil.rmtree(OUT_DIR)

    auto_extract_all_zips(RAW_DIR)
    pairs, split_counts = resolve_isic_pairs()

    # Gop TOAN BO cap (anh, mask) tu moi split tim duoc lai thanh 1 danh sach
    # duy nhat, roi TU CHIA train/val theo ty le rieng (xem ghi chu dau file).
    all_image_mask_pairs = []
    for image_dir, mask_dir in pairs:
        for img_path in sorted(image_dir.glob("*.jpg")):
            mask_path = mask_dir / f"{img_path.stem}_segmentation.png"
            if mask_path.exists():
                all_image_mask_pairs.append((img_path, mask_path))

    print(f"\n>>> TONG CONG gom duoc {len(all_image_mask_pairs)} cap anh+mask hop le "
          f"tu {len(pairs)} tap con.")
    assert len(all_image_mask_pairs) > 0, "Khong gom duoc cap anh+mask nao hop le."

    random.seed(SEED)
    random.shuffle(all_image_mask_pairs)
    n_val = int(len(all_image_mask_pairs) * VAL_RATIO)
    val_pairs = set(p[0] for p in all_image_mask_pairs[:n_val])
    n_train = len(all_image_mask_pairs) - n_val

    for split in ["train", "val"]:
        (OUT_DIR / split / "images").mkdir(parents=True, exist_ok=True)
        (OUT_DIR / split / "masks").mkdir(parents=True, exist_ok=True)

    corrupted_files = []
    processed_count = 0
    for img_path, mask_path in tqdm(all_image_mask_pairs, desc="Xu ly anh"):
        stem = img_path.stem
        split = "val" if img_path in val_pairs else "train"
        try:
            img, mask = resize_pair(img_path, mask_path, IMG_SIZE)
        except Exception as e:
            corrupted_files.append((str(img_path), str(e)))
            continue
        img.save(OUT_DIR / split / "images" / f"{stem}.jpg", quality=95)
        mask.save(OUT_DIR / split / "masks" / f"{stem}.png")
        processed_count += 1

    if corrupted_files:
        print(f"\n[!] Bo qua {len(corrupted_files)} anh loi/hong (khong doc duoc):")
        for path, err in corrupted_files[:10]:
            print(f"    - {path} ({err})")
        if len(corrupted_files) > 10:
            print(f"    ... va {len(corrupted_files) - 10} anh loi khac")
        # Cap nhat lai n_train/n_val cho dung so anh THAT SU da xu ly thanh cong
        n_val = sum(1 for p, _ in all_image_mask_pairs
                    if p in val_pairs and p not in [Path(c[0]) for c in corrupted_files])
        n_train = processed_count - n_val

    print(f"\nHOAN TAT. Train: {n_train} anh | Val: {n_val} anh")
    print(f"   Du lieu da xu ly luu tai: {OUT_DIR.resolve()}")

    # Ghi "bien ban du lieu" -- luu lai chinh xac da dung nhung tap con nao,
    # bao nhieu anh, luc nao -- de tranh tai dien tinh huong khong biet ro
    # chinh xac da huan luyen tren bao nhieu anh (da tung gap phai truoc do).
    manifest_path = Path("DATASET_MANIFEST.txt")
    manifest_lines = [
        f"Bien ban du lieu ISIC -- tao luc: {datetime.now().isoformat(timespec='seconds')}",
        f"Thu muc nguon: {RAW_DIR.resolve()}",
        "",
        "Cac tap con da tim thay va su dung:",
    ]
    for split, n in split_counts.items():
        status = f"{n} anh" if n is not None else "KHONG CO (bi bo qua)"
        manifest_lines.append(f"  - {split}: {status}")
    manifest_lines += [
        "",
        f"TONG SO CAP ANH+MASK TIM DUOC (truoc khi loc anh loi): {len(all_image_mask_pairs)}",
        f"So anh loi/hong bi bo qua khi xu ly: {len(corrupted_files)}",
        f"TONG SO ANH THUC TE DA XU LY THANH CONG: {processed_count}",
        f"Chia train/val (ty le {1-VAL_RATIO:.0%}/{VAL_RATIO:.0%}, random seed={SEED},",
        f"tinh tren so anh xu ly thanh cong, khong tinh anh loi):",
        f"  - Train: {n_train} anh",
        f"  - Val:   {n_val} anh",
        "",
        "LUU Y: file nay duoc tao lai MOI LAN chay script 02 -- neu chay lai",
        "voi du lieu trong isic2018_raw/ khac di, so lieu o day se thay doi theo.",
        "Luon doi chieu file nay voi so lieu ghi trong bao cao truoc khi nop.",
    ]
    if corrupted_files:
        manifest_lines.append("\nDanh sach anh loi/hong (khong tinh vao tong so):")
        for path, err in corrupted_files:
            manifest_lines.append(f"  - {path} ({err})")
    manifest_path.write_text("\n".join(manifest_lines), encoding="utf-8")
    print(f"   Da ghi bien ban du lieu tai: {manifest_path.resolve()}")


if __name__ == "__main__":
    main()
