"""Simple horizontal spaceship shooter built with pygame-ce.

Your Artemis II ship is on the left, green UFOs come from the right.

Controls: Up/Down (or W/S) to move, Space to shoot, P to pause,
Q to save & quit, R to resume a saved game.
"""

import json
import math
import random
import sys
from pathlib import Path

import pygame

SAVE_DIR = Path(__file__).resolve().parent
HIGH_SCORE_FILE = SAVE_DIR / "high_score.json"
SAVE_FILE = SAVE_DIR / "saved_game.json"

WIDTH, HEIGHT = 640, 480
FPS = 60
PLAYER_SPEED = 5
BULLET_SPEED = 8
ENEMY_BULLET_SPEED = 4
ENEMY_ROWS, ENEMY_COLS = 5, 4

BLACK = (8, 8, 16)
WHITE = (240, 240, 240)
GRAY = (150, 150, 160)
DARK_GRAY = (70, 70, 80)
ORANGE = (220, 110, 50)
CYAN = (90, 220, 255)
RED = (255, 80, 80)
YELLOW = (255, 220, 90)
GREEN = (100, 255, 140)
ALIEN_GREEN = (80, 220, 90)


def load_high_score():
    try:
        return int(json.loads(HIGH_SCORE_FILE.read_text())["high_score"])
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError):
        return 0


def save_high_score(score):
    HIGH_SCORE_FILE.write_text(json.dumps({"high_score": score}, indent=2))


def save_game(state):
    SAVE_FILE.write_text(json.dumps(state, indent=2))


def load_game():
    try:
        return json.loads(SAVE_FILE.read_text())
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError):
        return None


def clear_saved_game():
    SAVE_FILE.unlink(missing_ok=True)


def make_enemies():
    enemies = []
    for row in range(ENEMY_ROWS):
        for col in range(ENEMY_COLS):
            enemies.append(pygame.Rect(WIDTH - 80 - col * 70, 60 + row * 80, 34, 20))
    return enemies


