# วันที่ได้สาย: ลำดับทดสอบกับ CP1L จริง

ทำตามลำดับ ผ่านข้อไหนค่อยไปข้อถัดไป ถ้าติดให้จดข้อความ error ไว้

## A. สาย USB A–B → โหลด Ladder ลง PLC
1. เปิด `freezer_iot_Ladder.cxp` ใน CX-Programmer
2. ดูรหัสเต็มบนสติกเกอร์ข้าง PLC (เช่น CP1L-M30DR-A) → ดับเบิลคลิกชื่อ PLC ในแผนผังซ้าย → เช็ก Device Type = CP1L, CPU Type ตรงกับสติกเกอร์ (M30 → M), Network Type = USB
3. ⚠️ เปลี่ยน timer กลับเป็นค่าจริง: T0000 `#1800`, T0001 `#100`, T0002 `#7200`, T0003 `#4800`
4. ใส่ค่าเริ่มต้น D2 = -180 (setpoint), D3 = 25 (band) ผ่าน PLC Memory / Set Value ตอนออนไลน์
5. PLC → Work Online → Transfer → To PLC → เปลี่ยนโหมดเป็น **RUN** (หรือ MONITOR)
6. Online Edit/Monitor: ดู D5 ต้องเพิ่มทีละ 1 ทุกวินาที → Ladder รันอยู่

## B. USB-Ethernet adapter + สาย LAN → ตั้ง IP
1. เสียบ adapter + สาย LAN จาก adapter ไปที่ช่อง LAN ของบอร์ด CIF41
2. 🖥️ `ncpa.cpl` → คลิกขวา Ethernet ตัวใหม่ (ไม่ใช่ Wi-Fi / vEthernet) → Properties → IPv4 →
   IP `192.168.250.10`, Subnet mask `255.255.255.0`, **Default gateway เว้นว่าง**
3. 🖥️ `ping 192.168.250.1` → ต้องได้ Reply
   - ไม่ได้ → เช็กไฟ LINK ที่บอร์ด/adapter, IP จริงของ CIF41 (เว็บหรือคู่มือ), ปิดเปิด PLC
4. 🖥️ `Test-NetConnection 192.168.250.1 -Port 9600` → TcpTestSucceeded ต้องเป็น True
   - False → เข้าเว็บ `http://192.168.250.1` ดูว่าเปิด FINS/TCP อยู่ไหม

## C. FINS/TCP จาก Python
1. เปิด Wireshark จับที่ interface ของ adapter ใหม่ ใส่ filter `tcp.port == 9600`
2. 🖥️ `python client_test.py 192.168.250.1`
   - ควรได้ `nodes (me, plc): (xx, 1)` และ D0-D7 ที่ D0 = -180, D1 = 300
   - ใน Wireshark จะเห็นไบต์ `46 49 4E 53 ...` ชุดเดียวกับที่ทดสอบกับ PLC ปลอม
   - ⚠️ client_test เขียน D0/D1 ทับ → ไม่เป็นไรเพราะ sim.py จะเขียนใหม่ทุก 2 วิ

## D. วงปิดกับตู้เสมือน (3 หน้าต่าง + Docker)
| หน้าต่าง | คำสั่ง |
|---|---|
| 1 | `python sim.py 192.168.250.1` (ห้ามเร่งเวลา เพราะ timer ใน Ladder เดินตามเวลาจริง) |
| 2 | `.venv\Scripts\activate` แล้ว `python edge.py 192.168.250.1` |
| 3 | `docker exec -it mosquitto mosquitto_sub -t "lab/#" -v` |

สิ่งที่ควรเห็น:
- sim เริ่มที่ -15 °C → รอ 3 นาที (เวลาหน่วงตอนเริ่ม RUN) → comp 1 → T_box ลด → ต่ำกว่า -19.2 → comp 0
- plc_heartbeat เพิ่มทุกรอบ, q = good

## E. ทดสอบเคสอันตราย (ถ่ายคลิปได้)
1. ปิดหน้าต่าง sim.py → 10 วิ ต่อมา D7 comm_fault = 1 → คอมเดิน fallback 12 นาที / หยุด 8 นาที
2. เปลี่ยน PLC เป็นโหมด PROGRAM → plc_heartbeat ค้าง → edge ส่ง q = stale ทั้งที่ TCP ยังต่ออยู่
3. ดึงสาย LAN → edge/sim ขึ้น PLC error แต่ไม่ล่ม → เสียบกลับ → ต่อใหม่เอง
