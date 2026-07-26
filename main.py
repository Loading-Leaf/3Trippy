import sys
import os
import pygame
import time
import math
import random
import copy
import asyncio


from config import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BOARD_ROWS, BOARD_COLS, TILE_SIZE,
    BOARD_OFFSET_X, BOARD_OFFSET_Y, AREA_PROGRESSION,
    COLOR_BG, COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_BOARD_BG, COLOR_BOARD_GRID,
    COLOR_TEXT, COLOR_MUTED_TEXT, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_BUTTON, COLOR_BUTTON_HOVER, COLOR_BUTTON_SECONDARY, COLOR_BUTTON_SECONDARY_HOVER,
    COLOR_SELECTION, COLOR_COMBO_TEXT, COLOR_MILESTONE_BG, COLOR_MILESTONE_BORDER,
    get_resource_path
)

from audio_manager import AudioManager
from board import Board

def draw_special_item_overlay(surface, rect, special_type, anim_time):
    """Draws glowing icons/badges over special items."""
    cx, cy = rect.center
    if special_type == 'LINE_H':
        pygame.draw.rect(surface, (255, 255, 255), (cx - 20, cy - 3, 40, 6), border_radius=3)
        pygame.draw.polygon(surface, (255, 255, 255), [(cx - 20, cy - 7), (cx - 20, cy + 7), (cx - 26, cy)])
        pygame.draw.polygon(surface, (255, 255, 255), [(cx + 20, cy - 7), (cx + 20, cy + 7), (cx + 26, cy)])
        pygame.draw.circle(surface, (255, 215, 0), (cx, cy), 5)
    elif special_type == 'LINE_V':
        pygame.draw.rect(surface, (255, 255, 255), (cx - 3, cy - 20, 6, 40), border_radius=3)
        pygame.draw.polygon(surface, (255, 255, 255), [(cx - 7, cy - 20), (cx + 7, cy - 20), (cx, cy - 26)])
        pygame.draw.polygon(surface, (255, 255, 255), [(cx - 7, cy + 20), (cx + 7, cy + 20), (cx, cy + 26)])
        pygame.draw.circle(surface, (255, 215, 0), (cx, cy), 5)
    elif special_type == 'CROSS':
        pygame.draw.rect(surface, (255, 220, 0), (cx - 18, cy - 4, 36, 8), border_radius=4)
        pygame.draw.rect(surface, (255, 220, 0), (cx - 4, cy - 18, 8, 36), border_radius=4)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 5)
    elif special_type == 'BOMB_3X3':
        pygame.draw.circle(surface, (240, 50, 50), (cx, cy), 14)
        pygame.draw.circle(surface, (255, 215, 0), (cx, cy), 14, width=2)
        pygame.draw.circle(surface, (255, 255, 255), (cx - 3, cy - 3), 3)
    elif special_type == 'COLOR_BOMB':
        pulse = math.sin(anim_time * 6.0) * 0.15 + 1.0
        r_size = int(18 * pulse)
        colors = [(255, 80, 80), (255, 200, 40), (80, 220, 100), (80, 160, 255), (200, 100, 255)]
        num_c = len(colors)
        for i in range(num_c):
            angle = anim_time * 4.0 + i * (2 * math.pi / num_c)
            ox = int(cx + math.cos(angle) * (r_size * 0.65))
            oy = int(cy + math.sin(angle) * (r_size * 0.65))
            pygame.draw.circle(surface, colors[i], (ox, oy), 6)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 5)


# Scene Constants
SCENE_TITLE = 'TITLE'
SCENE_HOW_TO_PLAY = 'HOW_TO_PLAY'
SCENE_GAME = 'GAME'
SCENE_GAME_OVER = 'GAME_OVER'

def ease_out_quad(t):
    return t * (2 - t)

def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2.0

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(80, 260)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.size = random.uniform(4, 9)
        self.life = 1.0 # 1.0 down to 0
        self.decay = random.uniform(2.0, 3.5)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 150 * dt # gravity
        self.life -= self.decay * dt

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = int(255 * max(0, self.life))
        color_with_alpha = (*self.color[:3], alpha)
        s = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, color_with_alpha, (int(self.size), int(self.size)), int(self.size * self.life))
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))

class FloatingText:
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 1.0 # 1.0 down to 0
        self.decay = 1.2

    def update(self, dt):
        self.y -= 45 * dt # float up
        self.life -= self.decay * dt

    def draw(self, surface, font):
        if self.life <= 0:
            return
        alpha = int(255 * max(0, self.life))
        txt_surf = font.render(self.text, True, self.color)
        txt_surf.set_alpha(alpha)
        rect = txt_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(txt_surf, rect)

class Button:
    def __init__(self, rect, text, font, bg_color=COLOR_BUTTON, hover_color=COLOR_BUTTON_HOVER, text_color=COLOR_TEXT):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, (255, 255, 255, 60), self.rect, width=2, border_radius=12)
        
        txt_surf = self.font.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

