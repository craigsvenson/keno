
import random
import sys
import tkinter as tk
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

# All randomness comes from the operating system's secure random source
# (os.urandom / getrandom), not Python's predictable default generator.
rng = random.SystemRandom()

# Base Payouts (per $1 wagered)
# Format: {spots_played: {matches: (regular_keno, special_keno, bulls_eye)}}
PAYOUTS = {
    10: {
        10: (200000, 1000000, 300000),
        9: (4500, 22000, 15500),
        8: (500, 1200, 1000),
        7: (55, 140, 95),
        6: (10, 4, 25),
        5: (2, 0, 5),
        4: (0, 0, 5),
        3: (0, 0, 2),
        2: (0, 0, 2),
        1: (0, 0, 5),
        0: (5, 0, 0),
    },
    9: {
        9: (50000, 75000, 100000),
        8: (3000, 4000, 5000),
        7: (215, 300, 345),
        6: (25, 40, 50),
        5: (4, 2, 11),
        4: (1, 0, 5),
        3: (0, 0, 2),
        2: (0, 0, 2),
        1: (0, 0, 5),
    },
    8: {
        8: (15000, 25000, 40000),
        7: (600, 1750, 1400),
        6: (60, 75, 140),
        5: (10, 5, 27),
        4: (2, 0, 5),
        3: (0, 0, 2),
        2: (0, 0, 2),
        1: (0, 0, 5),
    },
    7: {
        7: (5500, 7500, 12000),
        6: (150, 330, 400),
        5: (15, 20, 60),
        4: (2, 1, 10),
        3: (1, 0, 3),
        2: (0, 0, 2),
        1: (0, 0, 5),
    },
    6: {
        6: (1600, 2500, 3200),
        5: (55, 90, 95),
        4: (5, 2, 20),
        3: (1, 0, 9),
        2: (0, 0, 3),
        1: (0, 0, 4),
    },
    5: {
        5: (465, 800, 1035),
        4: (15, 12, 70),
        3: (2, 0, 10),
        2: (0, 0, 4),
        1: (0, 0, 4),
    },
    4: {
        4: (72, 140, 318),
        3: (5, 5, 20),
        2: (1, 0, 10),
        1: (0, 0, 5),
    },
    3: {
        3: (27, 47, 128),
        2: (2, 0, 15),
        1: (0, 0, 8),
    },
    2: {
        2: (11, 11, 60),
        1: (0, 0, 15),
    },
    1: {
        1: (2.50, 2.50, 49.50),
    },
}

# Multiplier odds (drawn separately, before each regular drawing)
MULTIPLIERS = [1, 2, 3, 5, 10]
MULTIPLIER_WEIGHTS = [45.0, 28.3, 16.0, 9.7, 1.0]

# ---------------------------------------------------------------------------
# Game rules
# ---------------------------------------------------------------------------

WAGERS = (1, 2, 3, 4, 5, 10, 20)                     # base wager per game
GAME_COUNTS = (1, 2, 3, 4, 5, 10, 15, 20, 50, 100)   # consecutive games on one ticket
MAX_TICKET_COST = 100                                # maximum wager per ticket
PRIZE_CAP = 1_000_000                                # max prize per prize category

DRAW_INTERVAL = timedelta(minutes=4)                 # a new game every 4 minutes
OPEN_HOUR = 5                                        # first draw at 5:00 AM
CLOSE_HOUR = 4                                       # no draws from 4:00 to 5:00 AM
# Start times offered by "Keno To Go" (later today)
KENO_TO_GO_HOURS = (6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
                    18, 19, 20, 21, 22, 23, 0, 1, 2, 3)

JACKPOT_SPOTS = 8                     # the rolling Jackpot Bonus is on the 8-spot game
JACKPOT_SEED = 10_000.00              # reset amount after a win (assumed)
JACKPOT_RATE = 0.15                   # share of each base-wager dollar added (assumed)
# Simulated sales by other players around the state. The real jackpot averages
# about $30,000, so it grows a little every draw and is sometimes won elsewhere.
STATEWIDE_GROWTH = (5.00, 15.00)      # added to the jackpot per draw
STATEWIDE_JACKPOT_ODDS = 2000         # won elsewhere about once in this many draws

RETAILER_CLAIM_LIMIT = 600            # prizes up to this are paid by any retailer
SAME_DAY_CLAIM_LIMIT = 49_999         # up to this paid same day at a claim center

STARTING_BALANCE = 100.00

RULES_TEXT = f"""\
HOW KENO WORKS
  * A new game is drawn every 4 minutes, 5:00 AM to 4:00 AM every day.
  * Each game has its own game number; numbers count up by one per draw.
  * Pick 1 to 10 spots from 1-80. Each game draws 20 numbers.
  * Wager $1, $2, $3, $4, $5, $10 or $20 per game.
  * Play 1, 2, 3, 4, 5, 10, 15, 20, 50 or 100 consecutive games on one
    ticket with the same numbers. Maximum ${MAX_TICKET_COST} per ticket.

OPTIONS
  * Special Keno - bigger top prizes, fewer small prizes. No extra cost.
  * Multiplier - +$1 per $1 wagered. A multiplier (1x, 2x, 3x, 5x or 10x)
    is drawn before each game and multiplies Keno prizes. It does not
    multiply Bulls-Eye or Jackpot Bonus prizes.
  * Bulls-Eye - +$1 per $1 wagered. After the 20 numbers are drawn, one
    of them is chosen as the Bulls-Eye. If you picked it, you win the
    Bulls-Eye prize on top of your Keno prize.
  * Keno To Go - choose a time later today for your games to begin.

JACKPOT BONUS
  * Match 8 of 8 on an 8-spot game to win the rolling Jackpot Bonus on
    top of the 8-spot prize. It grows every draw until someone wins it.
  * Several winners in one game share it in proportion to their wagers.

PRIZES & CLAIMS
  * Maximum prize per prize category on any ticket is $1,000,000.
    The Jackpot Bonus is paid in addition.
  * Up to ${RETAILER_CLAIM_LIMIT}: any Lottery retailer.
  * ${RETAILER_CLAIM_LIMIT + 1} - ${SAME_DAY_CLAIM_LIMIT:,}: Lottery HQ or a payment center, paid same day.
  * ${SAME_DAY_CLAIM_LIMIT + 1:,}+: Lottery HQ, paid after 8 AM the next business day.
  * Multi-game tickets can be cashed at any time; you get an exchange
    ticket for the games that haven't been drawn yet.
  * You have one year from the date of the drawing to claim.

MULTIPLIER ODDS
  1x 45.0% (1:2.22)   2x 28.3% (1:3.53)   3x 16.0% (1:6.25)
  5x  9.7% (1:10.31)  10x 1.0% (1:100)
"""


