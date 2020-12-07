import time
from threading import Thread

class SimpleScheduler(Thread):
  def __init__(self, func, interval):
    Thread.__init__(self, target=self._loop)

    self._running = True

    self._func = func
    self._interval = interval
    

  def _loop(self):
    while self._running:
      before_func = time.time()

      self._func()
      
      # calculate time till next interval
      elapsed = (time.time() - before_func) * 1000.0
      sleep_time = (self._interval - (elapsed % self._interval)) / 1000.0      
      time.sleep(sleep_time)
  
    
  def stop(self):
    self._running = False


import psutil

class SysUtilLogger():
  def __init__(self, interval):
    self._measurements = []
    self._scheduler = SimpleScheduler(self._log_sys_util, interval)

  def mem_now(self):
    return psutil.virtual_memory().used

  def _log_sys_util(self):
    # memory usage
    mem_used = psutil.virtual_memory().used
    cpu_util = psutil.cpu_percent(percpu=True)

    self._measurements.append((mem_used, cpu_util))

  def start(self):
    self._scheduler.start()

  def stop(self) -> list():
    self._scheduler.stop()
    return self._measurements
