"""
ice_sim.py — ตู้แช่ on/off ที่มีน้ำแข็งค่อยๆ เกาะคอยล์
ดูว่าน้ำแข็งทำให้ duty ของคอมขึ้นยังไง และตู้เริ่มคุมไม่อยู่ตอนไหน

วิธีทำ: เติม TODO ทีละข้อ (พิมพ์เอง) ตอนนี้มีแค่ TODO 1 ข้อ 2 กับ 3 จะตามมา
ก่อนรัน ให้เขียนคำทายลงไปตรงนี้:
  ทาย 1: k_ice(0) = ...   k_ice(1) = ...   k_ice(3) = ...
"""
import matplotlib.pyplot as plt

# ---------- พารามิเตอร์ตู้ (ชุดเดียวกับ pid_sim.py) ----------
C = 50_000.0     # J/K  ต้องใส่ความร้อนกี่จูลตู้ถึงจะร้อนขึ้น 1 องศา
UA = 1.5         # W/K  ตู้รั่วความร้อนง่ายแค่ไหน
PMAX = 150.0     # W    ความเย็นตอนคอยล์สะอาด
T_ROOM = 30.0    # °C
SP = -18.0       # °C   ค่าตั้ง
BAND = 2.5       # K    ช่วง on/off จาก ADR-0001

# ---------- พารามิเตอร์น้ำแข็ง (ใหม่) ----------
M0 = 1.0               # kg  น้ำแข็งหนักเท่านี้ ความเย็นเหลือครึ่งเดียว (k_ice = 0.5)
R_RUN = 0.5 / 86400    # kg/s  น้ำแข็งที่เกาะเพิ่มตอนคอมเดิน (เดินครบ 1 วัน = 0.5 kg)
DOOR_EVERY = 2.0       # ชม.  เปิดประตูทุกๆ กี่ชั่วโมง
DOOR_ICE = 0.03        # kg  น้ำแข็งที่เพิ่มทันทีต่อการเปิดประตู 1 ครั้ง

DT = 1.0         # วินาที ต่อ 1 รอบ (เหมือน scan ของ PLC)
HOURS = 48
WINDOW = 4.0     # ชม.  นับ duty ทีละกี่ชั่วโมง

def k_ice(m):
    """รับมวลน้ำแข็ง m (kg) คืนสัดส่วนความเย็นที่เหลือ (0 ถึง 1)
    คอยล์สะอาด m = 0 -> 1.0,  m = M0 -> 0.5
    """
    # TODO 1: สูตร k_ice = 1 / (1 + m / M0)  เขียนเป็น return 1 บรรทัด
    return 1/(1 + m/M0)


def plant_step(T, u, m):
    """ตู้: เหมือน pid_sim.py แต่ความเย็นคูณด้วย k_ice(m)"""
    return T + DT * (UA * (T_ROOM - T) - PMAX * k_ice(m) * u) / C


def onoff_step(T, comp_on):
    """on/off แบบมี band (ตัวเดียวกับ pid_sim.py)"""
    if T >= SP + BAND / 2:
        return True
    if T <= SP - BAND / 2:
        return False
    return comp_on


def check_k_ice():
    """เช็ก TODO 1: พิมพ์ค่าเทียบกับที่ควรได้"""
    for m, expect in [(0, 1.0), (1, 0.5), (3, 0.25)]:
        got = k_ice(m)
        ok = "ผ่าน" if abs(got - expect) < 1e-9 else "ยังไม่ผ่าน"
        print(f"k_ice({m}) = {got:.3f}   ควรได้ {expect:.3f}   {ok}")


def run():
    """จำลอง HOURS ชั่วโมง เริ่มที่ SP คอยล์สะอาด คืน (เวลา[ชม.], อุณหภูมิ, u, k_ice, duty ทีละช่วง)"""
    T = SP
    comp_on = True
    m = 0.0                                      # มวลน้ำแข็งบนคอยล์ (kg) เริ่มสะอาด
    door_steps = int(DOOR_EVERY * 3600 / DT)     # เปิดประตูทุกๆ กี่รอบ (2 ชม. = 7200 รอบ)
    win_steps = int(WINDOW * 3600 / DT)          # 1 ช่วงนับ duty มีกี่รอบ (4 ชม. = 14400 รอบ)
    on_count = 0                                 # นับว่าในช่วงนี้คอมเดินไปกี่วินาทีแล้ว
    duties = []                                  # duty ของแต่ละช่วง
    times, temps, us, ks = [], [], [], []
    for k in range(int(HOURS * 3600 / DT)):
        comp_on = onoff_step(T, comp_on)
        u = 1.0 if comp_on else 0.0

        m += R_RUN * u * DT
        if k % door_steps == 0 and k > 0:
            m += DOOR_ICE

        T = plant_step(T, u, m)
        times.append(k * DT / 3600)
        temps.append(T)
        us.append(u)
        ks.append(k_ice(m))

        # TODO 3 ก: นับวินาทีที่คอมเดิน -> บวก u เข้า on_count (1 บรรทัด)
        on_count += u
        # TODO 3 ข: ถ้าครบ 1 ช่วงพอดี (ใช้ (k + 1) % win_steps == 0)
        #   -> append (on_count / win_steps) เข้า duties
        #   -> แล้วรีเซ็ต on_count กลับเป็น 0 (เริ่มนับช่วงใหม่)
        if (k + 1) % win_steps == 0:
            duties.append(on_count / win_steps)
            on_count = 0

    print(f"หลัง {HOURS} ชม.: น้ำแข็ง m = {m:.2f} kg,  k_ice = {k_ice(m):.3f},  T = {T:.2f} °C")
    for i, d in enumerate(duties):
        print(f"  ชม. {i * WINDOW:4.0f}-{(i + 1) * WINDOW:<4.0f} duty = {d * 100:5.1f} %")
    return times, temps, us, ks, duties


def main():
    check_k_ice()
    t, T, u, ks, duties = run()
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    a1.plot(t, T, lw=0.8)
    a1.axhline(SP + BAND / 2, color="k", ls=":", lw=0.8)
    a1.axhline(SP - BAND / 2, color="k", ls=":", lw=0.8)
    a1.set_ylabel("T [°C]"); a1.grid(alpha=0.3)
    a2.plot(t, ks, color="tab:blue")
    a2.axhline(0.48, color="tab:red", ls="--", lw=0.8, label="k_ice = 0.48")
    a2.set_ylabel("k_ice"); a2.legend(); a2.grid(alpha=0.3)
    # duty จากสูตรที่คิดมือ: 0.48 / k_ice (แต่ไม่เกิน 100%)
    a3.plot(t, [min(1.0, 0.48 / k) * 100 for k in ks], color="gray", ls="--", lw=1, label="0.48 / k_ice (hand calc)")
    if duties:
        mid = [(i + 0.5) * WINDOW for i in range(len(duties))]
        a3.plot(mid, [d * 100 for d in duties], "o-", color="tab:orange", label=f"duty from sim (every {WINDOW:.0f} h)")
    a3.set_ylabel("duty [%]"); a3.set_xlabel("time [h]"); a3.set_ylim(0, 110); a3.legend(); a3.grid(alpha=0.3)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()