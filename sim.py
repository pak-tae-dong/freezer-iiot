"""sim.py - ตู้เสมือน (virtual plant) คุยกับ PLC ผ่าน FINS/TCP

รัน:  python sim.py                      -> PLC ปลอม 127.0.0.1, เวลาจริง
      python sim.py 192.168.250.1        -> PLC จริง (CP1L + CIF41)
      python sim.py 127.0.0.1 60         -> เร่งเวลา 60 เท่า (ใช้กับ PLC ปลอมเท่านั้น
                                            เพราะ timer ใน Ladder จริงเดินตามเวลาจริง)
ทุก 2 วินาที: อ่าน comp_state (D4) -> คำนวณอุณหภูมิ 1 ก้าว -> เขียน D0, D1, D6
"""
import sys
import time

from fins import FinsClient

PLC_IP = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
SPEED = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

# โมเดลตู้ก้อนเดียว (ค่าเดียวกับ freezer_sim.py)
C = 50_000        # J/K
UA_WALL = 1.5     # W/K
Q_COOL = 150.0    # W
T_AMB = 30.0      # °C
T_START = -15.0   # °C  เริ่มอุ่นกว่าขอบบน -> Ladder ควรสั่งเปิดคอม (หลังเวลาหน่วง)

PERIOD = 2.0      # s   รอบสื่อสาร (เวลาจริง)

plc = FinsClient(PLC_IP)


def exchange(T, hb):
	# อ่าน D4 แล้วเขียน D0, D1 (ติดกัน) + D6; ถ้าหลุดให้ปิด แล้วรอบหน้าต่อใหม่
	try:
		if plc.sock is None:
			print("connecting to", PLC_IP, "...")
			plc.connect()
		comp = plc.read_dm(4, 1)[0]
		plc.write_dm(0, [round(T * 10), round(T_AMB * 10)])
		plc.write_dm(6, [hb])
		return comp
	except Exception:
		plc.close()
		raise


T = T_START
hb = 0
comp = 0
print(f"sim: PLC {PLC_IP}, speed x{SPEED:g}  (Ctrl+C to stop)")

try:
	while True:
		hb = (hb + 1) % 32768
		try:
			comp = exchange(T, hb)
		except Exception as e:
			print("PLC error:", e)
			time.sleep(PERIOD)
			continue

		# ฟิสิกส์ 1 ก้าว (Euler) ด้วย comp_state ที่ PLC สั่ง
		dt = PERIOD * SPEED
		q_leak = UA_WALL * (T_AMB - T)
		q_cool = Q_COOL if comp else 0.0
		T = T + dt / C * (q_leak - q_cool)

		print(f"T_box {T:6.2f} °C   comp {comp}   sim_hb {hb}")
		time.sleep(PERIOD)
except KeyboardInterrupt:
	print("stop")
finally:
	plc.close()
