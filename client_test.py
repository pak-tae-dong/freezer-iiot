from fins import FinsClient

plc = FinsClient("127.0.0.1")   # PLC จริง: "192.168.250.1"
print("nodes (me, plc):", plc.connect())

plc.write_dm(0, [-180, 300])    # D0 = -18.0 C, D1 = 30.0 C
print("D0-D7:", plc.read_dm(0, 8))

plc.close()
