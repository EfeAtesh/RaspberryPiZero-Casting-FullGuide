#!/usr/bin/env python3
import os, sys, time, math

os.environ["SDL_VIDEODRIVER"] = "fbcon"
os.environ["SDL_FBDEV"] = "/dev/fb0"

import pygame

pygame.init()

info = pygame.display.Info()
W, H = info.current_w or 1920, info.current_h or 1080
screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
clock = pygame.time.Clock()

start_time = time.time()
duration = 2.5

bar_w = int(320 * (W / 1920.0))
bar_h = max(6, int(8 * (H / 1080.0)))
bx = (W - bar_w) // 2
by = (H - bar_h) // 2

def draw_pill(surface, color, x, y, width, height):
    r = height // 2
    if width <= height:
        if width > 0:
            pygame.draw.circle(surface, color, (x + r, y + r), r)
    else:
        pygame.draw.circle(surface, color, (x + r, y + r), r)
        pygame.draw.circle(surface, color, (x + width - r, y + r), r)
        pygame.draw.rect(surface, color, (x + r, y, width - 2 * r, height))

while True:
    elapsed = time.time() - start_time
    prog = min(1.0, elapsed / duration)
    # Apple Cubic Ease-Out
    eased = 1.0 - math.pow(1.0 - prog, 3)

    screen.fill((0, 0, 0))

    # 1. macOS Background Track (Koyu Gri Kapsul)
    draw_pill(screen, (45, 45, 45), bx, by, bar_w, bar_h)

    # 2. macOS Progress Fill (Beyaz/Gumus Kapsul)
    cur_w = int(bar_w * eased)
    if cur_w > 0:
        draw_pill(screen, (235, 235, 235), bx, by, cur_w, bar_h)

    pygame.display.flip()
    clock.tick(60)

    if prog >= 1.0:
        break

pygame.quit()
