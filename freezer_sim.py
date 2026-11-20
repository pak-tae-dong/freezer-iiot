"""
บทที่ 1: โมเดลความร้อนของตู้แช่ + คุมแบบ on/off
สมดุลพลังงาน (ตู้ทั้งใบมองเป็นก้อนเดียว อุณหภูมิเดียว):

    C * dT/dt = UA_wall * (T_amb - T)  +  Q_load  -  u * Q_cool
                └─ ความร้อนรั่วผ่านผนัง ─┘  └ ภาระ ┘   └ ความเย็นจากคอยล์ (u = 0/1)

แปลงเป็นทีละก้าวเวลา (Euler):
    T[k+1] = T[k] + dt / C * (ผลรวมความร้อนข้างบน)
"""
import matplotlib.pyplot as plt

# ---------- พารามิเตอร์ของตู้ (ค่าประมาณตู้แช่เล็ก) ----------
C = 50_000        # J/K   ความจุความร้อนของอากาศ + ของในตู้ + ผนังด้านใน
UA_WALL = 1.5     # W/K   ความร้อนรั่วผ่านฉนวน ต่อองศาที่ต่างกัน
Q_COOL = 150.0    # W     ความเย็นที่คอยล์ให้ได้ตอนคอมเพรสเซอร์เดิน
Q_LOAD = 0.0      # W     ภาระเพิ่ม (เปิดประตู ใส่ของอุ่น) — ตอนนี้ยังไม่มี
T_AMB = 30.0      # °C    อุณหภูมิห้องข้างนอก

# ---------- ตัวควบคุม on/off ----------
SETPOINT = -18.0  # °C
BAND = 4.0        # K     ความกว้างช่วง: เปิดที่ -17, ปิดที่ -19

# ---------- การจำลอง ----------
DT = 10.0                 # s   ก้าวเวลา
DURATION = 12 * 3600      # s   จำลอง 12 ชั่วโมง

T = -18.0                 # อุณหภูมิเริ่มต้น
comp_on = False
times, temps, states = [], [], []
starts = 0                # นับจำนวนครั้งที่คอมเพรสเซอร์สตาร์ต

for k in range(int(DURATION / DT)):
    # 1) ตัวควบคุมตัดสินใจจากค่าที่วัดได้ (hysteresis)
    if T > SETPOINT + BAND / 2 and not comp_on:
        comp_on = True
        starts += 1
    elif T < SETPOINT - BAND / 2 and comp_on:
        comp_on = False

    # 2) ฟิสิกส์ของตู้: รวมความร้อนเข้า-ออก แล้วขยับอุณหภูมิไป 1 ก้าว
    q_leak = UA_WALL * (T_AMB - T)
    q_cool = Q_COOL if comp_on else 0.0
    T = T + DT / C * (q_leak + Q_LOAD - q_cool)

    times.append(k * DT / 3600)
    temps.append(T)
    states.append(1 if comp_on else 0)

duty = sum(states) / len(states)
print(f"ช่วงกว้าง {BAND} K: สตาร์ต {starts} ครั้ง/12 ชม., "
      f"เดินเครื่อง {duty:.0%} ของเวลา, "
      f"อุณหภูมิ {min(temps):.1f} ถึง {max(temps):.1f} °C")

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 5))
ax1.plot(times, temps)
ax1.axhline(SETPOINT, ls="--", c="gray")
ax1.set_ylabel("Temp (°C)")
ax2.step(times, states, where="post")
ax2.set_ylabel("Compressor (0/1)")
ax2.set_xlabel("Time (h)")
plt.tight_layout()
plt.show()