# ---------------------------------------------------------------------------
# Draw schedule
# ---------------------------------------------------------------------------

def _skip_closed_hour(t):
    if CLOSE_HOUR <= t.hour < OPEN_HOUR:
        t = t.replace(hour=OPEN_HOUR, minute=0, second=0, microsecond=0)
    return t


def business_day_open(t):
    """5:00 AM at the start of the Keno business day that contains t."""
    day_open = t.replace(hour=OPEN_HOUR, minute=0, second=0, microsecond=0)
    if t.hour < OPEN_HOUR:
        day_open -= timedelta(days=1)
    return day_open


def first_draw_at_or_after(t):
    """Return the first scheduled draw time at or after t."""
    t = _skip_closed_hour(t)
    day_open = business_day_open(t)
    seconds = (t - day_open).total_seconds()
    interval = DRAW_INTERVAL.total_seconds()
    slots = -(-seconds // interval)  # round up to the next draw slot
    return _skip_closed_hour(day_open + timedelta(seconds=slots * interval))


def next_draw_time(t):
    return _skip_closed_hour(t + DRAW_INTERVAL)


def fmt_time(t):
    return t.strftime("%I:%M %p").lstrip("0")


def fmt_hour(hour):
    suffix = "AM" if hour < 12 else "PM"
    return f"{(hour % 12) or 12} {suffix}"


def fmt_money(value):
    return f"${value:,.0f}" if value == int(value) else f"${value:,.2f}"


# ---------------------------------------------------------------------------
# Game logic (shared by the graphical and text versions)
# ---------------------------------------------------------------------------

def ticket_cost(wager, bulls_eye_opt, multiplier_opt):
    """Cost of one game on a ticket."""
    return wager * (1 + int(bulls_eye_opt) + int(multiplier_opt))


def calculate_winnings(picks, drawn, bulls_eye_num, multiplier, wager,
                       special_keno, bulls_eye_opt, multiplier_opt, jackpot):
    """Work out the prizes for one game on a ticket. Returns a dict of results."""
    spots = len(picks)
    matches = len(set(picks) & set(drawn))
    hit_bulls_eye = bulls_eye_num in picks

    base_prize = 0
    bulls_eye_prize = 0
    jackpot_win = 0

    spot_table = PAYOUTS[spots]
    if matches in spot_table:
        reg_pay, spec_pay, be_pay = spot_table[matches]

        # Regular or Special Keno Base Prize
        base_prize = (spec_pay if special_keno else reg_pay) * wager

        # Apply Multiplier (applies to Keno prizes, not Bulls-Eye or Jackpot)
        if multiplier_opt and base_prize > 0:
            base_prize *= multiplier

        # Apply Bulls-Eye Prize
        if bulls_eye_opt and hit_bulls_eye:
            bulls_eye_prize = be_pay * wager

    # Rolling Jackpot Bonus (the engine splits it if there are several winners)
    if spots == JACKPOT_SPOTS and matches == JACKPOT_SPOTS:
        jackpot_win = jackpot

    # Cap each prize category at $1,000,000 (the Jackpot Bonus is paid on top)
    base_prize = min(base_prize, PRIZE_CAP)
    bulls_eye_prize = min(bulls_eye_prize, PRIZE_CAP)

    return {
        "matches": matches,
        "hit_bulls_eye": hit_bulls_eye,
        "multiplier": multiplier,
        "base_prize": base_prize,
        "bulls_eye_prize": bulls_eye_prize,
        "jackpot_win": jackpot_win,
        "total_win": base_prize + bulls_eye_prize + jackpot_win,
    }


def claim_note(amount):
    if amount <= RETAILER_CLAIM_LIMIT:
        where = "Paid by any Lottery retailer."
    elif amount <= SAME_DAY_CLAIM_LIMIT:
        where = ("Claim at Lottery HQ (Salem) or the Wilsonville Payment "
                 "Center - paid the same day - or by registered mail.")
    else:
        where = ("Claim at Lottery HQ (Salem) - paid after 8:00 AM the next "
                 "business day - or by registered mail.")
    return where + " Claim within one year of the drawing."


@dataclass
class Draw:
    game: int
    time: datetime
    numbers: list
    bulls_eye: int
    multiplier: int
    jackpot: float                      # Jackpot Bonus on offer for this game
    jackpot_won_elsewhere: bool = False


@dataclass(eq=False)   # compare tickets by identity so they can be dict keys
class Ticket:
    ticket_id: int
    picks: tuple
    wager: int
    special: bool
    bulls_eye: bool
    multiplier: bool
    first_game: int
    first_time: datetime
    num_games: int
    results: dict = field(default_factory=dict)   # game number -> result dict
    cashed: float = 0.0

    @property
    def last_game(self):
        return self.first_game + self.num_games - 1

    @property
    def cost_per_game(self):
        return ticket_cost(self.wager, self.bulls_eye, self.multiplier)

    @property
    def total_cost(self):
        return self.cost_per_game * self.num_games

    @property
    def games_played(self):
        return len(self.results)

    @property
    def complete(self):
        return self.games_played == self.num_games

    @property
    def total_won(self):
        return sum(r["total_win"] for r in self.results.values())

    @property
    def unclaimed(self):
        return self.total_won - self.cashed

    def covers(self, game):
        return self.first_game <= game <= self.last_game

    def options_text(self):
        flags = [name for on, name in ((self.special, "Special"),
                                       (self.multiplier, "Mult"),
                                       (self.bulls_eye, "BE")) if on]
        return f"${self.wager}" + (" " + "/".join(flags) if flags else "")

    def status(self):
        if self.games_played == 0:
            return f"Starts {fmt_time(self.first_time)}"
        if not self.complete:
            text = f"In play {self.games_played}/{self.num_games}"
            return text + " (exchanged)" if self.cashed else text
        if self.unclaimed > 0.005:
            return "Ready to cash"
        return "Cashed" if self.total_won else "Finished"


class KenoGame:
    """The Lottery side of things: game numbers, the clock, tickets and draws."""

    def __init__(self, now=None):
        self.balance = STARTING_BALANCE
        self.jackpot = round(rng.uniform(JACKPOT_SEED, 3 * JACKPOT_SEED), 2)
        self.next_game = rng.randint(2_000_000, 2_900_000)
        self.next_time = first_draw_at_or_after(now or datetime.now())
        self.history = {}          # game number -> Draw
        self.tickets = []
        self._ticket_seq = 0

    # ----- schedule --------------------------------------------------------

    def game_at_or_after(self, when):
        """First upcoming game number (and its time) drawn at or after `when`."""
        game, t = self.next_game, self.next_time
        while t < when:
            game, t = game + 1, next_draw_time(t)
        return game, t

    def keno_to_go_options(self):
        """[(label, start datetime)] for the start times still available today."""
        day_open = business_day_open(self.next_time)
        options = []
        for hour in KENO_TO_GO_HOURS:
            start = day_open.replace(hour=hour)
            if hour < OPEN_HOUR:
                start += timedelta(days=1)
            if start > self.next_time:
                options.append((fmt_hour(hour), start))
        return options

    # ----- tickets ---------------------------------------------------------

    def buy_ticket(self, picks, wager, special, bulls_eye, multiplier,
                   num_games, start_time=None):
        if not 1 <= len(picks) <= 10:
            raise ValueError("Pick 1 to 10 numbers.")
        if wager not in WAGERS:
            raise ValueError("Choose a standard wager amount.")
        if num_games not in GAME_COUNTS:
            raise ValueError("Choose a standard number of games.")
        total = ticket_cost(wager, bulls_eye, multiplier) * num_games
        if total > MAX_TICKET_COST:
            raise ValueError(f"Ticket costs {fmt_money(total)}; the maximum "
                             f"per ticket is {fmt_money(MAX_TICKET_COST)}.")
        if total > self.balance:
            raise ValueError(f"Insufficient funds! Ticket costs {fmt_money(total)}, "
                             f"balance is ${self.balance:,.2f}.")

        if start_time is None:
            first_game, first_time = self.next_game, self.next_time
        else:
            first_game, first_time = self.game_at_or_after(start_time)

        self._ticket_seq += 1
        ticket = Ticket(self._ticket_seq, tuple(sorted(picks)), wager, special,
                        bulls_eye, multiplier, first_game, first_time, num_games)
        self.balance -= total
        self.tickets.append(ticket)
        return ticket

    def active_tickets(self):
        return [t for t in self.tickets if not t.complete]

    def tickets_for(self, game):
        return [t for t in self.tickets if t.covers(game)]

    def uncashed_total(self):
        return sum(t.unclaimed for t in self.tickets)

    def cash(self, ticket):
        """Pay out what the ticket has won so far. Returns the amount paid."""
        amount = round(ticket.unclaimed, 2)
        if amount <= 0:
            return 0
        ticket.cashed += amount
        self.balance += amount
        return amount

    def is_broke(self):
        return (self.balance < 1 and not self.active_tickets()
                and self.uncashed_total() < 0.005)

    # ----- drawing ---------------------------------------------------------

    def run_draw(self):
        """Draw the next game. Returns (Draw, [(ticket, result), ...])."""
        game, when = self.next_game, self.next_time
        playing = self.tickets_for(game)

        # The jackpot is funded from Keno sales (not Multiplier/Bulls-Eye sales)
        self.jackpot += sum(t.wager for t in playing) * JACKPOT_RATE
        self.jackpot += rng.uniform(*STATEWIDE_GROWTH)
        self.jackpot = round(self.jackpot, 2)

        multiplier = rng.choices(MULTIPLIERS, weights=MULTIPLIER_WEIGHTS, k=1)[0]
        numbers = sorted(rng.sample(range(1, 81), 20))
        bulls_eye = rng.choice(numbers)
        draw = Draw(game, when, numbers, bulls_eye, multiplier, self.jackpot)

        results = []
        for t in playing:
            r = calculate_winnings(t.picks, numbers, bulls_eye, multiplier, t.wager,
                                   t.special, t.bulls_eye, t.multiplier, self.jackpot)
            t.results[game] = r
            results.append((t, r))

        # Jackpot Bonus is pari-mutuel: winners share it by amount wagered
        winners = [(t, r) for t, r in results if r["jackpot_win"]]
        if winners:
            pool = self.jackpot
            total_wagered = sum(t.wager for t, _ in winners)
            for t, r in winners:
                share = round(pool * t.wager / total_wagered, 2)
                r["total_win"] += share - r["jackpot_win"]
                r["jackpot_win"] = share
            self.jackpot = JACKPOT_SEED
        elif rng.randrange(STATEWIDE_JACKPOT_ODDS) == 0:
            draw.jackpot_won_elsewhere = True
            self.jackpot = JACKPOT_SEED

        self.history[game] = draw
        self.next_game, self.next_time = game + 1, next_draw_time(when)
        return draw, results


# ---------------------------------------------------------------------------
# Graphical version (tkinter)
# ---------------------------------------------------------------------------

BG = "#14182e"
PANEL_BG = "#1f2547"
CELL_BG = "#2d3561"
CELL_OUTLINE = "#3e4780"
PICK_COLOR = "#f5a623"      # your pick
DRAWN_COLOR = "#4a90e2"     # drawn, not picked
HIT_COLOR = "#2ecc71"       # drawn and picked
BULLS_EYE_RING = "#ff3b3b"
TEXT_LIGHT = "#ecf0ff"
TEXT_DARK = "#14182e"
ACCENT = "#ffd166"
WARN = "#ff6b6b"

CELL = 50
PAD = 10
COLS, ROWS = 10, 8
DRAW_DELAY_MS = 90          # per number when revealing a single draw
AUTO_DELAY_MS = 350         # pause between games when playing tickets out
HISTORY_LIMIT = 500


class KenoApp:
    def __init__(self, root):
        self.root = root
        self.game = KenoGame()
        self.picks = set()
        self.revealed = set()
        self.bulls_eye = None
        self.busy = False
        self.auto_running = False
        self.start_options = {}

        self.wager_var = tk.IntVar(value=1)
        self.games_var = tk.IntVar(value=1)
        self.special_var = tk.BooleanVar(value=False)
        self.be_var = tk.BooleanVar(value=False)
        self.mult_var = tk.BooleanVar(value=False)
        self.qp_spots_var = tk.IntVar(value=10)
        self.start_var = tk.StringVar(value="Now")

        root.title("Keno")
        root.configure(bg=BG)
        root.resizable(False, False)

        self._style()
        self._build_ui()
        for var in (self.wager_var, self.games_var, self.be_var, self.mult_var):
            var.trace_add("write", lambda *_: self._update_labels())
        self._redraw_board()
        self._refresh_all()

    # ----- UI construction -------------------------------------------------

    def _style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Treeview", background=CELL_BG, fieldbackground=CELL_BG,
                        foreground=TEXT_LIGHT, rowheight=22, borderwidth=0,
                        font=("Helvetica", 10))
        style.configure("Treeview.Heading", background=PANEL_BG, foreground=ACCENT,
                        font=("Helvetica", 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", DRAWN_COLOR)])
        style.map("Treeview.Heading", background=[("active", CELL_OUTLINE)])
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL_BG, foreground=TEXT_LIGHT,
                        padding=(12, 4), font=("Helvetica", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", CELL_BG)],
                  foreground=[("selected", ACCENT)])

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(header, text="KENO", bg=BG, fg=ACCENT,
                 font=("Helvetica", 26, "bold")).pack(side="left")
        tk.Label(header, text="  New game every 4 minutes", bg=BG, fg=TEXT_LIGHT,
                 font=("Helvetica", 11)).pack(side="left", pady=(10, 0))
        self.jackpot_label = tk.Label(header, bg=BG, fg=ACCENT,
                                      font=("Helvetica", 14, "bold"))
        self.jackpot_label.pack(side="right")

        self.clock_label = tk.Label(self.root, bg=PANEL_BG, fg=TEXT_LIGHT,
                                    font=("Helvetica", 12, "bold"), pady=4)
        self.clock_label.pack(fill="x", padx=14)

        main = tk.Frame(self.root, bg=BG)
        main.pack(padx=14, pady=(8, 6))

        # ---- Board ----
        left = tk.Frame(main, bg=BG)
        left.grid(row=0, column=0, sticky="n")
        self.draw_info_label = tk.Label(left, text="Pick your numbers",
                                        bg=BG, fg=TEXT_LIGHT,
                                        font=("Helvetica", 12, "bold"))
        self.draw_info_label.pack(pady=(0, 4))

        width = COLS * CELL + PAD * 2
        height = ROWS * CELL + PAD * 2
        self.canvas = tk.Canvas(left, width=width, height=height, bg=PANEL_BG,
                                highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_board_click)

        self.cells = {}
        for n in range(1, 81):
            row, col = divmod(n - 1, COLS)
            x0 = PAD + col * CELL + 4
            y0 = PAD + row * CELL + 4
            x1, y1 = x0 + CELL - 8, y0 + CELL - 8
            oval = self.canvas.create_oval(x0, y0, x1, y1, fill=CELL_BG,
                                           outline=CELL_OUTLINE, width=2)
            text = self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2,
                                           text=str(n), fill=TEXT_LIGHT,
                                           font=("Helvetica", 13, "bold"))
            self.cells[n] = (oval, text)

        legend = tk.Frame(left, bg=BG)
        legend.pack(pady=(6, 0))
        for color, label in ((PICK_COLOR, "Your pick"), (DRAWN_COLOR, "Drawn"),
                             (HIT_COLOR, "Match"), (BULLS_EYE_RING, "Bulls-Eye")):
            swatch = tk.Canvas(legend, width=16, height=16, bg=BG, highlightthickness=0)
            if label == "Bulls-Eye":
                swatch.create_oval(2, 2, 14, 14, outline=color, width=3)
            else:
                swatch.create_oval(2, 2, 14, 14, fill=color, outline=color)
            swatch.pack(side="left", padx=(10, 3))
            tk.Label(legend, text=label, bg=BG, fg=TEXT_LIGHT,
                     font=("Helvetica", 10)).pack(side="left")

        # ---- Ticket builder / controls ----
        panel = tk.Frame(main, bg=PANEL_BG, padx=14, pady=10)
        panel.grid(row=0, column=1, sticky="ns", padx=(14, 0))

        self.balance_label = tk.Label(panel, bg=PANEL_BG, fg=HIT_COLOR,
                                      font=("Helvetica", 18, "bold"))
        self.balance_label.pack(anchor="w")
        self.uncashed_label = tk.Label(panel, bg=PANEL_BG, fg=ACCENT,
                                       font=("Helvetica", 10, "bold"))
        self.uncashed_label.pack(anchor="w")

        self._section(panel, "Wager per game")
        self._radio_row(panel, WAGERS, self.wager_var, lambda w: f"${w}")

        self._section(panel, "Consecutive games")
        self._radio_row(panel, GAME_COUNTS[:5], self.games_var, str)
        self._radio_row(panel, GAME_COUNTS[5:], self.games_var, str)

        self._section(panel, "Options")
        for text, var in (("Special Keno (bigger top prizes)", self.special_var),
                          ("Multiplier (+$1 per $1 wagered)", self.mult_var),
                          ("Bulls-Eye (+$1 per $1 wagered)", self.be_var)):
            tk.Checkbutton(panel, text=text, variable=var, bg=PANEL_BG, fg=TEXT_LIGHT,
                           selectcolor=CELL_BG, activebackground=PANEL_BG,
                           activeforeground=TEXT_LIGHT, font=("Helvetica", 10),
                           ).pack(anchor="w")

        togo = tk.Frame(panel, bg=PANEL_BG)
        togo.pack(anchor="w", pady=(4, 0))
        tk.Label(togo, text="Keno To Go - start:", bg=PANEL_BG, fg=TEXT_LIGHT,
                 font=("Helvetica", 10)).pack(side="left")
        self.start_menu = tk.OptionMenu(togo, self.start_var, "Now")
        self.start_menu.config(bg=CELL_BG, fg=TEXT_LIGHT, activebackground=CELL_OUTLINE,
                               activeforeground=TEXT_LIGHT, highlightthickness=0,
                               relief="flat", font=("Helvetica", 10), width=6)
        self.start_menu["menu"].config(bg=CELL_BG, fg=TEXT_LIGHT)
        self.start_menu.pack(side="left", padx=6)

        self._section(panel, "Numbers")
        qp_row = tk.Frame(panel, bg=PANEL_BG)
        qp_row.pack(anchor="w")
        tk.Spinbox(qp_row, from_=1, to=10, width=3, textvariable=self.qp_spots_var,
                   state="readonly", font=("Helvetica", 11)).pack(side="left")
        self.qp_button = self._button(qp_row, "Quick Pick", self._quick_pick)
        self.qp_button.pack(side="left", padx=6)
        self.clear_button = self._button(qp_row, "Clear", self._clear_picks)
        self.clear_button.pack(side="left")

        self.spots_label = tk.Label(panel, bg=PANEL_BG, fg=TEXT_LIGHT,
                                    font=("Helvetica", 10))
        self.spots_label.pack(anchor="w", pady=(6, 0))
        self.cost_label = tk.Label(panel, bg=PANEL_BG, fg=TEXT_LIGHT,
                                   font=("Helvetica", 11, "bold"))
        self.cost_label.pack(anchor="w")

        self.buy_button = tk.Button(panel, text="BUY TICKET", command=self._buy,
                                    bg=PICK_COLOR, fg=TEXT_DARK,
                                    activebackground="#d48f1c",
                                    font=("Helvetica", 14, "bold"),
                                    relief="flat", pady=4)
        self.buy_button.pack(fill="x", pady=(8, 6))

        draw_row = tk.Frame(panel, bg=PANEL_BG)
        draw_row.pack(fill="x")
        self.next_button = tk.Button(draw_row, text="NEXT DRAW", command=self._next_draw,
                                     bg=HIT_COLOR, fg=TEXT_DARK,
                                     activebackground="#27ae60",
                                     font=("Helvetica", 11, "bold"), relief="flat")
        self.next_button.pack(side="left", fill="x", expand=True)
        self.auto_button = tk.Button(draw_row, text="PLAY MY TICKETS",
                                     command=self._toggle_auto, bg=DRAWN_COLOR,
                                     fg=TEXT_DARK, activebackground="#3a78c2",
                                     font=("Helvetica", 11, "bold"), relief="flat")
        self.auto_button.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.result_label = tk.Label(panel, text="", bg=BG, fg=TEXT_LIGHT,
                                     font=("Courier", 10), justify="left",
                                     anchor="nw", width=36, height=6,
                                     padx=6, pady=4)
        self.result_label.pack(fill="both", pady=(8, 6))

        self._button(panel, "Rules & Pay Tables", self._show_rules).pack(fill="x")

        # ---- Tickets and history ----
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="x", padx=14, pady=(0, 12))

        tickets_tab = tk.Frame(notebook, bg=BG)
        notebook.add(tickets_tab, text="My Tickets")
        columns = (("id", "#", 40), ("numbers", "Numbers", 220), ("bet", "Bet", 120),
                   ("games", "Games", 180), ("won", "Won", 90),
                   ("unclaimed", "To cash", 90), ("status", "Status", 150))
        self.ticket_tree = self._tree(tickets_tab, columns)
        self.ticket_tree.bind("<<TreeviewSelect>>", self._on_ticket_select)
        buttons = tk.Frame(tickets_tab, bg=BG)
        buttons.pack(fill="x", pady=(4, 0))
        self._button(buttons, "Cash Selected", self._cash_selected).pack(side="left")
        self._button(buttons, "Cash All", self._cash_all).pack(side="left", padx=6)
        tk.Label(buttons, text="Select a ticket to load its numbers and settings.",
                 bg=BG, fg=TEXT_LIGHT, font=("Helvetica", 9)).pack(side="right")

        history_tab = tk.Frame(notebook, bg=BG)
        notebook.add(history_tab, text="Draw History")
        columns = (("game", "Game #", 90), ("time", "Time", 80), ("mult", "Mult", 50),
                   ("be", "Bulls-Eye", 75), ("jackpot", "Jackpot", 95),
                   ("numbers", "Winning numbers", 500))
        self.history_tree = self._tree(history_tab, columns)
        self.history_tree.bind("<<TreeviewSelect>>", self._on_history_select)

    def _tree(self, parent, columns):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="x")
        tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings",
                            height=5)
        for key, title, width in columns:
            tree.heading(key, text=title)
            tree.column(key, width=width, anchor="w", stretch=False)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="x", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    def _section(self, parent, title):
        tk.Label(parent, text=title.upper(), bg=PANEL_BG, fg=ACCENT,
                 font=("Helvetica", 9, "bold")).pack(anchor="w", pady=(8, 2))

    def _radio_row(self, parent, values, var, label):
        row = tk.Frame(parent, bg=PANEL_BG)
        row.pack(anchor="w", pady=1)
        for v in values:
            tk.Radiobutton(row, text=label(v), variable=var, value=v,
                           indicatoron=False, width=4, bg=CELL_BG, fg=TEXT_LIGHT,
                           selectcolor=PICK_COLOR, activebackground=CELL_OUTLINE,
                           font=("Helvetica", 10, "bold"), relief="flat",
                           ).pack(side="left", padx=1)

    def _button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg=CELL_BG,
                         fg=TEXT_LIGHT, activebackground=CELL_OUTLINE,
                         activeforeground=TEXT_LIGHT, relief="flat",
                         font=("Helvetica", 10, "bold"), padx=6)

    # ----- Board drawing ---------------------------------------------------

    def _redraw_cell(self, n):
        oval, text = self.cells[n]
        picked = n in self.picks
        drawn = n in self.revealed
        if picked and drawn:
            fill, fg = HIT_COLOR, TEXT_DARK
        elif drawn:
            fill, fg = DRAWN_COLOR, TEXT_LIGHT
        elif picked:
            fill, fg = PICK_COLOR, TEXT_DARK
        else:
            fill, fg = CELL_BG, TEXT_LIGHT
        if n == self.bulls_eye:
            outline, width = BULLS_EYE_RING, 4
        else:
            outline, width = CELL_OUTLINE, 2
        self.canvas.itemconfigure(oval, fill=fill, outline=outline, width=width)
        self.canvas.itemconfigure(text, fill=fg)

    def _redraw_board(self):
        for n in self.cells:
            self._redraw_cell(n)

    def _draw_title(self, draw, show_bulls_eye=True):
        text = (f"Game #{draw.game:,}  -  {fmt_time(draw.time)}  -  "
                f"Multiplier {draw.multiplier}x")
        if show_bulls_eye:
            text += f"  -  Bulls-Eye {draw.bulls_eye}"
        return text

    def _show_draw(self, draw, results):
        """Show a finished draw on the board, with any ticket results."""
        if len(results) == 1:
            self.picks = set(results[0][0].picks)
        self.revealed = set(draw.numbers)
        self.bulls_eye = draw.bulls_eye
        self.draw_info_label.config(text=self._draw_title(draw))
        self._redraw_board()
        self._show_results(draw, results)
        self._update_labels()

    def _show_results(self, draw, results):
        lines = []
        if draw.jackpot_won_elsewhere:
            lines.append("Jackpot Bonus won elsewhere!")
        if not results:
            lines.append(f"Game #{draw.game:,}: no tickets in play.")
        won_any = False
        for t, r in results[:6]:
            line = f"T{t.ticket_id}: {r['matches']}/{len(t.picks)}"
            if t.bulls_eye and r["hit_bulls_eye"]:
                line += " +BE"
            line += f"  won {fmt_money(r['total_win'])}" if r["total_win"] else "  -"
            if r["jackpot_win"]:
                line += "  JACKPOT!"
            won_any = won_any or r["total_win"] > 0
            lines.append(line)
        if len(results) > 6:
            lines.append(f"...and {len(results) - 6} more tickets")
        self.result_label.config(text="\n".join(lines),
                                 fg=HIT_COLOR if won_any else TEXT_LIGHT)

    # ----- Labels / tables -------------------------------------------------

    def _update_labels(self):
        g = self.game
        self.balance_label.config(text=f"Balance: ${g.balance:,.2f}")
        uncashed = g.uncashed_total()
        self.uncashed_label.config(
            text=f"Winnings to cash: ${uncashed:,.2f}" if uncashed > 0.005 else "")
        self.jackpot_label.config(text=f"8-Spot Jackpot Bonus: ${g.jackpot:,.2f}")
        self.clock_label.config(
            text=f"Next game #{g.next_game:,} at {fmt_time(g.next_time)}"
                 f"   |   {g.next_time:%a %b %d}")
        self.spots_label.config(text=f"Spots picked: {len(self.picks)} / 10")
        per_game = ticket_cost(self.wager_var.get(), self.be_var.get(),
                               self.mult_var.get())
        games = self.games_var.get()
        total = per_game * games
        self.cost_label.config(
            text=f"Ticket: {fmt_money(per_game)} x {games} game"
                 f"{'s' if games > 1 else ''} = {fmt_money(total)}",
            fg=WARN if total > MAX_TICKET_COST else TEXT_LIGHT)

    def _refresh_start_options(self):
        options = self.game.keno_to_go_options()
        self.start_options = {label: start for label, start in options}
        menu = self.start_menu["menu"]
        menu.delete(0, "end")
        for label in ["Now"] + list(self.start_options):
            menu.add_command(label=label, command=tk._setit(self.start_var, label))
        if self.start_var.get() not in self.start_options:
            self.start_var.set("Now")

    def _refresh_tickets(self):
        for t in self.game.tickets:
            values = (
                t.ticket_id,
                " ".join(str(n) for n in t.picks),
                t.options_text(),
                f"#{t.first_game:,}" + (f" - {t.last_game:,}"
                                        if t.num_games > 1 else ""),
                fmt_money(t.total_won),
                fmt_money(t.unclaimed) if t.unclaimed > 0.005 else "",
                t.status(),
            )
            iid = str(t.ticket_id)
            if self.ticket_tree.exists(iid):
                self.ticket_tree.item(iid, values=values)
            else:
                self.ticket_tree.insert("", 0, iid=iid, values=values)

    def _add_history(self, draw):
        jackpot = fmt_money(draw.jackpot)
        if draw.jackpot_won_elsewhere:
            jackpot += " (won)"
        self.history_tree.insert(
            "", 0, iid=str(draw.game),
            values=(f"{draw.game:,}", fmt_time(draw.time), f"{draw.multiplier}x",
                    draw.bulls_eye, jackpot,
                    " ".join(f"{n:02d}" for n in draw.numbers)))
        children = self.history_tree.get_children()
        for iid in children[HISTORY_LIMIT:]:
            self.history_tree.delete(iid)

    def _refresh_all(self):
        self._refresh_tickets()
        self._refresh_start_options()
        self._update_labels()

    def _set_busy(self, busy):
        self.busy = busy
        state = "disabled" if busy else "normal"
        for b in (self.buy_button, self.next_button, self.qp_button,
                  self.clear_button):
            b.config(state=state)
        if not self.auto_running:
            self.auto_button.config(state=state)

    # ----- Picking numbers -------------------------------------------------

    def _clear_last_draw(self):
        if self.revealed or self.bulls_eye is not None:
            self.revealed = set()
            self.bulls_eye = None
            self.draw_info_label.config(text="Pick your numbers")

    def _on_board_click(self, event):
        if self.busy:
            return
        col = (event.x - PAD) // CELL
        row = (event.y - PAD) // CELL
        if not (0 <= col < COLS and 0 <= row < ROWS):
            return
        n = row * COLS + col + 1
        self._clear_last_draw()
        if n in self.picks:
            self.picks.remove(n)
        elif len(self.picks) < 10:
            self.picks.add(n)
        else:
            self.result_label.config(text="You can pick at most 10 numbers.",
                                     fg=TEXT_LIGHT)
        self._redraw_board()
        self._update_labels()

    def _quick_pick(self):
        self._clear_last_draw()
        self.picks = set(rng.sample(range(1, 81), self.qp_spots_var.get()))
        self._redraw_board()
        self._update_labels()

    def _clear_picks(self):
        self._clear_last_draw()
        self.picks = set()
        self._redraw_board()
        self._update_labels()

    # ----- Buying and cashing ----------------------------------------------

    def _buy(self):
        if self.busy:
            return
        start = self.start_options.get(self.start_var.get())
        try:
            t = self.game.buy_ticket(sorted(self.picks), self.wager_var.get(),
                                     self.special_var.get(), self.be_var.get(),
                                     self.mult_var.get(), self.games_var.get(),
                                     start)
        except ValueError as e:
            self.result_label.config(text=self._wrap(str(e)), fg=WARN)
            return
        games = (f"game #{t.first_game:,}" if t.num_games == 1 else
                 f"games #{t.first_game:,} - #{t.last_game:,}")
        self.result_label.config(
            fg=TEXT_LIGHT,
            text=f"Ticket #{t.ticket_id} bought for {fmt_money(t.total_cost)}\n"
                 f"{games}\nFirst draw at {fmt_time(t.first_time)}\n\n"
                 "Press NEXT DRAW or PLAY MY TICKETS.")
        self._refresh_all()

    def _cash_tickets(self, tickets):
        paid = [(t, self.game.cash(t)) for t in tickets]
        paid = [(t, amount) for t, amount in paid if amount > 0]
        self._refresh_all()
        if not paid:
            self.result_label.config(text="Nothing to cash on the selected\n"
                                          "ticket(s).", fg=TEXT_LIGHT)
            return
        total = sum(amount for _, amount in paid)
        lines = [f"Ticket #{t.ticket_id}: {fmt_money(amount)}"
                 + ("  (exchange ticket issued)" if not t.complete else "")
                 for t, amount in paid]
        lines.append(f"\nTotal cashed: {fmt_money(total)}")
        biggest = max(amount for _, amount in paid)
        if biggest > RETAILER_CLAIM_LIMIT:
            lines.append("\n" + claim_note(biggest))
            messagebox.showinfo("Prize Claim", "\n".join(lines))
        self.result_label.config(text="\n".join(lines[:7]), fg=HIT_COLOR)
        self._check_game_over()

    def _cash_selected(self):
        ids = {int(i) for i in self.ticket_tree.selection()}
        if not ids:
            self.result_label.config(text="Select a ticket in My Tickets first.",
                                     fg=TEXT_LIGHT)
            return
        self._cash_tickets([t for t in self.game.tickets if t.ticket_id in ids])

    def _cash_all(self):
        self._cash_tickets(list(self.game.tickets))

    def _on_ticket_select(self, _event):
        if self.busy:
            return
        selection = self.ticket_tree.selection()
        if len(selection) != 1:
            return
        t = next(t for t in self.game.tickets if t.ticket_id == int(selection[0]))
        self.picks = set(t.picks)
        self.wager_var.set(t.wager)
        self.games_var.set(t.num_games)
        self.special_var.set(t.special)
        self.be_var.set(t.bulls_eye)
        self.mult_var.set(t.multiplier)

        if t.results:
            last = max(t.results)
            self._show_draw(self.game.history[last], [(t, t.results[last])])
            best_game = max(t.results, key=lambda g: t.results[g]["total_win"])
            best = t.results[best_game]
            summary = (f"Ticket #{t.ticket_id}: {t.games_played}/{t.num_games} "
                       f"games played\nCost {fmt_money(t.total_cost)}, "
                       f"won {fmt_money(t.total_won)}\n")
            if best["total_win"]:
                summary += (f"Best: game #{best_game:,}\n"
                            f"  {best['matches']} of {len(t.picks)} -> "
                            f"{fmt_money(best['total_win'])}\n")
            summary += f"Showing game #{last:,}"
            self.result_label.config(text=summary, fg=TEXT_LIGHT)
        else:
            self._clear_last_draw()
            self._redraw_board()
            self.result_label.config(
                text=f"Ticket #{t.ticket_id} starts at game\n"
                     f"#{t.first_game:,} ({fmt_time(t.first_time)}).",
                fg=TEXT_LIGHT)
        self._update_labels()

    def _on_history_select(self, _event):
        if self.busy:
            return
        selection = self.history_tree.selection()
        if len(selection) != 1:
            return
        game = int(selection[0])
        draw = self.game.history[game]
        results = [(t, t.results[game]) for t in self.game.tickets
                   if game in t.results]
        self._show_draw(draw, results)

    @staticmethod
    def _wrap(text, width=36):
        words, lines, line = text.split(), [], ""
        for w in words:
            if line and len(line) + 1 + len(w) > width:
                lines.append(line)
                line = w
            else:
                line = f"{line} {w}".strip()
        lines.append(line)
        return "\n".join(lines)

    # ----- Drawing games ---------------------------------------------------

    def _next_draw(self):
        if self.busy:
            return
        self._set_busy(True)
        draw, results = self.game.run_draw()
        if len(results) == 1:
            self.picks = set(results[0][0].picks)
        self.revealed = set()
        self.bulls_eye = None
        self._redraw_board()
        # The multiplier is drawn before the regular drawing
        self.draw_info_label.config(text=self._draw_title(draw, show_bulls_eye=False))
        self.result_label.config(text="Drawing...", fg=TEXT_LIGHT)
        order = rng.sample(draw.numbers, len(draw.numbers))
        self._reveal(draw, results, order, 0)

    def _reveal(self, draw, results, order, i):
        if i < len(order):
            self.revealed.add(order[i])
            self._redraw_cell(order[i])
            self.result_label.config(text=f"Drawing... {i + 1}/20")
            self.root.after(DRAW_DELAY_MS, self._reveal, draw, results, order, i + 1)
            return
        self._show_draw(draw, results)
        self._add_history(draw)
        self._refresh_all()
        self._set_busy(False)
        self._check_game_over()

    def _toggle_auto(self):
        if self.auto_running:
            self.auto_running = False
            return
        if not self.game.active_tickets():
            self.result_label.config(text="No tickets left to play.\n"
                                          "Buy a ticket first.", fg=TEXT_LIGHT)
            return
        self.auto_running = True
        self.auto_button.config(text="STOP")
        self._set_busy(True)
        self._auto_step()

    def _auto_step(self):
        if not self.auto_running or not self.game.active_tickets():
            self._stop_auto()
            return

        # Fast-forward through games none of our tickets are in (e.g. waiting
        # for a Keno To Go start time).
        skipped = 0
        while not self.game.tickets_for(self.game.next_game) and skipped < 50:
            draw, _ = self.game.run_draw()
            self._add_history(draw)
            skipped += 1
        if skipped:
            self.draw_info_label.config(text=f"Waiting... skipped {skipped} games")
            self._update_labels()
            if not self.game.tickets_for(self.game.next_game):
                self.root.after(10, self._auto_step)
                return

        draw, results = self.game.run_draw()
        self._add_history(draw)
        self._show_draw(draw, results)
        self._refresh_tickets()
        self.root.after(AUTO_DELAY_MS, self._auto_step)

    def _stop_auto(self):
        self.auto_running = False
        self.auto_button.config(text="PLAY MY TICKETS")
        self._set_busy(False)
        self._refresh_all()
        self._check_game_over()

    def _check_game_over(self):
        if not self.game.is_broke():
            return
        if messagebox.askyesno("Game Over",
                               "You're out of funds!\n\nStart over with "
                               f"${STARTING_BALANCE:,.2f}?"):
            self.game.balance = STARTING_BALANCE
            self._update_labels()
        else:
            self.root.destroy()

    # ----- Rules window ----------------------------------------------------

    def _show_rules(self):
        win = tk.Toplevel(self.root)
        win.title("Keno Rules & Pay Tables")
        win.configure(bg=BG)
        text = tk.Text(win, width=78, height=36, bg=PANEL_BG, fg=TEXT_LIGHT,
                       font=("Courier", 10), relief="flat", padx=10, pady=8)
        scroll = ttk.Scrollbar(win, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.insert("1.0", RULES_TEXT + "\n" + pay_table_text())
        text.config(state="disabled")
        text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")


def pay_table_text():
    lines = ["PAY TABLES (prize per $1 wagered)",
             "Bulls-Eye prizes are added to the Keno or Special Keno prize.", ""]
    for spots in range(10, 0, -1):
        title = f"{spots}-SPOT GAME"
        if spots == JACKPOT_SPOTS:
            title += "  (+ Jackpot Bonus for 8 of 8)"
        lines.append(title)
        lines.append(f"  {'Match':>5}  {'Keno':>10}  {'Special':>10}  {'Bulls-Eye':>10}")
        for matches, (reg, spec, be) in PAYOUTS[spots].items():
            lines.append(f"  {matches:>5}  {fmt_money(reg):>10}  "
                         f"{fmt_money(spec):>10}  {fmt_money(be):>10}")
        lines.append("")
    return "\n".join(lines)


def run_gui():
    root = tk.Tk()
    KenoApp(root)
    root.mainloop()


# ---------------------------------------------------------------------------
# Text version (run with: python keno.py --text)
# ---------------------------------------------------------------------------

BOARD_WIDTH = COLS * 5  # each number cell is 5 characters wide


def display_board(drawn_numbers, player_picks, bulls_eye, title="KENO BOARD"):
    print("\n" + "=" * BOARD_WIDTH)
    print(title.center(BOARD_WIDTH))
    print("=" * BOARD_WIDTH)
    for row in range(ROWS):
        line = ""
        for col in range(1, COLS + 1):
            num = row * COLS + col
            if num in drawn_numbers and num in player_picks:
                marker = f"[{num:02d}*]"  # Hit!
            elif num in drawn_numbers:
                marker = f"({num:02d})"   # Drawn
            elif num in player_picks:
                marker = f"<{num:02d}>"   # Your pick
            else:
                marker = f" {num:02d} "
            line += f"{marker:^5}"
        print(line)
    print("=" * BOARD_WIDTH)
    print("Legend: [XX*] = Match | (XX) = Drawn | <XX> = Pick")
    print(f"Bulls-Eye Number: {bulls_eye}")
    print("=" * BOARD_WIDTH)


def get_player_picks(num_spots):
    choice = input("Choose [Q]uick Pick or [M]anual selection? ").strip().upper()
    if choice == 'Q':
        picks = sorted(rng.sample(range(1, 81), num_spots))
        print(f"Quick Pick numbers: {picks}")
        return picks

    picks = set()
    print(f"Enter {num_spots} unique numbers between 1 and 80:")
    while len(picks) < num_spots:
        try:
            num = int(input(f"Spot {len(picks) + 1}/{num_spots}: "))
            if 1 <= num <= 80 and num not in picks:
                picks.add(num)
            else:
                print("Invalid or duplicate number. Try again.")
        except ValueError:
            print("Please enter a valid integer.")
    return sorted(picks)


def ask_choice(prompt, choices, error):
    while True:
        try:
            value = int(input(prompt))
            if value in choices:
                return value
            print(error)
        except ValueError:
            print("Enter a valid number.")


def play_keno_text():
    game = KenoGame()
    print("Welcome to Keno! A new game is drawn every 4 minutes.")

    while not game.is_broke():
        print(f"\nBalance: ${game.balance:.2f} | 8-Spot Jackpot Bonus: "
              f"${game.jackpot:,.2f}")
        print(f"Next game: #{game.next_game:,} at {fmt_time(game.next_time)}")

        spots = ask_choice("How many spots do you want to play (1-10)? ",
                           range(1, 11), "Choose between 1 and 10 spots.")
        wager = ask_choice("Base wager per game ($1, $2, $3, $4, $5, $10, $20): $",
                           WAGERS, "Please choose a standard wager amount.")
        num_games = ask_choice(
            "Consecutive games (1, 2, 3, 4, 5, 10, 15, 20, 50, 100)? ",
            GAME_COUNTS, "Please choose a standard number of games.")
        special_keno = input("Play Special Keno for bigger top prizes? (y/n): ").strip().lower() == 'y'
        multiplier_opt = input("Add Multiplier? (+$1 per $1 wagered) (y/n): ").strip().lower() == 'y'
        bulls_eye_opt = input("Add Bulls-Eye? (+$1 per $1 wagered) (y/n): ").strip().lower() == 'y'

        total = ticket_cost(wager, bulls_eye_opt, multiplier_opt) * num_games
        if total > MAX_TICKET_COST or total > game.balance:
            limit = min(MAX_TICKET_COST, game.balance)
            print(f"That ticket costs {fmt_money(total)}; you can spend at most "
                  f"${limit:,.2f}.")
            continue

        picks = get_player_picks(spots)
        ticket = game.buy_ticket(picks, wager, special_keno, bulls_eye_opt,
                                 multiplier_opt, num_games)
        print(f"\nTicket #{ticket.ticket_id}: games #{ticket.first_game:,} - "
              f"#{ticket.last_game:,}, cost {fmt_money(ticket.total_cost)}")

        while not ticket.complete:
            draw, results = game.run_draw()
            r = dict(results)[ticket]
            if num_games == 1:
                display_board(draw.numbers, picks, draw.bulls_eye,
                              f"GAME #{draw.game:,}  {fmt_time(draw.time)}")
                print(f"Drawn Multiplier: {draw.multiplier}x")
                print(f"\nYou matched {r['matches']} out of {spots} spots!")
            else:
                be = " BE-hit" if bulls_eye_opt and r["hit_bulls_eye"] else ""
                won = f"won {fmt_money(r['total_win'])}" if r["total_win"] else ""
                print(f"Game #{draw.game:,} {fmt_time(draw.time):>8}  "
                      f"{draw.multiplier:>2}x  matched {r['matches']}/{spots}{be}  {won}")
            if r["jackpot_win"]:
                print(f"*** 8-SPOT JACKPOT BONUS: ${r['jackpot_win']:,.2f}! ***")
            if draw.jackpot_won_elsewhere:
                print("(The Jackpot Bonus was won elsewhere this game.)")

        print(f"\nTicket #{ticket.ticket_id} won {fmt_money(ticket.total_won)} "
              f"over {num_games} game{'s' if num_games > 1 else ''}.")
        amount = game.cash(ticket)
        if amount:
            print(f"Cashed {fmt_money(amount)}. {claim_note(amount)}")
        else:
            print("No prize this time. Better luck next time!")

        if game.is_broke():
            print("\nYou're out of funds! Game over.")
            break
        if input("\nPlay another ticket? (y/n): ").strip().lower() != 'y':
            break

    print(f"\nThanks for playing! Final Balance: ${game.balance:.2f}")


if __name__ == "__main__":
    if "--text" in sys.argv:
        play_keno_text()
    else:
        run_gui()
