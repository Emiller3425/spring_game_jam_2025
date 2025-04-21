import pygame
import pytmx

NEIGHBORS_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
PHYSICS_TILE_TYPES = {'grass'}
INTRERACTABLE_TILE_TYPES = {'ladder'}

class Tilemap:
    def __init__(self, game, tile_size=16):
        self.tile_size = tile_size
        self.game = game
        self.tilemap = {}
        self.offgrid_tiles = []
        self.player_position = (0, 0)
        self.enemy_positions = []
        self.boss_positions = []
        self.trees = []
        self.boss_counter = 0

    def load(self, level):
        # Load the map tilemap
        self.tmx_data = pytmx.load_pygame(f'./graphics/levels/{level}/{level}.tmx')

        # Iterate through the layers and create the tilemap
        for layer_index, layer in enumerate(self.tmx_data.visible_layers):
            for x, y, surf in layer.tiles():
                key = str(x) + ';' + str(y)
                if key not in self.tilemap:
                    self.tilemap[key] = []
                if layer.name == 'Ground':
                    if layer.data[y][x] == 1:
                        self.tilemap[key].append({'type': 'grass', 'variant': 0, 'pos': (x, y), 'layer': layer_index})
                    if layer.data[y][x] == 2:
                        self.tilemap[key].append({'type': 'grass', 'variant': 2, 'pos': (x, y), 'layer': layer_index})
                    if layer.data[y][x] == 3:
                        self.tilemap[key].append({'type': 'grass', 'variant': 1, 'pos': (x, y), 'layer': layer_index})
                    if layer.data[y][x] == 4:
                        self.tilemap[key].append({'type': 'grass', 'variant': 3, 'pos': (x, y), 'layer': layer_index})
                if layer.name == 'Decor':
                    if layer.data[y][x] == 5:
                        self.tilemap[key].append({'type': 'decor', 'variant': 0, 'pos': (x, y), 'layer': layer_index})
                    if layer.data[y][x] == 6:
                        self.tilemap[key].append({'type': 'decor', 'variant': 1, 'pos': (x, y), 'layer': layer_index})
                    if layer.data[y][x] == 7:
                        self.tilemap[key].append({'type': 'decor', 'variant': 2, 'pos': (x, y), 'layer': layer_index})
                    if layer.data[y][x] == 8:
                        self.tilemap[key].append({'type': 'decor', 'variant': 3, 'pos': (x, y), 'layer': layer_index})
                    if layer.data[y][x] == 9:
                        self.tilemap[key].append({'type': 'decor', 'variant': 4, 'pos': (x, y), 'layer': layer_index})
                if layer.name == 'Trees':
                    if layer.data[y][x] == 10:
                        self.tilemap[key].append({'type': 'tree', 'variant': 0, 'pos': (x, y), 'layer': layer_index})
                    if layer.data[y][x] == 11:
                        self.tilemap[key].append({'type': 'tree', 'variant': 1, 'pos': (x, y), 'layer': layer_index})
                    if layer.data[y][x] == 12:
                        self.tilemap[key].append({'type': 'tree', 'variant': 2, 'pos': (x, y), 'layer': layer_index})
                    if layer.data[y][x] == 13:
                        self.tilemap[key].append({'type': 'tree', 'variant': 3, 'pos': (x, y), 'layer': layer_index})
                if layer.name == 'Ladder':
                    self.tilemap[key].append({'type': 'ladder', 'variant': 0, 'pos': (x, y), 'layer': layer_index})
                if layer.name == "Player":
                    self.player_position = (x, y)
                if layer.name == 'Enemy':
                    self.enemy_positions.append((x, y))
                if layer.name == 'Boss':
                    self.boss_counter += 1
                    if self.boss_counter == 4:
                        self.boss_positions.append((x, y))
                        self.boss_counter = 0
                        

    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)

        for loc in list(self.tilemap.keys()):
            for tile in self.tilemap[loc]:
                if (tile['type'], tile['variant']) in id_pairs:
                    match = tile.copy()
                    match['pos'] = list(match['pos'])
                    match['pos'][0] *= self.tile_size
                    match['pos'][1] *= self.tile_size
                    matches.append(match)
                    if not keep:
                        self.tilemap[loc].remove(tile)
                        if not self.tilemap[loc]:  # Remove the key if the list is empty
                            del self.tilemap[loc]

        return matches
    
    def get_player_spawn(self):
        return self.player_pos

    def tiles_arounds(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBORS_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.extend(self.tilemap[check_loc])
        return tiles
    
    def physics_rects_around(self, pos, entity_size):
        """
        Find all physics-related rectangles around the given position
        considering the size of the entity.

        :param pos: Position of the entity (x, y).
        :param entity_size: Size of the entity (width, height).
        :return: List of pygame.Rect representing the physics collision boxes.
        """
        rects = []
        # Calculate the number of tiles the entity covers
        start_tile_x = int(pos[0] // self.tile_size)
        end_tile_x = int((pos[0] + entity_size[0]) // self.tile_size) + 1
        start_tile_y = int(pos[1] // self.tile_size)
        end_tile_y = int((pos[1] + entity_size[1]) // self.tile_size) + 1

        for x in range(start_tile_x, end_tile_x):
            for y in range(start_tile_y, end_tile_y):
                check_loc = f"{x};{y}"
                if check_loc in self.tilemap:
                    for tile in self.tilemap[check_loc]:
                        if tile['type'] in PHYSICS_TILE_TYPES:
                            rect = pygame.Rect(
                                tile['pos'][0] * self.tile_size,
                                tile['pos'][1] * self.tile_size,
                                tile.get('width', self.tile_size),
                                tile.get('height', self.tile_size)
                            )
                            rects.append(rect)
        return rects
    
    def ladders_around(self, pos):
        ladders = []
        for tile in self.tiles_arounds(pos):
            if tile['type'] in INTRERACTABLE_TILE_TYPES:
                ladders.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return ladders
    
    def interaction_rects_around(self, pos):
        rects = []
        for tile in self.tiles_arounds(pos):
            if tile['type'] in INTRERACTABLE_TILE_TYPES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return rects

    def render(self, surf, offset=(0, 0)):
        # Offgrid tiles will need to be optimized for larger games
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))

        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    for tile in sorted(self.tilemap[loc], key=lambda t: t['layer']):
                        surf.blit(self.game.assets[tile['type']][tile['variant']], (x * self.tile_size - offset[0], y * self.tile_size - offset[1]))