def draw_artemis(screen, rect):
    """Tiny Artemis II style ship: white capsule + service module + orange tank."""
    x, y, w, h = rect
    # main body (horizontal)
    pygame.draw.rect(screen, WHITE, (x, y + h // 4, w - 8, h // 2))
    # nose cone
    pygame.draw.polygon(screen, DARK_GRAY, [(x + w - 8, y + h // 4), (x + w, y + h // 2), (x + w - 8, y + 3 * h // 4)])
    # orange service module stripe
    pygame.draw.rect(screen, ORANGE, (x, y + h // 4, 6, h // 2))
    # engine flame
    pygame.draw.polygon(screen, YELLOW, [(x, y + h // 3), (x - 8, y + h // 2), (x, y + 2 * h // 3)])


_ENEMY_IMG = None


def _enemy_sprite(size):
    """16-bit-style pixel art version of the enemy ship image."""
    global _ENEMY_IMG
    if _ENEMY_IMG is None:
        try:
            img = pygame.image.load(str(SAVE_DIR / "enemy ship.webp")).convert_alpha()
        except (pygame.error, FileNotFoundError):
            img = pygame.Surface((34, 20), pygame.SRCALPHA)
            img.fill(ALIEN_GREEN)
        img = pygame.transform.smoothscale(img, (24, 14))  # higher res = 16-bit feel
        # strip white / near-white pixels to transparent, brighten the rest
        for x in range(img.get_width()):
            for y in range(img.get_height()):
                r, g, b, a = img.get_at((x, y))
                if r > 235 and g > 235 and b > 235:
                    img.set_at((x, y), (0, 0, 0, 0))
                else:
                    br = lambda v: min(255, int(v * 1.45 + 25))  # boost brightness
                    img.set_at((x, y), (br(r), br(g), br(b), a))
        _ENEMY_IMG = img
    return pygame.transform.scale(_ENEMY_IMG, size)  # nearest-neighbor upscale


def draw_enemy(screen, rect, t):
    """Sprite plus big animated claw hands (50% larger than the body)."""
    screen.blit(_enemy_sprite((rect.w, rect.h)), rect)
    claw = int(rect.h * 1.5)  # 50% bigger than the body
    cx = rect.left - claw // 4
    cy = rect.centery
    open_amt = int(4 + 4 * math.sin(t * 0.008 + rect.left))  # claws open/close
    # top and bottom claw arms
    pygame.draw.arc(screen, WHITE, (cx - claw // 2, cy - claw // 2 - open_amt, claw, claw), math.radians(-70), math.radians(-10), 3)
    pygame.draw.arc(screen, WHITE, (cx - claw // 2, cy - claw // 2 + open_amt, claw, claw), math.radians(10), math.radians(70), 3)


_BG_FRAMES = []


def _make_bg_frames():
    """Load the black hole image and pixel-art it (32-bit look), animated."""
    frames = []
    pw, ph = 160, 100  # low-res canvas = big chunky pixels when scaled up
    try:
        img = pygame.image.load(str(SAVE_DIR / "black hole.webp")).convert()
    except (pygame.error, FileNotFoundError):
        # fallback: plain gradient if image missing
        img = pygame.Surface((pw, ph))
        img.fill((10, 10, 20))
    img = pygame.transform.smoothscale(img, (pw, ph))
    # quantize colors to a small palette for a pixel-art finish
    pal_img = img.convert(8)  # 8-bit palettized, keeps it pixel-chunky
    pal_img = pal_img.convert()  # back to 32-bit display surface
    for f in range(24):
        frame = pal_img.copy()
        # spinning ring highlights over the disk
        cx, cy = int(pw * 0.62), int(ph * 0.55)
        for r, thick, speed in ((30, 2, 1.0), (44, 1, 0.7), (22, 1, 1.4)):
            a0 = f / 24 * 2 * math.pi * speed
            rect = pygame.Rect(cx - r, cy - r // 2, r * 2, r)
            pygame.draw.arc(frame, (255, 230, 170), rect, a0, a0 + 1.6, thick)
        frames.append(frame)
    return frames


def draw_background(screen, t):
    """Looping pixel-art Interstellar black hole animation."""
    if not _BG_FRAMES:
        _BG_FRAMES.extend(_make_bg_frames())
    frame = _BG_FRAMES[(t // 80) % len(_BG_FRAMES)]
    screen.blit(pygame.transform.scale(frame, (WIDTH, HEIGHT)), (0, 0))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Artemis vs UFOs — pygame-ce")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Menlo", 22)
    big = pygame.font.SysFont("Menlo", 42, bold=True)

    high_score = load_high_score()

    def new_run():
        return {
            "player": pygame.Rect(60, HEIGHT // 2 - 10, 34, 22),
            "bullets": [],
            "enemy_bullets": [],
            "enemies": make_enemies(),
            "score": 0,
            "lives": 3,
            "shoot_cooldown": 0,
        }

    state = new_run()
    running = True
    paused = False
    game_over = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game({"score": state["score"], "lives": state["lives"]})
                save_high_score(max(high_score, state["score"]))
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    save_game({"score": state["score"], "lives": state["lives"]})
                    save_high_score(max(high_score, state["score"]))
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_p and not game_over:
                    paused = not paused
                if event.key == pygame.K_r and SAVE_FILE.exists():
                    saved = load_game()
                    if saved:
                        state = new_run()
                        state["score"] = saved["score"]
                        state["lives"] = saved["lives"]
                        clear_saved_game()
                        game_over = False
                if event.key == pygame.K_RETURN and game_over:
                    state = new_run()
                    game_over = False

        if not paused and not game_over:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                state["player"].y -= PLAYER_SPEED
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                state["player"].y += PLAYER_SPEED
            state["player"].clamp_ip(screen.get_rect())

            if keys[pygame.K_SPACE] and state["shoot_cooldown"] <= 0:
                state["bullets"].append(pygame.Rect(state["player"].right, state["player"].centery - 2, 12, 4))
                state["shoot_cooldown"] = 12
            state["shoot_cooldown"] = max(0, state["shoot_cooldown"] - 1)

            for b in state["bullets"]:
                b.x += BULLET_SPEED
            state["bullets"] = [b for b in state["bullets"] if b.left < WIDTH]

            drifting_up = True
            for i, e in enumerate(state["enemies"]):
                e.x -= 1
                e.y += 0.4 * (1 if (e.x // 40) % 2 else -1)
                e.clamp_ip(screen.get_rect())

            if state["enemies"] and random.random() < 0.02:
                shooter = random.choice(state["enemies"])
                state["enemy_bullets"].append(pygame.Rect(shooter.left - 10, shooter.centery - 2, 10, 4))

            for b in state["enemy_bullets"]:
                b.x -= ENEMY_BULLET_SPEED
            state["enemy_bullets"] = [b for b in state["enemy_bullets"] if b.right > 0]

            for b in list(state["bullets"]):
                for e in list(state["enemies"]):
                    if b.colliderect(e):
                        state["bullets"].remove(b)
                        state["enemies"].remove(e)
                        state["score"] += 10
                        break

            for b in list(state["enemy_bullets"]):
                if b.colliderect(state["player"]):
                    state["enemy_bullets"].remove(b)
                    state["lives"] -= 1
                    if state["lives"] <= 0:
                        game_over = True
                        save_high_score(max(high_score, state["score"]))

            if not state["enemies"]:
                state["enemies"] = make_enemies()

            for e in state["enemies"]:
                if e.left <= state["player"].right:
                    game_over = True

        t = pygame.time.get_ticks()
        draw_background(screen, t)
        draw_artemis(screen, state["player"])
        for b in state["bullets"]:
            pygame.draw.rect(screen, YELLOW, b)
        for b in state["enemy_bullets"]:
            pygame.draw.rect(screen, GREEN, b)  # green claw laser
            pygame.draw.rect(screen, (200, 255, 200), (b.x, b.centery - 1, b.w, 2))  # laser core
        for e in state["enemies"]:
            draw_enemy(screen, e, t)

        screen.blit(font.render(f"Score: {state['score']}", True, WHITE), (10, 10))
        screen.blit(font.render(f"Lives: {state['lives']}", True, WHITE), (10, 34))
        screen.blit(font.render(f"High: {high_score}", True, WHITE), (WIDTH - 120, 10))

        if paused:
            screen.blit(big.render("PAUSED", True, WHITE), (WIDTH // 2 - 90, HEIGHT // 2))
        if game_over:
            screen.blit(big.render("GAME OVER", True, RED), (WIDTH // 2 - 140, HEIGHT // 2 - 40))
            screen.blit(font.render("Press Enter to play again", True, WHITE), (WIDTH // 2 - 140, HEIGHT // 2 + 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
