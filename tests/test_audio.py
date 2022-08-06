import sys
import pygame

pygame.mixer.pre_init(44100, -16, 2, 256 * 2**4)
pygame.init()
pygame.mixer.init()

pygame.mixer.music.set_volume(1.)

fn = "resources/music/Shadow of the Enemy.ogg"
pygame.mixer.music.load(fn)
pygame.mixer.music.play(0)

def terminate():
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    pygame.quit()
    sys.exit()

FPSCLOCK = pygame.time.Clock()
DISPLAY = pygame.display.set_mode((1, 0))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
    FPSCLOCK.tick(60)
