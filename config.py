import sys
import os

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

LOGICAL_WIDTH = 960
LOGICAL_HEIGHT = 720
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720
FPS = 60


# Board Dimensions
BOARD_ROWS = 8
BOARD_COLS = 8
TILE_SIZE = 64
BOARD_OFFSET_X = 320
BOARD_OFFSET_Y = 120

NUM_PIECE_TYPES = 6

# Area Progression Table (requirements.md)
# Format: (Score Threshold, Flag/Area Name, Narrative Splash Message)
AREA_PROGRESSION = [
    (0, "東京 (日本)", "スタート地点\n馴染み深い街並みと準備編"),
    (5000, "ソウル (韓国)", "近場の海外へ！\nネオン街とグルメ"),
    (12000, "バンコク (タイ)", "アジアの熱気と寺院めぐり"),
    (22000, "デリー (インド)", "エキゾチックな街並みと\n賑やかな市場"),
    (35000, "ドバイ (UAE)", "近未来的な高層ビルと\n砂漠リゾート"),
    (52000, "パリ (フランス)", "ヨーロッパ到達！\nおしゃれなカフェと芸術の街"),
    (72000, "ロンドン (イギリス)", "歴史ある街並みとテック都市"),
    (95000, "リオデジャネイロ (ブラジル)", "大西洋を越えて南米へ！\n情熱的なビーチ"),
    (122000, "ニューヨーク (アメリカ)", "北米の大都市！\nエンタメと最新テック"),
    (155000, "ホノルル (ハワイ)", "太平洋の楽園で\nリゾート気分"),
    (200000, "東京 (ゴール/2周目へ)", "世界一周達成！\n凱旋帰国とハイスコア到達")
]

# Color Palette (Dark Mode & Vibrant Accent Theme)
COLOR_BG = (20, 24, 38)
COLOR_PANEL_BG = (32, 38, 58)
COLOR_PANEL_BORDER = (60, 72, 105)
COLOR_BOARD_BG = (15, 18, 30)
COLOR_BOARD_GRID = (45, 55, 80)
COLOR_TEXT = (240, 245, 255)
COLOR_MUTED_TEXT = (140, 155, 185)
COLOR_ACCENT = (255, 215, 0) # Gold
COLOR_ACCENT_HOVER = (255, 235, 100)
COLOR_BUTTON = (55, 115, 220)
COLOR_BUTTON_HOVER = (75, 140, 250)
COLOR_BUTTON_SECONDARY = (65, 75, 100)
COLOR_BUTTON_SECONDARY_HOVER = (85, 95, 125)
COLOR_SELECTION = (255, 255, 255)
COLOR_COMBO_TEXT = (255, 100, 180)
COLOR_MILESTONE_BG = (10, 15, 30, 230)
COLOR_MILESTONE_BORDER = (255, 215, 0)
