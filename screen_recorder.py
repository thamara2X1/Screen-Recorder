import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
import mss
import sounddevice as sd
import scipy.io.wavfile as wav
from moviepy.editor import VideoFileClip, AudioFileClip
import threading
import time
import os

# ===============================
# GLOBAL VARIABLES
# ===============================
recording = False
video_writer = None
audio_data = []
start_time = None
AUDIO_FILE = "temp_audio.wav"
VIDEO_FILE = "temp_video.avi"
FINAL_FILE = "screen_record.mp4"
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 20


# ===============================
# AUDIO CAPTURE
# ===============================
def audio_callback(indata, frames, time, status):
    if recording:
        audio_data.append(indata.copy())


# ===============================
# SCREEN RECORDING THREAD
# ===============================
def record_screen(output_path):
    global video_writer, recording, start_time

    # Start audio stream
    audio_data.clear()
    stream = sd.InputStream(samplerate=44100, channels=2, callback=audio_callback)
    stream.start()

    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    video_writer = cv2.VideoWriter(VIDEO_FILE, fourcc, FPS, (SCREEN_WIDTH, SCREEN_HEIGHT))

    sct = mss.mss()
    monitor = {"top": 0, "left": 0, "width": SCREEN_WIDTH, "height": SCREEN_HEIGHT}

    start_time = time.time()
    while recording:
        img = np.array(sct.grab(monitor))
        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        video_writer.write(frame)

    # Cleanup
    video_writer.release()
    stream.stop()
    stream.close()

    # Save audio
    if audio_data:
        audio_np = np.concatenate(audio_data, axis=0)
        wav.write(AUDIO_FILE, 44100, audio_np)

        # Merge video + audio
        video_clip = VideoFileClip(VIDEO_FILE)
        audio_clip = AudioFileClip(AUDIO_FILE)
        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(output_path, codec="libx264")

        # Clean temp files
        os.remove(AUDIO_FILE)
        os.remove(VIDEO_FILE)

    messagebox.showinfo("Done", f"Recording saved as:\n{output_path}")


# ===============================
# START RECORDING
# ===============================
def start_recording():
    global recording, save_path
    save_path = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4")],
        title="Save Recording As"
    )
    if not save_path:
        return

    recording = True
    threading.Thread(target=record_screen, args=(save_path,), daemon=True).start()
    status_label.config(text="🔴 Recording...", fg="red")


# ===============================
# STOP RECORDING
# ===============================
def stop_recording():
    global recording
    if recording:
        recording = False
        status_label.config(text="🟢 Idle", fg="green")


# ===============================
# TKINTER GUI
# ===============================
root = tk.Tk()
root.title("Screen Recorder")
root.geometry("300x180")
root.resizable(False, False)

title_label = tk.Label(root, text="🎥 Screen Recorder", font=("Arial", 14, "bold"))
title_label.pack(pady=10)

status_label = tk.Label(root, text="🟢 Idle", font=("Arial", 12), fg="green")
status_label.pack(pady=5)

start_btn = tk.Button(root, text="Start Recording", font=("Arial", 12), bg="green", fg="white", command=start_recording)
start_btn.pack(pady=5, fill="x", padx=20)

stop_btn = tk.Button(root, text="Stop Recording", font=("Arial", 12), bg="red", fg="white", command=stop_recording)
stop_btn.pack(pady=5, fill="x", padx=20)

root.mainloop()
