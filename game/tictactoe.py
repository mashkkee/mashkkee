"""Issue-driven tic-tac-toe for the profile README.

A README cannot run code, so each move is an issue: a cell link opens a new
issue whose title is "ttt <cell>", and a GitHub Action runs this script on it.
The script reads TITLE and AUTHOR from the environment, updates state.json,
redraws board.svg, and prints the reply the workflow posts back to the issue.
"""

import json
import os
from pathlib import Path

GAME = Path(__file__).resolve().parent
STATE = GAME / "state.json"
BOARD = GAME / "board.svg"

LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
]


def new_state():
    return {"board": [""] * 9, "turn": "X", "winner": None, "last": None, "by": None}


def load():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return new_state()


def winner_of(board):
    for a, b, c in LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if all(board):
        return "draw"
    return None


def apply_move(title, author, state):
    """Return (state, reply). The state is unchanged when the move is refused."""
    parts = title.strip().lower().split()
    if len(parts) != 2 or parts[0] != "ttt":
        return state, "Title must be `ttt <cell 1-9>` or `ttt reset`. Nothing changed."

    command = parts[1]
    if command == "reset":
        return new_state(), "Board reset. X starts again."

    if state["winner"]:
        return state, "The game is over. Open an issue titled `ttt reset` to start again."

    if not command.isdigit() or not 1 <= int(command) <= 9:
        return state, "Cell must be a number from 1 to 9. Nothing changed."

    cell = int(command) - 1
    if state["board"][cell]:
        return state, f"Cell {cell + 1} is already taken. Nothing changed."

    mark = state["turn"]
    state["board"][cell] = mark
    state["winner"] = winner_of(state["board"])
    state["turn"] = "O" if mark == "X" else "X"
    state["last"] = f"{mark} to cell {cell + 1}"
    state["by"] = author

    move = f"{mark} to cell {cell + 1} by @{author}"
    if state["winner"] == "draw":
        return state, f"{move}. It's a draw."
    if state["winner"]:
        return state, f"{move}. {state['winner']} wins!"
    return state, f"{move}. Next: {state['turn']}."


def render(state):
    board = state["board"]
    width, height = 560, 420
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Consolas, Courier New, monospace">',
        f'<rect width="{width}" height="{height}" rx="16" fill="#0d1117" stroke="#30363d"/>',
        '<text x="30" y="44" fill="#ff2e2e" font-size="17" font-weight="bold">'
        'TIC-TAC-TOE // PLAY IN THE ISSUES</text>',
    ]

    for i, mark in enumerate(board):
        row, col = divmod(i, 3)
        x, y = 40 + col * 100, 80 + row * 100
        cx, cy = x + 50, y + 50
        out.append(f'<rect x="{x + 5}" y="{y + 5}" width="90" height="90" rx="10" '
                   f'fill="#161b22" stroke="#30363d"/>')
        if mark == "X":
            out.append(f'<path d="M{cx - 25} {cy - 25} L{cx + 25} {cy + 25} M{cx + 25} {cy - 25} '
                       f'L{cx - 25} {cy + 25}" stroke="#ff2e2e" stroke-width="9" '
                       f'stroke-linecap="round"/>')
        elif mark == "O":
            out.append(f'<circle cx="{cx}" cy="{cy}" r="25" fill="none" stroke="#e6edf3" '
                       f'stroke-width="9"/>')
        else:
            out.append(f'<text x="{cx}" y="{cy + 8}" fill="#8b949e" font-size="20" '
                       f'text-anchor="middle">{i + 1}</text>')

    if state["winner"] == "draw":
        status = "DRAW"
    elif state["winner"]:
        status = f"WINNER: {state['winner']}"
    else:
        status = f"TURN: {state['turn']}"
    out.append(f'<text x="370" y="130" fill="#e6edf3" font-size="20" font-weight="bold">{status}</text>')
    out.append('<text x="370" y="170" fill="#8b949e" font-size="12">Click a number above.</text>')
    out.append('<text x="370" y="189" fill="#8b949e" font-size="12">Submit the issue it opens.</text>')
    out.append('<text x="370" y="208" fill="#8b949e" font-size="12">A bot plays and closes it.</text>')
    if state["last"]:
        out.append(f'<text x="370" y="270" fill="#8b949e" font-size="12">last: {state["last"]}</text>')
        out.append(f'<text x="370" y="289" fill="#8b949e" font-size="12">by: @{state["by"][:20]}</text>')
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
