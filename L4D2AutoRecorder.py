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


def wrap_left4dead2_demos(p):
    """
    Automates writing new demo file names to a cfg and manages
    the demos after game exit.
    """
    print("PLEASE DO NOT CLOSE THIS WINDOW UNLESS"
          + " IT HAS BEEN SOME TIME SINCE L4D2 HAS QUIT.")

    while (psutil.pid_exists(p.pid)):
        with open(path_to_record_cfg, "w") as cfg:
            stamp = str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
            cfg.write("record demo_{}".format(stamp))
            logging.debug("Wrote time \"{}\" to l4d2 cfg.".format(stamp))
            last_write = 0.25
            cfg.close()
            time.sleep(2)


def shutdown_recorder(status, message="", show=False):
    """
    The primary method of exiting the application if
    needed by user or caused by an unexpected error.
    """
    if (message is not ""):
        logging.debug(("Recorder was shut down with status: {}. "
                       + "\"{}\"").format(status, message))
    else:
        logging.debug("Recorder was shut down with status: {}".format(status))

    if (show):
        messagebox.showerror("Error", "{}".format(message))

    os._exit(status)


def move_and_archive(verbose=False):
    """
    Tells the AutoRecorder to look for demo files and to
    move them to their respective zip folders inside the demos
    directory.
    """
    zip_count = 0
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
            if (verbose):
                messagebox.showinfo(
                    "Demo Management", str(zip_count)
                    + " files were recorded and zipped\n"
                    + "to \"" + path_to_demos + "\".")


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
                shutdown_recorder(0, "Cancel selected on filedialog")
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
path_to_record_cfg = path_to_l4d2 + "cfg/L4D2AutoRecorder.cfg"

logging.debug("Path to exe was set to: {}".format(path_to_exe))
logging.debug("Path to l4d2 was set to: {}".format(path_to_l4d2))
logging.debug("Path to demos was set to: {}".format(path_to_demos))

if (not os.path.isdir(path_to_demos)):
    os.makedirs(path_to_demos)
    logging.debug("Path to demos did not exist. Path was created.")

autoexec_path = Path(path_to_l4d2 + "cfg/autoexec.cfg")

# Check if AutoRecorder failed to close correctly and left old demos
flag_path = Path("__autorecorder_flag")
if (os.path.isfile(flag_path)):
    logging.debug(
        "L4D2AutoRecorder did not shut down correctly.")
    move_and_archive()
else:
    with open(flag_path, "w") as flag:
        logging.debug("Startup flag successfully created.")

cfg_command = "alias +showexec \"+showscores;" + \
    " exec L4D2AutoRecorder.cfg\"; alias -showexec" + \
    " \"-showscores\"; bind TAB +showexec;"

# The whole point of this block is to make sure
# the cfg command is the last line in the autoexec
exec_temp = []
with open(autoexec_path, "r") as autoexec:
    for line in autoexec:
        if (line.strip('\n') != cfg_command):
            exec_temp.append(line.rstrip('\n'))
    exec_temp.append(cfg_command)
with open(autoexec_path, "w") as autoexec:
    for line in exec_temp:
        autoexec.write("{}\n".format(line))

subprocess.Popen("start steam://rungameid/550", shell=True)

logging.debug("attempted to start Left 4 Dead 2 via"
              + " 'start' steam id on the shell")

time.sleep(5)
detected = False
pythons_psutil = []

for p in psutil.process_iter():
    try:
        if p.name() == 'left4dead2.exe':
            detected = True
            wrap_left4dead2_demos(p)
            move_and_archive(True)
    except psutil.Error:
        pass

logging.debug(
    "Deleting progammatically added line from autoexec...")

with open(autoexec_path, "r") as file:
    lines = file.readlines()
    lines = lines[:-1]
with open(autoexec_path, "w") as file:
    for line in lines:
        file.write(line)

logging.debug("Line deleted.")

os.remove("__autorecorder_flag")
logging.debug("Startup flag was successfully removed.")

if (not detected):
    shutdown_recorder(
        1,
        "Did not detect the left4dead2.exe process. Shutting Down.",
        True
    )
