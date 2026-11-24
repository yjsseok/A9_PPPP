#!/usr/bin/env python3
"""OpenFOAM 결과(U, k, p) → vworld_cfd_demo.html 용 JSON 변환기.

하는 일
  1. OpenFOAM 케이스를 읽는다 (기본: 마지막 시간 폴더 = 정상 해석의 수렴 결과).
  2. 지정한 높이들(--z)에 nx × ny 규칙 격자를 깔고, 비정렬 격자의 값을 보간해 옮긴다.
     건물 내부처럼 격자가 없는 점은 null 이 된다.
  3. CFD 로컬 좌표(m)를 경위도로 바꾸고, 속도 벡터도 동/북 성분으로 회전한다.
  4. (선택) 풍동 센서 CSV 를 붙여 JSON 으로 저장한다.

전제
  - 지면이 평평한 격자 (지면의 로컬 z = --ground-z, 기본은 격자 최저 z).
  - 도메인 크기 수 km 이내 (경위도 변환에 평면 근사를 사용).
  - 병렬 해석이면 먼저 reconstructPar 로 합친다.

필요 패키지:  pip install pyvista

예시
  python openfoam_to_json.py ./myCase --origin-lon 127.0276 --origin-lat 37.4979 \\
      --x-bearing 90 --z 1.5 5 10 15 20 25 30 --nx 161 --ny 161 \\
      --uref 5 --zref 10 --sensors windtunnel.csv --out cfd_field.json
"""
import argparse
import csv
import json
import math
import os
import sys

import numpy as np


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case", help="OpenFOAM 케이스 폴더 (또는 .foam 파일)")
    ap.add_argument("--time", type=float, default=None, help="읽을 시간(폴더 이름). 생략하면 마지막 시간")
    ap.add_argument("--origin-lon", type=float, required=True, help="CFD 로컬 원점 (0,0) 의 경도")
    ap.add_argument("--origin-lat", type=float, required=True, help="CFD 로컬 원점 (0,0) 의 위도")
    ap.add_argument("--x-bearing", type=float, default=90.0,
                    help="CFD +x 축이 가리키는 방위각(도, 북=0 시계방향). 기본 90 = x 가 동쪽, y 가 북쪽")
    ap.add_argument("--bounds", type=float, nargs=4, metavar=("XMIN", "XMAX", "YMIN", "YMAX"), default=None,
                    help="내보낼 로컬 좌표 범위(m). 생략하면 격자 전체")
    ap.add_argument("--nx", type=int, default=121, help="서→동 격자 수")
    ap.add_argument("--ny", type=int, default=121, help="남→북 격자 수")
    ap.add_argument("--z", type=float, nargs="+", default=[1.5, 5, 10, 15, 20, 25, 30], help="지상 높이 목록(m)")
    ap.add_argument("--ground-z", type=float, default=None, help="지면의 로컬 z (m). 생략하면 격자 최저 z")
    ap.add_argument("--uref", type=float, default=None, help="기준 풍속 U_ref (m/s)")
    ap.add_argument("--zref", type=float, default=10.0, help="기준 높이 z_ref (m)")
    ap.add_argument("--pref", type=float, default=0.0, help="기준 압력 p_ref (p 와 같은 단위)")
    ap.add_argument("--fields", nargs=3, metavar=("U", "K", "P"), default=["U", "k", "p"],
                    help="필드 이름. 시간 평균을 쓰려면 예: UMean kMean pMean")
    ap.add_argument("--sensors", default=None,
                    help="풍동 센서 CSV. 열: name,x,y,z,measured (로컬 실척 m, z=지상 높이) 또는 name,lon,lat,z,measured")
    ap.add_argument("--out", default="cfd_field.json", help="출력 JSON 경로")
    return ap.parse_args()


def read_case(case, time_value, want):
    import pyvista as pv

    foam = case
    if os.path.isdir(case):
        foam = os.path.join(case, "case.foam")
        if not os.path.exists(foam):          # 리더가 케이스 위치를 알도록 하는 빈 표식 파일
            open(foam, "w").close()
            print(f"[정보] 표식 파일 생성: {foam}")
    reader = pv.POpenFOAMReader(foam)
    times = list(reader.time_values)
    if not times:
        sys.exit("시간 폴더를 찾지 못했습니다.")
    t = times[-1] if time_value is None else min(times, key=lambda v: abs(v - time_value))
    reader.set_active_time_value(t)
    reader.cell_to_point_creation = True      # 셀 중심 값 → 격자점 값 (보간용)
    print(f"[정보] 시간 {t:g} 읽는 중 (전체 {len(times)}개: {times[0]:g} ~ {times[-1]:g})")
    multi = reader.read()
    mesh = multi["internalMesh"]
    have = [n for n in want if n in mesh.point_data]
    if want[0] not in have:
        sys.exit(f"속도 필드 '{want[0]}' 가 없습니다. 있는 필드: {list(mesh.point_data.keys())}")
    return mesh, t, have


