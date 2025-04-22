import pygame
import random
import asyncio
from scripts.tilemap import Tilemap
from scripts.particle import SkullParticle  # Import SkullParticle


# Base class for all entities that have physics properties
class PhysicsEntity:
    def __init__(self, game, e_type, pos, size, health=100):
        self.game = game  # Reference to the game instance
        self.type = e_type  # Type of the entity (e.g., player, enemy)
        self.pos = list(pos)  # Position of the entity
        self.size = size  # Size of the entity (width, height)
        self.velocity = [0, 0]  # Velocity of the entity
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}  # Collision flags
        self.health = health  # Current health of the entity
        self.max_health = health  # Maximum health of the entity
        self.action = ''  # Current action/animation of the entity
        self.anim_offset = (0, 0)  # Offset for the animation
        self.flip = False  # Flag for flipping the sprite horizontally
        self.knockback = pygame.Vector2(0, 0)  # Initialize knockback vector
        self.set_action('idle')  # Set the initial action to 'idle'

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}  # Reset collision flags
        frame_movement = [movement[0] + self.velocity[0], movement[1] + self.velocity[1]]  # Calculate frame movement

        if self.velocity[0] != 0:
            self.velocity[0] *= 0.9  # Dampen horizontal velocity over time

        # Update horizontal position and check for collisions
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos, self.size):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        # Update vertical position and check for collisions
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos, self.size):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        # Update flip flag based on movement direction
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        # Apply gravity if not climbing
        if self.action != 'climb':
            self.velocity[1] = min(15, self.velocity[1] + 0.1)

        # Reset vertical velocity on collision with ground or ceiling
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        self.animation.update()  # Update animation

    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0],
                   self.pos[1] - offset[1] + self.anim_offset[1]))

# Class for the player character, inherits from PhysicsEntity
class Player(PhysicsEntity):
    def __init__(self, game, e_type, pos, size):
        super().__init__(game, e_type, pos, size)
        self.air_time = 0  # Time the player has been in the air
        self.dead = False

    def update(self, tilemap, movement=(0, 0)):
        if self.dead:
            return
        
        super().update(tilemap, movement=movement)  # Update position and handle collisions

        self.air_time += 1
        if self.collisions['down']:
            self.air_time = 0

        # Set appropriate action based on state
        if self.air_time > 4 and self.action != 'climb':
            self.set_action('jump')
        elif movement[0] != 0:
            if self.action != 'run':
                self.set_action('run') # Play footsteps sound
        else:
            self.set_action('idle')


    # Handle taking damage and apply knockback
    def take_damage(self, damage, knockback):
        if self.dead:
            return
        
        self.health -= damage
        self.apply_knockback(knockback)
        if self.health <= 0:
            self.health = 0  # Ensure health doesn't go below 0
            self.die()  # Player dies when health is zero
            return
        self.game.audio['damage'].play() 


    def die(self):
        self.health = 0  # Ensure health doesn't go below 0
        self.dead = True  # Set the player as dead

    # Override the render method and add custom offset for player sprite
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0] - 5,
                   self.pos[1] - offset[1] + self.anim_offset[1]))


