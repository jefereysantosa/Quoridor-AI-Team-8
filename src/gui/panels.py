"""
Modul komponen panel GUI (Gambar 4 proposal).

Menyediakan tombol, grup pilihan, panel statistik AI, dan layar bantuan.
Panel Explainable Hint dan tombol Dynamic Playstyle ada di innovations.py.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import pygame

from .controller import LEVEL_TIME_LIMITS

COLOR_PANEL = (49, 46, 43)
COLOR_BORDER = (74, 70, 65)
COLOR_TEXT = (232, 224, 208)
COLOR_MUTED = (170, 161, 147)
COLOR_ACCENT = (206, 180, 138)
COLOR_BUTTON = (59, 57, 55)
COLOR_BUTTON_ACTIVE = (88, 110, 60)
COLOR_BUTTON_ACTIVE_TEXT = (245, 240, 228)
COLOR_BUTTON_DISABLED = (44, 42, 39)
COLOR_SHADE = (16, 14, 12)
COLOR_ON_SHADE = (240, 232, 216)


def draw_panel(screen, rect: pygame.Rect) -> None:
    pygame.draw.rect(screen, COLOR_PANEL, rect, border_radius=8)
    pygame.draw.rect(screen, COLOR_BORDER, rect, width=1, border_radius=8)


def wrap_text(text: str, font, max_width: int) -> List[str]:
    """Memecah teks per kata agar muat pada lebar panel."""
    lines: List[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class Button:
    """Tombol sederhana dengan satu aksi."""

    def __init__(self, rect: pygame.Rect, label: str, key: str):
        self.rect = rect
        self.label = label
        self.key = key

    def hit(self, pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)

    def draw(self, screen, font, enabled: bool = True, active: bool = False) -> None:
        fill = COLOR_BUTTON_ACTIVE if active else COLOR_BUTTON if enabled else COLOR_BUTTON_DISABLED
        pygame.draw.rect(screen, fill, self.rect, border_radius=6)
        pygame.draw.rect(screen, COLOR_BORDER, self.rect, width=1, border_radius=6)
        color = COLOR_BUTTON_ACTIVE_TEXT if active else COLOR_TEXT if enabled else COLOR_MUTED
        label = font.render(self.label, True, color)
        screen.blit(label, label.get_rect(center=self.rect.center))


class ToggleGroup:
    """Deretan tombol yang hanya satu pilihannya aktif, misalnya Kesulitan."""

    def __init__(self, rect: pygame.Rect, options: Sequence[Tuple[str, object]]):
        width = rect.width // len(options)
        self.buttons = [
            (value, Button(pygame.Rect(rect.left + i * width, rect.top, width - 2, rect.height), label, str(value)))
            for i, (label, value) in enumerate(options)
        ]

    def hit(self, pos: Tuple[int, int]) -> Optional[object]:
        for value, button in self.buttons:
            if button.hit(pos):
                return value
        return None

    def draw(self, screen, font, active_value) -> None:
        for value, button in self.buttons:
            button.draw(screen, font, active=value == active_value)


def _format_score(score: Optional[float]) -> str:
    if score is None:
        return "-"
    if score == float("inf"):
        return "MENANG"
    if score == float("-inf"):
        return "KALAH"
    return f"{score:+.2f}"


def _format_depth(stats: Dict) -> str:
    if "depth" not in stats:
        return "-"
    limit = stats.get("limit")
    return f"{stats['depth']} ply" + (f" (batas {limit:g} detik)" if limit else "")


class StatsPanel:
    """Panel Statistik AI: angka dari pencarian terakhir."""

    def __init__(self, rect: pygame.Rect, title_font, font):
        self.rect = rect
        self.title_font = title_font
        self.font = font

    def draw(self, screen, stats: Dict, thinking: bool) -> None:
        draw_panel(screen, self.rect)
        x, y = self.rect.left + 14, self.rect.top + 10
        title = "PANEL STATISTIK AI" + ("  (AI berpikir...)" if thinking else "")
        screen.blit(self.title_font.render(title, True, COLOR_ACCENT), (x, y))
        y += 30

        rows = [
            ("Algoritma", "Minimax + Alpha-Beta"),
            ("Kedalaman", _format_depth(stats)),
            ("Node eval", f"{stats['nodes']:,}".replace(",", ".") if "nodes" in stats else "-"),
            ("Cutoff prune", f"{stats['cutoffs']:,}".replace(",", ".") if "cutoffs" in stats else "-"),
            ("Waktu", f"{stats['ms']:,.0f} ms".replace(",", ".") if "ms" in stats else "-"),
            ("Skor", _format_score(stats.get("score"))),
        ]
        for label, value in rows:
            screen.blit(self.font.render(f"{label:<13}: {value}", True, COLOR_TEXT), (x, y))
            y += 24


HELP_BOX_SIZE = (780, 600)
HELP_LINE_HEIGHT = 26

HELP_PAGES = [
    [
        "CARA BERMAIN",
        "Tujuan: bawa pion Anda ke baris berwarna di sisi seberang, kolom mana saja.",
        "Tiap giliran pilih satu: gerakkan pion atau pasang dinding (masing-masing 10).",
        "Klik sel bergaris hijau untuk menggerakkan pion.",
        "Klik celah antar sel untuk memasang dinding.",
        "Dinding merah berarti ditolak, alasannya tampil di kotak pesan.",
        "",
        "GHOST STEP",
        "Setelah memilih langkah, prediksi balasan AI tampil transparan.",
        "Klik langkah yang sama, tekan Enter, atau Konfirmasi untuk menjalankan.",
        "Prediksi hanya melihat satu langkah, balasan AI sebenarnya bisa berbeda.",
        "",
        "TOMBOL",
        "Enter konfirmasi   Esc batal   H hint   U undo   R restart",
        "G nyala/matikan Ghost Step   F1 tampilkan bantuan ini",
        "Undo pada vs AI membatalkan langkah AI dan langkah Anda sekaligus.",
    ],
    [
        "PLAYSTYLE (GAYA BERMAIN AI LAWAN)",
        "Aggressive: mengutamakan jalur terpendeknya sendiri.",
        "Defensive: lebih menghemat dinding dan membatasi gerak Anda.",
        "Balanced: seimbang, ini pilihan bawaan.",
        "Perbedaannya halus dan sering baru terlihat setelah dinding mulai dipasang.",
        "",
        "KESULITAN 1-5",
        "Makin tinggi, makin jauh AI menghitung ke depan.",
        f"Level 1 dan 2 cepat. Level 3, 4, dan 5 berpikir maksimal {LEVEL_TIME_LIMITS[3]:g}, "
        f"{LEVEL_TIME_LIMITS[4]:g}, dan {LEVEL_TIME_LIMITS[5]:g} detik.",
        "Papan terkunci selama AI berpikir.",
        "",
        "PANEL STATISTIK AI",
        "Tidak perlu untuk bermain, panel ini menunjukkan cara kerja AI.",
        "Kedalaman: langkah ke depan yang dihitung. Node eval: posisi yang dinilai.",
        "Cutoff prune: berapa kali Alpha-Beta memotong pencarian.",
        "Waktu: lama AI berpikir. Skor: nilai posisi, positif menguntungkan AI.",
        "",
        "KOTAK PESAN",
        "Berisi petunjuk, langkah pilihan, prediksi AI, alasan penolakan, dan pemenang.",
        "Langkah terakhir AI tidak ditulis di sini, lihat langsung di papan.",
    ],
]


def draw_help(screen, title_font, font, page: int = 0) -> None:
    """Layar bantuan di atas seluruh jendela."""
    shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    shade.fill((*COLOR_SHADE, 170))
    screen.blit(shade, (0, 0))
    box = pygame.Rect(0, 0, HELP_BOX_SIZE[0], HELP_BOX_SIZE[1])
    box.center = screen.get_rect().center
    draw_panel(screen, box)
    y = box.top + 20
    for line in HELP_PAGES[page]:
        heading = line.isupper()
        use_font = title_font if heading else font
        color = COLOR_ACCENT if heading else COLOR_TEXT
        screen.blit(use_font.render(line, True, color), (box.left + 28, y))
        y += HELP_LINE_HEIGHT

    last = page == len(HELP_PAGES) - 1
    action = "menutup" if last else "lanjut, Esc untuk menutup"
    footer = f"Halaman {page + 1}/{len(HELP_PAGES)}. Tekan tombol apa saja untuk {action}."
    screen.blit(font.render(footer, True, COLOR_MUTED), (box.left + 28, box.bottom - 36))
