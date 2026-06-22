import pygame
import numpy as np
import random
import sys
import time

# --- CONFIGURATION & CONSTANTS ---
GRID_ROWS = 10
GRID_COLS = 12
TILE_SIZE = 40
PADDING = 20
CONTROL_PANEL_WIDTH = 280

# Visual Window Bounds Calculation
SCREEN_WIDTH = (GRID_COLS * TILE_SIZE) + (PADDING * 2) + CONTROL_PANEL_WIDTH
SCREEN_HEIGHT = (GRID_ROWS * TILE_SIZE) + (PADDING * 2) + 80  # Extra footer room

# Colors (RGB Palette - Redesigned light theme with terracotta accent)
COLOR_BACKGROUND = (244, 246, 248)    # Light background
COLOR_AISLE = (255, 255, 255)         # Walkable aisles
COLOR_WALL = (241, 242, 244)          # Storage racks
COLOR_WALL_BORDER = (226, 228, 232)   # Rack border
COLOR_GRID_LINE = (234, 234, 236)     # Grid line
COLOR_PACKING = (39, 174, 96)         # Green
COLOR_ITEM_NORMAL = (246, 220, 210)   # Pale pink-peach
COLOR_ITEM_HOT = (222, 92, 60)         # Terracotta orange
COLOR_PICKER = (155, 89, 182)         # Purple picker bot
COLOR_PATH = (222, 92, 60)            # Terracotta paths / items in order
COLOR_TEXT = (26, 29, 32)             # Slate/Charcoal text
COLOR_PANEL_BG = (255, 255, 255)      # Pure white panels
COLOR_SLIDER_TRACK = (226, 228, 232)  # Light track
COLOR_SLIDER_FILL = (222, 92, 60)     # Terracotta slider handle

# Layout Setup: 0 = Aisle, 1 = Shelf/Rack, 2 = Packing Station
WAREHOUSE_MAP = np.zeros((GRID_ROWS, GRID_COLS), dtype=int)
for c in range(1, GRID_COLS - 1):
    if c % 3 != 0:
        for r in range(1, GRID_ROWS - 1):
            WAREHOUSE_MAP[r, c] = 1

PACKING_STATION = (GRID_ROWS - 1, 0)
WAREHOUSE_MAP[PACKING_STATION] = 2

# --- DATA STRUCTURES & DATA INITIALIZATION ---
SKUs = [f"SKU_{i:02d}" for i in range(35)]
sku_to_coords = {}
coords_to_sku = {}

shelf_cells = [(r, c) for r in range(GRID_ROWS) for c in range(GRID_COLS) if WAREHOUSE_MAP[r, c] == 1]
random.shuffle(shelf_cells)

for idx, sku in enumerate(SKUs):
    if idx < len(shelf_cells):
        cell = shelf_cells[idx]
        sku_to_coords[sku] = cell
        coords_to_sku[cell] = sku

sku_velocities = {sku: random.randint(5, 20) for sku in SKUs}

# --- INTERACTIVE SLIDER CLASS ---
class Slider:
    def __init__(self, x, y, w, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, w, 10)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.handle_radius = 8
        self.update_handle_pos()
        self.dragging = False

    def update_handle_pos(self):
        fraction = (self.val - self.min_val) / (self.max_val - self.min_val)
        self.handle_x = self.rect.x + int(fraction * self.rect.width)

    def draw(self, surface, font_obj):
        # Draw Label and Readout Value
        lbl = font_obj.render(f"{self.label}: {int(self.val) if self.val == int(self.val) else round(self.val, 1)}", True, COLOR_TEXT)
        surface.blit(lbl, (self.rect.x, self.rect.y - 18))
        # Draw track
        pygame.draw.rect(surface, COLOR_SLIDER_TRACK, self.rect, border_radius=4)
        # Draw handle thumb knob
        pygame.draw.circle(surface, COLOR_SLIDER_FILL, (self.handle_x, self.rect.y + 5), self.handle_radius)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            # Metric distance checking to see if handle knob clicked
            if np.hypot(mouse_pos[0] - self.handle_x, mouse_pos[1] - (self.rect.y + 5)) <= self.handle_radius + 4:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mx = max(self.rect.x, min(event.pos[0], self.rect.x + self.rect.width))
            fraction = (mx - self.rect.x) / self.rect.width
            self.val = self.min_val + fraction * (self.max_val - self.min_val)
            self.handle_x = mx
            return True
        return False