# Class for enemy characters, inherits from PhysicsEntity
class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size, health=30):
        super().__init__(game, 'enemy', pos, size, health=health)
        self.set_action('idle')  # Set initial action to 'idle'
        self.knockback = pygame.Vector2(0, 0)  # Initialize knockback vector
        self.dodge_cooldown = 0  # Cooldown for dodging
        self.attack_cooldown = 0  # Cooldown for attacking
        self.jump_cooldown = 0  # Cooldown for jumping
        self.patrol_left = self.pos[0] - 32  # Set patrol left boundary (2 tiles left)
        self.patrol_right = self.pos[0] + 32  # Set patrol right boundary (2 tiles right)
        self.patrol_direction = 1  # Start by moving right
        self.tracking_player = False  # Flag to indicate if the enemy is tracking the player
        self.exclamation_shown = False  # Flag to show exclamation point
        self.exclamation_counter = 0  # Counter for exclamation point duration
        self.trigger_exclamation = True  # Flag to trigger exclamation point

    def apply_knockback(self, knockback):
        self.knockback = knockback  # Apply knockback

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.game.audio['death'].play()  # Play enemy death sound
            self.game.enemies.remove(self)
            self.game.particles.append(SkullParticle(self.game, (self.pos[0] + self.size[0] / 2, self.pos[1])))  # Add skull particle
            return
        self.game.audio['damage'].play()

    def update(self, tilemap, movement=(0, 0)):
        # Check for dying from falling too fast
        if self.velocity[1] >= 15:
            self.game.enemies.remove(self)
            return

        # Move towards the player only if within 8 tiles horizontally (128 pixels) and 4 tiles vertically (64 pixels)
        player_pos = self.game.player.pos
        if abs(player_pos[0] - self.pos[0]) <= 128 and abs(player_pos[1] - self.pos[1]) <= 64:
            if player_pos[0] > self.pos[0]:
                movement = (0.5, 0)  # Move right
            elif player_pos[0] < self.pos[0]:
                movement = (-0.5, 0)  # Move left
            if not self.tracking_player and self.exclamation_counter == 0 and self.trigger_exclamation:
                self.exclamation_shown = True  # Show exclamation point when starting to track
                self.exclamation_counter = 30  # Show for 30 frames
                self.trigger_exclamation = False
            self.tracking_player = True  # Set tracking flag
        else:
            # Patrol logic
            self.exclamation_shown = False
            self.trigger_exclamation = True
            self.tracking_player = False
            self.exclamation_counter = 0
            if self.patrol_direction == 1:  # Moving right
                if self.pos[0] < self.patrol_right:
                    movement = (0.5, 0)
                else:
                    self.patrol_direction = -1
            elif self.patrol_direction == -1:  # Moving left
                if self.pos[0] > self.patrol_left:
                    movement = (-0.5, 0)
                else:
                    self.patrol_direction = 1

        # Update exclamation point counter
        if self.exclamation_counter > 0:
            self.exclamation_counter -= 1
        else:
            self.exclamation_shown = False

        # Apply knockback to movement
        if self.knockback.length() > 0:
            movement = (movement[0] + self.knockback.x, movement[1] + self.knockback.y)
            self.knockback *= 0.9  # Dampen knockback over time
            if self.knockback.length() < 0.1:
                self.knockback = pygame.Vector2(0, 0)  # Stop knockback if it's very small

        next_pos = [self.pos[0] + movement[0] * 16, self.pos[1] + self.size[1]]
        on_ground = False
        for rect in tilemap.physics_rects_around(next_pos, self.size):
            if pygame.Rect(next_pos[0], next_pos[1], self.size[0], 1).colliderect(rect):
                on_ground = True
                break

        # Prevent movement in the direction of the ledge
        if not on_ground and self.knockback == (0, 0):
            movement = (0, movement[1]) if movement[0] != 0 else movement

        # Check for collision with the player
        if self.rect().colliderect(self.game.player.rect()):
            if self.pos[0] < self.game.player.pos[0]:
                knockback = [3, -1]
            else:
                knockback = [-3, -1]  # Set knockback vector
            self.game.player.take_damage(5, knockback)  # Apply damage and knockback to the player

        # Check for collision with other enemies
        for enemy in self.game.enemies:
            if enemy != self and self.rect().colliderect(enemy.rect()) and self.knockback.length() < 0.1:
                if self.pos[0] < enemy.pos[0]:
                    self.pos[0] = enemy.pos[0] - self.size[0]
                elif self.pos[0] > enemy.pos[0]:
                    self.pos[0] = enemy.pos[0] + self.size[0]

        super().update(tilemap, movement=movement)  # Update position and handle collisions

        if movement[0] != 0:
            self.set_action('run')
        elif movement[1] != 0:
            self.set_action('idle')
        else:
            self.set_action('idle')

    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0] - 5,
                   self.pos[1] - offset[1] + self.anim_offset[1]))
        self.draw_health_bar(surf, offset)  # Draw health bar

        # Render the exclamation point if it should be shown
        if self.exclamation_shown:
            exclamation_img = self.game.assets['exclamation']  # Load the exclamation point image
            surf.blit(exclamation_img, (self.pos[0] - offset[0] + self.size[0] // 2 - exclamation_img.get_width() // 2,
                                        self.pos[1] - offset[1] - exclamation_img.get_height() - 10))  # Position it above the enemy's head


