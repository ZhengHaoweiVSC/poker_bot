from card_utils import Card
from game_state import GameStateView
from player_action import PlayerAction

RANKS = "23456789TJQKA"
RANK_VALUE = {ch: i + 2 for i, ch in enumerate(RANKS)}

# 50 weak hand types to fold. Format: two ranks + "o" (offsuit) or "s" (suited).
BAD_HANDS = [
    # 42 offsuit
    "32o", "42o", "43o", "52o", "53o", "54o",
    "62o", "63o", "64o",
    "72o", "73o", "74o", "75o",
    "82o", "83o", "84o", "85o", "86o",
    "92o", "93o", "94o", "95o", "96o", "97o",
    "T2o", "T3o", "T4o", "T5o", "T6o", "T7o",
    "J2o", "J3o", "J4o", "J5o", "J6o", "J7o",
    "Q2o", "Q3o", "Q4o", "Q5o", "Q6o",
    "K2o",
    # 8 suited
    "32s", "42s", "52s", "62s", "72s", "82s", "92s", "T2s",
]


def parse_hand(code):
    a, b, kind = code[0], code[1], code[2]
    hi = max(RANK_VALUE[a], RANK_VALUE[b])
    lo = min(RANK_VALUE[a], RANK_VALUE[b])
    return (hi, lo, kind == "s")


BAD_SET = {parse_hand(code) for code in BAD_HANDS}

FACE_RANKS = {"T": 10, "J": 11, "Q": 12, "K": 13, "A": 14}


def card_rank(card) -> int:
    """Return a card's rank as a number (2-14)."""
    r = getattr(card, "rank", None)
    if hasattr(r, "value"):
        r = r.value
    if isinstance(r, str):
        r = FACE_RANKS.get(r.upper()) or int(r)
    return r


class Model:
    """
    Folds 50 weak starting hands when facing a bet, goes all in with every
    other hand when a raise is possible, and calls otherwise.
    """

    def __init__(self):
        self.hand = []
        self.player_id = None
        self.fold_hand = False

    def seed(self, hand: list[Card], player_id: int):
        self.hand = hand
        self.player_id = player_id
        self.fold_hand = False
        try:
            c1, c2 = hand
            r1, r2 = card_rank(c1), card_rank(c2)
            suited = c1.suit == c2.suit
            key = (max(r1, r2), min(r1, r2), suited)
            self.fold_hand = key in BAD_SET
        except Exception:
            self.fold_hand = False

    def all_in_total(self, game_state):
        """Return the raise_to amount for an all-in, or None if we cannot raise."""
        me = self.player_id
        chips_behind = game_state.stacks[me]
        if chips_behind <= game_state.call_amount:
            return None
        others = [p for p in game_state.active_players if p != me]
        if not others:
            return None
        total = int(game_state.bets[me] + chips_behind)
        if total < game_state.min_raise_to:
            return None
        return total

    def run(self, actions: list[PlayerAction], game_state: GameStateView) -> PlayerAction:
        try:
            if self.fold_hand:
                if game_state.call_amount > 0:
                    return PlayerAction.fold(self.player_id)
                return PlayerAction.call(self.player_id)
            total = self.all_in_total(game_state)
            if total is not None:
                return PlayerAction.raise_to(self.player_id, total)
            return PlayerAction.call(self.player_id)
        except Exception:
            return PlayerAction.call(self.player_id)

    def end_game(self, actions: list[PlayerAction], game_state: GameStateView):
        pass