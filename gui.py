import tkinter as tk
from tkinter import filedialog, ttk
import main  # Import the main module

def generate_keybinds():
    config_file_1 = entry1.get()
    account_path = entry2.get()
    region = region_var.get()
    print(f"Generating keybinds for {config_file_1}, using Account Path: {account_path}, and Region: {region}")

    main.main(config_file_1, account_path, region)

def browse_file(entry, filetype):
    file_selected = filedialog.askopenfilename(filetypes=[("Config Files", filetype)])
    entry.delete(0, tk.END)
    entry.insert(0, file_selected)

def browse_folder(entry):
    folder_selected = filedialog.askdirectory()
    entry.delete(0, tk.END)
    entry.insert(0, folder_selected)

# Initialize Tkinter window
root = tk.Tk()
root.title("Keybinds Config Generator")

# Label and Entry for first config file
label1 = tk.Label(root, text="Enter the path for the config.ini file:")
label1.pack()
entry1 = tk.Entry(root, width=50)
entry1.pack()
browse_button1 = tk.Button(root, text="Browse", command=lambda: browse_file(entry1, "*.ini"))
browse_button1.pack()

# Label and Entry for Account Path
label2 = tk.Label(root, text="Enter the Account Path:")
label2.pack()
entry2 = tk.Entry(root, width=50)
entry2.pack()
browse_button2 = tk.Button(root, text="Browse", command=lambda: browse_folder(entry2))
browse_button2.pack()

# Dropdown for selecting region (NA or EU)
label3 = tk.Label(root, text="Select Region:")
label3.pack()
region_var = tk.StringVar(value='EU')  # default value
region_dropdown = ttk.Combobox(root, textvariable=region_var, values=["NA", "EU"])
region_dropdown.pack()

# Button to generate keybinds
generate_button = tk.Button(root, text="Generate Keybinds", command=generate_keybinds)
generate_button.pack()

# Run the Tkinter event loop
root.mainloop()