# Class for boss characters, inherits from PhysicsEntity
class Boss(PhysicsEntity):
    def __init__(self, game, pos, size, health=100):
        super().__init__(game, 'boss', pos, size, health)
        self.special_attack_cooldown = 0  # Cooldown for special attack
        self.knockback = pygame.Vector2(0, 0)  # Initialize knockback vector
        self.patrol_left = self.pos[0] - 32  # Set patrol left boundary (2 tiles left)
        self.patrol_right = self.pos[0] + 32  # Set patrol right boundary (2 tiles right)
        self.patrol_direction = 1  # Start by moving right
        self.tracking_player = False  # Flag to indicate if the enemy is tracking the player
        self.exclamation_shown = False  # Flag to show exclamation point
        self.exclamation_counter = 0  # Counter for exclamation point duration

    def apply_knockback(self, knockback):
        self.knockback = knockback  # Apply knockback

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.game.audio['death'].play()
            self.game.enemies.remove(self)
            self.game.particles.append(SkullParticle(self.game, (self.pos[0] + self.size[0] / 2, self.pos[1])))  # Add skull particle
            return
        self.game.audio['damage'].play()

    def update(self, tilemap, movement=(0, 0)):
        # Check for dying from falling too fast
        if self.velocity[1] >= 15:
            self.game.enemies.remove(self)
            return

        # Move towards the player only if within 8 tiles horizontally (128 pixels) and 4 tiles vertically (64 pixels)
        player_pos = self.game.player.pos
        if abs(player_pos[0] - self.pos[0]) <= 128 and abs(player_pos[1] - self.pos[1]) <= 64:
            if player_pos[0] > self.pos[0]:
                movement = (0.5, 0)  # Move right
            elif player_pos[0] < self.pos[0]:
                movement = (-0.5, 0)  # Move left
            if not self.tracking_player and self.exclamation_counter == 0 and self.trigger_exclamation:
                self.exclamation_shown = True  # Show exclamation point when starting to track
                self.exclamation_counter = 30  # Show for 30 frames
                self.trigger_exclamation = False
            self.tracking_player = True  # Set tracking flag
        else:
            # Patrol logic
            self.exclamation_shown = False
            self.trigger_exclamation = True
            self.tracking_player = False
            self.exclamation_counter = 0
            if self.patrol_direction == 1:  # Moving right
                if self.pos[0] < self.patrol_right:
                    movement = (0.5, 0)
                else:
                    self.patrol_direction = -1
            elif self.patrol_direction == -1:  # Moving left
                if self.pos[0] > self.patrol_left:
                    movement = (-0.5, 0)
                else:
                    self.patrol_direction = 1

        # Update exclamation point counter
        if self.exclamation_counter > 0:
            self.exclamation_counter -= 1
        else:
            self.exclamation_shown = False

        # Apply knockback to movement
        if self.knockback.length() > 0:
            movement = (movement[0] + self.knockback.x, movement[1] + self.knockback.y)
            self.knockback *= 0.9  # Dampen knockback over time
            if self.knockback.length() < 0.1:
                self.knockback = pygame.Vector2(0, 0)  # Stop knockback if it's very small

        # Special attack logic
        if self.special_attack_cooldown == 0 and self.tracking_player:
            self.special_attack()
            self.special_attack_cooldown = 100
        elif self.special_attack_cooldown > 0:
            self.special_attack_cooldown -= 1

        next_pos = [self.pos[0] + movement[0] * 16, self.pos[1] + self.size[1]]
        on_ground = False
        for rect in tilemap.physics_rects_around(next_pos, self.size):
            if pygame.Rect(next_pos[0], next_pos[1], self.size[0], 1).colliderect(rect):
                on_ground = True
                break

        # Prevent movement in the direction of the ledge
        if not on_ground and self.knockback == (0, 0):
            movement = (0, movement[1]) if movement[0] != 0 else movement

        # Check for collision with the player
        if self.rect().colliderect(self.game.player.rect()):
            if self.pos[0] < self.game.player.pos[0]:
                knockback = [3, -1]
            else:
                knockback = [-3, -1]  # Set knockback vector
            self.game.player.take_damage(5, knockback)  # Apply damage and knockback to the player

        # Check for collision with other enemies
        for enemy in self.game.enemies:
            if enemy != self and self.rect().colliderect(enemy.rect()) and self.knockback.length() < 0.1:
                if self.pos[0] < enemy.pos[0]:
                    self.pos[0] = enemy.pos[0] - self.size[0]
                elif self.pos[0] > enemy.pos[0]:
                    self.pos[0] = enemy.pos[0] + self.size[0]

        super().update(tilemap, movement=movement)  # Update position and handle collisions

        # Update action based on movement
        if movement[0] != 0:
            self.set_action('run')
        elif movement[1] != 0:
            self.set_action('idle')
        else:
            self.set_action('idle')

    def special_attack(self):
        # Define special attack behavior, such as shooting projectiles
        player_pos = self.game.player.pos
        direction = pygame.Vector2(player_pos[0] - self.pos[0], player_pos[1] - self.pos[1]).normalize()
        projectile_pos = (self.pos[0] + self.size[0] // 2, self.pos[1] + self.size[1] // 2)
        new_projectile = RedShuriken(self.game, projectile_pos, direction)
        self.game.projectiles.append(new_projectile)

    def render(self, surf, offset=(0, 0)):
        # draw hitbox
        # hitbox = self.rect().move(-offset[0], -offset[1])
        # pygame.draw.rect(surf, (0, 255, 0), hitbox, 1)

        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0] - 9,
                   self.pos[1] - offset[1] + self.anim_offset[1]))
        self.draw_health_bar(surf, offset)  # Draw health bar

        # Render the exclamation point if it should be shown
        if self.exclamation_shown:
            exclamation_img = self.game.assets['exclamation']  # Load the exclamation point image
            surf.blit(exclamation_img, (self.pos[0] - offset[0] + self.size[0] // 2 - exclamation_img.get_width() // 2,
                                        self.pos[1] - offset[1] - exclamation_img.get_height() - 10))  # Position it above the enemy's head
