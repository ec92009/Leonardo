import tkinter as tk    # Import tkinter module for GUI
from tkinter import filedialog  # Import filedialog module for file dialog
import subprocess   # Import subprocess module to run shell commands


def list_directory():   # Function to list the directory
    directory_path = entry.get()    # Get the directory path
    command = f"ls -l {directory_path}"  # Create the command
    result = subprocess.run(command, shell=True,    # Run the command
                            capture_output=True, text=True)
    output = result.stdout  # Get the output
    output_text.delete("1.0", tk.END)       # Clear the text widget
    output_text.insert(tk.END, output)    # Insert the output


def browse_directory():    # Function to browse the directory
    directory_path = filedialog.askdirectory()  # Get the directory path
    entry.delete(0, tk.END)    # Clear the entry field
    entry.insert(tk.END, directory_path)    # Insert the directory path


# Create the main window
window = tk.Tk()
window.title("Directory Listing")

# Create a label and an entry field for the directory path
label = tk.Label(window, text="Directory Path:")
label.pack()

entry_frame = tk.Frame(window)  # Create a frame to hold the entry field
entry_frame.pack(fill=tk.X, padx=10)        # Pack the frame

entry = tk.Entry(entry_frame)       # Create the entry field
entry.pack(side=tk.LEFT, expand=True, fill=tk.X)        # Pack the entry field

browse_button = tk.Button(entry_frame, text="...",
                          command=browse_directory, width=4)        # Create a button to browse the directory
browse_button.pack(side=tk.RIGHT)    # Pack the button

# Create a button to trigger the directory listing
# Create a button to browse the directory
button = tk.Button(window, text="List Directory", command=list_directory)
button.pack(pady=10)    # Pack the button

# Create a scrollable text widget to display the output
scrollbar = tk.Scrollbar(window)        # Create a scrollbar
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)    # Pack the scrollbar

output_text = tk.Text(window, height=10, width=50,
                      yscrollcommand=scrollbar.set)   # Create a text widget
output_text.pack(fill=tk.BOTH, expand=True)   # Pack the text widget

scrollbar.config(command=output_text.yview)  # Configure the scrollbar

# Start the main event loop
window.mainloop()
