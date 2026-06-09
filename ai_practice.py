import pygame
import sys
import math
from heapq import heappush, heappop

# ========== CONFIGURATION ==========
MAP_IMAGE_PATH = "./mapImages/ancientMapBlackWhite.webp"

CT_SPAWNS = [
    (48.0, 10.0),
    (50.0, 7.0),
    (52.0, 10.0),
    (54.0, 7.0),
    (56.0, 10.0)
]

T_SPAWNS_BASE = [
    (44.7, 90.0),
    (46.5, 88.0),
    (48.5, 90.0),
    (50.4, 88.0),
    (52.0, 90.0)
]

WHITE_THRESHOLD = 200
BLACK_THRESHOLD = 50
GRID_SIZE = 100
MOVE_SPEED = 0.8

DOT_RADIUS = 14
CT_COLOR = (88, 194, 242)
T_COLOR = (245, 158, 11)
OUTLINE_COLOR = (255, 255, 255)
OUTLINE_WIDTH = 3
SELECTED_WIDTH = 5
TEXT_COLOR = (0, 0, 0)
FONT_SIZE = 18

LINE_COLOR = (255, 255, 255, 80)
LINE_WIDTH = 2

# ---------- Tactical Info Positions (Ancient map) ----------
INFO_POSITIONS = [
    {"name": "A Main", "pos": (21.0, 32.0)},
    {"name": "Mid", "pos": (47.4, 31.5)},
    {"name": "Cave", "pos": (65.5, 48.9)},
    {"name": "B Ramp", "pos": (78.7, 37.8)},
    {"name": "Donut", "pos": (52.6, 24.4)},
    {"name": "Red Room", "pos": (67.1, 39.0)},
]

pygame.init()
screen = pygame.display.set_mode((1200, 800), pygame.RESIZABLE)
pygame.display.set_caption("AI Practice – Auto Info Fixed")
clock = pygame.time.Clock()

map_img = pygame.image.load(MAP_IMAGE_PATH).convert()
map_rect = map_img.get_rect()
font = pygame.font.SysFont("Arial", FONT_SIZE, bold=True)

offscreen = None
grid = None
cell_width = 0
cell_height = 0

def percent_to_pixel(percent_x, percent_y, surface_rect):
    x = surface_rect.x + (percent_x / 100.0) * surface_rect.width
    y = surface_rect.y + (percent_y / 100.0) * surface_rect.height
    return int(x), int(y)

def pixel_to_percent(pixel_x, pixel_y, surface_rect):
    x = ((pixel_x - surface_rect.x) / surface_rect.width) * 100.0
    y = ((pixel_y - surface_rect.y) / surface_rect.height) * 100.0
    return max(0, min(100, x)), max(0, min(100, y))

def build_grid(surface_rect):
    global offscreen, grid, cell_width, cell_height
    w, h = map_img.get_size()
    offscreen = pygame.Surface((w, h))
    offscreen.blit(map_img, (0, 0))
    grid = [[True] * GRID_SIZE for _ in range(GRID_SIZE)]
    cell_width = w / GRID_SIZE
    cell_height = h / GRID_SIZE
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x = int((col + 0.5) * cell_width)
            y = int((row + 0.5) * cell_height)
            if 0 <= x < w and 0 <= y < h:
                pixel = offscreen.get_at((x, y))
                r, g, b, _ = pixel
                is_white = (r > WHITE_THRESHOLD and g > WHITE_THRESHOLD and b > WHITE_THRESHOLD)
                is_black = (r < BLACK_THRESHOLD and g < BLACK_THRESHOLD and b < BLACK_THRESHOLD)
                if is_white or is_black:
                    grid[row][col] = False

def percent_to_grid(percent_x, percent_y):
    col = int((percent_x / 100.0) * GRID_SIZE)
    row = int((percent_y / 100.0) * GRID_SIZE)
    return max(0, min(GRID_SIZE-1, row)), max(0, min(GRID_SIZE-1, col))

