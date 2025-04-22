from PIL import Image
import os

# Directory containing the tilesheet file
directory = '../graphics/spritesheet_images'

# Path to the tilesheet file
tilesheet_path = os.path.join(directory, '0.png')

# Directory to save the individual tiles
output_directory = '.'

# Create the output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Open the tilesheet image
tilesheet = Image.open(tilesheet_path)

# Set the size of each tile
tile_width, tile_height = 16, 16

# Get the size of the tilesheet
tilesheet_width, tilesheet_height = tilesheet.size

# Calculate the number of tiles in each dimension
tiles_x = tilesheet_width // tile_width
tiles_y = tilesheet_height // tile_height

# Extract and save each tile
tile_index = 0
for y in range(tiles_y):
    for x in range(tiles_x):
        tile = tilesheet.crop((x * tile_width, y * tile_height, (x + 1) * tile_width, (y + 1) * tile_height))
        tile_path = os.path.join(output_directory, f'{tile_index}.png')
        tile.save(tile_path)
        tile_index += 1

print(f'Successfully saved {tile_index} tiles to {output_directory}')
