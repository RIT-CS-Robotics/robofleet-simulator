import pygame
import numpy as np
import heapq


"""
NOT THE FINALIZED PATH PLANNER, JUST BASE TO REFERENCE
"""
class PathPlanner:
    def __init__(self, pygame_surface, obstacle_threshold=50, grid_scale=5):
        """
        grid_scale: Compresses the map grid to speed up planning.
                    10 means a 2640x3069 map becomes 264x306 nodes.
        """
        self.orig_width = pygame_surface.get_width()
        self.orig_height = pygame_surface.get_height()
        self.grid_scale = grid_scale
        
        # create cistmap
        full_costmap = self._generate_costmap(pygame_surface, obstacle_threshold)
        
        # downsize costmap
        self.costmap = full_costmap[::grid_scale, ::grid_scale]
        self.width = self.costmap.shape[0]
        self.height = self.costmap.shape[1]
        
        print(f"📉 Costmap downsampled from ({self.orig_width}x{self.orig_height}) to ({self.width}x{self.height})")

    def _generate_costmap(self, surface, threshold):
        """Converts Pygame surface into a 2D binary obstacle grid."""
        grid = pygame.surfarray.array3d(surface)
        # Fast color evaluation wrapper
        return np.where((grid[..., 0] < threshold) & (grid[..., 1] < threshold) & (grid[..., 2] < threshold), 1, 0)

    def plan_path(self, start_pos, goal_pos, tolerance=5.0):
        """Computes a scaled, efficient 8-way A* path."""
        # Scale actual coordinates down to match the smaller map grid matrix
        start = (int(start_pos[0] // self.grid_scale), int(start_pos[1] // self.grid_scale))
        goal = (int(goal_pos[0] // self.grid_scale), int(goal_pos[1] // self.grid_scale))
        
        # Keep bounds safe
        start = (max(0, min(start[0], self.width-1)), max(0, min(start[1], self.height-1)))
        goal = (max(0, min(goal[0], self.width-1)), max(0, min(goal[1], self.height-1)))

        def heuristic(a, b):
            return np.hypot(b[0] - a[0], b[1] - a[1])

        neighbors = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
        close_set = set()
        came_from = {}
        gscore = {start: 0}
        fscore = {start: heuristic(start, goal)}
        oheap = []

        heapq.heappush(oheap, (fscore[start], start))
        
        while oheap:
            current_f, current = heapq.heappop(oheap)

            if current == goal or heuristic(current, goal) < (tolerance / self.grid_scale):
                path = []
                while current in came_from:
                    scaled_point = (current[0] * self.grid_scale, current[1] * self.grid_scale)
                    path.append(scaled_point)
                    current = came_from[current]
                path.reverse()
                return path
  
            close_set.add(current)
            
            for i, j in neighbors:
                neighbor = (current[0] + i, current[1] + j)
                move_cost = 1.414 if (i != 0 and j != 0) else 1.0
                tentative_g_score = gscore[current] + move_cost
                
                if 0 <= neighbor[0] < self.width and 0 <= neighbor[1] < self.height:
                    if self.costmap[neighbor[0]][neighbor[1]] == 1:
                        continue
                else:
                    continue
                
                if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, float('inf')):
                    continue
                    
                if tentative_g_score < gscore.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    gscore[neighbor] = tentative_g_score
                    fscore[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                    heapq.heappush(oheap, (fscore[neighbor], neighbor))
                    
        return []