"""
.chart (Chorus / Clone Hero) -> Adobe Audition marker CSV, WITH LANES.

Marker label format:  N<index>_L<lanes>
  N12_L0    -> note #12, lane 0
  N13_L02   -> note #13, chord on lanes 0 and 2
UE reads the label via the MetaSound Wave Player's "Cue Point Label" output.

Usage:  python chart_to_markers.py notes.chart audition_markers.csv
"""
import csv
import re
import sys

# --- config ---
DIFFICULTY = "MediumSingle"     # EasySingle / MediumSingle / HardSingle / ExpertSingle
# Clone Hero frets: 0 green, 1 red, 2 yellow, 3 blue, 4 orange, 7 open. 5/6 = modifiers (ignored).
FRET_TO_LANE = {0: 0, 1: 1, 2: 2, 3: 3, 4: 3}   # orange folds into lane 3; open (7) dropped
MIN_GAP_SEC = 0.75 # drops notes closer than 0.75s apart           
# --------------

def section(content, name):
    m = re.search(r"\[" + name + r"\]\s*\{([^}]*)\}", content)
    if not m:
        raise SystemExit(f"FAIL: section [{name}] not found in chart")
    return m.group(1).splitlines()


def main(chart_path, out_path):
    content = open(chart_path, encoding="utf-8-sig", errors="ignore").read()

    res = int(re.search(r"Resolution\s*=\s*(\d+)", content).group(1))
    off = re.search(r"Offset\s*=\s*(-?[\d.]+)", content)
    offset = float(off.group(1)) if off else 0.0

    bpms = sorted(
        (int(m.group(1)), int(m.group(2)) / 1000.0)
        for line in section(content, "SyncTrack")
        if (m := re.match(r"\s*(\d+)\s*=\s*B\s+(\d+)", line))
    )
    if not bpms or bpms[0][0] != 0:
        raise SystemExit("FAIL: no BPM at tick 0 in [SyncTrack]")

    # tick -> set of lanes
    notes = {}
    for line in section(content, DIFFICULTY):
        m = re.match(r"\s*(\d+)\s*=\s*N\s+(\d+)", line)
        if m and int(m.group(2)) in FRET_TO_LANE:
            notes.setdefault(int(m.group(1)), set()).add(FRET_TO_LANE[int(m.group(2))])

    def tick_to_sec(t):
        sec, cur_tick, cur_bpm = 0.0, 0, bpms[0][1]
        for nt, nb in bpms[1:]:
            if t <= nt:
                break
            sec += (nt - cur_tick) / res * 60.0 / cur_bpm
            cur_tick, cur_bpm = nt, nb
        return sec + (t - cur_tick) / res * 60.0 / cur_bpm + offset

    rows, last = [], -1e9
    for tick in sorted(notes):
        sec = tick_to_sec(tick)
        if sec - last < MIN_GAP_SEC:
            continue
        last = sec
        lanes = "".join(str(l) for l in sorted(notes[tick]))
        rows.append([f"N{len(rows) + 1}_L{lanes}", f"{int(sec // 60):02d}:{sec % 60:06.3f}",
                     "00:00.000", "decimal", "cue", "Rhythm Target"])

    with open(out_path, "w", newline="\r\n", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["Name", "Start", "Duration", "Time Format", "Type", "Description"])
        w.writerows(rows)

    counts = [sum(str(l) in r[0].split("_L")[1] for r in rows) for l in range(4)]
    print(f"{len(rows)} markers -> {out_path} | notes per lane 0-3: {counts}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "notes.chart",
         sys.argv[2] if len(sys.argv) > 2 else "audition_markers.csv")