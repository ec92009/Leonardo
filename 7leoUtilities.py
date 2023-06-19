import tkinter as tk
from tkinter import filedialog
import subprocess


def perform_extraction():
    directory_path = entry.get()
    days = days_entry.get() or 2
    generations = generations_entry.get() or 0
    command = f"python -m 2extraction -l {directory_path} -d {days} -s {generations}"
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output_text.delete("1.0", tk.END)

    while True:
        line = process.stdout.readline()
        if not line:
            break
        output_text.insert(tk.END, line)
        output_text.see(tk.END)
        output_text.update_idletasks()

    process.communicate()


def browse_directory():
    directory_path = filedialog.askdirectory()
    entry.delete(0, tk.END)
    entry.insert(tk.END, directory_path)


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

# Create an entry field to choose the generations to skip
generations_label = tk.Label(options_frame, text="Generations to Skip:")
generations_label.pack(side=tk.LEFT)

generations_entry = tk.Entry(options_frame)
generations_entry.insert(tk.END, "0")  # Default value
generations_entry.pack(side=tk.LEFT, padx=5)

# Create a button to trigger the extraction
button_label = f"Start Extraction to folder {entry.get()}, for the last {days_entry.get()} days, skipping the newest {generations_entry.get()} generations"
button = tk.Button(window, text=button_label, command=perform_extraction)
button.pack(pady=10)

# Create a scrollable text widget to display the output
scrollbar = tk.Scrollbar(window)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

output_text = tk.Text(window, height=10, width=50,
                      yscrollcommand=scrollbar.set)
output_text.pack(fill=tk.BOTH, expand=True)

scrollbar.config(command=output_text.yview)

# Start the main event loop
window.mainloop()
