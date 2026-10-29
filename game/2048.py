"""2048 for the profile README, played through issues like tic-tac-toe.

A direction link opens an issue titled "2048 <direction>". The workflow runs
this script with TITLE and AUTHOR in the environment, which updates
state2048.json and redraws board2048.svg. The script prints the reply that the
workflow posts back to the issue.
"""

import json
import os
import random
from pathlib import Path

GAME = Path(__file__).resolve().parent
STATE = GAME / "state2048.json"
BOARD = GAME / "board2048.svg"

DIRECTIONS = ("up", "down", "left", "right")

TILE_COLOURS = {
    0: "#1c2128", 2: "#eee4da", 4: "#ede0c8", 8: "#f2b179", 16: "#f59563",
    32: "#f67c5f", 64: "#f65e3b", 128: "#edcf72", 256: "#edcc61", 512: "#edc850",
    1024: "#edc53f", 2048: "#edc22e",
}


def spawn(grid):
    empty = [(r, c) for r in range(4) for c in range(4) if grid[r][c] == 0]
    if empty:
        r, c = random.choice(empty)
        grid[r][c] = 4 if random.random() < 0.1 else 2


def new_state():
    grid = [[0] * 4 for _ in range(4)]
    spawn(grid)
    spawn(grid)
    return {"grid": grid, "score": 0, "over": False, "last": None, "by": None}


def load():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return new_state()


def slide_left(row):
    """Slide one row to the left and merge equal neighbours once per move."""
    tiles = [v for v in row if v]
    out, gained, i = [], 0, 0
    while i < len(tiles):
        if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
            merged = tiles[i] * 2
            out.append(merged)
            gained += merged
            i += 2
        else:
            out.append(tiles[i])
            i += 1
    out += [0] * (4 - len(out))
    return out, gained


def move(grid, direction):
    """Return (new_grid, points_gained). The input grid is not modified."""
    columns = direction in ("up", "down")
    working = [list(col) for col in zip(*grid)] if columns else [row[:] for row in grid]
    reverse = direction in ("right", "down")

    rows, gained = [], 0
    for row in working:
        if reverse:
            new, points = slide_left(row[::-1])
            new = new[::-1]
        else:
            new, points = slide_left(row)
        rows.append(new)
        gained += points

    result = [list(col) for col in zip(*rows)] if columns else rows
    return result, gained


def has_move(grid):
    return any(move(grid, d)[0] != grid for d in DIRECTIONS)


def apply_move(title, author, state):
    """Return (state, reply). The state is unchanged when the move is refused."""
    parts = title.strip().lower().split()
    if len(parts) != 2 or parts[0] != "2048":
        return state, "Title must be `2048 up|down|left|right` or `2048 new`. Nothing changed."

    command = parts[1]
    if command == "new":
        return new_state(), "New game. Two tiles spawned."

    if state["over"]:
        return state, "No moves left. Open an issue titled `2048 new` to start again."

    if command not in DIRECTIONS:
        return state, "Direction must be up, down, left or right. Nothing changed."

    new_grid, gained = move(state["grid"], command)
    if new_grid == state["grid"]:
        return state, f"Nothing moved {command}. Try another direction. Nothing changed."

    spawn(new_grid)
    state["grid"] = new_grid
    state["score"] += gained
    state["last"] = command
    state["by"] = author
    state["over"] = not has_move(new_grid)

    reply = f"Moved {command} by @{author}, +{gained}. Score {state['score']}."
    if state["over"]:
        reply += " No moves left: game over."
    return state, reply


def render(state):
    width, height = 420, 490
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Consolas, Courier New, monospace">',
        f'<rect width="{width}" height="{height}" rx="16" fill="#0d1117" stroke="#30363d"/>',
        '<text x="30" y="44" fill="#ff2e2e" font-size="17" font-weight="bold">2048 // PLAY IN THE ISSUES</text>',
        f'<text x="30" y="72" fill="#e6edf3" font-size="14">score {state["score"]}</text>',
    ]
    if state["over"]:
        out.append('<text x="390" y="72" fill="#ff2e2e" font-size="14" font-weight="bold" '
                   'text-anchor="end">GAME OVER</text>')

    for r in range(4):
        for c in range(4):
            value = state["grid"][r][c]
            x, y = 30 + c * 94, 90 + r * 94
            out.append(f'<rect x="{x}" y="{y}" width="86" height="86" rx="8" '
                       f'fill="{TILE_COLOURS.get(value, "#3c3a32")}"/>')
            if value:
                size = 30 if value < 100 else 24 if value < 1000 else 19
                ink = "#776e65" if value <= 4 else "#f9f6f2"
                out.append(f'<text x="{x + 43}" y="{y + 52}" fill="{ink}" font-size="{size}" '
                           f'font-weight="bold" text-anchor="middle">{value}</text>')

    if state["last"]:
        out.append(f'<text x="30" y="474" fill="#8b949e" font-size="12">'
                   f'last: {state["last"]} by @{state["by"][:20]}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    title = os.environ.get("TITLE", "")
    author = os.environ.get("AUTHOR", "someone")

    state, reply = apply_move(title, author, load())
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    BOARD.write_text(render(state))
    print(reply)


if __name__ == "__main__":
    main()
