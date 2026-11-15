# Maritime Data Quality Audit Scorecard

- **Source File:** `events_raw_1.csv` → tập sạch `gfw_clean_2021_global.csv`
- **Total Records Audited:** 2.021 (từ 46.823 dòng thô)
- **Unique Vessels / Devices:** 1.296 MMSI / 1.309 vessel_id
- **Audit Timestamp:** 2026-11-14 17:09 UTC

## 1. Quality Dimension Summary
| Dimension | Metric | Pass Rate (%) | Severity | Notes |
| :--- | :--- | :---: | :---: | :--- |
| **Completeness** | Non-null critical fields (ID, Time, Lat, Lon) | 100.00% | LOW | 0/2.021 dòng thiếu `vessel_ssvid`, `start`, `position_lat/lon` |
| **Uniqueness** | Deduplicated `(ID + Timestamp)` records | 100.00% | LOW | 0 bản ghi trùng `(vessel_ssvid, start)` |
| **Identifier Validity** | Valid 9-digit ITU MMSI (excluding `98`/`99` gear) | 95.15% | HIGH | 1.923/2.021 hợp lệ; 98 dòng bị gắn cờ: 47 dòng tiền tố `98` (phụ trợ/phao), 51 dòng MID ngoài 201–775 (40 MMSI) |
| **Spatial Integrity** | Valid WGS84 bounds & non-zero coordinates | 100.00% | LOW | Không có (0,0), không ngoài khoảng; chưa kiểm tra tọa độ trên đất liền |
| **Kinematic Plausibility** | Implied speed within vessel physical limits | 100.00% | LOW | Tối đa 22,24 kn; không dòng nào vượt ngưỡng theo loại tàu (fishing ≤30, cargo ≤35, passenger ≤55) |

## 2. Anomaly Breakdown
- **Flagged Records Export:** `maritime_audit_flags.csv`
- **Key Domain Findings:** Dữ liệu là sự kiện GFW Gap (không phải ping thô) nên không tính được nhảy GPS giữa các ping. 98 dòng (4,85%) bị gắn cờ: 47 dòng tiền tố `98` và 51 dòng MID ngoài 201–775 (MID 987: 42 dòng, 785: 13, 108/109/100: 19). Bộ lọc `99` của nghiên cứu không loại tiền tố `98`. Vị trí tắt AIS đều cách bờ ≥ 93 km (khớp ngưỡng cắt 50 hải lý của GFW), nhưng 385 sự kiện kết thúc trong vòng 92,6 km từ bờ.
