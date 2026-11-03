"""
Modul Dynamic Playstyle (Inovasi 1, Bab 2.1.1 proposal).

Menyediakan preset bobot evaluasi bernama yang dapat dipilih pengguna
lewat GUI dan diganti secara runtime tanpa membuat ulang objek AI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Union


@dataclass(frozen=True)
class Playstyle:
    """Satu preset gaya bermain AI."""

    name: str
    weights: Tuple[float, float, float]  # (w_d, w_w, w_m) sesuai rumus Eval(s)
    description: str


AGGRESSIVE = Playstyle(
    "Aggressive",
    (1.5, 0.2, 0.1),
    "Fokus memperpendek jalur sendiri dan menekan jalur lawan.",
)
DEFENSIVE = Playstyle(
    "Defensive",
    (0.7, 0.9, 0.4),
    "Fokus menghemat dinding dan membatasi mobilitas lawan.",
)
BALANCED = Playstyle(
    "Balanced",
    (1.0, 0.5, 0.25),
    "Bobot default persis seperti rumus Eval(s) pada proposal.",
)

DEFAULT = BALANCED

PLAYSTYLES: Dict[str, Playstyle] = {
    "aggressive": AGGRESSIVE,
    "defensive": DEFENSIVE,
    "balanced": BALANCED,
}

PlaystyleLike = Union[str, Playstyle, Tuple[float, float, float], None]


def get_playstyle(key: str) -> Playstyle:
    """Mengambil preset berdasarkan kunci string dari GUI."""
    k = str(key).lower()
    if k not in PLAYSTYLES:
        raise ValueError(f"Playstyle tidak dikenal: {key}")
    return PLAYSTYLES[k]


def list_playstyles() -> List[Playstyle]:
    """Daftar preset untuk dirender sebagai tombol atau dropdown GUI."""
    return [AGGRESSIVE, DEFENSIVE, BALANCED]


def resolve_weights(playstyle: PlaystyleLike = None) -> Tuple[float, float, float]:
    """Menormalkan berbagai bentuk input playstyle menjadi tuple bobot."""
    if playstyle is None:
        return DEFAULT.weights
    if isinstance(playstyle, Playstyle):
        return playstyle.weights
    if isinstance(playstyle, tuple):
        return playstyle
    return get_playstyle(playstyle).weights