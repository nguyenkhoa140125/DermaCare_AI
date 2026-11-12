"""
Script: 01_fetch_melasma_images.py
Muc dich: Loc va tai cac anh lien quan den benh Nam (Melasma) tu bo du lieu
MultiCaRe (130,000+ anh y khoa trich xuat tu cac bai bao case report mo
tren PubMed Central).

LICH SU LOI (giu lai de tham khao khi viet phan han che trong khoa luan):
Thu vien 'multiversity' mac dinh tai toan bo dataset qua endpoint gop file
cua Zenodo (/files-archive). Endpoint nay HIEN DANG LOI/BI HAN CHE phia
Zenodo (tra ve HTTP 400) cho du dung version_id nao -- day la loi tu dich vu
Zenodo, khong phai do cau hinh. GIAI PHAP: tai TUNG FILE LE qua API chuan
cua Zenodo (van hoat dong binh thuong), dat dung vao thu muc ma thu vien
mong doi, de no bo qua buoc tu tai bi loi va dung thang du lieu co san.

LUU Y:
- Chi chay duoc tren may/Colab co ket noi Internet binh thuong.
- Can dung luong trong toi thieu ~5GB (file nen + sau khi giai nen).
- Dataset MultiCaRe co giay phep tong the CC BY-NC-SA (phi thuong mai);
  TUNG anh rieng le co the co giay phep khac (CC-BY, CC-BY-NC, CC0) --
  kiem tra metadata truoc khi dua anh vao khoa luan.

Cach chay:
    pip install multiversity
    python 01_fetch_melasma_images.py
"""

import os
import shutil
import requests
from tqdm import tqdm
from multiversity.multicare_dataset import MedicalDatasetCreator


def warn_if_not_on_drive():
    """Canh bao neu dang chay trong o dia tam cua Colab (/content/, ngoai
    Google Drive) -- du lieu tai ve se BI XOA neu runtime bi ngat/khoi dong
    lai. Day la nguyen nhan pho bien nhat gay mat du lieu da tai."""
    cwd = os.getcwd()
    is_colab = os.path.exists("/content")
    if is_colab and "/drive/MyDrive" not in cwd:
        print("=" * 70)
        print("CANH BAO QUAN TRONG: ban dang KHONG chay trong Google Drive!")
        print(f"    Thu muc hien tai: {cwd}")
        print("    Du lieu tai ve se bi XOA neu Colab runtime bi ngat/restart.")
        print("    -> Chay lai cell 'Ket noi Google Drive' (mount + %cd) o dau")
        print("       notebook TRUOC KHI tiep tuc, de dam bao dang o dung")
        print("       duong dan /content/drive/MyDrive/DermaCare_Pipeline/")
        print("=" * 70)
        response = input("Van tiep tuc chay du sao (khong khuyen nghi)? (y/N): ")
        if response.strip().lower() != "y":
            raise SystemExit("Da dung lai. Chay lai cell mount Google Drive truoc.")


DATA_DIR = "medical_datasets"
DATASET_NAME = "melasma_dataset"
WHOLE_DATASET_PATH = f"{DATA_DIR}/whole_multicare_dataset"

# Ban ghi Zenodo da xac minh con hoat dong (Version 2.1, 2.9GB). Neu ban ghi
# nay sau nay cung ngung hoat dong, tim ban ghi moi hon tai:
# https://github.com/mauro-nievoff/MultiCaRe_Dataset (muc "Useful Resources")
VERSION_ID = "14994046"


