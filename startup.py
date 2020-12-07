import subprocess
import time
import os
import signal
import sys
import time
import psutil

def launch_emulator():
  print("launching emulator")
  # disable snapshots with:
  #  -no-snapshot
  proc = subprocess.Popen(["/home/jannik/Android/Sdk/emulator/emulator -avd nexus"], shell=True)
  return proc


def launch_anbox():
  print("launching anbox")

  smgr = subprocess.Popen(["/home/jannik/Workspace/anbox-work/anbox/build/src/anbox session-manager"], shell=True)
  return smgr


def launch_adb():
  # start logcat with all buffers
  adb_proc = subprocess.Popen(["adb", "logcat", "-b all", "-v usec"], stdout=subprocess.PIPE)
  return adb_proc

def scan_adb(adb_stdout):
  result = {}
  result["begin"] = time.time()

  for line in iter(adb_stdout.readline,''):
    if "sysui_histogram: [framework_boot_completed," in str(line):
      result["boot_completed"] = time.time()
      break

  return result


# wait x seconds before and after testing
# to measure idle
measure_buffer = 5

test_emulator = False
if len(sys.argv) > 1 and sys.argv[1] == "emu":
  test_emulator = True


# launch adb
adb_proc = launch_adb()

# start system utilization logger
from systemlog import SysUtilLogger
util_logger = SysUtilLogger(1000)
util_logger.start()


# wait a few seconds to see utilization effect
time.sleep(measure_buffer)


# start emulator or anbox
if test_emulator:
  tested_proc = launch_emulator() 
else:
  tested_proc = launch_anbox()


# scan adb messages until boot_completed
adb_times = scan_adb(adb_proc.stdout)
mem_at_boot_complete = util_logger.mem_now()

# wait to capture more util data
time.sleep(measure_buffer)


sys_util = util_logger.stop()


# filename is startup_emulator_1234567890.txt
log_filename = ("emu" if test_emulator else "anb") + "_" + time.strftime("%H_%M_%S") + ".json"
log_filepath = os.path.dirname(os.path.realpath(__file__)) + "/measurements/" + log_filename

startup_duration = int(round((adb_times["boot_completed"] - adb_times["begin"]) * 1000))
mem_ticks = [data[0] for data in sys_util]
theads_ticks = [data[1] for data in sys_util]

log_item = {
  "boot_time": startup_duration,
  "mem_util": [tick / 1024 / 1024 for tick in mem_ticks],
  "mem_at_boot_complete": mem_at_boot_complete / 1024 / 1024,
  # matrix transpose thread ticks
  #   (vc0, vc1, vc2, vc3, ...) ---> (vc0, vc0, vc0, vc0, ...)
  "cpu_util": list(zip(*theads_ticks)),
}

import json
with open(log_filepath, "w") as file:
  json.dump(log_item, file)



print("close please")
time.sleep(10)

# kill processes
os.killpg(os.getpgid(adb_proc.pid), signal.SIGKILL)
os.killpg(os.getpgid(tested_proc.pid), signal.SIGKILL)



print("done")