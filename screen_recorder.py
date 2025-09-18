import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
import mss
import threading
import time
import os

# ===============================
# GLOBAL VARIABLES
# ===============================
recording = False
video_writer = None
start_time = None
FPS = 20
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# ===============================
# GET SCREEN DIMENSIONS
# ===============================
def get_screen_dimensions():
    """Get actual screen dimensions"""
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            return monitor["width"], monitor["height"]
    except:
        return 1920, 1080  # Fallback

# ===============================
# SCREEN RECORDING THREAD
# ===============================
def record_screen(output_path):
    global video_writer, recording, start_time, SCREEN_WIDTH, SCREEN_HEIGHT

    try:
        # Get actual screen dimensions
        SCREEN_WIDTH, SCREEN_HEIGHT = get_screen_dimensions()
        
        # Setup video writer (using MP4V codec)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = cv2.VideoWriter(output_path, fourcc, FPS, (SCREEN_WIDTH, SCREEN_HEIGHT))

        if not video_writer.isOpened():
            # Try different codec if mp4v doesn't work
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
            output_path = output_path.replace('.mp4', '.avi')
            video_writer = cv2.VideoWriter(output_path, fourcc, FPS, (SCREEN_WIDTH, SCREEN_HEIGHT))
            
        if not video_writer.isOpened():
            raise Exception("Could not initialize video writer")

        sct = mss.mss()
        monitor = {"top": 0, "left": 0, "width": SCREEN_WIDTH, "height": SCREEN_HEIGHT}

        start_time = time.time()
        frame_count = 0
        
        print(f"Recording started: {SCREEN_WIDTH}x{SCREEN_HEIGHT} at {FPS} FPS")
        
        while recording:
            try:
                # Capture screen
                img = np.array(sct.grab(monitor))
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                video_writer.write(frame)
                frame_count += 1
                
                # Update status every second
                elapsed = time.time() - start_time
                if frame_count % FPS == 0:  # Update every second
                    root.after(0, lambda e=elapsed: update_recording_status(e))
                
                # Control frame rate
                time.sleep(1/FPS)
                
            except Exception as e:
                print(f"Frame capture error: {e}")
                break

        # Cleanup
        video_writer.release()
        print(f"Recording finished. {frame_count} frames captured.")
        
        # Show completion message
        root.after(0, lambda: show_completion_message(output_path))

    except Exception as e:
        print(f"Recording error: {e}")
        messagebox.showerror("Recording Error", f"An error occurred during recording:\n{str(e)}")
        recording = False
        root.after(0, lambda: reset_ui())

def show_completion_message(output_path):
    """Show recording completion message"""
    reset_ui()
    messagebox.showinfo("Recording Complete", f"Video saved successfully!\n\nLocation: {output_path}\n\nNote: This version records video only (no audio)")

def update_recording_status(elapsed):
    """Update recording status display"""
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    status_label.config(text=f"🔴 Recording... {minutes:02d}:{seconds:02d}", fg="red")

def reset_ui():
    """Reset UI to initial state"""
    global recording
    recording = False
    status_label.config(text="🟢 Ready to Record", fg="green")
    start_btn.config(state="normal")
    stop_btn.config(state="disabled")

# ===============================
# START RECORDING
# ===============================
def start_recording():
    global recording
    
    if recording:
        messagebox.showwarning("Warning", "Recording is already in progress!")
        return
    
    # Get save location
    save_path = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4"), ("AVI files", "*.avi")],
        title="Save Recording As"
    )
    if not save_path:
        return

    # Test screen capture capability
    try:
        with mss.mss() as sct:
            test_shot = sct.grab({"top": 0, "left": 0, "width": 100, "height": 100})
            print("Screen capture test successful")
    except Exception as e:
        messagebox.showerror("Screen Capture Error", f"Cannot access screen:\n{str(e)}")
        return

    # Start recording
    recording = True
    start_btn.config(state="disabled")
    stop_btn.config(state="normal")
    status_label.config(text="🔴 Starting...", fg="orange")
    
    # Start recording thread
    recording_thread = threading.Thread(target=record_screen, args=(save_path,), daemon=True)
    recording_thread.start()

# ===============================
# STOP RECORDING
# ===============================
def stop_recording():
    global recording
    if recording:
        status_label.config(text="⏹️ Stopping...", fg="orange")
        recording = False

