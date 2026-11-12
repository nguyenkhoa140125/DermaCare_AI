"""
Script: 07_stage3_masi.py
Muc dich: GIAI DOAN 3 cua pipeline Huong 1 -- tinh chi so MASI (Melasma Area
and Severity Index) tu ket qua phan vung (mask) cua Giai doan 2, cho tung
vung giai phau da duoc khoanh vung o Giai doan 1.

CONG THUC GOC (Kimbrough-Green et al., 1994) -- CHI danh gia 4 vung: Tran,
Ma phai, Ma trai, Cam (KHONG bao gom Mui -- day la quy uoc chuan trong y
van, khong phai thieu sot cua pipeline):

    MASI = 0.3*A(f)*[D(f)+H(f)] + 0.3*A(rm)*[D(rm)+H(rm)]
         + 0.3*A(lm)*[D(lm)+H(lm)] + 0.1*A(c)*[D(c)+H(c)]

    f = forehead (tran), rm = right malar (ma phai), lm = left malar (ma trai),
    c = chin (cam)

    A (Area, dien tich ton thuong trong vung) thang diem 0-6:
        0=0% | 1=<10% | 2=10-29% | 3=30-49% | 4=50-69% | 5=70-89% | 6=90-100%
    D (Darkness, do dam mau) thang diem 0-4 (0=khong co .. 4=rat dam)
    H (Homogeneity, do dong deu) thang diem 0-4

Ghi chu quan trong (trich dan trong Chuong 4.4 khoa luan): cac nghien cuu
kiem dinh sau nay (Pandya et al., 2011) chi ra thanh phan Homogeneity (H)
kem tin cay/kem lap lai giua cac nguoi danh gia, va de xuat ban RUT GON:

    mMASI = 0.3*A(f)*D(f) + 0.3*A(rm)*D(rm) + 0.3*A(lm)*D(lm) + 0.1*A(c)*D(c)

Script nay tinh CA HAI phien ban, trong do A va D duoc uoc luong TU DONG tu
anh (thay vi bac si danh gia bang mat) -- day la dong gop/thich nghi cua
khoa luan, can neu ro la 'uoc luong tu dong, chua qua kiem dinh lam sang'
trong phan han che.
"""

from pathlib import Path
import numpy as np
import cv2

# Trong so tung vung theo cong thuc goc (KHONG co Mui)
REGION_WEIGHTS = {
    "Tran": 0.3,
    "Ma_phai": 0.3,
    "Ma_trai": 0.3,
    "Cam": 0.1,
}


def area_score(lesion_pct: float) -> int:
    """Quy doi % dien tich ton thuong sang thang diem 0-6 theo chuan MASI."""
    if lesion_pct <= 0:
        return 0
    elif lesion_pct < 10:
        return 1
    elif lesion_pct < 30:
        return 2
    elif lesion_pct < 50:
        return 3
    elif lesion_pct < 70:
        return 4
    elif lesion_pct < 90:
        return 5
    else:
        return 6


def darkness_score(lesion_pixels: np.ndarray, normal_pixels: np.ndarray) -> float:
    """Uoc luong do dam mau (0-4) bang cach so sanh do sang kenh L* (CIELAB)
    giua vung ton thuong va vung da binh thuong lan can trong cung ROI.
    Chenh lech L* cang lon (vung ton thuong toi hon) -> diem cang cao.
    """
    if len(lesion_pixels) == 0 or len(normal_pixels) == 0:
        return 0.0

    l_lesion = float(np.mean(lesion_pixels))
    l_normal = float(np.mean(normal_pixels))
    diff = max(0.0, l_normal - l_lesion)  # vung nam toi hon da thuong

    # Quy doi tuyen tinh: chenh lech L* tu 0->40 tuong ung diem 0->4
    # (Nguong 40 la uoc luong ban dau, NEN hieu chinh lai bang doi chieu
    # voi danh gia cua bac si da lieu tren mot tap mau nho neu co dieu kien.)
    score = min(4.0, (diff / 40.0) * 4.0)
    return float(round(score, 2))


def analyze_region(image_bgr: np.ndarray, mask: np.ndarray) -> dict:
    """image_bgr, mask: cung kich thuoc, mask la nhi phan {0,1} (1=vung ton thuong).
    Tra ve dict gom % dien tich, diem A, diem D."""
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    l_channel = lab[:, :, 0].astype(np.float32) * (100.0 / 255.0)  # quy doi ve thang L* 0-100

    total_pixels = mask.size
    lesion_pixels_mask = mask == 1
    normal_pixels_mask = mask == 0

    lesion_pct = 100.0 * float(lesion_pixels_mask.sum()) / total_pixels if total_pixels > 0 else 0.0

    a_score = area_score(lesion_pct)
    d_score = darkness_score(l_channel[lesion_pixels_mask], l_channel[normal_pixels_mask])

    return {"area_pct": float(round(lesion_pct, 2)), "A": int(a_score), "D": float(d_score)}


def compute_masi(region_results: dict) -> dict:
    """region_results: {"Tran": {"A":.., "D":..}, "Ma_phai": {...}, ...}
    (Homogeneity H duoc mac dinh = 0 do khong the tu dong uoc luong tin cay
    -- day la ly do chinh ban MASI day du can nguoi danh gia thu cong bo sung,
    trong khi mMASI khong phu thuoc H nen phu hop hon cho tu dong hoa)."""
    masi_total = 0.0
    mmasi_total = 0.0
    details = {}

    for region, weight in REGION_WEIGHTS.items():
        if region not in region_results:
            continue
        A = region_results[region]["A"]
        D = region_results[region]["D"]
        H = region_results[region].get("H", 0)  # mac dinh 0 (xem ghi chu tren)

        masi_contrib = weight * A * (D + H)
        mmasi_contrib = weight * A * D

        masi_total += masi_contrib
        mmasi_total += mmasi_contrib
        details[region] = {"A": A, "D": D, "H": H,
                            "masi_contrib": round(masi_contrib, 3),
                            "mmasi_contrib": round(mmasi_contrib, 3)}

    return {
        "MASI": round(masi_total, 3),        # thang diem ly thuyet 0-48
        "mMASI": round(mmasi_total, 3),       # thang diem ly thuyet 0-24
        "per_region": details,
    }


if __name__ == "__main__":
    # Vi du minh hoa voi du lieu gia lap -- trong pipeline that, region_results
    # se duoc dien tu ket qua thuc te cua analyze_region() cho tung ROI da
    # duoc cat o Giai doan 1 va phan vung o Giai doan 2.
    demo_regions = {
        "Tran": {"A": 3, "D": 2.1},
        "Ma_phai": {"A": 4, "D": 2.8},
        "Ma_trai": {"A": 4, "D": 2.6},
        "Cam": {"A": 1, "D": 1.0},
    }
    result = compute_masi(demo_regions)
    print("Vi du ket qua tinh MASI/mMASI (du lieu minh hoa):")
    print(result)
