import math, heapq, pygame
import numpy as np

"""
Path planner. A* navigation algorithm partially referenced from w3schools page 
here: https://www.geeksforgeeks.org/dsa/a-search-algorithm/.

Author: Anusha Ghosh
"""
 
OBSTACLE_THRESHOLD = 50
GRID_SCALE = 5
MAP_IMAGE = "data/golisano3v5.png"
ROBOT_RADIUS = 5

class Cell:
    def __init__(self):
        self.parent = None
        self.g = float('inf')
        self.h = float('inf')
        self.f = float('inf')
    
class PathPlanner:
    def __init__(self, pygame_board):   
        self.orig_width = pygame_board.get_width()
        self.orig_height = pygame_board.get_height()
        self.grid_scale = GRID_SCALE
        
        # create costmap
        full_costmap = self._generate_global_costmap(MAP_IMAGE)
        
        # downsize costmap
        downscaled = full_costmap[::self.grid_scale, ::self.grid_scale]
        self.width = downscaled.shape[0]
        self.height = downscaled.shape[1]
        
        # inflate
        grid_radius = int(math.ceil(ROBOT_RADIUS / self.grid_scale))
        self.costmap = self.inflate_costmap(downscaled, grid_radius)
        
    def _generate_global_costmap(self, surface):
        # in case i mess up somewhere, allows both pygame surface and image input
        if isinstance(surface, str):
            surface = pygame.image.load(surface)
        elif isinstance(surface, pygame.Surface):
            pass
        else:
            raise TypeError("Could not create costmap")
        
        rgb_array = pygame.surfarray.array3d(surface)
        grayscale = np.dot(rgb_array[..., :3], [0.2989, 0.5870, 0.1140])
        
        # match standard indexing
        costmap = np.where(grayscale < 254, 1, 0)
        return costmap
    
    def inflate_costmap(self, costmap, grid_radius):
        """
        Inflates obstacles to account for robot radius so it doesn't brush up against walls/appear like it's
        partially phasing through.
        """
        rows, cols = costmap.shape
        inflated_costmap = np.copy(costmap)
        
        for r in range(rows):
            for c in range(cols):
                if costmap[r, c] == 1:
                    for dr in range(-grid_radius, grid_radius + 1):
                        for dc in range(-grid_radius, grid_radius + 1):
                            if (dr**2 + dc**2) <= (grid_radius**2):
                                nr, nc = r + dr, c + dc
                                if 0 <= nr < rows and 0 <= nc < cols:
                                    inflated_costmap[nr, nc] = 1
                                
        return inflated_costmap
    
    def is_valid(self, row, col):
        return 0 <= row < self.width and 0 <= col < self.height
        
    def is_open(self, row, col):
        return self.costmap[row][col] == 0
    
    def is_destination(self, row, col, dest_pos):
        return row == dest_pos[0] and col == dest_pos[1]
    
    def calculate_heuristic(self, row, col, dest_pos):
        return ((row - dest_pos[0]) ** 2 + (col - dest_pos[1]) ** 2) ** 0.5
    
    def a_star_path(self, start_pos, goal_pos, tolerance=5.0):
        """
        A star path planning algorithm. Returns list path if found, otherwise returns None if invalid 
        or no path could be found.
        """
        start = (int(start_pos[0] // self.grid_scale), int(start_pos[1] // self.grid_scale))
        goal = (int(goal_pos[0] // self.grid_scale), int(goal_pos[1] // self.grid_scale))
        
        if not self.is_open(goal[0], goal[1]):
            print("Invalid destination coordinates. Obstacle / keepout zone detected.")
            return
        
        if self.is_destination(start[0], start[1], goal):
            print("Destination reached.")
            return [start_pos]
        
        # cell grid
        cell_details = [[Cell() for _ in range(self.height)] for _ in range(self.width)]
       
        s_row, s_col = start
        cell_details[s_row][s_col].g = 0.0
        cell_details[s_row][s_col].h = self.calculate_heuristic(s_row, s_col, goal)
        cell_details[s_row][s_col].f = cell_details[s_row][s_col].h
        
        # initialize the open list
        open_list = []
        heapq.heappush(open_list, (cell_details[s_row][s_col].f, s_row, s_col))
        
        # visited/closed list of nodes
        visited = set()
        
        # possible directions
        directions = [(-1, 0), (1, 0), (0, 1), (0, -1)]
        dest_found = False
        
        # while open list is not empty
        while len(open_list) != 0:
            # pop cell with smallest f and mark as visited
            p = heapq.heappop(open_list)
            x = p[1]
            y = p[2]
            coord = (x, y)
            visited.add(coord)
            
            # check successors
            for direction in directions:
                new_x = x + direction[0]
                new_y = y + direction[1]
                
                # can go?
                if self.is_valid(new_x, new_y) and self.is_open(new_x, new_y):
                    if (new_x, new_y) not in visited:
                        if self.is_destination(new_x, new_y, goal):
                            cell_details[new_x][new_y].parent = (x, y)
                            dest_found = True
                            break
                        
                        # calculate the new values
                        g_new = cell_details[x][y].g + 1.0
                        h_new = self.calculate_heuristic(new_x, new_y, goal)
                        f_new = g_new + h_new
                        
                        # cell not open or new f value is smaller
                        if cell_details[new_x][new_y].f == float('inf') or cell_details[new_x][new_y].f > f_new:
                            cell_details[new_x][new_y].g = g_new
                            cell_details[new_x][new_y].h = h_new
                            cell_details[new_x][new_y].f = f_new
                            cell_details[new_x][new_y].parent = (x, y)
                            heapq.heappush(open_list, (f_new, new_x, new_y))
            
            if dest_found:
                break
            
        if not dest_found:
            print("Could not form a path to destination.")
            return None
        
        # dest found - reconstruct path
        path = []
        current = goal
        while current is not None:
            r, c = current
            orig_x = r * self.grid_scale + (self.grid_scale / 2.0)
            orig_y = c * self.grid_scale + (self.grid_scale / 2.0)
            path.append((orig_x, orig_y))
            current = cell_details[r][c].parent

        path.reverse()
        return path
            