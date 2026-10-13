"""
Offcut-matching backtest on SYNTHETIC data (no client data used).

Point it proves: replaying the same project stream in date order, an assistant that
packs parts into ANY compatible offcut (grade + thickness + fit) cuts virgin plate
versus a baseline that only uses an offcut when the whole job fits on it.
The baseline rule is an ASSUMPTION about manual practice, not a known fact.
Parts are rectangles, no rotation (grain direction); real nesting uses true shapes.
"""
import random, statistics

PW, PH = 6000, 2000            # virgin plate, mm
MIN_OFFCUT_AREA = 0.5e6        # mm^2 (0.5 m^2) smallest usable remnant
MIN_DIM = 300
DENS = 7.85                    # t/m^3
GRADES = ["S275", "S355"]
THICK = [10, 12, 16, 20, 25]

def shelf_pack(parts, W, H):
    """Shelf packing. Returns placed parts, unplaced parts, used height."""
    shelves, placed, unplaced, used_h = [], [], [], 0
    for p in sorted(parts, key=lambda p: -p["h"]):
        for s in shelves:
            if p["h"] <= s["h"] and s["x"] + p["w"] <= W:
                s["x"] += p["w"]; placed.append(p); break
        else:
            if p["w"] <= W and used_h + p["h"] <= H:
                shelves.append({"h": p["h"], "x": p["w"]}); used_h += p["h"]; placed.append(p)
            else:
                unplaced.append(p)
    return placed, unplaced, used_h

def remainder(W, H, used_h):
    r = (W, H - used_h)
    return r if r[0] * r[1] >= MIN_OFFCUT_AREA and min(r) >= MIN_DIM else None

def tonnes(area_mm2, t):
    return area_mm2 / 1e6 * (t / 1000) * DENS

def make_stream(rng, n_projects=60):
    stream = []
    for pid in range(n_projects):
        groups = []
        for _ in range(rng.randint(3, 6)):
            g, t = rng.choice(GRADES), rng.choice(THICK)
            parts = [{"w": rng.choice([200, 300, 450, 600, 900, 1200, 1500]),
                      "h": rng.choice([200, 300, 450, 600, 900, 1200, 1500])}
                     for _ in range(rng.randint(40, 160))]
            groups.append((g, t, parts))
        stream.append(groups)
    return stream

def run(stream, mode):
    register = []          # open offcuts: dict(g,t,w,h)
    virgin_area = {}       # per thickness for tonnage
    part_t = virgin_t = 0.0
    infeasible = 0
    for groups in stream:
        for g, t, parts in groups:
            part_t += sum(tonnes(p["w"] * p["h"], t) for p in parts)
            todo = list(parts)
            if mode == "baseline":    # whole job must fit on one offcut
                for oc in sorted([o for o in register if o["g"] == g and o["t"] == t],
                                 key=lambda o: o["w"] * o["h"]):
                    pl, un, uh = shelf_pack(todo, oc["w"], oc["h"])
                    if not un:
                        register.remove(oc)
                        r = remainder(oc["w"], oc["h"], uh)
                        if r: register.append({"g": g, "t": t, "w": r[0], "h": r[1]})
                        todo = []; break
            else:                     # matcher: fill any compatible offcut, partial OK
                while todo:
                    best = None
                    for oc in register:
                        if oc["g"] != g or oc["t"] != t: continue
                        pl, un, uh = shelf_pack(todo, oc["w"], oc["h"])
                        a = sum(p["w"] * p["h"] for p in pl)
                        if pl and (best is None or a > best[0]): best = (a, oc, pl, un, uh)
                    if not best: break
                    a, oc, pl, un, uh = best
                    if any(p["w"] > oc["w"] or p["h"] > oc["h"] for p in pl): infeasible += 1
                    register.remove(oc)
                    r = remainder(oc["w"], oc["h"], uh)
                    if r: register.append({"g": g, "t": t, "w": r[0], "h": r[1]})
                    todo = un
            while todo:               # virgin plates for what is left
                pl, un, uh = shelf_pack(todo, PW, PH)
                if not pl:            # part larger than a plate (cannot happen here)
                    break
                virgin_t += tonnes(PW * PH, t)
                r = remainder(PW, PH, uh)
                if r: register.append({"g": g, "t": t, "w": r[0], "h": r[1]})
                todo = un
    idle_t = sum(tonnes(o["w"] * o["h"], o["t"]) for o in register)
    waste = 1 - part_t / virgin_t
    return {"virgin_t": virgin_t, "parts_t": part_t, "waste_pct": waste * 100,
            "idle_offcut_t": idle_t, "infeasible": infeasible,
            "virgin_per_part": virgin_t / part_t}

if __name__ == "__main__":
    rows = []
    for seed in range(20):
        s = make_stream(random.Random(seed))
        b, m = run(s, "baseline"), run(s, "matcher")
        rows.append((b, m))
    bw = [b["waste_pct"] for b, _ in rows]; mw = [m["waste_pct"] for _, m in rows]
    diff = [x - y for x, y in zip(bw, mw)]
    print(f"Runs (synthetic 60-project streams): {len(rows)}")
    print(f"Baseline plate waste: mean {statistics.mean(bw):.1f}%  (min {min(bw):.1f}, max {max(bw):.1f})")
    print(f"Matcher  plate waste: mean {statistics.mean(mw):.1f}%  (min {min(mw):.1f}, max {max(mw):.1f})")
    print(f"Improvement (points): mean {statistics.mean(diff):.1f}  (min {min(diff):.1f}, max {max(diff):.1f})")
    print(f"Virgin plate per tonne of parts: baseline {statistics.mean(b['virgin_per_part'] for b,_ in rows):.3f} "
          f"-> matcher {statistics.mean(m['virgin_per_part'] for _,m in rows):.3f}")
    print(f"Infeasible suggestions (must be 0): {sum(m['infeasible'] for _, m in rows)}")
    print(f"Idle offcut stock left at end (t/run): baseline {statistics.mean(b['idle_offcut_t'] for b,_ in rows):.1f} "
          f"-> matcher {statistics.mean(m['idle_offcut_t'] for _,m in rows):.1f}")
    print("Gate 2 test (>=2 points better, 0 infeasible):",
          "PASS" if statistics.mean(diff) >= 2 and sum(m['infeasible'] for _, m in rows) == 0 else "FAIL")
