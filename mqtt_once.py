import paho.mqtt.client as mqtt

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect("localhost", 1883, 60)
client.loop_start()

info = client.publish("lab/freezer1/T_box", "-18.2")
info.wait_for_publish()

client.loop_stop()
client.disconnect()
print("sent")