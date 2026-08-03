import socket, ast, os, queue, threading, time, logging, random
import heapq

import numpy as np
import speech_recognition as sr
import pygame

from contextlib import AbstractContextManager
from pathplanner import PathPlanner

"""
Pure simulator version of robot.py
"""

SCALE_FACTOR = 1
MAP_HEIGHT = 3069 * SCALE_FACTOR
MAP_WIDTH = 2640 * SCALE_FACTOR

SPEED = 5.0
IMAGE_PATH = "data/golisano3v5.png"
POINTS_FILE = "data/point_database.txt"

START_X = 1228.0 * SCALE_FACTOR
START_Y = 815.0 * SCALE_FACTOR

VOICE_LIB = ['en-gb-scotland', 'en-gb-x-gbclan', 'en-gb-x-rp', 'en-us']
SPEAK_RATE = 175
BANNED_WORDS = "data/banned.txt"

SONG_FILE = "data/songs.txt"

IMAGE_FILE = "data/images.txt"
FACE_FILE = "data/recognizer_out.txt"
COCO_FILE = "data/coco_out.txt"
IMG_HEIGHT = 480
IMG_WIDTH = 640

MAX_LEGS = 50

class Robot(AbstractContextManager):
    def __init__(self, degrees):
        self._is_traveling = False
        self._block_queue = queue.Queue()
        self._nonblock_queue = queue.Queue()
        
        self.dest_name = "N/A"
        self.dest_pos = "N/A"
        
        self._running_program = True 
        
        self.x, self.y = float(START_X), float(START_Y)
        self.degrees = float(degrees)
        self.speed = SPEED
        self.path = []
        
        # banned words
        self._banned_words = set()
        with open(BANNED_WORDS) as file:
            for line in file:
                self._banned_words.add(line.strip())
           
        # songs
        self._songs = []
        with open(SONG_FILE) as file:
            for line in file:
                self._songs.append(line.strip())
                
        # image library (simulator only)
        self._images = []
        with open(IMAGE_FILE) as file:
            for line in file:
                self._images.append(line.strip())
        
        # object recognizer (fake: simulator only)
        self._coco = []
        with open(COCO_FILE) as file:
            for line in file:
                info = ast.literal_eval(line.strip())
                self._coco.append(info)
                
        # face recognizer (fake: simulator only)
        self._recognizer = []
        with open(FACE_FILE) as file:
                info = ast.literal_eval(line.strip())
                self._coco.append(info)

        # pygame: running on main thread
        pygame.init()
        self.screen = pygame.display.set_mode((MAP_WIDTH, MAP_HEIGHT))
        try:
            raw_image = pygame.image.load(IMAGE_PATH)
            self.map_background = raw_image.convert()
        except pygame.error as e:
            print(f"Failed to load map image: {IMAGE_PATH}, {e}")        
            os._exit(1)
            
        self.width, self.height = self.map_background.get_size()
        pygame.display.set_caption("Robot Simulator")
        self.clock = pygame.time.Clock()
        self.planner = PathPlanner(self.map_background)

        # movement thread setup
        self._movement_queue = queue.Queue()
        self._movement_thread = threading.Thread(target=self._queue_executor, daemon=True)
        self._movement_thread.start()

        # threads
        self._main_thread = threading.Thread(target=self.run_program, daemon=True)
        self._main_thread.start()

    # --- POSITION AND DESTINATION GETTERS ---

    def get_pos(self):
        """
        Get the current position (x, y) of the robot.
        """
        return self.x, self.y

    def get_dest_name(self):
        """
        Return the current destination name of the robot, or "N/A".
        """
        return self.dest_name

    def get_dest_pos(self):
        """
        Return the current destination coordinates of the robot, or None.
        """
        return self.dest_pos

    def is_traveling(self):
        """
        Returns whether the robot is currently executing a movement task.
        """
        return self._is_traveling or not self._movement_queue.empty()
    
    # -- MOVEMENT --
    
    def rotate(self, degrees, wait=True):
        """
        Rotate the robot by {degrees}.
        """
        if wait:
            self._movement_queue.put(("rotate", (degrees,)))
            self._movement_queue.join()
        else:
            self._movement_queue.put(("rotate", (degrees,)))

    def _execute_rotate(self, degrees):
        """
        Internal execution logic for rotation over time.
        """
        target_heading = (self.degrees + degrees) % 360.0
        step = 2.0 if degrees > 0 else -2.0
        total_steps = int(abs(degrees) / abs(step))

        for _ in range(total_steps):
            if not self._running_program:
                break
            self.degrees = (self.degrees + step) % 360.0
            time.sleep(0.016)
            
    def go_to(self, x, y, wait=True):
        """
        Go to (x, y) location, if valid.
        
        if wait:
            self._movement_queue.put(("go_to", (x,y)))
            self._movement_queue.join()
        else:
            self._movement_queue.put(("go_to", (x,y)))
        """
        self._is_traveling = True
        self._movement_queue.put(("go_to", (x, y)))
    
        if wait:
            # Main thread handles Pygame updates while waiting
            while self._is_traveling or not self._movement_queue.empty():
                self.refresh_window()
                time.sleep(0.01)

    def _execute_go_to(self, x, y):
        """
        Internal synchronous movement logic executed inside the movement thread.
        """
        self.path = self.planner.a_star_path((self.x, self.y), (x, y))
        
        if not self.path:
            print("FAILED: No path found.")
            return
        
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

            time.sleep(0.016)
        
        self._is_traveling = False

    def move(self, metres, wait=True):
        """
        Move 
        """
        if wait:
            self._movement_queue.put(("move", (metres,)))
            self._movement_queue.join()
        else:
            self._movement_queue.put(("move", (metres,)))

    def _execute_move(self, metres):
        pass

    
    def move_to(self, metres, wait=True):
        if wait:
            self._movement_queue.put(("go_to", (x,y)))
            self._movement_queue.join()
        else:
            self._movement_queue.put(("go_to", (x,y)))

    def _execute_move_to(self, metres):
        pass
    
    def nav_to(self, location, wait=True):
        if wait:
            self._movement_queue.put(("go_to", (x,y)))
            self._movement_queue.join()
        else:
            self._movement_queue.put(("go_to", (x,y)))

    def _execute_nav_to(self, location):
        pass

    def request_path(self, target_x, target_y):
        """
        Attempt to get a path to target coordinates.
        """
        print(f"Planning path from ({self.x}, {self.y}) to ({target_x}, {target_y})...")
        self.dest_pos = (target_x, target_y)
        
        # get path
        calculated_path = self.planner.a_star_path((self.x, self.y), (target_x, target_y), tolerance=self.speed)
        
        if calculated_path:
            self.path = calculated_path
            self._is_traveling = True
            print("Path successfully found!")
        else:
            self.dest_pos = None
            print("Failed to find a valid path or destination is blocked.")
        
    def halt(self):
        """
        Clear movement queue and halt current travel.
        """
        while not self._movement_queue.empty():
            try:
                self._movement_queue.get_nowait()
                self._movement_queue.task_done()
            except queue.Empty:
                break
        self._is_traveling = False
        self.dest_name = "N/A"
        self.dest_pos = None
        
        
    # -- BLOCKING COMMANDS: SPEECH AND AUDIO --
    # -- (just print)
    
    def speak(self, msg, vc=1):
        message = msg
        for word in self._banned_words:
            if word in message:
                return "ERROR: message contains banned word(s)."

        # would normally be the type of voice, doesn't do anything in simulation
        if vc < 0:
            return "ERROR: invalid voice type"
        elif vc > 3:
            vc = 3
            print("WARNING: voice libarary only goes up to index 3. Using voice at index 3.")
                
        voice = VOICE_LIB[vc]
        # CHANGE TO "SHOW"
        print(f"{voice}: robot says {message}.")
        # add a time.sleep to simulate block
    
    def listen(self, wait_timeout=10, talk_timeout=10):
        """
        Listen until person stops talking, or the wait/phrase timeout occurs
        and return text heard. 
        """
        mic = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                mic.adjust_for_ambient_noise(source, duration=1)
                audio = mic.listen(source)
                print("Listening...")
                text = mic.recognize_google(audio)
                text = text.lower()
        finally:
            pass
        return text
    
    def listen_until(self, phrases, listen_timeout=10, phrase_timeout=10):
        """
        Listen until one of the specified phrases is detected.
        """
        mic = sr.Recognizer()
        while self._running_program:
            try:
                with sr.Microphone() as source:
                    mic.adjust_for_ambient_noise(source, duration=1)
                    audio = mic.listen(source, timeout=listen_timeout, phrase_time_limit=phrase_timeout)
                    text = mic.recognize_google(audio).lower()
                    for phrase in phrases:
                        if phrase in text:
                            return phrase, text
            except Exception as e:
                print(f"listen_until error: {e}")
                return "",""
        return "", ""
    
    # -- PSEUDO COMMANDS (example of possible outputs) --
	# -- (but they don't actually "work") -- 
 
    def take_photo(self):
        pass
 
    def play_music(self, song_id):
        max_size = len(self._songs) - 1
        if max_size < song_id:
            print(f"WARNING: songs library is not that large. Playing sound at {max_size} instead.")
            song_id = max_size
        elif song_id < 0:
            print(f"ERROR: invalid song id, play_music() failed.")
            return
        
        song = self._songs[song_id]
        song = song[:-4] # remove the .mp3
        print(f"Now playing: {song}")
        
    def get_legs(self):
        """
        Return the number of "legs" detected. On the actual robot, this returns the number of objects
        detected that are about the width of a leg, so the randomizer might not be far off anyway...
        """
        legs = random.randint(0, MAX_LEGS)
        return legs
    
    def whos_there(self):
        """
        Choose a random image from library and return the people detected (excluding Unknown).
        """
        max_file = len(self._images) - 1
        img = random.randint(0, max_file)
        targets = self._recognizer[img]
        
        # go from list of tuples to set
        people = set()
        for t in targets:
            if t[0] != "Unknown":
                people.add(t[0])
        return people
    
    def get_targets(self):
        """
        """
        max_file = len(self._images) - 1
        img = random.randint(0, max_file)
        targets = self._recognizer[img]
        return targets
    
    def get_laser_scan(self):
        pass
 
    def objects_seen(self):
        """
        Choose a random image from library and return the object classes detected.
        """
        max_file = len(self._images) - 1
        img = random.randint(0, max_file)
        objects = self._coco[img]
        
        # go from list of tuples to set
        objects = set()
        for o in objects:
            if o[0] != "Unknown":
                objects.add(t[0])
        return objects
    
    def scan_for(self, obj):
        max_file = len(self._images) - 1
        img = random.randint(0, max_file)
        objects = self._coco[img]
        
        # convert to list of tuples (x, y)
        found = []
        for o in objects:
            if o[0] == obj:
                x = o[1]
                y = o[2]
                coords = (x, y)
                found.append(coords)
        return found      
    
    def get_object_scan(self):
        max_file = len(self._images) - 1
        img = random.randint(0, max_file)
        objects = self._coco[img]
        return objects
    
    # -- EXECUTORS  --
    def run_program(self):
        while self._running_program:
            time.sleep(0.1)
    
    def _queue_executor(self):
        """
        Run non blocking movement commands in the background.
        """
        while self._running_program:
            try:
                item = self._movement_queue.get(timeout=0.1)
                cmd = item[0]
                args = item[1]

                if cmd == "go_to":
                    self._execute_go_to(args[0], args[1])
                elif cmd == "rotate":
                    self._execute_rotate(args[0])
                elif cmd == "move":
                    self._execute_move(args[0])
                elif cmd == "move_to":
                    self._execute_move_to(args[0])
                elif cmd == "nav_to":
                    self._execute_nav_to(args[0])

                self._movement_queue.task_done()
            except queue.Empty:
                continue
            
	# -- PYGAME --
    def done(self):
        while self._running_program:
            self.refresh_window()
                        
    def refresh_window(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running_program = False
                pygame.quit()
                os._exit(0)

        self.screen.blit(self.map_background, (0, 0))
        pygame.draw.circle(self.screen, (0, 255, 100), (int(self.x), int(self.y)), 10)
        pygame.draw.circle(self.screen, (0, 180, 70), (int(self.x), int(self.y)), 10, 2)

        pygame.display.flip()
        self.clock.tick(60)
        
    def _generate_costmap(self):
        grid = pygame.surfarray.array3d(self.map_background)
        gray = np.dot(grid[..., :3], [0.2989, 0.5870, 0.1140])
        binary_grid = np.where(gray < 50, 1, 0)
        return binary_grid
    
        
    def __exit__(self, exc_type, exc_value, traceback):
        while self._is_traveling:
            time.sleep(0.1)  
        self._running_program = False
        time.sleep(0.1)
        return
    
    
# -- THE PHOTO CLASS --

class Photo:
    def __init__(self, robot_obj, data):
        self.data = []
        self.height = IMG_HEIGHT
        self.width = IMG_WIDTH
        
        # randomize the pixels TODO
        self.pixels = [[[0, 0, 0] for _ in range(self.width)] for _ in range(self.height)]

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width

    def get_pixels(self):
        return self.pixels

    def objects_seen(self):
        return set()

    def whos_there(self):
        return set()