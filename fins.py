"""fins.py - Omron FINS/TCP client (CP1L + CP1W-CIF41)

ใช้งาน:
    from fins import FinsClient
    plc = FinsClient("127.0.0.1")    # PLC ปลอม | PLC จริงใช้ "192.168.250.1"
    plc.connect()
    plc.write_dm(0, [-180, 300])     # เขียน D0, D1
    print(plc.read_dm(0, 8))         # อ่าน D0-D7
    plc.close()
"""
import socket
import struct

FINS_PORT = 9600


# ---------- สร้าง / แยกข้อความ (ทดสอบแล้ว 27 พ.ย.) ----------

def build_handshake():
    # FINS | length | command 0 (ขอ node) | error | client node 0 (ให้ PLC เลือกให้)
    return struct.pack(">4sIIII", b"FINS", 12, 0, 0, 0)


def parse_handshake(resp):
    magic, length, cmd, err, my_node, plc_node = struct.unpack(">4sIIIII", resp)
    if magic != b"FINS" or cmd != 1 or err != 0:
        raise RuntimeError(f"handshake failed: cmd={cmd} err={err}")
    return my_node, plc_node


def _address(my_node, plc_node):
    # ICF RSV GCT DNA DA1 DA2 SNA SA1 SA2 SID
    return bytes([0x80, 0x00, 0x02, 0x00, plc_node, 0x00, 0x00, my_node, 0x00, 0x00])


def _wrap(body):
    # ห่อซอง FINS/TCP: command 2 = ส่ง FINS frame
    return struct.pack(">4sIII", b"FINS", 8 + len(body), 2, 0) + body


def build_read_dm(start, count, my_node, plc_node):
    command = struct.pack(">BBBHBH", 0x01, 0x01, 0x82, start, 0x00, count)
    return _wrap(_address(my_node, plc_node) + command)


def build_write_dm(start, values, my_node, plc_node):
    command = struct.pack(">BBBHBH", 0x01, 0x02, 0x82, start, 0x00, len(values))
    data = struct.pack(">" + "h" * len(values), *values)
    return _wrap(_address(my_node, plc_node) + command + data)


def _check_response(resp):
    tcp_err = struct.unpack(">I", resp[12:16])[0]
    if tcp_err != 0:
        raise RuntimeError(f"FINS/TCP error code {tcp_err}")
    end_code = resp[28:30]
    if end_code != b"\x00\x00":
        raise RuntimeError("PLC end code: " + end_code.hex(" "))


def parse_read_dm(resp, count):
    _check_response(resp)
    data = resp[30:30 + count * 2]
    return list(struct.unpack(">" + "h" * count, data))


# ---------- ส่ง / รับผ่าน TCP ----------

def _recv_exact(sock, n):
    # TCP อาจส่งมาเป็นหลายก้อน -> วนรับจนครบ n ไบต์
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("PLC closed the connection")
        buf += chunk
    return buf


def recv_message(sock):
    # อ่าน 8 ไบต์แรก (FINS + length) แล้วอ่านต่ออีก length ไบต์
    head = _recv_exact(sock, 8)
    length = struct.unpack(">I", head[4:8])[0]
    return head + _recv_exact(sock, length)


class FinsClient:
    def __init__(self, ip, port=FINS_PORT, timeout=2.0):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.my_node = None
        self.plc_node = None

    def connect(self):
        self.sock = socket.create_connection((self.ip, self.port), timeout=self.timeout)
        self.sock.sendall(build_handshake())
        self.my_node, self.plc_node = parse_handshake(recv_message(self.sock))
        return self.my_node, self.plc_node

    def read_dm(self, start, count):
        self.sock.sendall(build_read_dm(start, count, self.my_node, self.plc_node))
        return parse_read_dm(recv_message(self.sock), count)

    def write_dm(self, start, values):
        self.sock.sendall(build_write_dm(start, values, self.my_node, self.plc_node))
        _check_response(recv_message(self.sock))

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None


# ---------- ทดสอบไบต์ (รันเฉพาะตอนสั่ง python fins.py) ----------

if __name__ == "__main__":
    assert build_handshake() == bytes.fromhex(
        "46 49 4E 53 00 00 00 0C 00 00 00 00 00 00 00 00 00 00 00 00")
    assert parse_handshake(bytes.fromhex(
        "46 49 4E 53 00 00 00 10 00 00 00 01 00 00 00 00 00 00 00 0A 00 00 00 01")) == (10, 1)
    assert build_read_dm(0, 8, 10, 1) == bytes.fromhex(
        "46 49 4E 53 00 00 00 1A 00 00 00 02 00 00 00 00"
        "80 00 02 00 01 00 00 0A 00 00 01 01 82 00 00 00 00 08")
    assert parse_read_dm(bytes.fromhex(
        "46 49 4E 53 00 00 00 26 00 00 00 02 00 00 00 00"
        "C0 00 02 00 0A 00 00 01 00 00 01 01 00 00"
        "FF 4C 01 2C FF 4C 00 19 00 01 00 2A 00 07 00 00"), 8) == [-180, 300, -180, 25, 1, 42, 7, 0]
    assert build_write_dm(0, [-180, 300], 10, 1) == bytes.fromhex(
        "46 49 4E 53 00 00 00 1E 00 00 00 02 00 00 00 00"
        "80 00 02 00 01 00 00 0A 00 00 01 02 82 00 00 00 00 02 FF 4C 01 2C")
    print("all frame tests OK")
