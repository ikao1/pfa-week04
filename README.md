# pfa-week04
Assignment 4
# ArtemisII vs UFOs

A horizontal spaceship shooter built with pygame-ce. Your NASA Artemis-style
ship is on the left, green-alien UFOs come from the right, and the backdrop
is an Interstellar black hole with twinkling diamond stars.

## How to run it

```
python3 -m venv .venv
source .venv/bin/activate
pip install pygame-ce
python3 galaga_vertical_backup.py
```

The line that starts the game: `python3 galaga_vertical_backup.py`

Controls: Up/Down or W/S to move, Space to shoot, P to pause, R to resume a
saved game, Q or Esc to save & quit, Enter to restart after game over.

## What I made better

- Sound: laser blip when firing, explosion noise when a UFO is hit, and a
  chill looping lofi track in the background.
- Explosions when alien ships are destroyed.
- Wave counter; enemies fly faster each wave.
- Bigger, brighter player laser bolts.
- 32-bit pixel-art enemy/black-hole look, NASA logo fitted on the ship,
  animated engine flames, animated heartbeat diamond stars.

## How it works

Three of my `def`s:

- `draw_background(screen, t)` — builds the pixel-art Interstellar backdrop
  once, then each frame blits the current animation frame (twinkling stars).
- `draw_artemis(screen, rect, t)` — draws the player ship: flames, body,
  nose, nozzle, and the NASA logo text on the side.
- `draw_ufo(screen, rect, t)` — draws each green-alien UFO (saucer, dome,
  alien face, antennae).

The one I wrote by hand: `draw_artemis` — I designed the NASA ship's shape,
the NASA lettering placement on the hull.
def draw_artemis(screen, rect, t=0):
    """NASA Artemis-style ship with extra detail, animated engine flames."""

## One undo

Commit `6726361` ("YOLO: remove shot cooldown for auto-fire") set the shot
cooldown to 0 so the ship fired every frame. It made the game trivial and the
laser sound was constant, so I threw it away with `git revert` (commit
`86beeb8`).
