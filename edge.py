import json
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt

from fins import FinsClient

BROKER = "localhost"
PORT = 1883
TOPIC_BASE = "lab/freezer1"
# python edge.py -> PLC ปลอม | python edge.py 192.168.250.1 -> PLC จริง
PLC_IP = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"

# D0-D7 ตาม register map: (ชื่อ metric, ตัวหาร, หน่วย, signed?)
# อุณหภูมิติดลบได้ -> signed; ตัวนับ heartbeat นับวน 0-65535 -> unsigned
REGISTERS = [
	("T_box", 10, "degC", True),
	("T_room", 10, "degC", True),
	("setpoint", 10, "degC", True),
	("band", 10, "K", True),
	("comp_state", 1, "", False),
	("plc_heartbeat", 1, "", False),
	("sim_heartbeat", 1, "", False),
	("comm_fault", 1, "", False),
]

plc = FinsClient(PLC_IP)


# อ่าน D0-D7 รวดเดียวด้วย FINS/TCP; ถ้าสายหลุดให้ปิด แล้วรอบหน้าต่อใหม่เอง
def read_plc():
	try:
		if plc.sock is None:
			plc.connect()
		return plc.read_dm(0, 8)
	except Exception:
		plc.close()
		raise


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, PORT, 60)
client.loop_start()

last_hb = None

try:
	while True:
		ts = datetime.now().astimezone().isoformat(timespec="seconds")

		try:
			raw = read_plc()
		except Exception as e:
			print(ts, "PLC read failed:", e)
			time.sleep(2)
			continue

		# heartbeat ของ PLC (D5) ไม่เปลี่ยน = Ladder ไม่ได้รัน -> ข้อมูล stale
		hb = raw[5]
		q = "good" if hb != last_hb else "stale"
		last_hb = hb

		values = []
		for (name, div, unit, signed), v in zip(REGISTERS, raw):
			if not signed:
				v = v & 0xFFFF	# -12195 -> 53341 (อ่านแบบไม่มีเครื่องหมาย)
			value = v / div if div != 1 else v
			values.append(value)
			payload = {"ts": ts, "value": value, "unit": unit, "q": q}
			client.publish(f"{TOPIC_BASE}/{name}", json.dumps(payload))

		print(ts, q, values)
		time.sleep(2)
except KeyboardInterrupt:
	print("stop")
finally:
	client.loop_stop()
	client.disconnect()
	plc.close()
