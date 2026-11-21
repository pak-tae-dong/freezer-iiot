"""
pid_sim.py — เทียบ on/off กับ PI (มี/ไม่มี anti-windup) บนตู้แช่ก้อนเดียว
เริ่มจากตู้อุ่น 30 °C แล้วดึงลงไปที่ -18 °C ดูผล 30 ชั่วโมง

วิธีทำ: เติม TODO 1 ถึง 4 ตามลำดับ (พิมพ์เอง) ส่วนอื่นเขียนไว้ให้แล้ว
ก่อนรัน ให้เขียนคำทายลงไปตรงนี้:
  ทาย 1: on/off ต่ำสุดได้กี่ °C ?          -> ...
  ทาย 2: PI ไม่มี clamp ต่ำสุดได้กี่ °C ?   -> ...
  ทาย 3: PI มี clamp ต่ำสุดได้กี่ °C ?      -> ...
"""
import matplotlib.pyplot as plt

# ---------- พารามิเตอร์ (ชุดเดียวกับ ADR-0001) ----------
C = 50_000.0     # J/K  ต้องใส่ความร้อนกี่จูลตู้ถึงจะร้อนขึ้น 1 องศา
UA = 1.5         # W/K  ตู้รั่วความร้อนง่ายแค่ไหน
PMAX = 150.0     # W    คอมเพรสเซอร์ดึงความร้อนออกได้เท่าไรตอน 100%
T_ROOM = 30.0    # °C
SP = -18.0       # °C   ค่าตั้ง (Set Point)

BAND = 2.5       # K    ช่วง on/off จาก ADR-0001
KP = 0.5         # ห่าง 1 องศา สั่ง 50%
KI = 1.95e-4     # จากเงื่อนไข zeta = 1

DT = 1.0         # วินาที ต่อ 1 รอบ (เหมือน scan ของ PLC)
HOURS = 30


def plant_step(T, u):
    """ตู้: รับอุณหภูมิตอนนี้ T กับคำสั่ง u (0 ถึง 1) แล้วคืนอุณหภูมิของวินาทีถัดไป"""
    # TODO 1: สมดุลพลังงาน 1 บรรทัด
    #   อุณหภูมิเปลี่ยน = DT * (รั่วเข้า - ดึงออก) / C
    #   รั่วเข้า = UA * (T_ROOM - T),  ดึงออก = PMAX * u
    return T + DT * ((UA * (T_ROOM - T)) - PMAX * u) / C


def onoff_step(T, comp_on):
    """on/off แบบมี band (เหมือนที่ทำใน freezer_sim.py)"""
    if T >= SP + BAND / 2:      # อุ่นถึงขอบบน -> เปิด
        return True
    if T <= SP - BAND / 2:      # เย็นถึงขอบล่าง -> ปิด
        return False
    return comp_on              # อยู่ในช่วง -> คงสถานะเดิม


def pi_step(T, state, antiwindup):
    """ตัวคุม PI คืนค่า u (0 ถึง 1)
    state["box"] = กล่องสะสม error ของ I (เหมือน D register ใน PLC ที่ค่าค้างอยู่ข้ามรอบ scan)
    """
    # TODO 2: หา error (ตู้เย็น -> อุ่นกว่าเป้า ต้องได้ค่าบวก)
    e = T - SP

    # TODO 3: คำนวณ u ก่อนจำกัด (u_raw) = ส่วน P + ส่วน I
    u_raw = KP * e + KI * state["box"]

    # TODO 4: anti-windup แบบ clamp
    #   ถ้า antiwindup เป็น True และ u_raw ชนเพดาน (> 1) ทั้งที่ e ยังเป็นบวก -> ไม่ต้องบวกกล่อง
    #   นอกนั้น -> บวก e * DT เข้ากล่อง
    #   (ใบ้: if not (antiwindup and ...): state["box"] += ...)
    if antiwindup and u_raw > 1 and e > 0:
        pass
    else:
        state["box"] += e * DT

    return min(1.0, max(0.0, u_raw))   # จำกัด 0–100% เพราะคอมทำได้แค่นี้


def run(mode):
    """mode = 'onoff', 'pi', 'pi_clamp'  คืน (เวลาเป็นชั่วโมง, อุณหภูมิ, u)"""
    T = T_ROOM
    comp_on = False
    state = {"box": 0.0}
    times, temps, us = [], [], []
    for k in range(int(HOURS * 3600 / DT)):
        if mode == "onoff":
            comp_on = onoff_step(T, comp_on)
            u = 1.0 if comp_on else 0.0
        elif mode == "pi":
            u = pi_step(T, state, antiwindup=False)
        else:
            u = pi_step(T, state, antiwindup=True)
        T = plant_step(T, u)
        times.append(k * DT / 3600)
        temps.append(T)
        us.append(u)
    return times, temps, us


def main():
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for mode, label in [("onoff", "on/off band 2.5 K"),
                        ("pi", "PI, no anti-windup"),
                        ("pi_clamp", "PI + clamping")]:
        t, T, u = run(mode)
        print(f"{label:22s} ต่ำสุด {min(T):7.2f} °C   ท้ายสุด {T[-1]:7.2f} °C")
        a1.plot(t, T, label=label)
        a2.plot(t, [x * 100 for x in u], label=label)
    a1.axhline(SP, color="k", ls=":", lw=0.8)
    a1.set_ylabel("T [°C]"); a1.legend(); a1.grid(alpha=0.3)
    a2.set_ylabel("u [%]"); a2.set_xlabel("time [h]"); a2.grid(alpha=0.3)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
