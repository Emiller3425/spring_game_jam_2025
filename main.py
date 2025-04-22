import pygame
import sys
import math
import random
import collections
import asyncio
from scripts.entities import PhysicsEntity, Player, Enemy, Boss
from scripts.utils import *
from scripts.tilemap import Tilemap
from scripts.particle import Particle, SkullParticle
import asyncio

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Penumbra path")
        self.screen_width, self.screen_height = 720, 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.display_width, self.display_height = 240, 200
        self.display = pygame.Surface((self.display_width, self.display_height), pygame.SRCALPHA)
        self.clock = pygame.time.Clock()

        self.current_level = None

        self.levels = {
            'level_1': {'completed': False, 'tilemap': 'level_1', 'background': 'background_1'}
        }

        self.assets = {
            'walls' : load_images('spritesheet_images/walls'),
            'background_1' : load_image("backgrounds/0.png"),
            'shadow' : load_image('animations_spritesheet/shadow/0.png'),
            'shadow/idle': Animation(load_images('animations_spritesheet/shadow/idle'), img_dur=10),
            'light' : load_image('animations_spritesheet/light/0.png'),
            'light/idle': Animation(load_images('animations_spritesheet/light/idle'), img_dur=10),
        }

        self.audio = {

        }

        self.music = {

        }

    def load_level(self, level_name):
        self.tilemap = Tilemap(self, tile_size=16)
        self.tilemap.load(self.levels[level_name]['tilemap'])

        self.player1 = Player(self, 'light', (self.tilemap.player_position[0] * self.tilemap.tile_size, self.tilemap.player_position[1] * self.tilemap.tile_size), (6, 16))

        self.player2 = Player(self, 'shadow', (self.tilemap.player_position[0] * self.tilemap.tile_size, self.tilemap.player_position[1] * self.tilemap.tile_size), (6, 16))


    def main(self):
        self.current_level = "level_1"
        self.load_level("level_1")
        self.current_background = self.assets[self.levels[self.current_level]['background']]
        while True:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

            # Scale the display to the screen size
            scaled_display = pygame.transform.scale(self.display, (self.screen_width, self.screen_height))
            self.screen.blit(scaled_display, (0, 0))
            self.display.blit(self.current_background, (0, 0))

            # Update the display
            pygame.display.update()
            self.clock.tick(60)  # Limit to 60 FPS


if __name__ == "__main__":
   game = Game()
   game.main()