# --- TIER 1: GREEDY SLOTTING CONFIG ENGINE ---
def run_greedy_reslotting():
    global sku_to_coords, coords_to_sku
    def manhattan_dist(p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
    
    sku_scores = {}
    for sku in SKUs:
        curr_loc = sku_to_coords.get(sku, shelf_cells[0])
        dist = manhattan_dist(curr_loc, PACKING_STATION) or 1
        sku_scores[sku] = sku_velocities[sku] / dist
        
    sorted_skus = sorted(SKUs, key=lambda x: sku_scores[x], reverse=True)
    sorted_shelves = sorted(shelf_cells, key=lambda cell: manhattan_dist(cell, PACKING_STATION))
    
    sku_to_coords.clear()
    coords_to_sku.clear()
    for idx, sku in enumerate(sorted_skus):
        if idx < len(sorted_shelves):
            cell = sorted_shelves[idx]
            sku_to_coords[sku] = cell
            coords_to_sku[cell] = sku

run_greedy_reslotting()

# --- TIER 2: BITMASK DP ROUTE OPTIMIZER ---
def compute_distance_matrix(targets):
    n = len(targets)
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dist_matrix[i, j] = abs(targets[i][0] - targets[j][0]) + abs(targets[i][1] - targets[j][1])
    return dist_matrix

def solve_tsp_bitmask_dp(targets):
    n = len(targets)
    if n <= 1:
        return [0], 0
    dist_matrix = compute_distance_matrix(targets)
    memo = {}
    
    def tsp(mask, pos):
        if mask == (1 << n) - 1:
            return dist_matrix[pos][0], [0]
        state = (mask, pos)
        if state in memo:
            return memo[state]
        min_dist = float('inf')
        best_path = []
        for next_node in range(n):
            if not (mask & (1 << next_node)):
                new_mask = mask | (1 << next_node)
                cost, path = tsp(new_mask, next_node)
                total_cost = dist_matrix[pos][next_node] + cost
                if total_cost < min_dist:
                    min_dist = total_cost
                    best_path = [next_node] + path
        memo[state] = (min_dist, best_path)
        return memo[state]

    total_shortest_dist, final_path = tsp(1, 0)
    return [targets[idx] for idx in [0] + final_path], total_shortest_dist

def generate_parameterized_order(size):
    size = max(1, min(int(size), 12))  # Keep scale bounding safe for DP performance
    weights = [sku_velocities[sku] for sku in SKUs]
    total_w = sum(weights)
    probs = [w/total_w for w in weights]
    chosen_skus = np.random.choice(SKUs, size=size, replace=False, p=probs)
    return list(chosen_skus)

# --- INITIALIZING INTERACTIVE UI WIDGETS ---
panel_x_start = (GRID_COLS * TILE_SIZE) + (PADDING * 2)

slider_order_size = Slider(panel_x_start + 20, 50, 240, 2, 11, 4, "Basket Order Size (SKUs)")
slider_speed = Slider(panel_x_start + 20, 120, 240, 1, 10, 4, "Picker Speed Factor")
slider_surge_freq = Slider(panel_x_start + 20, 190, 240, 2, 20, 8, "Demand Surge Engine Timer (s)")
slider_hot_intensity = Slider(panel_x_start + 20, 260, 240, 10, 60, 30, "Surge Spike Velocity Weight")

sliders = [slider_order_size, slider_speed, slider_surge_freq, slider_hot_intensity]

# --- PYGAME RUNTIME GAME LOOP SETUP ---
pygame.init()
pygame.display.set_caption("Blinkit Interactive Parameter Testing Sandbox")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 13)
font_bold = pygame.font.SysFont("Arial", 15, bold=True)

# Application state metrics Initialization
current_order = generate_parameterized_order(slider_order_size.val)
current_targets = [PACKING_STATION] + [sku_to_coords[sku] for sku in current_order if sku in sku_to_coords]
optimized_route, path_distance = solve_tsp_bitmask_dp(current_targets)

picker_sub_target_idx = 0
picker_pos_x = PACKING_STATION[1] * TILE_SIZE + PADDING + TILE_SIZE // 2
picker_pos_y = PACKING_STATION[0] * TILE_SIZE + PADDING + TILE_SIZE // 2

last_reslot_time = time.time()
orders_completed = 0
total_distance_covered = 0

