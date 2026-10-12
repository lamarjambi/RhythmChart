import librosa
import pandas as pd

# loading song
print("1/3 loading audio file...")

audio_path = "halloween1.wav"
y, sr = librosa.load(audio_path, sr=None)

# estimating bpm
print("2/3 analyzing beats and BPM...")

bpm, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
beat_times = librosa.frames_to_time(beat_frames, sr=sr)

# creating a table of times/lanes
print("3/3 creating CSV chart...")

rows = []
for i, t in enumerate(beat_times):
    lane = i % 4
    rows.append({"Name": str(i + 1), "Time": round(float(t), 3), "Lane": lane})

# saving as CSV for unreal
df = pd.DataFrame(rows)
df.to_csv("song_chart.csv", index=False)
print(f"Chart saved! Detected BPM: {bpm}")