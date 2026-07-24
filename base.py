import socket, ast, os, queue, threading, time, random, heapq

import numpy as np
import pygame
import speech_recognition as sr

from contextlib import AbstractContextManager

SCALE_FACTOR = 0.5
MAP_HEIGHT - 3069 * SCALE_FACTOR
MAP_WIDTH = 2640 * SCALE_FACTOR

MOVE_SPEED = 5.0
IMAGE_PATH = "golisano3v5.png"
POINTS_FILE = "point_database.txt"

START_X = 1228.0 * SCALE_FACTOR
START_Y = 815.0 * SCALE_FACTOR

VOICE_LIB = ['en-gb-scotland', 'en-gb-x-gbclan', 'en-gb-x-rp', 'en-us']
SPEAK_RATE = 175
BANNED_WORDS = "banned.txt"

class Robot(AbstractContextManager):
	def __init__(self):
		self._is_traveling = False
		self._dest_name = "N/A"
		self._dest_pos = None

		self.x = START_X
		self.y = START_Y
		self.speed = SPEED

		self._block_queue = queue.Queue()
		self._non_block_queue = queue.Queue()


		self.width = MAP_WIDTH
		self.height = MAP_HEIGHT

		# banned words
		self._banned_words = set()
		with open(BANNED_WORDS) as file:
				for line in file:
        			self._banned_words.add(line.strip())
           
		# INCLUDE:  audios allowed, points
		# set up pygame on main thread
		self.screen = pygame.display.set_mode((self.width, self.height))
		try:
			raw_image = pygame.image_load(IMAGE_PATH)
			self.map_background = raw_image.convert()
		except pygame.error as e:
			print(f"Failed: count not load map image {IMAGE_PATH}, {e}")
			os_.exit(1)

		pygame.display.set_caption("Robot Simulator")
		self.clock = pygame.time.Clock()

		# previously named non blocking queue, but also basically nothing properly "blocks" now lol
		self._movement_queue = queue.Queue()
		self._movement_thread = threading.Thread(target=self._queue_executor, daemon=True)
		self._movement_thread.start()

		# main thread - pygame
		self._main_thread = threading.Thread(target=self.run_program, daemon=True)
		self._main_thread.start()

	# -- MOVEMENT COMMANDS --

	def get_pos(self): 
		""" 
		Returns the current position of the robot.
		"""
		return self.x, self.y

	def move(self, metres):
		pass

	def move_to(self, metres):
		pass

	def rotate(self, degrees):
		pass

	def nav_to(self, location):
		pass

	def go_to(self, x, y):
		pass

	def halt(self):
		pass

	# -- BLOCKING COMMANDS --
	# -- (actually work) --

	def speak(self, vc=1, msg):
		message = msg
		for word in self._banned_words:
            if word in message:
                return "ERROR: message contains banned word(s)."

        # would normally be the type of voice, doesn't do anything in simulation
        if vc < 0:
            return "ERROR: invalid voice type"
        elif vc > 3:
            vc = 3
			print("WARNING: voice libarary only goes up to index 3.")
                
        voice = VOICE_LIB[vc]
        # CHANGE TO "SHOW"
        print(f"{voice}: robot says {message}.")
        # add a time.sleep to simulate block
                
    # -- PSEUDO COMMANDS (example of possible outputs) --
	# -- (but they don't actually "work") -- 

	def get_legs(self):
		legs = random.randint(0, MAX_LEGS)
		return legs

	def objects_seen(self):
		pass

	def get_object_scan(self):
		pass

	def scan_for(self, type):
		pass

	def whos_there(self):
		pass	

	def get_targets(self):
		pass


	# -- HELPER FUNCTIONS --
	def _pixel_to_map(self, x, y):

	# -- PYGAME --
	def done(self):
        while self._running_program:
            self.refresh_window()
                        
    def refresh_window(self):
        for event in pygame.event.get()
            if event.type == pygame.QUIT:
                self._running_program = False
                pygame.quit()
                os._exit(0)

        self.screen.blit(self.map_background, (0, 0))
        pygame.draw.circle(self.screen, (0, 255, 100), (int(self.x), int(self.y)), 15)
        pygame.draw.circle(self.screen, (0, 180, 70), (int(self.x), int(self.y)), 15, 2)

        pygame.display.flip()
        self.clock.tick(60)

	# -- THREADS --
	def _queue_executor(self):
		pass

	def _run_program(self):
		pass

	def __exit__(self, exc_type, exc_value, traceback):
                while self._is_traveling:
                        time.sleep(0.1)
                self._running_program = False
                time.sleep(0.1)
                return

if __name__ == "__main__":
    def student_script(robot):
        robot.go_to(1225, 815, wait=False)

    x = 0
    y = 0
    r = Robot(x, y)
    
    threading.Thread(target=student_script, args=(r,), daemon=True).start()
    
    r.done()