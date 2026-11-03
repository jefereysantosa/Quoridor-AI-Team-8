"""Test MoveGenerator: gerak pion, lompatan lurus, lompatan diagonal, dan dinding."""
from src.game.moves import MoveGenerator
from src.game.state import State


def _pawn_moves(s, idx):
    return {payload for kind, payload in MoveGenerator._get_pawn_moves(s, idx)}


def test_langkah_awal_pemain_0_di_tepi_papan():
    s = State()  # P0 di (0,4): tidak bisa ke atas
    assert _pawn_moves(s, 0) == {(1, 4), (0, 3), (0, 5)}


def test_langkah_awal_pemain_1_di_tepi_papan():
    s = State()  # P1 di (8,4): tidak bisa ke bawah
    assert _pawn_moves(s, 1) == {(7, 4), (8, 3), (8, 5)}


def test_jumlah_aksi_legal_awal():
    s = State()
    moves = MoveGenerator.get_legal_moves(s, 0)
    walls = [m for m in moves if m[0] == "wall"]
    assert len(walls) == 128          # 64 persimpangan x 2 orientasi, papan kosong
    assert len(moves) == 3 + 128


def test_pion_di_tengah_punya_empat_arah():
    s = State()
    s.pawns[0] = (4, 4)
    s.pawns[1] = (8, 0)
    assert _pawn_moves(s, 0) == {(3, 4), (5, 4), (4, 3), (4, 5)}


def test_dinding_horizontal_memblokir_gerak_vertikal():
    s = State()
    s.pawns = [(4, 4), (8, 0)]
    s.h_walls[4][4] = True   # di bawah (4,4) dan (4,5)
    assert (5, 4) not in _pawn_moves(s, 0)
    assert (3, 4) in _pawn_moves(s, 0)


def test_dinding_horizontal_menutup_dua_kolom():
    s = State()
    s.pawns = [(4, 5), (8, 0)]
    s.h_walls[4][4] = True   # memanjang ke kolom 5
    assert (5, 5) not in _pawn_moves(s, 0)


def test_dinding_vertikal_memblokir_gerak_horizontal():
    s = State()
    s.pawns = [(4, 4), (8, 0)]
    s.v_walls[4][4] = True   # di kanan (4,4) dan (5,4)
    assert (4, 5) not in _pawn_moves(s, 0)
    assert (4, 3) in _pawn_moves(s, 0)


def test_lompat_lurus_atas_pion_lawan():
    s = State()
    s.pawns = [(4, 4), (5, 4)]
    moves = _pawn_moves(s, 0)
    assert (6, 4) in moves
    assert (5, 4) not in moves     # tidak boleh berdiri di sel lawan


def test_lompat_lurus_terblokir_dinding_menjadi_diagonal():
    s = State()
    s.pawns = [(4, 4), (5, 4)]
    s.h_walls[5][4] = True         # dinding tepat di belakang lawan
    moves = _pawn_moves(s, 0)
    assert (6, 4) not in moves
    assert {(5, 3), (5, 5)} <= moves


def test_lompat_diagonal_hanya_ke_sisi_yang_tidak_terblokir():
    s = State()
    s.pawns = [(4, 4), (5, 4)]
    s.h_walls[5][4] = True
    s.v_walls[5][4] = True         # menutup (5,4)->(5,5)
    moves = _pawn_moves(s, 0)
    assert (5, 5) not in moves
    assert (5, 3) in moves


def test_lompat_di_tepi_papan_menjadi_diagonal():
    s = State()
    s.pawns = [(7, 4), (8, 4)]     # lawan di tepi bawah, tidak ada sel di belakangnya
    moves = _pawn_moves(s, 0)
    assert (8, 4) not in moves
    assert {(8, 3), (8, 5)} <= moves


def test_lompat_horizontal_dan_diagonal_vertikal():
    s = State()
    s.pawns = [(4, 4), (4, 5)]
    assert (4, 6) in _pawn_moves(s, 0)
    s.v_walls[4][5] = True         # di belakang lawan (kanan (4,5))
    moves = _pawn_moves(s, 0)
    assert (4, 6) not in moves
    assert {(3, 5), (5, 5)} <= moves


def test_dinding_tidak_dihasilkan_jika_habis():
    s = State()
    s.walls_remaining[0] = 0
    assert all(m[0] == "move" for m in MoveGenerator.get_legal_moves(s, 0))


def test_semua_dinding_yang_dihasilkan_lolos_validasi():
    from src.game.rules import Rules
    s = State()
    s.apply_move(("wall", (3, 3, "H")), 0)
    for kind, (r, c, o) in (m for m in MoveGenerator.get_legal_moves(s, 1) if m[0] == "wall"):
        assert Rules.is_wall_valid(s, r, c, o, 1)
    assert ("wall", (3, 3, "H")) not in MoveGenerator.get_legal_moves(s, 1)
    assert ("wall", (3, 3, "V")) not in MoveGenerator.get_legal_moves(s, 1)
