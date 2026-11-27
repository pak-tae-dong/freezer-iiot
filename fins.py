import struct

def build_handshake():
    # FINS | length | command | error | client node
    return struct.pack(">4sIIII", b"FINS", 12, 0, 0, 0)

if __name__ == "__main__":
    frame = build_handshake()
    print(frame.hex(" "))
    assert frame == bytes.fromhex(
        "46 49 4E 53 00 00 00 0C 00 00 00 00 00 00 00 00 00 00 00 00"
    )
    print("handshake OK")
def parse_handshake(resp):
    magic, length, cmd, err, my_node, plc_node = struct.unpack(">4sIIIII", resp)
    return my_node, plc_node

fake_resp = bytes.fromhex(
    "46 49 4E 53 00 00 00 10 00 00 00 01 00 00 00 00 00 00 00 0A 00 00 00 01"
)
print(parse_handshake(fake_resp))
def build_read_dm(start, count, my_node, plc_node):
    address = bytes([0x80, 0x00, 0x02, 0x00, plc_node, 0x00, 0x00, my_node, 0x00, 0x00])
    command = struct.pack(">BBBHBH", 0x01, 0x01, 0x82, start, 0x00, count)
    body = address + command
    header = struct.pack(">4sIII", b"FINS", 8 + len(body), 2, 0)
    return header + body

print(build_read_dm(0, 8, 10, 1).hex(" "))
def parse_read_dm(resp, count):
    end_code = resp[28:30]
    if end_code != b"\x00\x00":
        raise RuntimeError("PLC error: " + end_code.hex())
    data = resp[30:30 + count * 2]
    return list(struct.unpack(">" + "h" * count, data))

fake_read = bytes.fromhex(
    "46 49 4E 53 00 00 00 26 00 00 00 02 00 00 00 00"
    "C0 00 02 00 0A 00 00 01 00 00 01 01 00 00"
    "FF 4C 01 2C FF 4C 00 19 00 01 00 2A 00 07 00 00"
)
print(parse_read_dm(fake_read, 8))
def build_write_dm(start, values, my_node, plc_node):
    address = bytes([0x80, 0x00, 0x02, 0x00, plc_node, 0x00, 0x00, my_node, 0x00, 0x00])
    command = struct.pack(">BBBHBH", 0x01, 0x02, 0x82, start, 0x00, len(values))
    data = struct.pack(">" + "h" * len(values), *values)
    body = address + command + data
    header = struct.pack(">4sIII", b"FINS", 8 + len(body), 2, 0)
    return header + body

print(build_write_dm(0, [-180, 300], 10, 1).hex(" "))