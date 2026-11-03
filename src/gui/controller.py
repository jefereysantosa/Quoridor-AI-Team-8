"""
Modul pengendali permainan untuk GUI (M2 dan integrasi M3-M4).

Menyimpan state permainan dan alur giliran tanpa menggambar apa pun, sehingga
bisa diuji tanpa jendela. Pencarian AI, Ghost Step, dan Explainable Hint
dijalankan di thread terpisah pada salinan state agar GUI tidak membeku.
"""

from __future__ import annotations

import threading
import time
from typing import Dict, List, Optional, Tuple

from ..ai.evaluation import evaluate_state
from ..ai.explain import Hint, generate_hint
from ..ai.ghost import GhostPrediction, clear_ghost_cache, predict_response
from ..ai.minimax import QuoridorAI
from ..ai.pathfinding import bfs_distance
from ..game.moves import MoveGenerator
from ..game.rules import Rules
from ..game.state import State

HUMAN_IDX = 0
AI_IDX = 1

MODE_AI = "ai"
MODE_HUMAN = "human"

DEFAULT_LEVEL = 2
DEFAULT_PLAYSTYLE = "balanced"
LEVEL_TIME_LIMITS = {3: 3.0, 4: 5.0, 5: 10.0}  # detik berpikir maksimal per langkah
HINT_MAX_DEPTH = 2
ANIMATION_SECONDS = 0.25
NOTICE_SECONDS = 5.0


class SearchCancelled(Exception):
    """Pencarian dihentikan karena hasilnya sudah tidak dibutuhkan."""


class SearchTimedOut(Exception):
    """Batas waktu level habis sebelum kedalaman ini selesai dicari."""


class CancellableAI(QuoridorAI):
    """QuoridorAI yang bisa dihentikan saat New Game, Restart, Undo, atau batas waktu habis."""

    def __init__(self, cancel: threading.Event, max_depth: int, playstyle=None, deadline: Optional[float] = None):
        super().__init__(max_depth=max_depth, playstyle=playstyle)
        self.cancel = cancel
        self.deadline = deadline

    def _minimax(self, *args, **kwargs):
        if self.cancel.is_set():
            raise SearchCancelled()
        if self.deadline is not None and time.perf_counter() > self.deadline:
            raise SearchTimedOut()
        return super()._minimax(*args, **kwargs)


class BackgroundTask:
    """Menjalankan satu fungsi di thread latar dan menyimpan hasilnya."""

    def __init__(self, fn, *args):
        self.result = None
        self.error: Optional[Exception] = None
        self._thread = threading.Thread(target=self._run, args=(fn, args), daemon=True)
        self._thread.start()

    def _run(self, fn, args) -> None:
        try:
            self.result = fn(*args)
        except SearchCancelled:
            pass
        except Exception as exc:
            self.error = exc

    @property
    def done(self) -> bool:
        return not self._thread.is_alive()


def wall_rejection_reason(state, r: int, c: int, orient: str, player_idx: int) -> Optional[str]:
    """
    Alasan penolakan dinding untuk notifikasi GUI (Bab 2.1.6).
    Return None bila dinding legal menurut Logical Constraint Engine.
    """
    if Rules.is_wall_valid(state, r, c, orient, player_idx):
        return None
    if state.walls_remaining[player_idx] <= 0:
        return "Dinding ditolak: sisa dinding sudah habis."

    trial = state.clone()
    (trial.h_walls if orient == "H" else trial.v_walls)[r][c] = True
    if bfs_distance(trial, 0) == -1 or bfs_distance(trial, 1) == -1:
        return "Dinding ditolak: menutup seluruh jalur pion ke garis tujuan (BFS Reachability Test)."
    return "Dinding ditolak: bertumpuk atau bersilang dengan dinding lain."


def _wins(state, action: Tuple, player_idx: int) -> bool:
    child = state.clone()
    child.apply_move(action, player_idx)
    return child.is_winner(player_idx)


