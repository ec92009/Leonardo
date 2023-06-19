import tkinter as tk
from tkinter import filedialog
import subprocess


def list_directory():
    directory_path = entry.get()
    command = f"ls -l {directory_path}"
    result = subprocess.run(command, shell=True,
                            capture_output=True, text=True)
    output = result.stdout
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, output)


def browse_directory():
    directory_path = filedialog.askdirectory()
    entry.delete(0, tk.END)
    entry.insert(tk.END, directory_path)


# Create the main window
window = tk.Tk()
window.title("Directory Listing")

# Create a label and an entry field for the directory path
label = tk.Label(window, text="Directory Path:")
label.pack()

entry_frame = tk.Frame(window)
entry_frame.pack(fill=tk.X, padx=10)

entry = tk.Entry(entry_frame)
entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

browse_button = tk.Button(entry_frame, text="...",
                          command=browse_directory, width=4)
browse_button.pack(side=tk.RIGHT)

# Create a button to trigger the directory listing
button = tk.Button(window, text="List Directory", command=list_directory)
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
