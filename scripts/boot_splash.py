#!/usr/bin/env python3
import os, sys, time, math

os.environ["SDL_VIDEODRIVER"] = "fbcon"
os.environ["SDL_FBDEV"] = "/dev/fb0"

import pygame

pygame.init()
pygame.font.init()

info = pygame.display.Info()
W, H = info.current_w or 1920, info.current_h or 1080
screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
clock = pygame.time.Clock()

font_logo = pygame.font.Font(None, int(54 * (H/1080.0)))
font_sub = pygame.font.Font(None, int(26 * (H/1080.0)))

start_time = time.time()
duration = 2.5

bar_w = int(360 * (W/1920.0))
bar_h = int(6 * (H/1080.0))
bx = (W - bar_w) // 2
by = (H // 2) + int(60 * (H/1080.0))

while True:
    elapsed = time.time() - start_time
    prog = min(1.0, elapsed / duration)
    eased = 1.0 - math.pow(1.0 - prog, 3)

    screen.fill((0, 0, 0))

    logo_t = font_logo.render("WIRELESS DISPLAY", True, (255, 255, 255))
    screen.blit(logo_t, logo_t.get_rect(center=(W//2, H//2 - int(40 * (H/1080.0)))))

    sub_t = font_sub.render("Starting Receiver...", True, (100, 116, 139))
    screen.blit(sub_t, sub_t.get_rect(center=(W//2, H//2 + int(10 * (H/1080.0)))))

    # macOS Style Progress Bar
    pygame.draw.rect(screen, (38, 38, 38), (bx, by, bar_w, bar_h))
    cur_w = int(bar_w * eased)
    if cur_w > 0:
        pygame.draw.rect(screen, (220, 220, 220), (bx, by, cur_w, bar_h))

    pygame.display.flip()
    clock.tick(60)

    if prog >= 1.0:
        break

pygame.quit()
