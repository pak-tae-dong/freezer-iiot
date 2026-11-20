"""
บทที่ 5: วนลองความกว้างช่วง on/off หลายค่าอัตโนมัติ แล้ววาดกราฟ
ส่วน ① ผมเขียนให้แล้ว (คือ freezer_sim.py ที่ห่อเป็นฟังก์ชัน)
ส่วน ② คุณเติม TODO เอง
"""
import matplotlib.pyplot as plt

# ---------- พารามิเตอร์ของตู้ (เหมือน freezer_sim.py) ----------
C = 50_000
UA_WALL = 1.5
Q_COOL = 150.0
T_AMB = 30.0
SETPOINT = -18.0
DT = 10.0
DURATION = 12 * 3600


# ========== ① ฟังก์ชันจำลอง: ใส่ band เข้าไป ได้จำนวนสตาร์ตกลับมา ==========
def simulate(band):
    T = SETPOINT
    comp_on = False
    starts = 0
    for k in range(int(DURATION / DT)):
        if T > SETPOINT + band / 2 and not comp_on:
            comp_on = True
            starts += 1
        elif T < SETPOINT - band / 2 and comp_on:
            comp_on = False
        q_cool = Q_COOL if comp_on else 0.0
        T = T + DT / C * (UA_WALL * (T_AMB - T) - q_cool)
    return starts


# ========== ② ส่วนของคุณ ==========
# ตัวอย่างการใช้ฟังก์ชัน:  n = simulate(2.0)   → n จะได้ 16

# TODO 1: สร้าง list ของความกว้างช่วงที่อยากลอง เช่น 0.5, 1, 1.5, ... ไปจนถึง 5
bands = [i * 0.5 for i in range(1,11)]

# TODO 2: วนทีละค่าใน bands เรียก simulate() แล้วเก็บผลใส่ list ชื่อ starts_list
#         และ print ผลแต่ละค่าออกมาให้ดูด้วย
starts_list = []
for b in bands:
    x = simulate(b)
    starts_list.append(x)
    print(b, x)
# TODO 3: วาดกราฟ แกน x = bands, แกน y = starts_list
#         ใส่ชื่อแกน x, แกน y และชื่อกราฟ (ภาษาอังกฤษ เพราะ matplotlib แสดงภาษาไทยไม่ได้)
#         ใช้ plt.plot(...), plt.xlabel(...), plt.ylabel(...), plt.title(...), plt.show()
plt.plot(bands, starts_list, marker="o")   # marker="o" ใส่จุดกลมที่ข้อมูลแต่ละจุด
plt.xlabel("Band (K)")                     # ชื่อแกน x
plt.ylabel("Compressor starts per 12 h")                     # ชื่อแกน y
plt.title("relation between band and starting")                      # ชื่อกราฟ
plt.grid(True)                        # ใส่ตาราง อ่านค่าง่ายขึ้น
plt.show()                            # แสดงกราฟ