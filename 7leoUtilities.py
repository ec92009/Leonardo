import tkinter as tk
from tkinter import filedialog
import subprocess
import threading
import queue


def stop_execution():
    global stop_event
    stop_event.set()
    button_stop.config(state=tk.DISABLED)


def browse_directory():
    directory_path = filedialog.askdirectory()
    entry.delete(0, tk.END)
    entry.insert(tk.END, directory_path)


def clear_output_text():
    output_text.delete(1.0, tk.END)


def update_button_label():
    folder = entry.get()
    days = days_entry.get() or "2"
    generations = generations_entry.get() or "0"
    button_label = f"Start Extraction to folder {folder}, for the last {days} days, skipping the newest {generations} generations"
    button_start.config(text=button_label)


def perform_extraction():
    def execute_command():
        directory_path = entry.get()
        days = days_entry.get() or "2"
        generations = generations_entry.get() or "0"
        command = f"python -m 2extraction -l {directory_path} -d {days} -s {generations}"
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        while True:
            if stop_event.is_set():
                process.terminate()
                break

            line = process.stdout.readline()
            if not line:
                break
            # if line does not contain "Marker Scan"
            if "Marker scan hit" not in line:
                output_queue.put(line)

        process.communicate()

    def update_output_text():
        while True:
            line = output_queue.get()
            output_text.insert(tk.END, line)
            output_text.see(tk.END)
            output_text.update_idletasks()
            output_queue.task_done()

    global stop_event

    output_queue = queue.Queue()
    stop_event = threading.Event()

    # Create a separate thread for executing the command
    execution_thread = threading.Thread(target=execute_command)
    execution_thread.start()

    # Create a separate thread for updating the output text widget
    update_thread = threading.Thread(target=update_output_text)
    update_thread.daemon = True  # This will exit the thread when the main thread exits
    update_thread.start()

    # Enable the stop button
    button_stop.config(state=tk.NORMAL)


# Create the main window
window = tk.Tk()
window.title("Leonardo Companion")

# Create a label and an entry field for the directory path
label = tk.Label(window, text="Output Folder:")
label.pack()

entry_frame = tk.Frame(window)
entry_frame.pack(fill=tk.X, padx=10)

entry = tk.Entry(entry_frame)
entry.insert(tk.END, "./from_leonardo")  # Default value
entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

browse_button = tk.Button(entry_frame, text="...",
                          command=browse_directory, width=4)
browse_button.pack(side=tk.RIGHT)

# Create a frame for the number of days and generations to skip
options_frame = tk.Frame(window)
options_frame.pack(padx=10, pady=5, anchor=tk.W)

# Create an entry field to choose the number of days
days_label = tk.Label(options_frame, text="Number of Days:")
days_label.pack(side=tk.LEFT)

days_entry = tk.Entry(options_frame)
days_entry.insert(tk.END, "2")  # Default value
days_entry.pack(side=tk.LEFT, padx=5)
days_entry.bind("<KeyRelease>", lambda event: update_button_label())

# Create an entry field to choose the generations to skip
generations_label = tk.Label(options_frame, text="Generations to Skip:")
generations_label.pack(side=tk.LEFT)

generations_entry = tk.Entry(options_frame)
generations_entry.insert(tk.END, "0")  # Default value
generations_entry.pack(side=tk.LEFT, padx=5)
generations_entry.bind("<KeyRelease>", lambda event: update_button_label())

# Create a button to trigger the extraction
button_label = f"Start Extraction to folder {entry.get()}, for the last {days_entry.get() or '2'} days, skipping the newest {generations_entry.get() or '0'} generations"
button_start = tk.Button(window, text=button_label, command=perform_extraction)
button_start.pack(pady=10)

# Create a scrollable text widget to display the output
scrollbar = tk.Scrollbar(window)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

output_text = tk.Text(window, height=10, width=50,
                      yscrollcommand=scrollbar.set)
output_text.pack(fill=tk.BOTH, expand=True)

scrollbar.config(command=output_text.yview)

# Create a button to stop the execution
button_stop = tk.Button(window, text="Stop Execution",
                        command=stop_execution, state=tk.DISABLED)
button_stop.pack(pady=10)

# Create a button to clear the output
button_clear = tk.Button(window, text="Clear Output",
                         command=clear_output_text)
button_clear.pack(pady=5)

# Start the main event loop
window.mainloop()