def download_files_individually(version_id: str, dest_dir: str):
    """Tai TUNG FILE trong ban ghi Zenodo (bo qua endpoint /files-archive bi loi),
    roi tu giai nen cac file .zip -- lam thay cho buoc _download_dataset() bi
    loi ben trong thu vien multiversity."""
    os.makedirs(dest_dir, exist_ok=True)

    print(f">>> Lay danh sach file tu Zenodo record {version_id}...")
    resp = requests.get(f"https://zenodo.org/api/records/{version_id}")
    resp.raise_for_status()
    record = resp.json()
    files = record.get("files", [])
    if not files:
        raise RuntimeError(
            f"Khong lay duoc danh sach file tu record {version_id}. "
            f"Kiem tra lai ID hoac thu ban ghi khac."
        )
    print(f"    Tim thay {len(files)} file: {[f['key'] for f in files]}")

    downloaded_zip_paths = []
    for f in files:
        filename = f["key"]
        # Zenodo co 2 kieu cau truc link tuy thoi diem ban ghi duoc tao:
        # kieu cu dung 'links.self' de tai truc tiep, kieu moi can them
        # 'links.content'. Uu tien 'content' neu co, fallback ve 'self'.
        links = f.get("links", {})
        url = links.get("content") or links.get("self")
        size_mb = f.get("size", 0) / 1e6
        dest_path = os.path.join(dest_dir, filename)

        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1024:
            print(f"    Da co san {filename}, bo qua tai lai.")
        else:
            print(f"    Dang tai {filename} ({size_mb:.1f} MB)...")
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                # Kiem tra content-type truoc khi luu -- neu Zenodo tra ve
                # trang loi (html/json) thay vi file that, dung lai ngay
                # thay vi luu nham nhu loi da gap truoc do.
                content_type = r.headers.get("content-type", "")
                if "html" in content_type or "json" in content_type:
                    raise RuntimeError(
                        f"URL cho {filename} tra ve noi dung khong hop le "
                        f"(content-type={content_type}). Zenodo co the dang gap "
                        f"su co. Thu lai sau vai phut, hoac bao loi nay lai cho Claude."
                    )
                total = int(r.headers.get("content-length", 0))
                with open(dest_path, "wb") as out, tqdm(
                    total=total, unit="B", unit_scale=True, desc=filename
                ) as pbar:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        out.write(chunk)
                        pbar.update(len(chunk))

        if filename.lower().endswith(".zip"):
            downloaded_zip_paths.append(dest_path)

    print(">>> Giai nen cac file .zip...")
    for zip_path in downloaded_zip_paths:
        print(f"    Giai nen {zip_path}...")
        shutil.unpack_archive(zip_path, dest_dir)
        os.remove(zip_path)

    print(">>> Hoan tat tai va giai nen du lieu goc MultiCaRe.")


def main():
    warn_if_not_on_drive()

    # Buoc 1: neu thu muc du lieu goc chua co gi, tu tai thu cong (bo qua
    # endpoint bi loi cua thu vien). Neu da co roi (vd chay lai lan 2), bo qua.
    if not os.path.exists(WHOLE_DATASET_PATH) or not os.listdir(WHOLE_DATASET_PATH):
        download_files_individually(VERSION_ID, WHOLE_DATASET_PATH)
    else:
        print(f">>> Du lieu goc da co san tai {WHOLE_DATASET_PATH}, bo qua buoc tai.")

    # Buoc 2: khoi tao MedicalDatasetCreator -- vi thu muc da co san du lieu,
    # thu vien se TU DONG BO QUA buoc tu tai (_download_dataset) bi loi, va
    # di thang vao doc file de xu ly.
    print(">>> Buoc 2: Khoi tao MedicalDatasetCreator (doc du lieu da co san)...")
    mdc = MedicalDatasetCreator(directory=DATA_DIR, version_id=VERSION_ID)

    print(">>> Buoc 3: Dinh nghia bo loc tu khoa lien quan Melasma...")
    filters = [
        {
            "field": "case_strings",
            "string_list": ["melasma", "chloasma", "hyperpigmentation", "hypermelanosis"],
            "operator": "any",
        },
        {
            "field": "caption",
            "string_list": ["melasma", "chloasma", "hyperpigmentation", "facial pigmentation"],
            "operator": "any",
        },
    ]

    print(">>> Buoc 4: Tao subset 'melasma_dataset' (loai 'multimodal': anh + case text + caption)...")
    output_path = os.path.join(DATA_DIR, DATASET_NAME)
    if os.path.exists(output_path) and os.listdir(output_path):
        print(f"    Da co san dataset '{DATASET_NAME}' tai {output_path} (tu lan chay truoc).")
        print("    Bo qua buoc tao lai -- neu muon tao moi hoan toan, xoa thu muc nay roi chay lai.")
    else:
        mdc.create_dataset(
            dataset_name=DATASET_NAME,
            filter_list=filters,
            dataset_type="multimodal",
        )
    print(f"\nHOAN TAT. Du lieu da luu tai: {output_path}")
    print("   QUAN TRONG VE GIAY PHEP: dataset MultiCaRe co giay phep tong the")
    print("   CC BY-NC-SA (phi thuong mai), nhung TUNG anh rieng le co the co")
    print("   giay phep khac nhau (CC-BY, CC-BY-NC, CC-BY-NC-SA, hoac CC0).")
    print("   Kiem tra cot 'license' trong file metadata di kem TUNG anh truoc")
    print("   khi dua vao khoa luan, va trich dan dung nguon bai bao goc.")


if __name__ == "__main__":
    main()
