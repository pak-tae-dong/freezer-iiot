"""
สัปดาห์ 1 — สคริปต์บันทึกค่าเซนเซอร์ลง CSV
ตอนนี้ยังไม่มีเซนเซอร์จริง เลยใช้ฟังก์ชันจำลองแทน
(สัปดาห์ 3 จะเปลี่ยนเป็นอ่านจากตู้เสมือนผ่าน Modbus — ส่วนอื่นใช้ต่อได้)
"""
import csv
import random
import time
from datetime import datetime
from pathlib import Path

CSV_FILE = Path("freezer_log.csv")
INTERVAL_S = 5          # อ่านทุกกี่วินาที (edge จริงจะอยู่ที่ 1–5 วิ)


def read_sensor() -> float:
    """จำลองการอ่านอุณหภูมิ: บางครั้งอ่านพลาด เหมือนสายหลุดหรือ PLC ไม่ตอบ"""
    if random.random() < 0.3:                      # พลาด 30% ของครั้ง
        raise ConnectionError("อ่านเซนเซอร์ไม่ได้")
    return round(-18 + random.gauss(0, 0.5), 2)    # ค่าแกว่งรอบ -18 °C


def main():
    new_file = not CSV_FILE.exists()
    with CSV_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["ts", "metric", "value", "q"])   # หัวตารางครั้งแรกเท่านั้น

        print("เริ่มบันทึก กด Ctrl+C เพื่อหยุด")
        try:
            while True:
                ts = datetime.now().astimezone().isoformat(timespec="seconds")
                try:
                    value, q = read_sensor(), "good"
                except ConnectionError as e:
                    value, q = None, "stale"               # ไม่ให้โปรแกรมล้ม แต่จดไว้ว่าข้อมูลหาย
                    print(f"{ts}  ⚠ {e}")
                writer.writerow([ts, "evap_air_out", value, q])
                f.flush()                                  # เขียนลงดิสก์ทันที ไฟดับก็ไม่หาย
                print(f"{ts}  {value}  {q}")
                time.sleep(INTERVAL_S)
        except KeyboardInterrupt:
            print("หยุดแล้ว")


if __name__ == "__main__":
    main()