def main():
    a = parse_args()
    import pyvista as pv

    fU, fK, fP = a.fields
    mesh, t, have = read_case(a.case, a.time, [fU, fK, fP])
    xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds
    if a.bounds:
        xmin, xmax, ymin, ymax = a.bounds
    ground = zmin if a.ground_z is None else a.ground_z
    print(f"[정보] 로컬 범위 x {xmin:g}~{xmax:g}, y {ymin:g}~{ymax:g}, 지면 z {ground:g}, 격자 상단 z {zmax:g}")
    zs = sorted(a.z)
    if ground + zs[-1] > zmax:
        print(f"[경고] 높이 {zs[-1]} m 는 격자 상단보다 높습니다. 해당 층은 null 이 됩니다.")

    # 로컬 (x, y) ↔ 동/북 (E, N).  +x 의 방위각 θ:  E = x sinθ − y cosθ,  N = x cosθ + y sinθ
    th = math.radians(a.x_bearing)
    s, c = math.sin(th), math.cos(th)
    corners = [(x, y) for x in (xmin, xmax) for y in (ymin, ymax)]
    E = [x * s - y * c for x, y in corners]
    N = [x * c + y * s for x, y in corners]
    e0, e1, n0, n1 = min(E), max(E), min(N), max(N)       # 회전된 도메인을 감싸는 동서남북 사각형

    m_lat = 111320.0
    m_lon = 111320.0 * math.cos(math.radians(a.origin_lat))
    out = {
        "west": a.origin_lon + e0 / m_lon, "east": a.origin_lon + e1 / m_lon,
        "south": a.origin_lat + n0 / m_lat, "north": a.origin_lat + n1 / m_lat,
        "nx": a.nx, "ny": a.ny, "nz": len(zs), "z": zs, "z_ref": a.zref,
        "source": {"solver": "OpenFOAM", "time": t, "fields": have},
    }

    ee, nn = np.meshgrid(np.linspace(e0, e1, a.nx), np.linspace(n0, n1, a.ny))   # 행: 남→북, 열: 서→동
    lx = ee * s + nn * c
    ly = -ee * c + nn * s
    # 도메인 경계에 정확히 걸친 점은 보간에서 빠지므로 아주 조금 안쪽으로 당긴다
    for arr, lo, hi in ((lx, xmin, xmax), (ly, ymin, ymax)):
        tol, inset = 1e-6 * (hi - lo), 1e-4 * (hi - lo)
        arr[(arr > lo - tol) & (arr < lo + inset)] = lo + inset
        arr[(arr < hi + tol) & (arr > hi - inset)] = hi - inset
    u_all, v_all, w_all, k_all, p_all = [], [], [], [], []
    for z in zs:
        pts = np.column_stack([lx.ravel(), ly.ravel(), np.full(lx.size, ground + z)])
        res = pv.PolyData(pts).sample(mesh)
        ok = res["vtkValidPointMask"].astype(bool)
        U = np.asarray(res[fU], dtype=float)
        ue = np.where(ok, U[:, 0] * s - U[:, 1] * c, np.nan)     # 동 성분
        vn = np.where(ok, U[:, 0] * c + U[:, 1] * s, np.nan)     # 북 성분
        u_all.append(ue); v_all.append(vn); w_all.append(np.where(ok, U[:, 2], np.nan))
        if fK in have:
            k_all.append(np.where(ok, np.asarray(res[fK], dtype=float), np.nan))
        if fP in have:
            p_all.append(np.where(ok, np.asarray(res[fP], dtype=float), np.nan))
        spd = np.sqrt(ue**2 + vn**2)
        print(f"[정보] z={z:g} m: 유효 {ok.sum()}/{ok.size} 점, 평균 풍속 {np.nanmean(spd) if ok.any() else float('nan'):.2f} m/s")

    def pack(lst):
        arr = np.concatenate(lst)
        return [None if np.isnan(x) else round(float(x), 3) for x in arr]

    out["u"], out["v"], out["w"] = pack(u_all), pack(v_all), pack(w_all)
    if k_all:
        out["k"] = pack(k_all)
    if p_all:
        out["p"] = pack(p_all)
        out["p_ref"] = a.pref
        out["p_unit"] = "kinematic"       # OpenFOAM 비압축성 솔버의 p 는 p/ρ (m²/s²)
    if a.uref:
        out["U_ref"] = a.uref
    else:
        print("[경고] --uref 가 없어 뷰어가 최상층 평균 풍속을 기준 풍속으로 대신 씁니다.")

    if a.sensors:
        out["sensors"] = []
        with open(a.sensors, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                if "lon" in row and row["lon"] not in (None, ""):
                    lon, lat = float(row["lon"]), float(row["lat"])
                else:
                    x, y = float(row["x"]), float(row["y"])
                    lon = a.origin_lon + (x * s - y * c) / m_lon
                    lat = a.origin_lat + (x * c + y * s) / m_lat
                out["sensors"].append({"name": row.get("name", ""), "lon": lon, "lat": lat,
                                       "z": float(row["z"]), "measured": float(row["measured"])})
        print(f"[정보] 센서 {len(out['sensors'])}개 추가")

    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print(f"[완료] {a.out} 저장 ({os.path.getsize(a.out) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