def _search(state, level: int, playstyle, cancel: threading.Event) -> Tuple[Optional[Tuple], Dict]:
    """
    Mencari langkah AI lalu merangkum angka untuk panel statistik.

    Level dengan batas waktu memakai iterative deepening: kedalaman dinaikkan
    sampai sama dengan level atau waktu habis, lalu hasil kedalaman terakhir
    yang selesai dipakai. Level tanpa batas langsung mencari di kedalaman level.
    """
    player_idx = state.current_player
    limit = LEVEL_TIME_LIMITS.get(level)
    start = time.perf_counter()
    action = None
    stats = {"depth": 0, "nodes": 0, "cutoffs": 0, "limit": limit}

    for depth in ([level] if limit is None else range(1, level + 1)):
        # Kedalaman 1 selalu diselesaikan agar AI pasti punya langkah
        deadline = start + limit if limit is not None and depth > 1 else None
        ai = CancellableAI(cancel, depth, playstyle, deadline)
        try:
            action = ai.get_best_move(state, player_idx)
            stats["depth"] = depth
        except SearchTimedOut:
            break
        finally:
            stats["nodes"] += ai.nodes_evaluated
            stats["cutoffs"] += ai.nodes_pruned
        if action is None or _wins(state, action, player_idx):
            break  # Langkah menang tidak perlu dicari lebih dalam

    stats["ms"] = (time.perf_counter() - start) * 1000.0
    if action is not None:
        child = state.clone()
        child.apply_move(action, player_idx)
        stats["score"] = evaluate_state(child, player_idx, playstyle)
    return action, stats


