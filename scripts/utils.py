import pygame
import re
import os

BASE_IMG_PATH = "graphics/"


def load_image(path):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img

def load_images(path):
    images = []

    def extract_number(f):
        return int(re.search(r'(\d+)', f).group(0))
    
    img_names = sorted([f for f in os.listdir(BASE_IMG_PATH + path) if f.endswith('.png')],
                       key=extract_number)
    for img_name in img_names:
        if img_name.endswith('.png'):
            images.append(load_image(path + '/' + img_name).convert())
    return images

class Animation:
    def __init__ (self, images, img_dur=5, loop=True):
        self.images = images
        self.img_duration = img_dur
        self.loop = loop
        self.done = False
        self.frame = 0

    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)
    
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (len(self.images) * self.img_duration)
        else:
            if not self.done:
                self.frame += 1
                if self.frame >= len(self.images) * self.img_duration - 1:
                    self.done = True
                    self.frame = len(self.images) * self.img_duration - 1

    def img(self):
        return self.images[int(self.frame) // self.img_duration]
    


