import tkinter as tk
from tkinter import filedialog
import subprocess
import threading


def browse_folder():
    folder_path = filedialog.askdirectory()
    download_folder_var.set(folder_path)


def start_extraction():
    leonardo_dir = download_folder_var.get()
    key = api_key_var.get()
    days = num_days_var.get()
    skip = skip_var.get()
    originals = originals_var.get()
    variants = variants_var.get()
    upscale = upscale_var.get()

    if leonardo_dir == "":
        leonardo_dir = "/Users/ecohen/Documents/LR/_All Leonardo"
    if days == "":
        days = 2
    if skip == "":
        skip = 0
    if originals == "":
        originals = True
    if variants == "":
        variants = True
    if upscale == "":
        upscale = True

    # Call the "2extraction.py" script with the given parameters
    cmd = ["python", "2extraction.py"]
    if leonardo_dir:
        cmd.append(f"--leonardo_dir={leonardo_dir}")
    if key:
        cmd.append(f"--key={key}")
    if days:
        cmd.append(f"--days={days}")
    if skip:
        cmd.append(f"--skip={skip}")
    if originals:
        cmd.append("--originals")
    if variants:
        cmd.append("--variants")
    if upscale:
        cmd.append("--upscale")

    cmd1 = " ".join(cmd)
    print(f'cmd: {cmd1}')

    process = subprocess.Popen(cmd1, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)

    def read_output():
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output_text.config(state=tk.NORMAL)
            output_text.insert(tk.END, line)
            output_text.config(state=tk.DISABLED)
            output_text.see(tk.END)  # Auto-scroll to the end
        process.stdout.close()

    output_thread = threading.Thread(target=read_output)
    output_thread.start()


# Function to resize the output window


def resize_output(event):
    output_text.config(width=(app.winfo_width() - 5))


# Create the main application window
app = tk.Tk()
app.title("Script Controller")

# Variables to hold user input
download_folder_var = tk.StringVar()
# Set the default value
download_folder_var.set("/Users/ecohen/Documents/LR/All_Leonardo")

api_key_var = tk.StringVar()
api_key_var.set("")

num_days_var = tk.IntVar()
num_days_var.set(2)

skip_var = tk.IntVar()
skip_var.set(0)

originals_var = tk.BooleanVar()
originals_var.set(True)

variants_var = tk.BooleanVar()
variants_var.set(True)

upscale_var = tk.BooleanVar()
upscale_var.set(True)


# Labels and Entry fields
tk.Label(app, text="Download Folder:").grid(row=0, column=0)
tk.Entry(app, textvariable=download_folder_var, width=40).grid(row=0, column=1)
tk.Button(app, text="Browse", command=browse_folder).grid(row=0, column=2)

tk.Label(app, text="API Key:").grid(row=1, column=0)
tk.Entry(app, textvariable=api_key_var).grid(row=1, column=1)

tk.Label(app, text="Number of Days:").grid(row=2, column=0)
tk.Entry(app, textvariable=num_days_var).grid(row=2, column=1)

tk.Label(app, text="Skip:").grid(row=3, column=0)
tk.Entry(app, textvariable=skip_var).grid(row=3, column=1)

tk.Checkbutton(app, text="Originals",
               variable=originals_var).grid(row=4, column=0)
tk.Checkbutton(app, text="Variants",
               variable=variants_var).grid(row=4, column=1)
tk.Checkbutton(app, text="Upscale", variable=upscale_var).grid(row=4, column=2)

# Start button
tk.Button(app, text="Start", command=start_extraction).grid(row=5, column=1)

# Output text field
output_text = tk.Text(app, wrap=tk.WORD, height=10,
                      width=(app.winfo_width() - 5))
output_text.grid(row=6, column=0, columnspan=3)
output_text.config(state=tk.DISABLED)


# Bind the resize function to the "<Configure>" event of the main window
app.bind("<Configure>", resize_output)

# Start the Tkinter event loop
app.mainloop()