class GameController:
    """Alur satu sesi permainan: giliran, konfirmasi langkah, undo, dan tugas latar."""

    def __init__(self):
        self.mode = MODE_AI
        self.level = DEFAULT_LEVEL
        self.playstyle = DEFAULT_PLAYSTYLE
        self.ghost_enabled = True
        self._cancel = threading.Event()
        self._reset_game()

    # ------------------------------------------------------------------
    # Status permainan
    # ------------------------------------------------------------------

    def _reset_game(self) -> None:
        self.state = State()
        self.history: List[State] = []
        self.stats: Dict = {}
        self.animation: Optional[Dict] = None
        self._clear_turn_data()
        self.ai_task: Optional[BackgroundTask] = None
        self.notice: Optional[str] = None
        self.notice_until = 0.0

    def _clear_turn_data(self) -> None:
        self.pending: Optional[Tuple] = None
        self.ghost_task: Optional[BackgroundTask] = None
        self.ghost_pred: Optional[GhostPrediction] = None
        self.hint_task: Optional[BackgroundTask] = None
        self.hint: Optional[Hint] = None
        self.rejected_wall: Optional[Tuple] = None

    @property
    def winner(self) -> Optional[int]:
        for idx in (0, 1):
            if self.state.is_winner(idx):
                return idx
        return None

    @property
    def ai_turn(self) -> bool:
        return self.mode == MODE_AI and self.state.current_player == AI_IDX

    @property
    def human_can_act(self) -> bool:
        return self.winner is None and not self.ai_turn and self.animation is None

    @property
    def ai_thinking(self) -> bool:
        return self.ai_task is not None

    @property
    def hint_loading(self) -> bool:
        return self.hint_task is not None

    @property
    def ghost_loading(self) -> bool:
        return self.ghost_task is not None

    def player_name(self, idx: int) -> str:
        if self.mode == MODE_AI:
            return "Anda" if idx == HUMAN_IDX else "AI"
        return f"Pemain {idx + 1}"

    def legal_pawn_moves(self) -> List[Tuple]:
        return MoveGenerator._get_pawn_moves(self.state, self.state.current_player)

    def wall_reason(self, action: Tuple) -> Optional[str]:
        r, c, orient = action[1]
        return wall_rejection_reason(self.state, r, c, orient, self.state.current_player)

    def pawn_display_pos(self, idx: int) -> Tuple[float, float]:
        """Posisi gambar pion, termasuk posisi antara saat animasi berjalan."""
        anim = self.animation
        if anim and anim["kind"] == "move" and anim["player"] == idx:
            t = min(1.0, (time.perf_counter() - anim["start"]) / ANIMATION_SECONDS)
            (r0, c0), (r1, c1) = anim["from"], anim["to"]
            return (r0 + (r1 - r0) * t, c0 + (c1 - c0) * t)
        return self.state.pawns[idx]

    def fresh_wall_alpha(self) -> Optional[Tuple[Tuple, float]]:
        """Dinding yang baru dipasang beserta tingkat kemunculannya (0-1)."""
        anim = self.animation
        if anim and anim["kind"] == "wall":
            t = min(1.0, (time.perf_counter() - anim["start"]) / ANIMATION_SECONDS)
            return anim["wall"], t
        return None

    # ------------------------------------------------------------------
    # Aksi pengguna
    # ------------------------------------------------------------------

    def click(self, action: Tuple) -> None:
        """Klik pada papan. Klik kedua pada kandidat yang sama berarti konfirmasi."""
        if not self.human_can_act:
            return
        if action == self.pending:
            self.confirm()
            return

        if action[0] == "wall":
            reason = self.wall_reason(action)
            if reason:
                self._cancel_pending()
                self.rejected_wall = action[1]
                self._notify(reason)
                return
        elif action not in self.legal_pawn_moves():
            return

        self.rejected_wall = None
        self.notice = None
        if self.mode == MODE_AI and self.ghost_enabled:
            self.pending = action
            self.ghost_pred = None
            self.ghost_task = BackgroundTask(
                predict_response,
                self.state.clone(), action, self.state.current_player, 1, self.playstyle,
            )
        else:
            self._apply(action)

    def confirm(self) -> None:
        if self.pending is not None and self.human_can_act:
            self._apply(self.pending)

    def _cancel_pending(self) -> None:
        self.pending = None
        self.ghost_task = None
        self.ghost_pred = None

    def cancel(self) -> None:
        self._cancel_pending()
        self.rejected_wall = None

    def request_hint(self) -> None:
        if not self.human_can_act or self.hint_task is not None:
            return
        self.hint = None
        self.hint_task = BackgroundTask(
            generate_hint,
            self.state.clone(), self.state.current_player,
            min(self.level, HINT_MAX_DEPTH), self.playstyle,
        )

    def undo(self) -> None:
        """Mundur ke giliran manusia sebelumnya. Pada mode AI, langkah AI ikut dibatalkan."""
        if not self.history:
            self._notify("Belum ada langkah yang bisa dibatalkan.")
            return
        self._stop_ai()
        self.state = self.history.pop()
        while self.ai_turn and self.history:
            self.state = self.history.pop()
        self.animation = None
        self._clear_turn_data()
        clear_ghost_cache()

    def restart(self) -> None:
        """Papan baru dengan pengaturan yang sama."""
        self._stop_ai()
        clear_ghost_cache()
        self._reset_game()

    def new_game(self) -> None:
        """Papan baru dengan pengaturan AI kembali ke bawaan."""
        self.level = DEFAULT_LEVEL
        self.playstyle = DEFAULT_PLAYSTYLE
        self.ghost_enabled = True
        self.restart()

    def set_mode(self, mode: str) -> None:
        if mode != self.mode:
            self.mode = mode
            self.restart()

    def set_level(self, level: int) -> None:
        self.level = level
        self._cancel_pending()
        self.hint = None
        limit = LEVEL_TIME_LIMITS.get(level)
        if limit is not None:
            self._notify(f"Level {level}: AI berpikir maksimal {limit:g} detik per langkah.")

    def set_playstyle(self, key: str) -> None:
        self.playstyle = key
        clear_ghost_cache()
        self._cancel_pending()
        self.hint = None

    def toggle_ghost(self) -> None:
        self.ghost_enabled = not self.ghost_enabled
        self._cancel_pending()

    # ------------------------------------------------------------------
    # Pembaruan tiap frame
    # ------------------------------------------------------------------

    def update(self) -> None:
        if self.animation and time.perf_counter() - self.animation["start"] >= ANIMATION_SECONDS:
            self.animation = None
        if self.notice and time.perf_counter() > self.notice_until:
            self.notice = None
            self.rejected_wall = None

        self._poll_ghost()
        self._poll_hint()
        self._poll_ai()

        if self.ai_turn and self.winner is None and self.animation is None and self.ai_task is None:
            self._cancel = threading.Event()
            self.ai_task = BackgroundTask(
                _search, self.state.clone(), self.level, self.playstyle, self._cancel
            )

    def _poll_ghost(self) -> None:
        task = self.ghost_task
        if task and task.done:
            self.ghost_task = None
            if task.error:
                self._notify(f"Ghost Step gagal: {task.error}")
            else:
                self.ghost_pred = task.result

    def _poll_hint(self) -> None:
        task = self.hint_task
        if task and task.done:
            self.hint_task = None
            if task.error:
                self._notify(f"Hint gagal: {task.error}")
            else:
                self.hint = task.result

    def _poll_ai(self) -> None:
        task = self.ai_task
        if not (task and task.done):
            return
        self.ai_task = None
        if task.error:
            self._notify(f"Pencarian AI gagal: {task.error}")
        elif task.result is not None:
            action, stats = task.result
            self.stats = stats
            if action is None:
                self._notify("AI tidak menemukan langkah legal.")
            else:
                self._apply(action)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _apply(self, action: Tuple) -> None:
        player = self.state.current_player
        kind, payload = action
        self.history.append(self.state.clone())
        if kind == "move":
            self.animation = {
                "kind": "move", "player": player,
                "from": self.state.pawns[player], "to": payload,
                "start": time.perf_counter(),
            }
        else:
            self.animation = {"kind": "wall", "wall": payload, "start": time.perf_counter()}
        self.state.apply_move(action, player)
        self._clear_turn_data()
        clear_ghost_cache()

    def _stop_ai(self) -> None:
        self._cancel.set()
        self.ai_task = None

    def _notify(self, text: str) -> None:
        self.notice = text
        self.notice_until = time.perf_counter() + NOTICE_SECONDS