def render_wrapped_text(surface, text, font, color, rect, align='left', line_spacing=4):
    """
    Renders multi-line wrapped text inside `rect` on `surface`.
    Supports CJK (Japanese) character wrapping and explicit newline (\n) splitting without overflowing rect boundaries.
    `align` can be 'left' or 'center'.
    """
    if not text:
        return
    paragraphs = text.split('\n')
    lines = []
    for para in paragraphs:
        if not para:
            lines.append("")
            continue
        words_or_chars = []
        current_word = ""
        for char in para:
            if char == ' ':
                if current_word:
                    words_or_chars.append(current_word + ' ')
                    current_word = ""
            else:
                if ord(char) > 127: # CJK / Japanese character
                    if current_word:
                        words_or_chars.append(current_word)
                        current_word = ""
                    words_or_chars.append(char)
                else:
                    current_word += char
        if current_word:
            words_or_chars.append(current_word)

        current_line = ""
        for item in words_or_chars:
            test_line = current_line + item
            if font.size(test_line.strip())[0] <= rect.width:
                current_line = test_line
            else:
                if current_line.strip():
                    lines.append(current_line.strip())
                current_line = item
        if current_line.strip():
            lines.append(current_line.strip())

    line_height = font.get_height()
    y = rect.top

    for line in lines:
        if y + line_height > rect.bottom:
            break
        if line:
            txt_surf = font.render(line, True, color)
            if align == 'center':
                txt_rect = txt_surf.get_rect(center=(rect.centerx, y + line_height // 2))
                surface.blit(txt_surf, txt_rect)
            else:
                surface.blit(txt_surf, (rect.left, y))
        y += line_height + line_spacing


class GameApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("3 Trippy - スリー・トリッピー パズル")
        
        self.win_width = SCREEN_WIDTH
        self.win_height = SCREEN_HEIGHT
        self.is_fullscreen = False
        
        # Display setup with REZISABLE flag
        self.real_screen = pygame.display.set_mode((self.win_width, self.win_height), pygame.RESIZABLE)
        self.virtual_surface = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
        self.screen = self.virtual_surface

        
        self.clock = pygame.time.Clock()
        self.audio = AudioManager()
        
        self.setup_fonts()
        self.load_images()
        
        # State Variables
        self.scene = SCENE_TITLE
        self.board = Board()
        self.score = 0
        self.selected_tile = None
        self.drag_start_tile = None
        self.drag_start_pos = None
        
        # Area Progression Tracking
        self.current_area_index = 0
        self.unlocked_area_indices = {0}
        
        # Milestone Popup Banner (5-second display requirement)
        self.milestone_banner = None
        self.last_combo = 0
        self.combo_timer = 0
        
        # Animation States & Systems
        self.is_animating = False
        self.anim_queue = [] # Queue of animation steps
        self.current_anim = None
        
        self.particles = []
        self.floating_texts = []
        
        # Pulse timer for selected tile
        self.anim_time = 0.0

        self.setup_buttons()
        self.audio.play_bgm('sounds/bgm_title.wav')

    def get_scale_and_offset(self):
        cur_w, cur_h = self.real_screen.get_size()
        scale = min(cur_w / float(LOGICAL_WIDTH), cur_h / float(LOGICAL_HEIGHT))
        offset_x = int((cur_w - LOGICAL_WIDTH * scale) / 2.0)
        offset_y = int((cur_h - LOGICAL_HEIGHT * scale) / 2.0)
        return scale, offset_x, offset_y

    def get_logical_pos(self, win_pos):
        scale, offset_x, offset_y = self.get_scale_and_offset()
        wx, wy = win_pos
        lx = int((wx - offset_x) / scale)
        ly = int((wy - offset_y) / scale)
        return (lx, ly)

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.real_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
        else:
            self.real_screen = pygame.display.set_mode((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.RESIZABLE)
        self.screen = self.virtual_surface

    def setup_fonts(self):
        font_path = get_resource_path(os.path.join('fonts', 'JapaneseFont.ttf'))
        if os.path.exists(font_path):
            try:
                self.font_large = pygame.font.Font(font_path, 40)
                self.font_medium = pygame.font.Font(font_path, 24)
                self.font_small = pygame.font.Font(font_path, 18)
                self.font_tiny = pygame.font.Font(font_path, 14)
                return
            except Exception as e:
                print(f"Failed loading bundled Japanese font: {e}")

        jp_fonts = ['msgothic', 'meiryo', 'yu gothic', 'hiragino sans', 'arial']
        self.font_large = pygame.font.SysFont(jp_fonts, 42, bold=True)
        self.font_medium = pygame.font.SysFont(jp_fonts, 28, bold=True)
        self.font_small = pygame.font.SysFont(jp_fonts, 20)
        self.font_tiny = pygame.font.SysFont(jp_fonts, 16)


    def load_images(self):
        title_path = get_resource_path(os.path.join('sprite', 'title.png'))
        if os.path.exists(title_path):
            title_raw = pygame.image.load(title_path).convert_alpha()
            self.img_title = pygame.transform.smoothscale(title_raw, (300, 300))
        else:
            self.img_title = None

        self.tile_sprites = []
        puzzle_dir = get_resource_path(os.path.join('sprite', 'puzzle'))
        self.tile_colors = [
            (255, 80, 80), (80, 160, 255), (80, 220, 100),
            (255, 220, 60), (200, 100, 255), (255, 140, 40)
        ]
        
        for i in range(6):
            p_path = os.path.join(puzzle_dir, f'trippy_{i}.png')
            if os.path.exists(p_path):
                img = pygame.image.load(p_path).convert_alpha()
                img_scaled = pygame.transform.smoothscale(img, (TILE_SIZE - 6, TILE_SIZE - 6))
                self.tile_sprites.append(img_scaled)
            else:
                surf = pygame.Surface((TILE_SIZE - 6, TILE_SIZE - 6), pygame.SRCALPHA)
                surf.fill(self.tile_colors[i % 6])
                self.tile_sprites.append(surf)

    def setup_buttons(self):
        cx = LOGICAL_WIDTH // 2
        self.btn_title_start = Button((cx - 130, 465, 260, 52), "ゲームスタート", self.font_medium)
        self.btn_title_howto = Button((cx - 130, 530, 260, 48), "遊び方・説明", self.font_medium, bg_color=COLOR_BUTTON_SECONDARY, hover_color=COLOR_BUTTON_SECONDARY_HOVER)
        self.btn_title_audio = Button((cx - 130, 590, 260, 45), "サウンド: ON", self.font_small, bg_color=(45, 55, 80), hover_color=(65, 75, 105))

        self.btn_howto_back = Button((cx - 100, 630, 200, 50), "タイトルへ戻る", self.font_medium)

        self.btn_game_audio = Button((40, 620, 120, 45), "音量 ON", self.font_small, bg_color=COLOR_BUTTON_SECONDARY, hover_color=COLOR_BUTTON_SECONDARY_HOVER)
        self.btn_game_title = Button((170, 620, 120, 45), "タイトルへ", self.font_small, bg_color=COLOR_BUTTON_SECONDARY, hover_color=COLOR_BUTTON_SECONDARY_HOVER)


        self.btn_over_restart = Button((cx - 130, 480, 300, 55), "もう一度遊ぶ", self.font_medium)
        self.btn_over_title = Button((cx - 130, 555, 300, 50), "タイトルへ戻る", self.font_medium, bg_color=COLOR_BUTTON_SECONDARY, hover_color=COLOR_BUTTON_SECONDARY_HOVER)


    def start_new_game(self):
        self.score = 0
        self.board.reset_board()
        self.selected_tile = None
        self.drag_start_tile = None
        self.drag_start_pos = None
        self.current_area_index = 0
        self.unlocked_area_indices = {0}
        self.milestone_banner = None
        self.is_animating = False
        self.anim_queue = []
        self.current_anim = None
        self.particles = []
        self.floating_texts = []
        self.scene = SCENE_GAME
        self.audio.play_bgm('sounds/bgm_main.wav')

    def check_area_progression(self):
        for i, (threshold, area_name, msg) in enumerate(AREA_PROGRESSION):
            if self.score >= threshold and i not in self.unlocked_area_indices:
                self.unlocked_area_indices.add(i)
                self.current_area_index = i
                self.milestone_banner = {
                    'title': area_name,
                    'msg': msg,
                    'start_time': time.time()
                }
                self.audio.play_sfx('levelup')
                break
        
        for i in range(len(AREA_PROGRESSION) - 1, -1, -1):
            if self.score >= AREA_PROGRESSION[i][0]:
                self.current_area_index = i
                break

    def spawn_match_particles(self, r, c, piece):
        cx = BOARD_OFFSET_X + c * TILE_SIZE + TILE_SIZE // 2
        cy = BOARD_OFFSET_Y + r * TILE_SIZE + TILE_SIZE // 2
        p_type = self.board.get_piece_type(piece)
        if p_type is None or p_type >= len(self.tile_colors):
            color = (255, 215, 0)
        else:
            color = self.tile_colors[p_type % len(self.tile_colors)]
        for _ in range(14):
            self.particles.append(Particle(cx, cy, color))

    def trigger_swap_animation(self, r1, c1, r2, c2):
        is_valid = self.board.can_swap_and_match(r1, c1, r2, c2)
        swap_dir = 'H' if r1 == r2 else 'V'
        
        swap_step = {
            'type': 'SWAP',
            'pos1': (r1, c1),
            'pos2': (r2, c2),
            'piece1': copy.deepcopy(self.board.grid[r1][c1]),
            'piece2': copy.deepcopy(self.board.grid[r2][c2]),
            'duration': 0.16,
            'timer': 0.0,
            'is_valid': is_valid
        }
        
        if is_valid:
            self.board.swap_grid_cells(r1, c1, r2, c2)
            self.anim_queue = [swap_step]
            self.queue_cascade_animations(combo_step=0, last_swap_pair=((r1, c1), (r2, c2)), swap_dir=swap_dir)
        else:
            revert_step = {
                'type': 'SWAP',
                'pos1': (r2, c2),
                'pos2': (r1, c1),
                'piece1': copy.deepcopy(self.board.grid[r1][c1]),
                'piece2': copy.deepcopy(self.board.grid[r2][c2]),
                'duration': 0.16,
                'timer': 0.0,
                'is_valid': True
            }
            self.anim_queue = [swap_step, revert_step]
            
        self.is_animating = True

    def queue_cascade_animations(self, combo_step, last_swap_pair=None, swap_dir=None):
        matched_cells, match_groups, created_specials = self.board.find_current_matches(last_swap_pair=last_swap_pair, swap_dir=swap_dir)
        if not matched_cells:
            if not self.board.has_valid_moves():
                self.anim_queue.append({'type': 'GAME_OVER'})
            return


        score_gained = self.board.calculate_score_for_groups(match_groups, combo_step)
        
        pop_step = {
            'type': 'POP',
            'matched_cells': list(matched_cells),
            'created_specials': created_specials,
            'pieces': {cell: copy.deepcopy(self.board.grid[cell[0]][cell[1]]) for cell in matched_cells},
            'duration': 0.18,
            'timer': 0.0,
            'score_gained': score_gained,
            'combo_step': combo_step
        }
        self.anim_queue.append(pop_step)

        # Clear matched cells in board logic, spawning created special items!
        for r, c in matched_cells:
            if (r, c) in created_specials:
                self.board.grid[r][c] = copy.deepcopy(created_specials[(r, c)])
            else:
                self.board.grid[r][c] = None

        drops = self.board.apply_gravity_step()
        
        drop_step = {
            'type': 'DROP',
            'drops': drops,
            'duration': 0.22,
            'timer': 0.0
        }
        self.anim_queue.append(drop_step)
        
        self.queue_cascade_animations(combo_step + 1)


    async def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.anim_time += dt
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()
            await asyncio.sleep(0)


    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.VIDEORESIZE:
                if not self.is_fullscreen:
                    self.win_width, self.win_height = event.w, event.h
                    self.real_screen = pygame.display.set_mode((self.win_width, self.win_height), pygame.RESIZABLE)
                    self.screen = self.virtual_surface


            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11 or (event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)):
                    self.toggle_fullscreen()

            # Map mouse coordinates from window space to virtual canvas space
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                if hasattr(event, 'pos'):
                    logical_pos = self.get_logical_pos(event.pos)
                    event = pygame.event.Event(event.type, {**event.dict, 'pos': logical_pos})

            if self.scene == SCENE_TITLE:
                if self.btn_title_start.handle_event(event):
                    self.audio.play_sfx('click')
                    self.start_new_game()
                elif self.btn_title_howto.handle_event(event):
                    self.audio.play_sfx('click')
                    self.scene = SCENE_HOW_TO_PLAY
                elif self.btn_title_audio.handle_event(event):
                    muted = self.audio.toggle_mute()
                    self.btn_title_audio.text = "サウンド: OFF" if muted else "サウンド: ON"
                    self.btn_game_audio.text = "音量 OFF" if muted else "音量 ON"

            elif self.scene == SCENE_HOW_TO_PLAY:
                if self.btn_howto_back.handle_event(event):
                    self.audio.play_sfx('click')
                    self.scene = SCENE_TITLE

            elif self.scene == SCENE_GAME:
                if self.btn_game_audio.handle_event(event):
                    muted = self.audio.toggle_mute()
                    self.btn_game_audio.text = "音量 OFF" if muted else "音量 ON"
                    self.btn_title_audio.text = "サウンド: OFF" if muted else "サウンド: ON"
                elif self.btn_game_title.handle_event(event):
                    self.audio.play_sfx('click')
                    self.scene = SCENE_TITLE
                    self.drag_start_tile = None
                    self.drag_start_pos = None
                    self.selected_tile = None
                    self.audio.play_bgm('sounds/bgm_title.wav')

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.is_animating:
                        continue
                    mx, my = event.pos
                    col = (mx - BOARD_OFFSET_X) // TILE_SIZE
                    row = (my - BOARD_OFFSET_Y) // TILE_SIZE
                    if 0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS:
                        self.drag_start_tile = (row, col)
                        self.drag_start_pos = (mx, my)
                        self.selected_tile = (row, col)
                        self.audio.play_sfx('select')

                elif event.type == pygame.MOUSEMOTION:
                    if self.drag_start_tile is not None and not self.is_animating:
                        r1, c1 = self.drag_start_tile
                        sx, sy = self.drag_start_pos
                        mx, my = event.pos
                        dx = mx - sx
                        dy = my - sy
                        
                        SWIPE_THRESHOLD = 15
                        if abs(dx) >= SWIPE_THRESHOLD or abs(dy) >= SWIPE_THRESHOLD:
                            if abs(dx) > abs(dy):
                                dr, dc = 0, 1 if dx > 0 else -1
                            else:
                                dr, dc = 1 if dy > 0 else -1, 0
                            
                            r2, c2 = r1 + dr, c1 + dc
                            self.selected_tile = None
                            self.drag_start_tile = None
                            self.drag_start_pos = None
                            if 0 <= r2 < BOARD_ROWS and 0 <= c2 < BOARD_COLS:
                                self.trigger_swap_animation(r1, c1, r2, c2)

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.drag_start_tile is not None:
                        if not self.is_animating:
                            r1, c1 = self.drag_start_tile
                            sx, sy = self.drag_start_pos
                            mx, my = event.pos
                            dx = mx - sx
                            dy = my - sy
                            SWIPE_THRESHOLD = 15
                            if abs(dx) >= SWIPE_THRESHOLD or abs(dy) >= SWIPE_THRESHOLD:
                                if abs(dx) > abs(dy):
                                    dr, dc = 0, 1 if dx > 0 else -1
                                else:
                                    dr, dc = 1 if dy > 0 else -1, 0
                                r2, c2 = r1 + dr, c1 + dc
                                if 0 <= r2 < BOARD_ROWS and 0 <= c2 < BOARD_COLS:
                                    self.trigger_swap_animation(r1, c1, r2, c2)
                        self.selected_tile = None
                        self.drag_start_tile = None
                        self.drag_start_pos = None

            elif self.scene == SCENE_GAME_OVER:
                if self.btn_over_restart.handle_event(event):
                    self.audio.play_sfx('click')
                    self.start_new_game()
                elif self.btn_over_title.handle_event(event):
                    self.audio.play_sfx('click')
                    self.scene = SCENE_TITLE
                    self.audio.play_bgm('sounds/bgm_title.wav')

    def update(self, dt):
        # Update particles & floating texts
        for p in self.particles[:]:
            p.update(dt)
            if p.life <= 0:
                self.particles.remove(p)
                
        for ft in self.floating_texts[:]:
            ft.update(dt)
            if ft.life <= 0:
                self.floating_texts.remove(ft)

        if self.combo_timer > 0:
            self.combo_timer -= dt

        if self.milestone_banner:
            elapsed = time.time() - self.milestone_banner['start_time']
            if elapsed >= 5.0: # 5-second milestone banner display
                self.milestone_banner = None

        # Process Animation Queue
        if self.is_animating:
            if self.current_anim is None and len(self.anim_queue) > 0:
                self.current_anim = self.anim_queue.pop(0)
                
                # Trigger sound effects on anim start
                if self.current_anim['type'] == 'SWAP':
                    self.audio.play_sfx('swap')
                elif self.current_anim['type'] == 'POP':
                    combo = self.current_anim['combo_step']
                    score = self.current_anim['score_gained']
                    self.score += score
                    self.check_area_progression()
                    
                    if combo > 0:
                        self.audio.play_sfx('combo')
                        self.last_combo = combo + 1
                        self.combo_timer = 2.0
                    else:
                        self.audio.play_sfx('match')
                        
                    # Spawn particles and floating score texts
                    for r, c in self.current_anim['matched_cells']:
                        p_type = self.current_anim['pieces'][(r, c)]
                        self.spawn_match_particles(r, c, p_type)
                        
                    # Calculate center position for floating score text
                    avg_r = sum(r for r, c in self.current_anim['matched_cells']) / len(self.current_anim['matched_cells'])
                    avg_c = sum(c for r, c in self.current_anim['matched_cells']) / len(self.current_anim['matched_cells'])
                    fx = BOARD_OFFSET_X + avg_c * TILE_SIZE + TILE_SIZE // 2
                    fy = BOARD_OFFSET_Y + avg_r * TILE_SIZE + TILE_SIZE // 2
                    
                    txt = f"+{score}" if combo == 0 else f"{combo + 1} COMBO! +{score}"
                    color = COLOR_COMBO_TEXT if combo > 0 else COLOR_ACCENT
                    self.floating_texts.append(FloatingText(fx, fy, txt, color))
                    
                elif self.current_anim['type'] == 'GAME_OVER':
                    self.scene = SCENE_GAME_OVER
                    self.audio.play_sfx('gameover')
                    self.is_animating = False
                    self.current_anim = None
                    return

            if self.current_anim:
                self.current_anim['timer'] += dt
                if self.current_anim['timer'] >= self.current_anim['duration']:
                    self.current_anim = None
                    if len(self.anim_queue) == 0:
                        self.is_animating = False

    def draw(self):
        self.virtual_surface.fill(COLOR_BG)

        if self.scene == SCENE_TITLE:
            self.draw_title_scene()
        elif self.scene == SCENE_HOW_TO_PLAY:
            self.draw_howto_scene()
        elif self.scene == SCENE_GAME:
            self.draw_game_scene()
        elif self.scene == SCENE_GAME_OVER:
            self.draw_game_scene()
            self.draw_gameover_scene()

        # Scale virtual_surface onto real_screen keeping aspect ratio
        scale, offset_x, offset_y = self.get_scale_and_offset()
        scaled_w = max(1, int(LOGICAL_WIDTH * scale))
        scaled_h = max(1, int(LOGICAL_HEIGHT * scale))

        self.real_screen.fill(COLOR_BG)
        scaled_surf = pygame.transform.smoothscale(self.virtual_surface, (scaled_w, scaled_h))
        self.real_screen.blit(scaled_surf, (offset_x, offset_y))


    def draw_title_scene(self):
        pygame.draw.circle(self.screen, (30, 45, 75), (150, 130), 180)
        pygame.draw.circle(self.screen, (35, 30, 65), (800, 580), 220)

        # 1. Title Image at Top (centered at y=170)
        if self.img_title:
            rect = self.img_title.get_rect(center=(LOGICAL_WIDTH // 2, 170))
            self.screen.blit(self.img_title, rect)

        # 2. Main Title Text placed UNDER Title Image (at y=345)
        t_surf = self.font_large.render("3 Trippy", True, COLOR_ACCENT)
        self.screen.blit(t_surf, t_surf.get_rect(center=(LOGICAL_WIDTH // 2, 345)))

        # 3. Subtitle Text placed UNDER Title Text (at y=395), with auto wrapping
        sub_rect = pygame.Rect(60, 395, 840, 50)
        render_wrapped_text(self.screen, "トリッピーの3マッチ・世界一周パズル旅！", self.font_small, COLOR_MUTED_TEXT, sub_rect, align='center')

        # 4. Action Buttons
        self.btn_title_start.draw(self.screen)
        self.btn_title_howto.draw(self.screen)
        self.btn_title_audio.draw(self.screen)

    def draw_howto_scene(self):
        panel_rect = pygame.Rect(100, 40, LOGICAL_WIDTH - 200, 560)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, panel_rect, width=3, border_radius=16)

        title = self.font_large.render("遊び方・ルール説明", True, COLOR_ACCENT)
        self.screen.blit(title, title.get_rect(center=(LOGICAL_WIDTH // 2, 85)))

        instructions = [
            "【基本操作】",
            "・ピースを動かしたい方向にスワイプ（ドラッグ）して入れ替え、3つ以上並べます。",
            "",
            "【特殊爆弾＆アイテム（Candy & POP）】",
            "・4消し（横/縦移動）: 一行・一列を全消去する「ライン爆弾 ↔/↕」生成！",
            "・5直列消し: 指定した色を全消しする「虹色オーブ 🌈」生成！",
            "・十字/L字消し: 縦横クロスに爆発する「十字爆弾 ✚」生成！",
            "・2×2消し: 周囲9マスを吹き飛ばす「9マス爆弾 💣」生成！",
            "",
            "【エリア進行＆世界一周】",
            "・スコアに応じて「東京」から「ソウル」「パリ」を経て世界一周を目指そう！"
        ]


        y_pos = 145
        for line in instructions:
            if line.startswith("【"):
                color = COLOR_ACCENT
                font = self.font_medium
                txt = font.render(line, True, color)
                self.screen.blit(txt, (140, y_pos))
                y_pos += 32
            elif line == "":
                y_pos += 12
            else:
                color = COLOR_TEXT
                font = self.font_small
                line_rect = pygame.Rect(140, y_pos, panel_rect.width - 80, 50)
                render_wrapped_text(self.screen, line, font, color, line_rect, align='left')
                y_pos += 30

        self.btn_howto_back.draw(self.screen)

    def draw_game_scene(self):
        # Draw Sidebar
        sidebar_rect = pygame.Rect(30, 30, 265, 660)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, sidebar_rect, border_radius=16)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, sidebar_rect, width=2, border_radius=16)

        sb_title = self.font_medium.render("3 Trippy", True, COLOR_ACCENT)
        self.screen.blit(sb_title, (50, 50))

        lbl_score = self.font_tiny.render("CURRENT SCORE", True, COLOR_MUTED_TEXT)
        self.screen.blit(lbl_score, (50, 95))
        txt_score = self.font_large.render(f"{self.score:,}", True, COLOR_TEXT)
        self.screen.blit(txt_score, (50, 120))

        cur_area = AREA_PROGRESSION[self.current_area_index]
        lbl_area = self.font_tiny.render("CURRENT AREA", True, COLOR_MUTED_TEXT)
        self.screen.blit(lbl_area, (50, 185))
        txt_area_name = self.font_medium.render(cur_area[1], True, COLOR_ACCENT)
        self.screen.blit(txt_area_name, (50, 210))
        
        # Wrapped Narrative Description for Current Area
        desc_rect = pygame.Rect(50, 245, 225, 45)
        render_wrapped_text(self.screen, cur_area[2], self.font_tiny, COLOR_MUTED_TEXT, desc_rect, align='left')

        if self.current_area_index < len(AREA_PROGRESSION) - 1:
            next_area = AREA_PROGRESSION[self.current_area_index + 1]
            prev_thresh = cur_area[0]
            next_thresh = next_area[0]
            prog_ratio = min(1.0, max(0.0, (self.score - prev_thresh) / float(next_thresh - prev_thresh)))
            
            next_text = f"NEXT: {next_area[1]}\n({next_thresh:,} pt)"
            next_rect = pygame.Rect(50, 290, 225, 40)
            render_wrapped_text(self.screen, next_text, self.font_tiny, COLOR_MUTED_TEXT, next_rect, align='left', line_spacing=2)
            
            bar_rect = pygame.Rect(50, 335, 225, 14)
            pygame.draw.rect(self.screen, (20, 25, 40), bar_rect, border_radius=7)
            fill_rect = pygame.Rect(50, 335, int(225 * prog_ratio), 14)
            if fill_rect.width > 0:
                pygame.draw.rect(self.screen, COLOR_ACCENT, fill_rect, border_radius=7)

        else:
            lbl_next = self.font_small.render("🎉 世界一周達成！", True, COLOR_ACCENT)
            self.screen.blit(lbl_next, (50, 290))

        if self.combo_timer > 0 and self.last_combo > 1:
            combo_txt = self.font_medium.render(f"{self.last_combo} COMBO!! (+{self.last_combo * 40})", True, COLOR_COMBO_TEXT)
            self.screen.blit(combo_txt, (50, 360))

        self.btn_game_audio.draw(self.screen)
        self.btn_game_title.draw(self.screen)



        # Draw Board Grid Background
        board_rect = pygame.Rect(BOARD_OFFSET_X - 10, BOARD_OFFSET_Y - 10, BOARD_COLS * TILE_SIZE + 20, BOARD_ROWS * TILE_SIZE + 20)
        pygame.draw.rect(self.screen, COLOR_BOARD_BG, board_rect, border_radius=16)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, board_rect, width=3, border_radius=16)

        # Build rendering matrix / overrides for active animations
        # Default position map: (r, c) -> (screen_x, screen_y, scale, alpha, piece_type)
        render_tiles = []
        animated_cells = set()
        
        if self.current_anim:
            anim = self.current_anim
            progress = min(1.0, anim['timer'] / anim['duration'])
            eased_p = ease_out_quad(progress)
            
            if anim['type'] == 'SWAP':
                r1, c1 = anim['pos1']
                r2, c2 = anim['pos2']
                animated_cells.add((r1, c1))
                animated_cells.add((r2, c2))
                
                x1 = BOARD_OFFSET_X + c1 * TILE_SIZE
                y1 = BOARD_OFFSET_Y + r1 * TILE_SIZE
                x2 = BOARD_OFFSET_X + c2 * TILE_SIZE
                y2 = BOARD_OFFSET_Y + r2 * TILE_SIZE
                
                # Lerp positions
                curr_x1 = x1 + (x2 - x1) * eased_p
                curr_y1 = y1 + (y2 - y1) * eased_p
                curr_x2 = x2 + (x1 - x2) * eased_p
                curr_y2 = y2 + (y1 - y2) * eased_p
                
                render_tiles.append((curr_x1, curr_y1, 1.0, 255, anim['piece1']))
                render_tiles.append((curr_x2, curr_y2, 1.0, 255, anim['piece2']))
                
            elif anim['type'] == 'POP':
                scale = max(0.0, 1.0 - eased_p)
                alpha = int(255 * (1.0 - eased_p))
                for cell in anim['matched_cells']:
                    animated_cells.add(cell)
                    r, c = cell
                    tx = BOARD_OFFSET_X + c * TILE_SIZE
                    ty = BOARD_OFFSET_Y + r * TILE_SIZE
                    render_tiles.append((tx, ty, scale, alpha, anim['pieces'][cell]))
                    
            elif anim['type'] == 'DROP':
                for drop in anim['drops']:
                    to_cell = (drop['to_r'], drop['c'])
                    animated_cells.add(to_cell)
                    
                    from_y = BOARD_OFFSET_Y + drop['from_r'] * TILE_SIZE
                    to_y = BOARD_OFFSET_Y + drop['to_r'] * TILE_SIZE
                    curr_y = from_y + (to_y - from_y) * eased_p
                    curr_x = BOARD_OFFSET_X + drop['c'] * TILE_SIZE
                    
                    render_tiles.append((curr_x, curr_y, 1.0, 255, drop['piece']))

        # Draw grid cells & stationary tiles
        for r in range(BOARD_ROWS):
            for c in range(BOARD_COLS):
                tx = BOARD_OFFSET_X + c * TILE_SIZE
                ty = BOARD_OFFSET_Y + r * TILE_SIZE
                cell_rect = pygame.Rect(tx, ty, TILE_SIZE - 2, TILE_SIZE - 2)
                pygame.draw.rect(self.screen, COLOR_BOARD_GRID, cell_rect, border_radius=8)
                
                if (r, c) not in animated_cells:
                    piece = self.board.grid[r][c]
                    self.draw_piece_cell(self.screen, cell_rect, piece, 1.0, 255)

        # Draw animated tiles overlay
        for tx, ty, scale, alpha, piece in render_tiles:
            cell_rect = pygame.Rect(tx, ty, TILE_SIZE - 2, TILE_SIZE - 2)
            self.draw_piece_cell(self.screen, cell_rect, piece, scale, alpha)

    def draw_piece_cell(self, surface, cell_rect, piece, scale=1.0, alpha=255):
        if piece is None:
            return
        p_type = self.board.get_piece_type(piece)
        p_special = self.board.get_piece_special(piece)

        if p_type is None:
            return

        if 0 <= p_type < len(self.tile_sprites):
            base_sprite = self.tile_sprites[p_type]
        elif p_special == 'COLOR_BOMB':
            base_sprite = pygame.Surface((TILE_SIZE - 6, TILE_SIZE - 6), pygame.SRCALPHA)
            pygame.draw.circle(base_sprite, (255, 215, 0), ((TILE_SIZE - 6)//2, (TILE_SIZE - 6)//2), (TILE_SIZE - 10)//2)
        else:
            base_sprite = self.tile_sprites[0]

        if scale != 1.0 or alpha != 255:
            w = max(1, int(base_sprite.get_width() * scale))
            h = max(1, int(base_sprite.get_height() * scale))
            s_scaled = pygame.transform.smoothscale(base_sprite, (w, h))
            if alpha != 255:
                s_scaled.set_alpha(alpha)
            dest_rect = s_scaled.get_rect(center=cell_rect.center)
            surface.blit(s_scaled, dest_rect)
        else:
            dest_rect = base_sprite.get_rect(center=cell_rect.center)
            surface.blit(base_sprite, dest_rect)

        if p_special:
            draw_special_item_overlay(surface, dest_rect, p_special, self.anim_time)


        # Draw pulsating highlight on selected tile
        if self.selected_tile and not self.is_animating:
            sr, sc = self.selected_tile
            stx = BOARD_OFFSET_X + sc * TILE_SIZE
            sty = BOARD_OFFSET_Y + sr * TILE_SIZE
            cell_rect = pygame.Rect(stx, sty, TILE_SIZE - 2, TILE_SIZE - 2)
            
            # Pulse glow width
            pulse = math.sin(self.anim_time * 8.0) * 0.5 + 0.5
            glow_width = int(3 + pulse * 2)
            pygame.draw.rect(self.screen, COLOR_SELECTION, cell_rect, width=glow_width, border_radius=8)

        # Draw Particles & Floating Text
        for p in self.particles:
            p.draw(self.screen)
            
        for ft in self.floating_texts:
            ft.draw(self.screen, self.font_medium)

        # Draw 5-Second Area Milestone Splash Banner (Requirement)
        if self.milestone_banner:
            self.draw_milestone_banner()

    def draw_milestone_banner(self):
        banner_rect = pygame.Rect(200, 220, 560, 240)
        
        overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, banner_rect, border_radius=20)
        pygame.draw.rect(self.screen, COLOR_MILESTONE_BORDER, banner_rect, width=4, border_radius=20)

        badge_txt = self.font_small.render("STAGE UNLOCKED! / エリア到達！", True, COLOR_ACCENT)
        self.screen.blit(badge_txt, badge_txt.get_rect(center=(banner_rect.centerx, banner_rect.top + 35)))

        area_txt = self.font_large.render(self.milestone_banner['title'], True, COLOR_TEXT)
        self.screen.blit(area_txt, area_txt.get_rect(center=(banner_rect.centerx, banner_rect.top + 85)))

        msg_rect = pygame.Rect(banner_rect.left + 30, banner_rect.top + 135, banner_rect.width - 60, 55)
        render_wrapped_text(self.screen, self.milestone_banner['msg'], self.font_medium, COLOR_ACCENT_HOVER, msg_rect, align='center')

        elapsed = time.time() - self.milestone_banner['start_time']
        remaining_ratio = max(0.0, (5.0 - elapsed) / 5.0)
        timer_bar = pygame.Rect(banner_rect.left + 40, banner_rect.bottom - 25, int((banner_rect.width - 80) * remaining_ratio), 6)
        pygame.draw.rect(self.screen, COLOR_ACCENT, timer_bar, border_radius=3)


    def draw_gameover_scene(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 20, 230))
        self.screen.blit(overlay, (0, 0))

        box_rect = pygame.Rect(230, 140, 500, 480)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, box_rect, border_radius=20)
        pygame.draw.rect(self.screen, (220, 70, 70), box_rect, width=3, border_radius=20)

        title = self.font_large.render("GAME OVER", True, (240, 80, 80))
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 195)))

        reason = self.font_small.render("操作できる組み合わせが無くなりました！", True, COLOR_MUTED_TEXT)
        self.screen.blit(reason, reason.get_rect(center=(SCREEN_WIDTH // 2, 240)))

        s_lbl = self.font_small.render("最終スコア", True, COLOR_MUTED_TEXT)
        self.screen.blit(s_lbl, s_lbl.get_rect(center=(SCREEN_WIDTH // 2, 290)))

        s_val = self.font_large.render(f"{self.score:,} pt", True, COLOR_ACCENT)
        self.screen.blit(s_val, s_val.get_rect(center=(SCREEN_WIDTH // 2, 330)))

        cur_area = AREA_PROGRESSION[self.current_area_index]
        a_lbl = self.font_small.render(f"到達エリア: {cur_area[1]}", True, COLOR_TEXT)
        self.screen.blit(a_lbl, a_lbl.get_rect(center=(SCREEN_WIDTH // 2, 385)))

        self.btn_over_restart.draw(self.screen)
        self.btn_over_title.draw(self.screen)

async def main():
    app = GameApp()
    await app.run()

if __name__ == '__main__':
    asyncio.run(main())

