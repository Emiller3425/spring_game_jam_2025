import pygame

class Particle:
    def __init__(self, game, p_type, pos, velocity=[0, 0], frame=0):
        self.game = game
        self.type = p_type
        self.pos = list(pos)
        self.velocity = list(velocity)
        self.animation = self.game.assets['particle/' + p_type].copy()
        self.animation_frame = frame

    def update(self):
        kill = False
        if self.animation.done:
            kill = True

        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

        self.animation.update()

        return kill

    def render(self, surf, offset=(0, 0)):
        img = self.animation.img()
        surf.blit(img, (self.pos[0] - offset[0] - img.get_width() // 2, self.pos[1] - offset[1] - img.get_height() // 2))


class SkullParticle:
    def __init__(self, game, pos):
        self.game = game
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(0, -0.3)
        self.lifetime = 120  # 3 seconds at 60 FPS
        self.image = game.assets['skull']
        self.alpha = 255

    def update(self):
        self.pos += self.velocity
        self.lifetime -= 1
        self.alpha = max(0, int(255 * (self.lifetime / 180)))
        if self.lifetime <= 0:
            return True
        return False

    def render(self, surf, offset=(0, 0)):
        img = self.image.copy()
        img.set_alpha(self.alpha)
        surf.blit(img, (self.pos.x - offset[0], self.pos.y - offset[1]))

