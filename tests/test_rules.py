"""
Test Logical Constraint Engine (Bab 2.2 bagian B.1).

Berisi 30 kasus penempatan dinding dengan verdict yang ditetapkan manual
dari aturan resmi Quoridor (bukan dari keluaran kode), termasuk konfigurasi
jebakan yang dirancang untuk memicu blokir total. Target akurasi: 100 persen.
Ditambah pemeriksaan silang acak terhadap oracle BFS independen.
"""
import random
from collections import deque

import pytest

from src.game.rules import Rules
from src.game.state import State


def _state(h=(), v=(), pawns=None, walls=None):
    s = State()
    for r, c in h:
        s.h_walls[r][c] = True
    for r, c in v:
        s.v_walls[r][c] = True
    if pawns:
        s.pawns = list(pawns)
    if walls:
        s.walls_remaining = list(walls)
    return s


# Dinding pengisi: empat H sepanjang batas baris 3|4 pada kolom 1-8,
# menyisakan satu celah di kolom 0 (sel (3,0) -> (4,0)).
WALL_ROW = [(3, 1), (3, 3), (3, 5), (3, 7)]

# (nama, state, aksi (r, c, orientasi), pemain penempat, verdict legal?)
CASES = [
    # --- A. Penempatan dasar yang legal (8 kasus)
    ("H tengah papan", _state(), (3, 3, "H"), 0, True),
    ("V tengah papan", _state(), (3, 3, "V"), 0, True),
    ("H pojok kiri atas", _state(), (0, 0, "H"), 0, True),
    ("V pojok kanan bawah", _state(), (7, 7, "V"), 1, True),
    ("H pojok kanan atas", _state(), (0, 7, "H"), 1, True),
    ("V pojok kiri bawah", _state(), (7, 0, "V"), 0, True),
    ("H bersebelahan tanpa tumpang tindih (c+2)", _state(h=[(3, 3)]), (3, 5, "H"), 0, True),
    ("V bersebelahan tanpa tumpang tindih (r+2)", _state(v=[(3, 3)]), (5, 3, "V"), 1, True),
    # --- B. Tumpang tindih dan persilangan yang ilegal (9 kasus)
    ("H di slot yang sama", _state(h=[(3, 3)]), (3, 3, "H"), 0, False),
    ("H tumpang tindih kanan (c+1)", _state(h=[(3, 3)]), (3, 4, "H"), 0, False),
    ("H tumpang tindih kiri (c-1)", _state(h=[(3, 3)]), (3, 2, "H"), 0, False),
    ("V di slot yang sama", _state(v=[(3, 3)]), (3, 3, "V"), 1, False),
    ("V tumpang tindih bawah (r+1)", _state(v=[(3, 3)]), (4, 3, "V"), 1, False),
    ("V tumpang tindih atas (r-1)", _state(v=[(3, 3)]), (2, 3, "V"), 1, False),
    ("V bersilang H di persimpangan sama", _state(h=[(3, 3)]), (3, 3, "V"), 0, False),
    ("H bersilang V di persimpangan sama", _state(v=[(3, 3)]), (3, 3, "H"), 0, False),
    ("H sejajar baris berbeda tetap legal", _state(h=[(3, 3)]), (4, 3, "H"), 0, True),
    # --- C. Batas papan dan sisa dinding (4 kasus)
    ("Di luar papan: baris 8", _state(), (8, 0, "H"), 0, False),
    ("Di luar papan: kolom 8", _state(), (0, 8, "V"), 0, False),
    ("Di luar papan: indeks negatif", _state(), (-1, 0, "H"), 0, False),
    ("Sisa dinding habis", _state(walls=[0, 10]), (3, 3, "H"), 0, False),
    # --- D. Jebakan blokir total (9 kasus)
    ("Kantong pojok P0 (0,0): V menutup total",
        _state(h=[(0, 0)], pawns=[(0, 0), (8, 4)]), (0, 1, "V"), 1, False),
    ("Kantong pojok P0 di (0,1): V menutup total",
        _state(h=[(0, 0)], pawns=[(0, 1), (8, 4)]), (0, 1, "V"), 0, False),
    ("Kantong pojok P1 (8,8): V menutup total",
        _state(h=[(7, 7)], pawns=[(0, 4), (8, 8)]), (7, 6, "V"), 0, False),
    ("Kantong pojok P1 (8,7): V menutup total",
        _state(h=[(7, 7)], pawns=[(0, 4), (8, 7)]), (7, 6, "V"), 1, False),
    ("Celah tunggal satu baris ditutup dari atas",
        _state(h=WALL_ROW, v=[(3, 0)]), (2, 0, "H"), 0, False),
    ("Celah tunggal ditutup oleh pemain lawan",
        _state(h=WALL_ROW, v=[(3, 0)]), (2, 0, "H"), 1, False),
    ("Kontrol: celah tunggal tanpa V masih bisa dikitari",
        _state(h=WALL_ROW), (2, 0, "H"), 0, True),
    ("Kontrol: kantong pojok tanpa V penutup tetap legal",
        _state(h=[(0, 0)], pawns=[(0, 0), (8, 4)]), (4, 4, "H"), 0, True),
    ("Dinding memperpanjang jalur tetapi tidak menutup total",
        _state(h=[(0, 0)], pawns=[(0, 0), (8, 4)]), (0, 2, "V"), 0, True),
]