# ===============================
# SETTINGS WINDOW
# ===============================
def open_settings():
    global FPS
    
    settings_window = tk.Toplevel(root)
    settings_window.title("Recording Settings")
    settings_window.geometry("300x200")
    settings_window.resizable(False, False)
    settings_window.grab_set()
    
    # FPS Setting
    fps_label = tk.Label(settings_window, text="Frames Per Second (FPS):", font=("Arial", 10))
    fps_label.pack(pady=10)
    
    fps_var = tk.StringVar(value=str(FPS))
    fps_spinbox = tk.Spinbox(settings_window, from_=10, to=60, textvariable=fps_var, width=10)
    fps_spinbox.pack(pady=5)
    
    # Screen resolution info
    width, height = get_screen_dimensions()
    res_label = tk.Label(settings_window, text=f"Screen Resolution: {width} x {height}", font=("Arial", 9))
    res_label.pack(pady=10)
    
    def save_settings():
        global FPS
        try:
            new_fps = int(fps_var.get())
            if 10 <= new_fps <= 60:
                FPS = new_fps
                messagebox.showinfo("Settings", "Settings saved successfully!")
                settings_window.destroy()
            else:
                messagebox.showerror("Error", "FPS must be between 10 and 60")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid FPS value")
    
    save_btn = tk.Button(settings_window, text="Save Settings", command=save_settings, bg="blue", fg="white")
    save_btn.pack(pady=20)

# ===============================
# GUI CREATION
# ===============================
def create_gui():
    global root, status_label, start_btn, stop_btn
    
    root = tk.Tk()
    root.title("Screen Recorder")
    root.geometry("350x280")
    root.resizable(False, False)

    # Title
    title_label = tk.Label(root, text="🎥 Screen Recorder", font=("Arial", 16, "bold"))
    title_label.pack(pady=15)

    # Status
    status_label = tk.Label(root, text="🟢 Ready to Record", font=("Arial", 12), fg="green")
    status_label.pack(pady=5)

    # Info about capabilities
    info_text = "Records screen video only\n"
    info_label = tk.Label(root, text=info_text, font=("Arial", 9), fg="gray")
    info_label.pack(pady=5)

    # Buttons frame
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=15, padx=20, fill="x")

    start_btn = tk.Button(
        btn_frame, 
        text="🔴 Start Recording", 
        font=("Arial", 12), 
        bg="green", 
        fg="white", 
        command=start_recording,
        height=2
    )
    start_btn.pack(pady=5, fill="x")

    stop_btn = tk.Button(
        btn_frame, 
        text="⏹️ Stop Recording", 
        font=("Arial", 12), 
        bg="red", 
        fg="white", 
        command=stop_recording,
        state="disabled",
        height=2
    )
    stop_btn.pack(pady=5, fill="x")

    # Settings button
    settings_btn = tk.Button(
        btn_frame, 
        text="⚙️ Settings", 
        font=("Arial", 10), 
        bg="gray", 
        fg="white", 
        command=open_settings
    )
    settings_btn.pack(pady=5, fill="x")

    # Instructions
    instructions = "1. Click 'Start Recording'\n2. Choose save location\n3. Recording begins immediately\n4. Click 'Stop' when finished"
    instructions_label = tk.Label(root, text=instructions, font=("Arial", 9), justify="left")
    instructions_label.pack(pady=10)

    return root

# ===============================
# TEST DEPENDENCIES
# ===============================
def test_dependencies():
    """Test if required modules are available"""
    try:
        import cv2
        print(f"✓ OpenCV version: {cv2.__version__}")
    except ImportError:
        print("✗ OpenCV not found")
        return False
        
    try:
        import mss
        print("✓ MSS available")
    except ImportError:
        print("✗ MSS not found")
        return False
        
    try:
        import numpy
        print(f"✓ NumPy version: {numpy.__version__}")
    except ImportError:
        print("✗ NumPy not found")
        return False
        
    return True

# ===============================
# MAIN EXECUTION
# ===============================
if __name__ == "__main__":
    print("Simple Screen Recorder")
    print("=" * 30)
    
    if test_dependencies():
        print("✓ All required dependencies available")
        print("Starting GUI...")
        root = create_gui()
        root.mainloop()
    else:
        print("✗ Missing dependencies!")
        print("\nPlease install required packages:")
        print("pip install opencv-python mss numpy")
        input("Press Enter to exit...")