def grid_to_percent(row, col):
    x = ((col + 0.5) / GRID_SIZE) * 100.0
    y = ((row + 0.5) / GRID_SIZE) * 100.0
    return x, y

def heuristic(r1, c1, r2, c2):
    return abs(r1 - r2) + abs(c1 - c2)

def find_path(start_row, start_col, target_row, target_col):
    if not grid[start_row][start_col] or not grid[target_row][target_col]:
        return None
    open_set = []
    heappush(open_set, (0, start_row, start_col))
    came_from = {}
    g_score = {(start_row, start_col): 0}
    while open_set:
        _, r, c = heappop(open_set)
        if (r, c) == (target_row, target_col):
            path = [(r, c)]
            while (r, c) in came_from:
                r, c = came_from[(r, c)]
                path.append((r, c))
            path.reverse()
            return path
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and grid[nr][nc]:
                tentative_g = g_score[(r, c)] + 1
                if (nr, nc) not in g_score or tentative_g < g_score[(nr, nc)]:
                    g_score[(nr, nc)] = tentative_g
                    f = tentative_g + heuristic(nr, nc, target_row, target_col)
                    heappush(open_set, (f, nr, nc))
                    came_from[(nr, nc)] = (r, c)
    return None

def line_is_clear_grid(p1_percent, p2_percent):
    if grid is None:
        return False
    r1, c1 = percent_to_grid(p1_percent[0], p1_percent[1])
    r2, c2 = percent_to_grid(p2_percent[0], p2_percent[1])
    dr = abs(r2 - r1)
    dc = abs(c2 - c1)
    sr = 1 if r1 < r2 else -1
    sc = 1 if c1 < c2 else -1
    err = dr - dc
    r, c = r1, c1
    while True:
        if not grid[r][c]:
            return False
        if r == r2 and c == c2:
            break
        e2 = 2 * err
        if e2 > -dc:
            err -= dc
            r += sr
        if e2 < dr:
            err += dr
            c += sc
    return True

def draw_dashed_line(surf, color, start_pos, end_pos, width, dash_length=6, gap_length=6):
    x1, y1 = start_pos
    x2, y2 = end_pos
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length == 0:
        return
    dash_total = dash_length + gap_length
    num_dashes = int(length / dash_total)
    for i in range(num_dashes + 1):
        start_frac = i * dash_total / length
        end_frac = min((i * dash_total + dash_length) / length, 1.0)
        sx = x1 + dx * start_frac
        sy = y1 + dy * start_frac
        ex = x1 + dx * end_frac
        ey = y1 + dy * end_frac
        pygame.draw.line(surf, color, (sx, sy), (ex, ey), width)

def draw_connection_lines(screen, ct_dots, t_dots, map_rect):
    line_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    for ct in ct_dots:
        for t in t_dots:
            if line_is_clear_grid((ct.x, ct.y), (t.x, t.y)):
                p1 = percent_to_pixel(ct.x, ct.y, map_rect)
                p2 = percent_to_pixel(t.x, t.y, map_rect)
                draw_dashed_line(line_surface, LINE_COLOR, p1, p2, LINE_WIDTH)
    screen.blit(line_surface, (0, 0))

# ---------- Tactical functions ----------
def is_safe_position(ct_pos, t_positions):
    for t_pos in t_positions:
        if line_is_clear_grid(ct_pos, t_pos):
            return False
    return True

