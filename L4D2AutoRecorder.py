import psutil
import subprocess
import time
import zipfile
import os
import tkinter as tk
from pathlib import Path
from datetime import datetime
from tkinter import filedialog
from tkinter import messagebox

root = tk.Tk()
root.withdraw()
need_path = True

while need_path:
    try:
        settings = Path("pathinfo.txt")
        my_abs_path = settings.resolve(strict=True)
    except FileNotFoundError:
        path_to_exe = filedialog.askopenfilename(
            title="Please select your Left 4 Dead 2 .exe file",
            filetypes=[("executable files", "*.exe")])
        if(path_to_exe.endswith("left4dead2.exe")):
            path_to_exe = path_to_exe[:-14]
            with open("pathinfo.txt", "w") as path:
                path.write(path_to_exe)
                need_path = False
        else:
            messagebox.showerror(
                "Invalid File",
                "The file selected was incorrect. Try again.")
            continue
    else:
        with open("pathinfo.txt", "r") as path:
            path_to_exe = path.read()
            need_path = False

path_to_l4d2 = path_to_exe + "left4dead2/"
path_to_demos = path_to_l4d2 + "demos/"

if (not os.path.isdir(path_to_demos)):
    os.makedirs(path_to_demos)

try:
    autoexec_path = Path(path_to_l4d2 + "cfg/autoexec.cfg")
    my_abs_path = autoexec_path.resolve(strict=True)
except FileNotFoundError:
    messagebox.showerror(
        "File Not Found",
        "Could not find \"" + path_to_l4d2 + "cfg/autoexec.cfg\"."
        + " Please verify left 4 dead 2 game files.")
    exit(1)
else:
    with open(autoexec_path, "a") as autoexec:
        autoexec.write("alias +showexec \"+showscores;"
                       + " exec L4D2AutoRecorder.cfg\"; alias -showexec"
                       + " \"-showscores\"; bind TAB +showexec")


subprocess.Popen("start steam://rungameid/550", shell=True)

time.sleep(5)

pythons_psutil = []


def wrap_left4dead2_demos(p):
    zip_count = 0
    print("Waiting to see if left4dead2.exe still exists...")
    while (psutil.pid_exists(p.pid)):
        with open(
                path_to_exe
                + "left4dead2\cfg\L4D2AutoRecorder.cfg", "w") as cfg:
            cfg.write(
                "record demo_"
                + str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
        time.sleep(20)      
    today = str(datetime.now().strftime('%Y-%m-%d'))
    file_list = os.listdir(path_to_l4d2)

    if len(file_list):
        zipfile_list = []
        for file in file_list:
            if file.lower().endswith(".dem") & \
               file.lower().startswith("demo"):
                file_no_dem = file[:-4]
                strings = file_no_dem.split("_")
                date = strings[1]
                if (date == today):
                    zipfile_list.append(file)
        if len(zipfile_list):
            with zipfile.ZipFile(
                    path_to_demos
                    + today
                    + ".zip", "a", zipfile.ZIP_DEFLATED) as myzip:
                for zfile in zipfile_list:
                    myzip.write(path_to_l4d2 + zfile, zfile)
                    os.remove(path_to_l4d2 + zfile)
                    zip_count += 1
                    
    messagebox.showinfo(
        "Demo Management", str(zip_count)
        + " files were recorded and zipped\n"
        + "to \"" + path_to_demos + "\".")


for p in psutil.process_iter():
    try:
        if p.name() == 'left4dead2.exe':
            wrap_left4dead2_demos(p)

            # Found this nice piece of code of deleting the last
            # line in large files on stackoverflow. kudos to Saqib
            # This code is to remove the AutoRecorder command that was
            # appended to the end of the autoexec.cfg at startup
            with open(autoexec_path, "r+") as file:
                file.seek(0, os.SEEK_END)
                pos = file.tell() - 1
                while pos > 0 and file.read(1) != "\n":
                    pos -= 1
                    file.seek(pos, os.SEEK_SET)
                if pos > 0:
                    file.seek(pos, os.SEEK_SET)
                    file.truncate()

    except psutil.Error:
        pass
