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
ENEMY_ROWS, ENEMY_COLS = 5, 1

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


def draw_artemis(screen, rect, t=0):
    """NASA Artemis-style ship with extra detail, animated engine flames."""
    x, y, w, h = rect
    # animated rocket flames behind the ship (left side)
    flame_len = 10 + int(6 * math.sin(t * 0.02))
    pygame.draw.polygon(screen, ORANGE, [(x - 2, y + h // 4 + 2), (x - 2 - flame_len - 4, y + h // 2), (x - 2, y + 3 * h // 4 - 2)])
    pygame.draw.polygon(screen, YELLOW, [(x - 2, y + h // 3 + 2), (x - 2 - flame_len, y + h // 2), (x - 2, y + 2 * h // 3 - 2)])
    # main capsule body
    pygame.draw.rect(screen, WHITE, (x, y + h // 4, w - 10, h // 2))
    # service module tail section
    pygame.draw.rect(screen, (190, 190, 200), (x, y + h // 4, 8, h // 2))
    pygame.draw.line(screen, DARK_GRAY, (x + 8, y + h // 4), (x + 8, y + 3 * h // 4), 2)
    # orange fuel tank stripe
    pygame.draw.rect(screen, ORANGE, (x + 8, y + h // 4, 5, h // 2))
    # crew capsule taper (nose)
    pygame.draw.polygon(screen, WHITE, [(x + w - 10, y + h // 4), (x + w - 2, y + 3 * h // 8), (x + w - 2, y + 5 * h // 8), (x + w - 10, y + 3 * h // 4)])
    # launch escape tower (needle at nose)
    pygame.draw.line(screen, DARK_GRAY, (x + w - 2, y + h // 2), (x + w + 4, y + h // 2), 2)
    # windows
    pygame.draw.rect(screen, (40, 60, 90), (x + w - 18, y + h // 2 - 4, 4, 3))
    pygame.draw.rect(screen, (40, 60, 90), (x + w - 26, y + h // 2 - 4, 4, 3))
    # engine nozzle
    pygame.draw.polygon(screen, DARK_GRAY, [(x, y + h // 4 + 2), (x - 4, y + 3 * h // 4 - 2), (x, y + 3 * h // 4 - 2)])
    # panel lines / detail pixels
    pygame.draw.line(screen, GRAY, (x + 14, y + h // 4), (x + 14, y + 3 * h // 4), 1)
    pygame.draw.line(screen, GRAY, (x + w // 2, y + h // 4), (x + w // 2, y + 3 * h // 4), 1)
    pygame.draw.circle(screen, CYAN, (x + w // 2 + 8, y + h // 2), 2)  # thruster detail
    # NASA logo fitted to the ship side — text only, no blue circle
    logo_font = pygame.font.SysFont("Menlo", max(8, int(h * 0.35)), bold=True)
    text = logo_font.render("NASA", True, (11, 61, 145))
    text_rect = text.get_rect(center=(x + (w - 10) // 2 + 6, y + h // 2))
    screen.blit(text, text_rect)


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


def draw_ufo(screen, rect, t=0):
    """Generic green alien in a UFO saucer."""
    x, y, w, h = rect
    cx = x + w // 2
    pygame.draw.ellipse(screen, GRAY, (x, y + h // 2, w, h // 2))
    pygame.draw.ellipse(screen, DARK_GRAY, (x + 4, y + 2 * h // 3, w - 8, h // 4))
    pygame.draw.circle(screen, CYAN, (cx, y + h // 3), w // 5)       # dome
    pygame.draw.circle(screen, ALIEN_GREEN, (cx, y + h // 3), w // 7)  # green alien
    pygame.draw.circle(screen, YELLOW, (cx - w // 5, y + 3 * h // 4), 2)
    pygame.draw.circle(screen, YELLOW, (cx + w // 5, y + 3 * h // 4), 2)


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
        # scattered twinkling diamond stars, pulsing like a heartbeat
        random.seed(42)
        stars = [(random.randrange(2, pw - 2), random.randrange(2, ph - 2), random.random()) for _ in range(60)]
        for sx, sy, phase in stars:
            s = (f / 24 + phase) % 1.0  # one heartbeat cycle per 24 frames
            # lub-dub: two bright bumps close together, then dark
            hb = math.exp(-((s - 0.12) ** 2) / 0.004) + 0.55 * math.exp(-((s - 0.32) ** 2) / 0.006)
            bright = min(255, 60 + int(195 * hb))
            size = 1 + int(1.5 * hb)
            color = (bright, bright, bright)
            pygame.draw.polygon(frame, color, [
                (sx, sy - size), (sx + size, sy), (sx, sy + size), (sx - size, sy)
            ])
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

    # sounds
    pygame.mixer.init()
    try:
        laser_snd = pygame.mixer.Sound(str(SAVE_DIR / "laser.wav"))
        explosion_snd = pygame.mixer.Sound(str(SAVE_DIR / "explosion.wav"))
        laser_snd.set_volume(0.25)
        explosion_snd.set_volume(0.5)
        pygame.mixer.music.load(str(SAVE_DIR / "music.wav"))
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)  # loop forever
    except pygame.error:
        class _Silent:
            def play(self): pass
            def set_volume(self, v): pass
        laser_snd = explosion_snd = _Silent()

    high_score = load_high_score()

    def new_run():
        return {
            "player": pygame.Rect(55, HEIGHT // 2 - 17, 51, 33),  # 50% smaller
            "bullets": [],
            "enemy_bullets": [],
            "enemies": make_enemies(),
            "score": 0,
            "lives": 3,
            "shoot_cooldown": 0,
            "explosions": [],
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
                laser_snd.play()
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
                        state["explosions"].append({"x": e.centerx, "y": e.centery, "age": 0})
                        explosion_snd.play()
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
        draw_artemis(screen, state["player"], t)
        for b in state["bullets"]:
            pygame.draw.rect(screen, YELLOW, b)
        for b in state["enemy_bullets"]:
            pygame.draw.rect(screen, GREEN, b)  # green claw laser
            pygame.draw.rect(screen, (200, 255, 200), (b.x, b.centery - 1, b.w, 2))  # laser core
        for e in state["enemies"]:
            draw_ufo(screen, e, t)
        # explosions
        for ex in list(state["explosions"]):
            ex["age"] += 1
            r = ex["age"] * 3
            if ex["age"] % 2:
                pygame.draw.circle(screen, ORANGE, (ex["x"], ex["y"]), r)
                pygame.draw.circle(screen, YELLOW, (ex["x"], ex["y"]), r // 2)
            if ex["age"] > 12:
                state["explosions"].remove(ex)

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
