# Keno

A lottery-style Keno game in a single Python file, with a graphical board
(tkinter) and a text mode.

## Run

```sh
python3 keno.py          # graphical version
python3 keno.py --text   # terminal version
```

Needs Python 3 with tkinter (included with most Python installs; on Fedora
install `python3-tkinter`, on Debian/Ubuntu `python3-tk`). No other packages.

## How to play

- Click 1 to 10 numbers on the board, or use **Quick Pick**.
- Choose a wager ($1-$20 per game) and how many consecutive games to play
  (1-100, up to $100 per ticket).
- Optional add-ons:
  - **Special Keno**: bigger top prizes, fewer small prizes. No extra cost.
  - **Multiplier**: +$1 per $1. Multiplies Keno prizes by 1x-10x.
  - **Bulls-Eye**: +$1 per $1. Bonus prize if you picked the Bulls-Eye number.
  - **Keno To Go**: start your games at a later hour today.
- **BUY TICKET**, then **NEXT DRAW** (one animated game) or **PLAY MY TICKETS**
  (runs every game on your tickets).
- Cash winnings from the **My Tickets** tab. Past games are in **Draw History**.
- **Rules & Pay Tables** shows the full rules and prize tables.

A new game is drawn every 4 simulated minutes. Each game has its own game
number. Match 8 of 8 on an 8-spot ticket to win the rolling Jackpot Bonus.

## Randomness

All draws use `random.SystemRandom`, which reads the operating system's
secure random source.

This is a simulation for entertainment only; no real money is involved.
