"""
Script ho tro: filter_face_candidates.py
Muc dich: Loc TRUOC cac anh co kha nang cao la anh khuon mat (dua vao caption/
mo ta di kem tung anh trong metadata cua MultiCaRe), giam cong suc phai tu
xem bang mat tung anh khong lien quan (soi da, mo hoc, bieu do...).

CACH DUNG:
    python filter_face_candidates.py

Ket qua: copy cac anh co caption chua tu khoa lien quan khuon mat vao thu muc
anh_mau_uu_tien/, ban chi can uu tien xem/gan nhan cac anh trong thu muc nay
truoc, thay vi lan luot ca 74 anh.

LUU Y: day la buoc LOC SO BO, khong hoan hao -- van co the sot anh mat khong
co tu khoa ro rang trong caption, hoac lan anh khong phai mat nhung caption
co nhac tu khoa trung. Ban VAN CAN tu xem lai bang mat (nhan 's'/'x' khi
annotate) de xac nhan cuoi cung.
"""

import json
import os
import shutil
from pathlib import Path

DATASET_DIR = Path("medical_datasets/melasma_dataset")
IMAGE_DIR = DATASET_DIR / "images"
OUTPUT_DIR = Path("anh_mau_uu_tien")

# Tu khoa goi y day la anh khuon mat (khong phan biet hoa/thuong)
FACE_KEYWORDS = [
    "face", "facial", "cheek", "forehead", "chin", "frontal view",
    "front view", "patient's face", "malar", "perioral",
]


def find_metadata_file():
    """Tu dong do tim file metadata chua caption -- ten file co the khac nhau
    tuy phien ban thu vien multiversity. UU TIEN image_metadata.json (chua
    caption cap-do-anh), BO QUA article_metadata.json (chi la metadata cap
    bai bao -- pmcid/license/keywords, khong co caption tung anh)."""
    priority_names = ["image_metadata.json", "captions_and_labels.json",
                       "captions_and_labels.csv"]
    candidates = []
    for name in priority_names:
        p = DATASET_DIR / name
        if p.exists():
            candidates.append(p)
    if not candidates:
        candidates = [p for p in DATASET_DIR.glob("*.json")
                      if "article" not in p.name.lower()]

    print(f">>> Uu tien doc file metadata cap-anh:")
    for c in candidates:
        print(f"    - {c.name}")
    return candidates


def load_json_or_jsonl(path):
    """Doc file co the o dinh dang JSON thuong (1 object/array lon) HOAC
    JSON Lines (moi dong 1 object JSON rieng biet, hay dung cho dataset
    lon vi khong can nap toan bo vao bo nho cung luc)."""
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Thu doc theo dinh dang JSON Lines (JSONL/NDJSON)
        records = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # bo qua dong loi, khong dung ca chuong trinh
        return records


def load_captions_from_json(path):
    """Thu doc file JSON/JSONL metadata, tra ve dict {ten_file_anh: caption_text}.
    Ho tro vai cau truc pho bien -- neu khong khop, in ra cau truc that
    de nguoi dung/Claude dieu chinh lai."""
    data = load_json_or_jsonl(path)

    captions = {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                # Thu cac ten truong pho bien cho ten file va caption
                fname = item.get("file_name") or item.get("image_id") or \
                        item.get("filename") or item.get("file")
                caption = item.get("caption") or item.get("text") or \
                          item.get("description") or ""
                if fname:
                    captions[str(fname)] = str(caption)
    elif isinstance(data, dict):
        # Truong hop dict {ten_file: caption} truc tiep, hoac dict long nhau
        for k, v in data.items():
            if isinstance(v, str):
                captions[k] = v
            elif isinstance(v, dict):
                caption = v.get("caption") or v.get("text") or v.get("description") or ""
                captions[k] = str(caption)

    return captions


def main():
    metadata_files = find_metadata_file()
    json_files = [f for f in metadata_files if f.suffix == ".json"]

    if not json_files:
        print("\n[!] Khong tim thay file JSON metadata nao chua caption.")
        print("    Kiem tra lai danh sach file o tren, gui cho Claude neu can ho tro.")
        return

    all_captions = {}
    for jf in json_files:
        try:
            caps = load_captions_from_json(jf)
            print(f">>> Doc duoc {len(caps)} caption tu {jf.name}")
            all_captions.update(caps)
        except Exception as e:
            print(f"    Loi doc {jf.name}: {e}")

    if not all_captions:
        print("\n[!] Khong trich xuat duoc caption nao. Cau truc file metadata")
        print("    co the khac gia dinh cua script. In thu 1 phan tu dau tien de kiem tra:")
        for jf in json_files:
            data = load_json_or_jsonl(jf)
            sample = data[0] if isinstance(data, list) else next(iter(data.items()))
            print(f"    {jf.name} -> mau du lieu dau tien: {sample}")
        return

    # Tim tat ca file anh thuc te tren dia
    all_image_files = {}
    for root, dirs, files in os.walk(IMAGE_DIR):
        for f in files:
            all_image_files[f] = os.path.join(root, f)

    OUTPUT_DIR.mkdir(exist_ok=True)
    matched = 0
    for fname, caption in all_captions.items():
        caption_lower = caption.lower()
        if any(kw in caption_lower for kw in FACE_KEYWORDS):
            # Tim file anh tuong ung (co the ten file trong metadata khac
            # doi chut so voi ten file thuc te, vd co/khong co duoi file)
            base_name = os.path.basename(fname)
            if base_name in all_image_files:
                shutil.copy(all_image_files[base_name], OUTPUT_DIR / base_name)
                matched += 1

    print(f"\nHOAN TAT. Da loc va copy {matched} anh co kha nang cao la anh mat")
    print(f"vao thu muc {OUTPUT_DIR}/ (uu tien xem/gan nhan cac anh nay truoc).")
    print(f"Tong so caption da quet: {len(all_captions)} | Tong so anh tren dia: {len(all_image_files)}")


if __name__ == "__main__":
    main()
