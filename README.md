# pfa-week04
Assignment 4
# Artemis vs UFOs

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

The one I wrote by hand: 

def ship_name():
    return "Artemis"
    
pygame.display.set_caption(ship_name() + " vs UFOs")

I did this to change the window name to "Artemis vs UfOs"

## One undo

I wasn't fully understanding how to approach this and I find that I'm at a loss with a lot of terminology with assignments. I think it could be helpful to review necessary vocab. I was using my agent to figure out around vocab I found unfamiliar even simple vocab like git, trying to find definitions is quite difficult to understand and apply to assignments.
I just used my agent to do this:

Commit 6726361 — "YOLO: remove shot cooldown for auto-fire" (the agent's bad idea)
Commit 86beeb8 — "Revert YOLO: remove shot cooldown for auto-fire" (thrown away)

It was to 
