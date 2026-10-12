import os
import re
import csv

# --- config stuff ---
chart_file = "notes.chart"  
output_csv = "audition_markers.csv"
# ---------------------

def parse_chart_to_markers(chart_path, output_path):
    if not os.path.exists(chart_path):
        print(f"uh oh: couldnt find '{chart_path}' in this folder.")
        return

    resolution = 192  # fallback default resolution
    bpm_changes = []  # stores (tick, bpm) pairs
    note_ticks = set() # handles unique note spots

    # read the chart text
    with open(chart_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # find the chart resolution value
    res_match = re.search(r"Resolution\s*=\s*(\d+)", content)
    if res_match:
        resolution = int(res_match.group(1))

    # parse bpm changes out of synctrack
    sync_section = re.search(r"\[SyncTrack\]\s*\{([^}]+)\}", content)
    if sync_section:
        for line in sync_section.group(1).split("\n"):
            line = line.strip()
            # searching for something like tick = B bpm
            bpm_match = re.match(r"(\d+)\s*=\s*B\s*(\d+)", line)
            if bpm_match:
                tick = int(bpm_match.group(1))
                # divide by 1000 because charts format it big
                bpm = int(bpm_match.group(2)) / 1000.0 
                bpm_changes.append((tick, bpm))
    
    # sort the bpm updates by tick order
    bpm_changes.sort(key=lambda x: x[0])
    if not bpm_changes:
        bpm_changes.append((0, 120.0)) # safe fallback 

    # grab expert notes for player interactions
    expert_section = re.search(r"\[ExpertSingle\]\s*\{([^}]+)\}", content)
    if expert_section:
        for line in expert_section.group(1).split("\n"):
            line = line.strip()
            # searching for tick = N note_id length
            note_match = re.match(r"(\d+)\s*=\s*N\s*(\d+)", line)
            if note_match:
                note_ticks.add(int(note_match.group(1)))

    # math out ticks to seconds with bpm changes
    note_ticks = sorted(list(note_ticks))
    timestamps_seconds = []

    for target_tick in note_ticks:
        current_time = 0.0
        current_tick = 0
        current_bpm = bpm_changes[0][1]

        # cycle through bpm changes to track time elapsed
        for next_tick, next_bpm in bpm_changes[1:]:
            if target_tick <= next_tick:
                break
            delta_ticks = next_tick - current_tick
            current_time += (delta_ticks / resolution) * (60.0 / current_bpm)
            current_tick = next_tick
            current_bpm = next_bpm

        # add remaining ticks from final bpm change to the note
        delta_ticks = target_tick - current_tick
        current_time += (delta_ticks / resolution) * (60.0 / current_bpm)
        timestamps_seconds.append(current_time)

    # map out format audition needs
    headers = ["Name", "Start", "Duration", "Time Format", "Type", "Description"]
    audition_markers = []

    for i, sec in enumerate(timestamps_seconds):
        minutes = int(sec // 60)
        seconds = sec % 60
        time_string = f"{minutes:02d}:{seconds:06.3f}"
        
        audition_markers.append([
            f"Interact_Node_{i+1}", # cue point name for ue5 blueprint
            time_string,           
            "00:00.000",           
            "Decimal",             
            "Cue",                 
            "Rhythm Target"        
        ])

    # save as tab-delimited file so audition reads it right
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t") 
        writer.writerow(headers)
        writer.writerows(audition_markers)

    print(f"done! converted '{chart_path}' into '{output_path}'")
    print(f"made {len(audition_markers)} interactive notes total.")

# run everything
parse_chart_to_markers(chart_file, output_csv)
