import socket, ast, os, queue, threading, time, logging, random
import heapq
import numpy as np
import speech_recognition as sr
import pygame
import sys
from contextlib import AbstractContextManager
from pathplanner import PathPlanner

MAP_HEIGHT = 3069
MAP_WIDTH = 2640
IMAGE_PATH = "golisano3v5.png"
SPEED = 3.0

class Robot(AbstractContextManager):
    def __init__(self, x, y):
        self._is_traveling = False
        self._block_queue = queue.Queue()
        self._nonblock_queue = queue.Queue()
        
        self.dest_name = "N/A"
        self.dest_pos = "N/A"
        self._running_program = True 
        
        self.x, self.y = float(x), float(y)
        self.speed = SPEED
        self.path = []
        
        # 1. Initialize Pygame core first
        pygame.init()
        
        # 2. STEP 1: Set a temporary or expected window size FIRST so a "video mode" exists
        # Since we know your map dimensions are 2640x3069, we set it here.
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Robot Simulator")
        self.clock = pygame.time.Clock()
        
        # 3. STEP 2: NOW you can safely load and convert the image without crashing
        try:
            absolute_path = os.path.join(os.path.dirname(__file__), IMAGE_PATH) if '__file__' in locals() else IMAGE_PATH
            raw_image = pygame.image.load(absolute_path)
            self.map_background = raw_image.convert() # <-- This will no longer fail!
            print("🗺️ Map loaded successfully on Main Thread!")
            
            # Update width/height to match actual image dimensions just in case
            self.width, self.height = self.map_background.get_size()
        except pygame.error as e:
            print(f"❌ Pygame failed to load image: {e}")        
            os._exit(1)
            
        print("⚙️ Generating costmap...")
        self.planner = PathPlanner(self.map_background)
        print("✅ Costmap ready!")

        # --- SPIN UP YOUR BACKGROUND THREADS ---
        self._main_thread = threading.Thread(target=self.run_program, daemon=True)
        self._main_thread.start()
        
        self._nonblock_thread = threading.Thread(target=self.queue_executor, daemon=True)
        self._nonblock_thread.start()

    def request_path(self, target_x, target_y):
        """Plans path using the pathplanner class without blocking background threads."""
        print(f"Planning path from ({self.x}, {self.y}) to ({target_x}, {target_y})...")
        calculated_path = self.planner.plan_path((self.x, self.y), (target_x, target_y), tolerance=self.speed)
        
        if calculated_path:
            self.path = calculated_path
            self._is_traveling = True
            print("🚀 Path successfully found!")
        else:
            print("❌ Failed to find a valid path.")
            self._is_traveling = False

    def go_to(self, x, y):
        """Blocks the background worker thread until destination arrival."""
        self.request_path(x, y)
        
        while self._is_traveling and len(self.path) > 0:
            target = self.path[0]
            dx = target[0] - self.x
            dy = target[1] - self.y
            distance = np.hypot(dx, dy)

            if distance <= self.speed:
                self.x, self.y = float(target[0]), float(target[1])
                self.path.pop(0)
            else:
                self.x += (dx / distance) * self.speed
                self.y += (dy / distance) * self.speed
            
            # Match simulation tick delay
            time.sleep(0.015) 
        
        self._is_traveling = False

    def refresh_window(self):
        """Processes OS display window events and renders canvas."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running_program = False
                pygame.quit()
                sys.exit()

        # Render pipeline
        self.screen.blit(self.map_background, (0, 0))                              
        pygame.draw.circle(self.screen, (0, 255, 100), (int(self.x), int(self.y)), 15)  
        pygame.draw.circle(self.screen, (0, 180, 70), (int(self.x), int(self.y)), 15, 2) 
        
        pygame.display.flip()
        self.clock.tick(60) 

    def run_program(self):
        """Your background script logic container."""
        print("🤖 Background execution sequence started...")
        time.sleep(2)
        
        # Test structural path execution sequence
        self.go_to(1110, 1270)
        print("Reached target")
    
    def queue_executor(self):
        """Your background queue logic worker loop."""
        while self._running_program:
            time.sleep(1)
    
    def start_sim_loop(self):
        """Keeps the Main Thread processing UI window refreshes persistently."""
        while self._running_program:
            self.refresh_window()
        
    def __exit__(self, exc_type, exc_value, traceback):
        self._running_program = False

if __name__ == "__main__":
    # 1. Main thread initializes the robot object and components safely
    r = Robot(1225.0, 815.0)
    
    # 2. Main thread enters the persistent screen rendering loop
    r.start_sim_loop()