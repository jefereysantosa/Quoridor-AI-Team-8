"""Test M2: hit-test papan, alasan penolakan dinding, dan alur GameController."""
import os
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from src.gui.board_view import BoardView, CELL_SIZE, ORIGIN
from src.gui.controller import (
    AI_IDX, HUMAN_IDX, MODE_HUMAN, GameController, wall_rejection_reason,
)
from src.game.state import State

OX, OY = ORIGIN


def tunggu(ctrl, kondisi, batas_detik=30.0):
    """Memanggil update seperti loop GUI sampai kondisi terpenuhi."""
    mulai = time.perf_counter()
    while not kondisi():
        assert time.perf_counter() - mulai < batas_detik
        ctrl.update()
        time.sleep(0.005)


def test_hit_test_tengah_sel_adalah_gerak_pion():
    view = BoardView()
    pos = (OX + int(4.5 * CELL_SIZE), OY + int(1.5 * CELL_SIZE))
    assert view.hit_test(pos) == ("move", (1, 4))


def test_hit_test_celah_adalah_dinding():
    view = BoardView()
    horizontal = (OX + int(2.7 * CELL_SIZE), OY + 3 * CELL_SIZE)
    assert view.hit_test(horizontal) == ("wall", (2, 2, "H"))
    vertikal = (OX + 5 * CELL_SIZE, OY + int(6.7 * CELL_SIZE))
    assert view.hit_test(vertikal) == ("wall", (6, 4, "V"))


def test_hit_test_tepi_dan_luar_papan():
    view = BoardView()
    assert view.hit_test((OX + int(4.5 * CELL_SIZE), OY + 2)) == ("move", (0, 4))
    assert view.hit_test((OX + int(8.9 * CELL_SIZE), OY + 3 * CELL_SIZE)) == ("wall", (2, 7, "H"))
    assert view.hit_test((OX - 5, OY - 5)) is None


def test_alasan_dinding_legal_bertumpuk_dan_habis():
    s = State()
    assert wall_rejection_reason(s, 3, 3, "H", 0) is None
    s.h_walls[3][3] = True
    assert "bertumpuk" in wall_rejection_reason(s, 3, 4, "H", 0)
    assert "bersilang" in wall_rejection_reason(s, 3, 3, "V", 0)
    s.walls_remaining[0] = 0
    assert "habis" in wall_rejection_reason(s, 6, 6, "H", 0)


def test_alasan_dinding_menutup_jalur():
    # Deretan dinding menyisakan kolom 8, lalu dinding vertikal menutup celahnya
    s = State()
    for c in (0, 2, 4, 6):
        s.h_walls[3][c] = True
    s.h_walls[2][7] = True
    assert "menutup" in wall_rejection_reason(s, 3, 7, "V", 0)


def test_ghost_step_menunggu_konfirmasi_lalu_ai_membalas():
    ctrl = GameController()
    ctrl.level = 1
    ctrl.click(("move", (1, 4)))
    assert ctrl.state.pawns[HUMAN_IDX] == (0, 4)  # belum dieksekusi
    tunggu(ctrl, lambda: ctrl.ghost_pred is not None)
    assert ctrl.ghost_pred.ai_response is not None

    ctrl.confirm()
    assert ctrl.state.pawns[HUMAN_IDX] == (1, 4)
    assert ctrl.state.current_player == AI_IDX
    tunggu(ctrl, lambda: ctrl.state.current_player == HUMAN_IDX)
    assert ctrl.stats["nodes"] > 0


def test_klik_kedua_mengonfirmasi_dan_batal_membatalkan():
    ctrl = GameController()
    ctrl.level = 1
    ctrl.click(("move", (1, 4)))
    ctrl.cancel()
    assert ctrl.pending is None and ctrl.state.pawns[HUMAN_IDX] == (0, 4)
    ctrl.click(("move", (1, 4)))
    ctrl.click(("move", (1, 4)))
    assert ctrl.state.pawns[HUMAN_IDX] == (1, 4)


def test_dinding_ilegal_ditolak_dengan_notifikasi():
    ctrl = GameController()
    ctrl.state.h_walls[3][3] = True
    ctrl.click(("wall", (3, 4, "H")))
    assert ctrl.rejected_wall == (3, 4, "H")
    assert "bertumpuk" in ctrl.notice
    assert ctrl.pending is None and ctrl.state.current_player == HUMAN_IDX


def test_mode_manusia_bergantian_tanpa_ai():
    ctrl = GameController()
    ctrl.set_mode(MODE_HUMAN)
    ctrl.click(("move", (1, 4)))
    assert ctrl.state.current_player == 1
    tunggu(ctrl, lambda: ctrl.animation is None)
    ctrl.click(("wall", (4, 4, "H")))
    assert ctrl.state.walls_remaining[1] == 9
    ctrl.update()
    assert ctrl.ai_task is None


def test_undo_membatalkan_langkah_manusia_dan_ai():
    ctrl = GameController()
    ctrl.level = 1
    ctrl.ghost_enabled = False
    ctrl.click(("move", (1, 4)))
    tunggu(ctrl, lambda: ctrl.state.current_player == HUMAN_IDX and ctrl.animation is None)
    ctrl.undo()
    assert ctrl.state.pawns == [(0, 4), (8, 4)]
    assert ctrl.state.walls_remaining == [10, 10]
    assert ctrl.state.current_player == HUMAN_IDX


def test_restart_saat_ai_berpikir_mengabaikan_hasil_lama():
    ctrl = GameController()
    ctrl.level = 3
    ctrl.ghost_enabled = False
    ctrl.click(("move", (1, 4)))
    tunggu(ctrl, lambda: ctrl.ai_thinking)
    ctrl.restart()
    assert not ctrl.ai_thinking and ctrl.state.pawns == [(0, 4), (8, 4)]
    time.sleep(0.2)
    ctrl.update()
    assert ctrl.state.current_player == HUMAN_IDX and not ctrl.history


def test_hint_tersedia_tanpa_mengubah_state():
    ctrl = GameController()
    ctrl.level = 1
    ctrl.request_hint()
    tunggu(ctrl, lambda: ctrl.hint is not None)
    assert ctrl.hint.action is not None
    assert not ctrl.history and ctrl.state.pawns == [(0, 4), (8, 4)]
