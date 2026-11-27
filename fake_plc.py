"""fake_plc.py - PLC ปลอมที่ตอบ FINS/TCP เหมือน CP1W-CIF41 (ใช้ทดสอบตอนยังไม่มีสาย)

รัน: python fake_plc.py   (หยุดด้วย Ctrl+C)
- รับ client ได้หลายตัวพร้อมกัน (sim.py + edge.py)
- มี DM 100 word: D2 = -180 (setpoint), D3 = 25 (band), D5 = heartbeat +1 ทุกวินาที
- ไม่มี Ladder: ไม่คุมคอม ไม่มี watchdog
"""
import socket
import struct
import threading
import time

from fins import recv_message

HOST, PORT = "127.0.0.1", 9600
PLC_NODE = 1

dm = [0] * 100
dm[2] = -180
dm[3] = 25
lock = threading.Lock()
next_node = [10]


def heartbeat():
    while True:
        time.sleep(1)
        with lock:
            dm[5] = (dm[5] + 1) & 0x7FFF


def reply(conn, req, data=b""):
    # สลับผู้ส่ง/ผู้รับ, ICF C0 = คำตอบ, ตามด้วยคำสั่งเดิม + end code 00 00
    a = req[16:26]
    address = bytes([0xC0, 0x00, 0x02, a[6], a[7], a[8], a[3], a[4], a[5], a[9]])
    body = address + req[26:28] + b"\x00\x00" + data
    conn.sendall(struct.pack(">4sIII", b"FINS", 8 + len(body), 2, 0) + body)


def serve(conn, addr):
    print("connected:", addr)
    try:
        while True:
            req = recv_message(conn)
            cmd = struct.unpack(">I", req[8:12])[0]
            if cmd == 0:  # ขอ node
                with lock:
                    node = next_node[0]
                    next_node[0] += 1
                conn.sendall(struct.pack(">4sIIIII", b"FINS", 16, 1, 0, node, PLC_NODE))
                print(f"  handshake -> client node {node}")
                continue
            mrc_src = req[26:28]
            area, start, _bit, count = struct.unpack(">BHBH", req[28:34])
            if area != 0x82:
                print("  area not supported:", hex(area))
                continue
            if mrc_src == b"\x01\x01":  # read
                with lock:
                    values = dm[start:start + count]
                reply(conn, req, struct.pack(">" + "h" * count, *values))
            elif mrc_src == b"\x01\x02":  # write
                values = struct.unpack(">" + "h" * count, req[34:34 + count * 2])
                with lock:
                    dm[start:start + count] = values
                reply(conn, req)
                print(f"  write D{start}..D{start + count - 1} = {list(values)}")
    except (ConnectionError, OSError):
        pass
    finally:
        conn.close()
        print("disconnected:", addr)


def main():
    threading.Thread(target=heartbeat, daemon=True).start()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen()
    srv.settimeout(1.0)  # ให้ Ctrl+C หยุดได้บน Windows
    print(f"fake PLC listening on {HOST}:{PORT}  (Ctrl+C to stop)")
    try:
        while True:
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            conn.settimeout(None)
            threading.Thread(target=serve, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("stopped")
    finally:
        srv.close()


if __name__ == "__main__":
    main()