def get_best_ray(ct_pos):
    if offscreen is None:
        return None, 0.0
    x_percent, y_percent = ct_pos
    w, h = map_img.get_size()
    start_x = int((x_percent / 100.0) * w)
    start_y = int((y_percent / 100.0) * h)
    start_x = max(0, min(w - 1, start_x))
    start_y = max(0, min(h - 1, start_y))

    best_ray_end = None
    best_score = -1.0

    for angle in range(0, 360, 5):
        rad = math.radians(angle)
        dx = math.cos(rad)
        dy = math.sin(rad)
        x, y = float(start_x), float(start_y)
        while 0 <= x < w and 0 <= y < h:
            pixel = offscreen.get_at((int(x), int(y)))
            r, g, b, _ = pixel
            is_white = (r > WHITE_THRESHOLD and g > WHITE_THRESHOLD and b > WHITE_THRESHOLD)
            if is_white:
                break
            x += dx
            y += dy
        end_x = max(0, min(w - 1, int(x - dx)))
        end_y = max(0, min(h - 1, int(y - dy)))
        end_y_percent = (end_y / h) * 100.0
        if end_y_percent > best_score:
            best_score = end_y_percent
            best_ray_end = (end_x, end_y)

    if best_ray_end is None:
        return None, 0.0
    end_x_pix, end_y_pix = best_ray_end
    end_x_percent = (end_x_pix / w) * 100.0
    end_y_percent = (end_y_pix / h) * 100.0
    return (end_x_percent, end_y_percent), best_score

def get_depth_score(pos_percent):
    _, score = get_best_ray(pos_percent)
    return score

def calculate_total_score(ct_dots, t_dots):
    if offscreen is None:
        return 0.0
    t_positions = [(t.x, t.y) for t in t_dots]
    total = 0.0
    for ct in ct_dots:
        if is_safe_position((ct.x, ct.y), t_positions):
            total += get_depth_score((ct.x, ct.y))
    return total

def draw_depth_lines(screen, ct_dots, map_rect):
    if offscreen is None:
        return
    line_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    for ct in ct_dots:
        best_endpoint, score = get_best_ray((ct.x, ct.y))
        if best_endpoint is None:
            continue
        p1 = percent_to_pixel(ct.x, ct.y, map_rect)
        p2 = percent_to_pixel(best_endpoint[0], best_endpoint[1], map_rect)
        pygame.draw.line(line_surface, (0, 255, 255, 120), p1, p2, 2)
    screen.blit(line_surface, (0, 0))

# ---------- Walkability helpers ----------
def is_walkable_percent(percent_pos):
    if grid is None:
        return False
    r, c = percent_to_grid(percent_pos[0], percent_pos[1])
    return grid[r][c]

def snap_to_walkable(percent_pos, max_radius=10):
    if grid is None:
        return None
    start_r, start_c = percent_to_grid(percent_pos[0], percent_pos[1])
    if grid[start_r][start_c]:
        return percent_pos
    visited = set()
    queue = [(start_r, start_c)]
    visited.add((start_r, start_c))
    directions = [(-1,0), (1,0), (0,-1), (0,1)]
    for _ in range(max_radius):
        if not queue:
            break
        next_queue = []
        for r, c in queue:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and (nr, nc) not in visited:
                    if grid[nr][nc]:
                        return grid_to_percent(nr, nc)
                    visited.add((nr, nc))
                    next_queue.append((nr, nc))
        queue = next_queue
    return None

def assign_cts_to_info(ct_dots, t_dots):
    t_positions = [(t.x, t.y) for t in t_dots]
    scored_positions = []
    for info in INFO_POSITIONS:
        pos = info["pos"]
        if not is_safe_position(pos, t_positions):
            continue
        walkable_pos = snap_to_walkable(pos)
        if walkable_pos is None:
            continue
        score = get_depth_score(walkable_pos)
        scored_positions.append((score, info, walkable_pos))
    scored_positions.sort(key=lambda x: x[0], reverse=True)
    for i, ct in enumerate(ct_dots):
        if i < len(scored_positions):
            score, info, walkable_pos = scored_positions[i]
            ct.set_destination(walkable_pos)

