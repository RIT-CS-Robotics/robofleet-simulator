import socket, ast, os, queue, threading, time, logging
import numpy as np
from contextlib import AbstractContextManager

    """
    Pure simulator version of robot.py
    """
class Robot(AbstractContextManager):
    def __init__(self):
        self._is_traveling = False
        self._block_queue = queue.Queue()
        self._nonblock_queue = queue.Queue()
        
        self.dest_name = "N/A"
        self.dest_pos = "N/A"
        self._running_program = False
        
        self._main_thread = threading.Thread(target=self.run_program, daemon=True)
        self._main_thread.start()
        self._nonblock_thread = threading.Thread(target=self.queue_executor, daemon=True)
        self._nonblock_thread.start()

    def get_pos(self):
        pass
    
    def move(self, metres):
        pass
    
    def rotate(self, degrees):
        pass
    
    def move_to(self, metres):
        pass
    
    def nav_to(self, location):
        pass
    
    def go_to(self, location):
        pass
    
    def halt(self):
        pass
    
    def speak(self, msg):
        pass
    
    def listen(self, wait_timeout=10, talk_timeout=10):
        pass
    
    def get_legs(self):
        pass
    
    def get_laser_scan(self):
        pass
    
    def get_object_scan(self):
        pass
    
    def objects_seen(self):
        pass
    
    def scan_for(self):
        pass
    
    def main_thread(self):
        while self._running_program:
            pass
    
    def queue_executor(self):
        while self._running_program:
            pass
        
    def __exit__(self, exc_type, exc_value, traceback):
        while self._is_traveling:
            time.sleep(0.1)  
        self._running_program = False
        time.sleep(0.1)
        return