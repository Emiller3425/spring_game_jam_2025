import pygame
import sys
import math
import random
import collections
import asyncio

# Define a Star class to manage individual stars

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pygame Spring Jam")
        self.screen_width, self.screen_height = 720, 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.display_width, self.display_height = 240, 200
        self.display = pygame.Surface((self.display_width, self.display_height), pygame.SRCALPHA)
        self.clock = pygame.time.Clock()

        self.cx = self.display_width // 2
        self.cy = self.display_height // 2

    def main(self):
        self.rotation_speed_y = random.randint(-2,2) * 0.02  # radians per frame around Y-axis
        self.rotation_speed_x = random.randint(-2,2) * 0.01 
        while True:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Create a Pygame surface for the frame
            main_surface = pygame.Surface((self.display_width, self.display_height), pygame.SRCALPHA)
            main_surface.fill((0, , 0, 255))  # Fill with black

            # Scale the display to the screen size
            scaled_display = pygame.transform.scale(main_surface, (self.screen_width, self.screen_height))
            self.screen.blit(scaled_display, (0, 0))

            # Update the display
            pygame.display.update()
            self.clock.tick(60)  # Limit to 60 FPS


if __name__ == "__main__":
   game = Game()
   game.main()
