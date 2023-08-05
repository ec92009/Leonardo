import tkinter as tk    # https://docs.python.org/3/library/tkinter.html

from tkinter import filedialog
import concurrent.futures as cf


import EC_extraction


def browse_folder():
    folder_path = filedialog.askdirectory()
    download_folder_var.set(folder_path)


def stop_extraction():
    global process
    try:
        process.terminate()
    except Exception as e:
        pass


def start_extraction():
    leonardo_dir = download_folder_var.get()

    try:
        config = dotenv_values(".env")
        EC_EXTRACTION_KEY = config["LEO_KEY"]
        # print(f'using bearer key: from .env file')
    except Exception as e:
        pass

    key = api_key_var.get()
    if key != "":
        EC_EXTRACTION_KEY = key
        print(f'using bearer key: from command line')

    days = num_days_var.get()
    skip = skip_var.get()

    EC_EXTRACTION_ORIGINALS = originals_var.get()
    EC_EXTRACTION_VARIANTS = variants_var.get()
    EC_EXTRACTION_UPSCALES = upscale_var.get()

    with cf.ProcessPoolExecutor() as PPexecutor:
        with cf.ThreadPoolExecutor() as TPexecutor:
            f = TPexecutor.submit(EC_extraction.extract, days,
                                  leonardo_dir, skip, PPexecutor)
            print(f'f.result: {f.result()}')


# Function to resize the output window


def resize_output(event):
    output_text.config(width=(app.winfo_width() - 5))


# Create the main application window
app = tk.Tk()
app.title("Leonardo Companion")

# Variables to hold user input
download_folder_var = tk.StringVar()
# Set the default value
download_folder_var.set("/Users/ecohen/Documents/LR/_All Leonardo")

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
tk.Button(app, text="Start", command=start_extraction).grid(row=5, column=0)
# Stop button
tk.Button(app, text="Stop", command=stop_extraction).grid(row=5, column=2)

# Output text field
output_text = tk.Text(app, wrap=tk.WORD, height=10,
                      width=(app.winfo_width() - 5))
output_text.grid(row=6, column=0, columnspan=3)
output_text.config(state=tk.DISABLED)


# Bind the resize function to the "<Configure>" event of the main window
# app.bind("<Configure>", resize_output)

# Start the Tkinter event loop
app.mainloop()