def test_jumlah_kasus_sesuai_proposal():
    assert len(CASES) == 30


@pytest.mark.parametrize("nama,state,aksi,pemain,verdict", CASES, ids=[c[0] for c in CASES])
def test_verdict_logical_constraint_engine(nama, state, aksi, pemain, verdict):
    r, c, orient = aksi
    assert Rules.is_wall_valid(state, r, c, orient, pemain) is verdict


def test_validasi_tidak_mengubah_state():
    s = _state(h=[(0, 0)], pawns=[(0, 0), (8, 4)])
    before = ([row[:] for row in s.h_walls], [row[:] for row in s.v_walls])
    Rules.is_wall_valid(s, 0, 1, "V", 1)   # ditolak
    Rules.is_wall_valid(s, 4, 4, "H", 0)   # diterima
    assert ([row[:] for row in s.h_walls], [row[:] for row in s.v_walls]) == before


# ----------------------------------------------------------------------
# Oracle independen: graf sisi diblokir dibangun langsung dari geometri
# dinding, tanpa memakai logika indeks milik Rules.
# ----------------------------------------------------------------------

def _oracle_has_path(h, v, start, target_row):
    blocked = set()
    for r, c in h:   # H(r,c): menutup dua sisi vertikal antara baris r dan r+1
        blocked.add(frozenset({(r, c), (r + 1, c)}))
        blocked.add(frozenset({(r, c + 1), (r + 1, c + 1)}))
    for r, c in v:   # V(r,c): menutup dua sisi horizontal antara kolom c dan c+1
        blocked.add(frozenset({(r, c), (r, c + 1)}))
        blocked.add(frozenset({(r + 1, c), (r + 1, c + 1)}))
    seen, q = {start}, deque([start])
    while q:
        r, c = q.popleft()
        if r == target_row:
            return True
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < 9 and 0 <= nc < 9 and (nr, nc) not in seen \
                    and frozenset({(r, c), (nr, nc)}) not in blocked:
                seen.add((nr, nc))
                q.append((nr, nc))
    return False


def _oracle_legal(h, v, pawns, r, c, orient):
    if not (0 <= r < 8 and 0 <= c < 8):
        return False
    hs, vs = set(h), set(v)
    if orient == "H":
        if {(r, c), (r, c - 1), (r, c + 1)} & hs or (r, c) in vs:
            return False
        hs = hs | {(r, c)}
    else:
        if {(r, c), (r - 1, c), (r + 1, c)} & vs or (r, c) in hs:
            return False
        vs = vs | {(r, c)}
    return (_oracle_has_path(hs, vs, pawns[0], 8)
            and _oracle_has_path(hs, vs, pawns[1], 0))


def test_silang_terhadap_oracle_acak():
    rng = random.Random(7)
    checked = 0
    for _ in range(60):
        s = State()
        s.pawns = [(rng.randrange(9), rng.randrange(9)), (rng.randrange(9), rng.randrange(9))]
        if s.pawns[0] == s.pawns[1]:
            continue
        for _ in range(rng.randrange(4, 16)):
            r, c, o = rng.randrange(8), rng.randrange(8), rng.choice("HV")
            if Rules.is_wall_valid(s, r, c, o, 0):
                (s.h_walls if o == "H" else s.v_walls)[r][c] = True
        h = [(r, c) for r in range(8) for c in range(8) if s.h_walls[r][c]]
        v = [(r, c) for r in range(8) for c in range(8) if s.v_walls[r][c]]
        for r in range(8):
            for c in range(8):
                for o in "HV":
                    assert Rules.is_wall_valid(s, r, c, o, 0) == _oracle_legal(h, v, s.pawns, r, c, o), (h, v, r, c, o)
                    checked += 1
    assert checked > 1000