class Dot:
    def __init__(self, x_percent, y_percent, color, number, team):
        self.x = x_percent
        self.y = y_percent
        self.color = color
        self.number = number
        self.team = team
        self.path = []
        self.selected = False

    def set_destination(self, target_percent):
        start = percent_to_grid(self.x, self.y)
        target = percent_to_grid(target_percent[0], target_percent[1])
        raw_path = find_path(start[0], start[1], target[0], target[1])
        if raw_path:
            self.path = [grid_to_percent(r, c) for r, c in raw_path]
        else:
            self.path = []

    def update(self, speed):
        if self.path:
            target_x, target_y = self.path[0]
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)
            if dist < speed:
                self.x, self.y = target_x, target_y
                self.path.pop(0)
            else:
                self.x += (dx / dist) * speed
                self.y += (dy / dist) * speed

    def draw(self, screen, surface_rect):
        center = percent_to_pixel(self.x, self.y, surface_rect)
        pygame.draw.circle(screen, self.color, center, DOT_RADIUS)
        outline_width = SELECTED_WIDTH if self.selected else OUTLINE_WIDTH
        pygame.draw.circle(screen, OUTLINE_COLOR, center, DOT_RADIUS, outline_width)
        text_surf = font.render(str(self.number), True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=center)
        screen.blit(text_surf, text_rect)

    def contains(self, mouse_pos, surface_rect):
        center = percent_to_pixel(self.x, self.y, surface_rect)
        return math.hypot(mouse_pos[0] - center[0], mouse_pos[1] - center[1]) <= DOT_RADIUS

def create_dots():
    map_h = map_img.get_height()
    pixel_offset_percent = (50.0 / map_h) * 100.0
    ct = [Dot(x, y, CT_COLOR, i+1, 'ct') for i, (x, y) in enumerate(CT_SPAWNS)]
    t = [Dot(x, y + pixel_offset_percent, T_COLOR, i+6, 't') for i, (x, y) in enumerate(T_SPAWNS_BASE)]
    return ct, t

ct_dots, t_dots = create_dots()
all_dots = ct_dots + t_dots
selected_dot = None

running = True
while running:
    win_w, win_h = screen.get_size()
    map_w, map_h = map_img.get_size()
    scale = min(win_w / map_w, win_h / map_h)
    new_w = int(map_w * scale)
    new_h = int(map_h * scale)
    map_scaled = pygame.transform.scale(map_img, (new_w, new_h))
    map_rect = map_scaled.get_rect(center=(win_w//2, win_h//2))

    if offscreen is None or (new_w, new_h) != offscreen.get_size():
        build_grid(map_rect)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                ct_dots, t_dots = create_dots()
                all_dots = ct_dots + t_dots
                selected_dot = None
            elif event.key == pygame.K_i:
                assign_cts_to_info(ct_dots, t_dots)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                clicked_dot = None
                for dot in all_dots:
                    if dot.contains(event.pos, map_rect):
                        clicked_dot = dot
                        break
                if clicked_dot:
                    for d in all_dots:
                        d.selected = False
                    clicked_dot.selected = True
                    selected_dot = clicked_dot
                else:
                    if selected_dot:
                        target = pixel_to_percent(event.pos[0], event.pos[1], map_rect)
                        selected_dot.set_destination(target)
                        selected_dot.selected = False
                        selected_dot = None

    for dot in all_dots:
        dot.update(MOVE_SPEED)

    screen.fill((30, 30, 30))
    screen.blit(map_scaled, map_rect)

    draw_connection_lines(screen, ct_dots, t_dots, map_rect)
    draw_depth_lines(screen, ct_dots, map_rect)

    for dot in all_dots:
        dot.draw(screen, map_rect)

    current_score = calculate_total_score(ct_dots, t_dots)
    score_font = pygame.font.SysFont("Arial", 24, bold=True)
    score_text = f"Depth Score: {current_score:.1f}"
    score_surf = score_font.render(score_text, True, (255, 255, 255))
    score_rect = score_surf.get_rect(topright=(win_w - 20, 20))
    pygame.draw.rect(screen, (20, 20, 20, 180), score_rect.inflate(20, 12))
    screen.blit(score_surf, score_rect)

    status_font = pygame.font.SysFont("Arial", 16)
    if selected_dot:
        team_name = "CT" if selected_dot.team == 'ct' else "T"
        status = f"{team_name} #{selected_dot.number} selected – click map to set destination"
    else:
        status = "Click dot to select • R reset • I depth info (fixed)"
    text_surf = status_font.render(status, True, (200, 200, 200))
    screen.blit(text_surf, (10, win_h - 25))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()