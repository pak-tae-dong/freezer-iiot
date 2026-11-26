import json
import time
from datetime import datetime

import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "lab/freezer1/T_box"

# ค่าปลอมไปก่อน → วันศุกร์เปลี่ยนเป็นอ่าน D0–D7 ผ่าน FINS/TCP
def read_plc():
	return -18.2

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, PORT, 60)
client.loop_start()

try:
	while True:
		ts = datetime.now().astimezone().isoformat(timespec="seconds")

		payload = {
			"ts" : ts,
			"value" : read_plc(),
			"unit" : "degC",
			"q" : "good"
		}

		client.publish(TOPIC, json.dumps(payload))
		print(TOPIC, json.dumps(payload))
		time.sleep(2)
except KeyboardInterrupt:
	print("stop")
finally:
	client.loop_stop()
	client.disconnect()