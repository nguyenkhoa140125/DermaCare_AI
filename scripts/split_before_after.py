"""
Script ho tro: split_before_after.py
Muc dich: Cat doi (trai/phai) cac anh ghep "truoc/sau dieu tri" thanh 2 anh
rieng biet, dung khi anh lay tu bai bao co dang 1 anh ghep 2 khuon mat canh
nhau (composite before/after).

CACH DUNG:
    python split_before_after.py duong_dan_anh_ghep.jpg [anh2.jpg ...]

Ket qua: voi moi anh "ten.jpg", tao ra "ten_trai.jpg" va "ten_phai.jpg"
trong cung thu muc.

LUU Y: Script gia dinh anh ghep chia doi THEO CHIEU DOC (trai/phai), la
kieu pho bien nhat cho anh truoc/sau lam sang. Neu anh cua ban ghep theo
kieu khac (tren/duoi, hoac co khoang trang o giua), hay xem truoc anh va
tu cat bang trinh chinh sua anh thong thuong (Paint, Photos...) thay vi
dung script nay.
"""

import sys
from pathlib import Path
import cv2


def split_image(image_path: str):
    image = cv2.imread(image_path)
    if image is None:
        print(f"[!] Khong doc duoc: {image_path}")
        return

    h, w = image.shape[:2]
    mid = w // 2

    left = image[:, :mid]
    right = image[:, mid:]

    stem = Path(image_path).stem
    parent = Path(image_path).parent
    ext = Path(image_path).suffix

    left_path = parent / f"{stem}_trai{ext}"
    right_path = parent / f"{stem}_phai{ext}"

    cv2.imwrite(str(left_path), left)
    cv2.imwrite(str(right_path), right)
    print(f"[OK] {image_path} -> {left_path.name} + {right_path.name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cach dung: python split_before_after.py anh1.jpg [anh2.jpg ...]")
        sys.exit(1)

    for path in sys.argv[1:]:
        split_image(path)

    print("\nHOAN TAT. Kiem tra lai bang mat cac anh _trai/_phai vua tao --")
    print("neu ty le trai/phai khong dung 50/50 (mat bi cat lech), xoa anh loi")
    print("va tu cat tay lai bang trinh chinh sua anh thong thuong.")
