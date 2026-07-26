import os
import pygame

class AudioManager:
    def __init__(self):
        pygame.mixer.init()
        self.muted = False
        self.current_bgm = None
        self.sounds = {}
        self.load_sounds()
        
    def load_sounds(self):
        sound_files = {
            'click': 'sounds/sfx_click.wav',
            'select': 'sounds/sfx_select.wav',
            'swap': 'sounds/sfx_swap.wav',
            'match': 'sounds/sfx_match.wav',
            'combo': 'sounds/sfx_combo.wav',
            'levelup': 'sounds/sfx_levelup.wav',
            'gameover': 'sounds/sfx_gameover.wav'
        }
        for key, path in sound_files.items():
            if os.path.exists(path):
                self.sounds[key] = pygame.mixer.Sound(path)
                
    def play_sfx(self, name):
        if self.muted or name not in self.sounds:
            return
        self.sounds[name].play()
        
    def play_bgm(self, filename):
        if self.current_bgm == filename:
            return
        self.current_bgm = filename
        if os.path.exists(filename):
            try:
                pygame.mixer.music.load(filename)
                pygame.mixer.music.set_volume(0.4 if not self.muted else 0.0)
                pygame.mixer.music.play(-1)
            except Exception as e:
                print(f"Error playing BGM {filename}: {e}")
                
    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            pygame.mixer.music.set_volume(0.0)
            for s in self.sounds.values():
                s.set_volume(0.0)
        else:
            pygame.mixer.music.set_volume(0.4)
            for s in self.sounds.values():
                s.set_volume(1.0)
        return self.muted
