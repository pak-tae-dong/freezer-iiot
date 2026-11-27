import sys

from fins import FinsClient

# python client_test.py                 -> PLC ปลอม
# python client_test.py 192.168.250.1   -> PLC จริง
ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
plc = FinsClient(ip)
print("nodes (me, plc):", plc.connect())

plc.write_dm(0, [-180, 300])    # D0 = -18.0 C, D1 = 30.0 C
print("D0-D7:", plc.read_dm(0, 8))

plc.close()
