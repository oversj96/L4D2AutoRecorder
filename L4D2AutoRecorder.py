import psutil
import subprocess
import time
import zipfile
import os
import tkinter as tk
import logging
from pathlib import Path
from datetime import datetime
from tkinter import filedialog
from tkinter import messagebox

logging.basicConfig(
    filename="debug.log", 
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s"
    )

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
            if (path_to_exe == ''):
                logging.debug("Cancel selected, shutting down.")
                exit(0)
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

logging.debug("Path to exe was set to: {}".format(path_to_exe))
logging.debug("Path to l4d2 was set to: {}".format(path_to_l4d2))
logging.debug("Path to demos was set to: {}".format(path_to_demos))

if (not os.path.isdir(path_to_demos)):
    os.makedirs(path_to_demos)
    logging.debug("Path to demos did not exist. Path was created.")

autoexec_path = Path(path_to_l4d2 + "cfg/autoexec.cfg")
with open(autoexec_path, "a") as autoexec:
    autoexec.write("alias +showexec \"+showscores;"
                   + " exec L4D2AutoRecorder.cfg\"; alias -showexec"
                   + " \"-showscores\"; bind TAB +showexec")


subprocess.Popen("start steam://rungameid/550", shell=True)

logging.debug("attempted to start Left 4 Dead 2 via"
              + " 'start' steam id on the shell")

time.sleep(1)

pythons_psutil = []


def wrap_left4dead2_demos(p):
    zip_count = 0
    print("PLEASE DO NOT CLOSE THIS WINDOW UNLESS"
          + " IT HAS BEEN SOME TIME SINCE L4D2 HAS QUIT.")
    while (psutil.pid_exists(p.pid)):
        with open(
                path_to_exe
                + "left4dead2\cfg\L4D2AutoRecorder.cfg", "w") as cfg:
            cfg.write(
                "record demo_"
                + str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
            logging.debug("Wrote new time to l4d2 cfg.")
        time.sleep(1)
    today = str(datetime.now().strftime('%Y-%m-%d'))
    logging.debug("Today was set to: {}".format(today))
    file_list = os.listdir(path_to_l4d2)
    logging.debug("List of files in Left 4 Dead 2/left4dead2 directory:")
    for file in file_list:
        logging.debug("\t{}".format(file))

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
                    logging.debug("{} added to zip list.".format(file))
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

            # Found this nice piece of code for deleting the last
            # line in large files on stackoverflow. kudos to Saqib and co
            # This code is to remove the AutoRecorder command that was
            # appended to the end of the autoexec.cfg at startup
            logging.debug("Deleting progammatically added line from autoexec...")
            with open(autoexec_path, "r+") as file:
                file.seek(0, os.SEEK_END)
                pos = file.tell() - 1
                while pos > 0 and file.read(1) != "\n":
                    pos -= 1
                    file.seek(pos, os.SEEK_SET)
                if pos > 0:
                    file.seek(pos, os.SEEK_SET)
                    file.truncate()
            logging.debug("Line deleted.")
    except psutil.Error:
        pass