running = True
while running:
    dt = clock.tick(60)
    
    # --- EVENT REGISTRATION ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        for s in sliders:
            if s.handle_event(event):
                # If the order slider itself is moved, drop the active run loop and generate a new order batch size frame immediately
                if s == slider_order_size:
                    current_order = generate_parameterized_order(slider_order_size.val)
                    current_targets = [PACKING_STATION] + [sku_to_coords[sku] for sku in current_order if sku in sku_to_coords]
                    optimized_route, path_distance = solve_tsp_bitmask_dp(current_targets)
                    picker_sub_target_idx = 0
                    picker_pos_x = PACKING_STATION[1] * TILE_SIZE + PADDING + TILE_SIZE // 2
                    picker_pos_y = PACKING_STATION[0] * TILE_SIZE + PADDING + TILE_SIZE // 2

    # --- SIMULATOR EVENT UPDATES ---
    # Trigger a Greedy Allocation restructure frame based on customizable timer slider
    if time.time() - last_reslot_time > slider_surge_freq.val:
        for _ in range(3):
            lucky_sku = random.choice(SKUs)
            sku_velocities[lucky_sku] += int(slider_hot_intensity.val)
        run_greedy_reslotting()
        last_reslot_time = time.time()
        
        # Keep layout targets maps synchronized with positions shifts
        current_targets = [PACKING_STATION] + [sku_to_coords[sku] for sku in current_order if sku in sku_to_coords]
        optimized_route, path_distance = solve_tsp_bitmask_dp(current_targets)
        picker_sub_target_idx = 0

    # --- PICKER WORKER MOVEMENT SIMULATION ---
    if picker_sub_target_idx < len(optimized_route):
        target_grid_pos = optimized_route[picker_sub_target_idx]
        target_pixel_x = target_grid_pos[1] * TILE_SIZE + PADDING + TILE_SIZE // 2
        target_pixel_y = target_grid_pos[0] * TILE_SIZE + PADDING + TILE_SIZE // 2
        
        dx = target_pixel_x - picker_pos_x
        dy = target_pixel_y - picker_pos_y
        dist = np.hypot(dx, dy)
        
        step_speed = slider_speed.val
        if dist > step_speed:
            picker_pos_x += (dx / dist) * step_speed
            picker_pos_y += (dy / dist) * step_speed
        else:
            picker_pos_x, picker_pos_y = target_pixel_x, target_pixel_y
            picker_sub_target_idx += 1
    else:
        # Loop Cycle Wrapup
        orders_completed += 1
        total_distance_covered += path_distance
        
        current_order = generate_parameterized_order(slider_order_size.val)
        current_targets = [PACKING_STATION] + [sku_to_coords[sku] for sku in current_order if sku in sku_to_coords]
        optimized_route, path_distance = solve_tsp_bitmask_dp(current_targets)
        picker_sub_target_idx = 0

    # --- RENDERING PIPELINE GRAPHICS ENGINE ---
    screen.fill(COLOR_BACKGROUND)
    
    # 1. Draw Map Cells Grid Layout
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            rect = pygame.Rect(c * TILE_SIZE + PADDING, r * TILE_SIZE + PADDING, TILE_SIZE, TILE_SIZE)
            if WAREHOUSE_MAP[r, c] == 1:
                pygame.draw.rect(screen, COLOR_WALL, rect)
                pygame.draw.rect(screen, COLOR_WALL_BORDER, rect, 1)
            elif WAREHOUSE_MAP[r, c] == 2:
                pygame.draw.rect(screen, COLOR_PACKING, rect)
            else:
                pygame.draw.rect(screen, COLOR_AISLE, rect)
                pygame.draw.rect(screen, COLOR_GRID_LINE, rect, 1)

    # 2. Draw Assigned SKU Elements
    for sku, (r, c) in sku_to_coords.items():
        rect = pygame.Rect(c * TILE_SIZE + PADDING + 4, r * TILE_SIZE + PADDING + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        is_hot = sku_velocities[sku] > 40
        color = COLOR_ITEM_HOT if is_hot else COLOR_ITEM_NORMAL
        
        if sku in current_order:
            pygame.draw.rect(screen, COLOR_PATH, rect)
            pygame.draw.rect(screen, color, rect.inflate(-4, -4))
        else:
            pygame.draw.rect(screen, color, rect)
            
        # Draw high-contrast text based on class intensity
        txt_color = (255, 255, 255) if is_hot or sku in current_order else COLOR_TEXT
        v_txt = font.render(str(sku_velocities[sku]), True, txt_color)
        screen.blit(v_txt, (rect.x + 3, rect.y + 4))

    # 3. Draw Path Route Matrix Trace Overlay
    if len(optimized_route) > 1:
        points = [(n[1] * TILE_SIZE + PADDING + TILE_SIZE // 2, n[0] * TILE_SIZE + PADDING + TILE_SIZE // 2) for n in optimized_route]
        pygame.draw.lines(screen, COLOR_PATH, False, points, 3)

    # 4. Draw Active Moving Picker
    pygame.draw.circle(screen, COLOR_PICKER, (int(picker_pos_x), int(picker_pos_y)), 10)

    # 5. Draw Persistence Right Edge Sidebar Control Panel
    panel_rect = pygame.Rect(panel_x_start, 0, CONTROL_PANEL_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, COLOR_PANEL_BG, panel_rect)
    pygame.draw.line(screen, COLOR_SLIDER_TRACK, (panel_x_start, 0), (panel_x_start, SCREEN_HEIGHT), 2)
    
    # Draw out slider controls panels elements list loop
    for s in sliders:
        s.draw(screen, font_bold)

    # 6. Draw Informational Footer Summary Banner
    footer_y = GRID_ROWS * TILE_SIZE + PADDING * 2
    txt_order = font_bold.render(f"Active Pick Basket: {', '.join(current_order)}", True, COLOR_TEXT)
    txt_stats = font.render(f"Batches Sorted: {orders_completed}  | Total Step Cost Tally: {int(total_distance_covered)} units", True, COLOR_TEXT)
    txt_engine = font.render(f"Dynamic Programming Cost Rating: {int(path_distance)} Optimal Steps Calculated", True, COLOR_PATH)
    
    screen.blit(txt_order, (PADDING, footer_y + 10))
    screen.blit(txt_stats, (PADDING, footer_y + 32))
    screen.blit(txt_engine, (PADDING, footer_y + 50))

    pygame.display.flip()

pygame.quit()
sys.exit()