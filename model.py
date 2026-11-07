from card_utils import Card
from game_state import GameStateView
from player_action import PlayerAction

# 20 offsuit hands to fold (rank pairs; T=10, J=11, Q=12)
TRASH_HANDS = {
    # original 10
    frozenset((7, 2)),
    frozenset((8, 2)),
    frozenset((6, 2)),
    frozenset((7, 3)),
    frozenset((8, 3)),
    frozenset((9, 2)),
    frozenset((9, 3)),
    frozenset((10, 2)),
    frozenset((11, 2)),
    frozenset((3, 2)),
    # 10 more
    frozenset((4, 2)),
    frozenset((5, 2)),
    frozenset((4, 3)),
    frozenset((5, 3)),
    frozenset((6, 3)),
    frozenset((7, 4)),
    frozenset((8, 4)),
    frozenset((9, 4)),
    frozenset((10, 3)),
    frozenset((12, 2)),
}

FACE_RANKS = {"T": 10, "J": 11, "Q": 12, "K": 13, "A": 14}


def card_rank(card) -> int:
    """Return a card's rank as a number (2-14). Adjust if Card uses other names."""
    r = getattr(card, "rank", None)
    if hasattr(r, "value"):
        r = r.value
    if isinstance(r, str):
        r = FACE_RANKS.get(r.upper()) or int(r)
    return r


class Model:
    """
    Calls every hand, folds 20 weak offsuit hands, and tries to go all in
    (once per hand) with pocket aces or kings, calling if a raise is not legal.
    """

    def __init__(self):
        self.hand = []
        self.player_id = None
        self.fold_hand = False
        self.all_in = False
        self.raised = False

    def seed(self, hand: list[Card], player_id: int):
        self.hand = hand
        self.player_id = player_id
        self.fold_hand = False
        self.all_in = False
        self.raised = False
        try:
            c1, c2 = hand
            r1, r2 = card_rank(c1), card_rank(c2)
            offsuit = c1.suit != c2.suit
            self.fold_hand = offsuit and frozenset((r1, r2)) in TRASH_HANDS
            self.all_in = r1 == r2 and r1 in (14, 13)  # AA or KK
        except Exception:
            self.fold_hand = False
            self.all_in = False

    def _read(self, game_state, names):
        """Return the first value found under any of these names (calls it if it is a method)."""
        for name in names:
            value = getattr(game_state, name, None)
            if value is None:
                continue
            if callable(value):
                try:
                    value = value(self.player_id)
                except TypeError:
                    try:
                        value = value()
                    except Exception:
                        continue
                except Exception:
                    continue
            return value
        return None

    def raise_target(self, game_state):
        """Return the all-in amount if a raise is legal, else None."""
        # GUESSED names: replace with the real ones from CLAUDE.md / game_state.py
        allowed = self._read(game_state, ("can_raise", "raise_allowed", "can_bet"))
        if allowed is not True:      # unknown or False: do not raise
            return None
        amount = self._read(game_state, ("max_raise_to", "all_in_amount", "max_raise"))
        if isinstance(amount, (int, float)):
            return amount
        return None

    def run(
        self, actions: list[PlayerAction], game_state: GameStateView
    ) -> PlayerAction:
        try:
            if self.all_in and not self.raised:
                amount = self.raise_target(game_state)
                if amount is not None:
                    self.raised = True
                    return PlayerAction.raise_to(self.player_id, amount)
                return PlayerAction.call(self.player_id)  # cannot raise: call
            if self.fold_hand and game_state.call_amount > 0:
                return PlayerAction.fold(self.player_id)
            return PlayerAction.call(self.player_id)  # call, or check if free
        except Exception:
            return PlayerAction.call(self.player_id)

    def end_game(
        self, actions: list[PlayerAction], game_state: GameStateView
    ):
        pass