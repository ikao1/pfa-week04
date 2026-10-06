"""Simple Galaga-style spaceship shooter built with pygame-ce.

Controls: Left/Right (or A/D) to move, Space to shoot, P to pause,
Q to save & quit, R to resume a saved game from the menu.

All game data (high score, saved game) is stored in this file's folder.
"""

import json
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
ENEMY_ROWS, ENEMY_COLS = 4, 8

BLACK = (8, 8, 16)
WHITE = (240, 240, 240)
CYAN = (90, 220, 255)
RED = (255, 80, 80)
YELLOW = (255, 220, 90)
GREEN = (100, 255, 140)


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
            enemies.append(pygame.Rect(60 + col * 65, 60 + row * 45, 30, 24))
    return enemies


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Galaga-ish — pygame-ce")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Menlo", 22)
    big = pygame.font.SysFont("Menlo", 42, bold=True)

    high_score = load_high_score()

    def new_run():
        return {
            "player": pygame.Rect(WIDTH // 2 - 15, HEIGHT - 60, 30, 20),
            "bullets": [],
            "enemy_bullets": [],
            "enemies": make_enemies(),
            "enemy_dir": 1,
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

        if paused or game_over:
            pass
        else:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                state["player"].x -= PLAYER_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                state["player"].x += PLAYER_SPEED
            state["player"].clamp_ip(screen.get_rect())

            if keys[pygame.K_SPACE] and state["shoot_cooldown"] <= 0:
                state["bullets"].append(pygame.Rect(state["player"].centerx - 2, state["player"].top, 4, 12))
                state["shoot_cooldown"] = 12
            state["shoot_cooldown"] = max(0, state["shoot_cooldown"] - 1)

            for b in state["bullets"]:
                b.y -= BULLET_SPEED
            state["bullets"] = [b for b in state["bullets"] if b.bottom > 0]

            moved = False
            for e in state["enemies"]:
                e.x += state["enemy_dir"] * 1
            if any(e.right >= WIDTH - 10 or e.left <= 10 for e in state["enemies"]) and state["enemies"]:
                state["enemy_dir"] *= -1
                for e in state["enemies"]:
                    e.y += 20
                    moved = True

            if state["enemies"] and random.random() < 0.02:
                shooter = random.choice(state["enemies"])
                state["enemy_bullets"].append(pygame.Rect(shooter.centerx - 2, shooter.bottom, 4, 10))

            for b in state["enemy_bullets"]:
                b.y += ENEMY_BULLET_SPEED
            state["enemy_bullets"] = [b for b in state["enemy_bullets"] if b.top < HEIGHT]

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
                if e.bottom >= state["player"].top:
                    game_over = True

        screen.fill(BLACK)
        pygame.draw.rect(screen, CYAN, state["player"])
        for b in state["bullets"]:
            pygame.draw.rect(screen, YELLOW, b)
        for b in state["enemy_bullets"]:
            pygame.draw.rect(screen, RED, b)
        for e in state["enemies"]:
            pygame.draw.rect(screen, GREEN, e)

        screen.blit(font.render(f"Score: {state['score']}", True, WHITE), (10, 10))
        screen.blit(font.render(f"Lives: {state['lives']}", True, WHITE), (10, 34))
        screen.blit(font.render(f"High: {high_score}", True, WHITE), (WIDTH - 130, 10))

        if paused:
            screen.blit(big.render("PAUSED", True, WHITE), (WIDTH // 2 - 80, HEIGHT // 2))
        if game_over:
            screen.blit(big.render("GAME OVER", True, RED), (WIDTH // 2 - 130, HEIGHT // 2 - 40))
            screen.blit(font.render("Press Enter to play again", True, WHITE), (WIDTH // 2 - 130, HEIGHT // 2 + 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
