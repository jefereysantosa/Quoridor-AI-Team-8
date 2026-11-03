# Quoridor AI - Team 8

Aplikasi permainan Quoridor berbasis Pygame untuk mata kuliah
Artificial Intelligence (IMT01307503), Universitas Ciputra.
Tersedia mode melawan AI dan melawan pemain lain.

## Tim
- Jeferey Teddy Santosa (0706012410039)
- Hans Vere Liem (0706012410013)
- Flabianos Jason Muljono (0706012410019)

---

## 1. Library yang Digunakan

Proyek ini menggunakan library Python berikut:

| Library | Versi | Kegunaan |
|---|---|---|
| **pygame-ce** | >= 2.5.0 | Rendering GUI, input handling, dan visualisasi papan permainan (Community Edition untuk kompatibilitas Python 3.14) |
| **pytest** | >= 8.0.0 | Framework pengujian otomatis untuk menjalankan test suite di folder `tests/` |

**Catatan:** Proyek ini menggunakan **Python 3.14.0** sebagai interpreter utama.

---

## 2. IDE yang Digunakan

| IDE | Versi | Kontributor |
|---|---|---|
| **Visual Studio Code** | 1.95.0 (atau versi terbaru) | Jeferey, Hans, Jason |

**Extensions yang direkomendasikan:**
- Python (Microsoft) - IntelliSense, debugging, dan environment management
- Pylance - Type checking dan auto-completion
- Python Debugger - Debugging dengan breakpoint

---

## 3. Langkah Instalasi dan Menjalankan

### Prasyarat
- Python 3.12 atau lebih baru (direkomendasikan 3.14.0)
- Git untuk version control

### Langkah-langkah Setup

**Langkah 1: Clone Repository**
```bash
git clone https://github.com/jefereysantosa/Quoridor-AI-Team-8.git
cd Quoridor-AI-Team-8
```

**Langkah 2: Buat Virtual Environment**

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows (Git Bash):
```bash
python -m venv .venv
source .venv/Scripts/activate
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Setelah aktivasi berhasil, prompt terminal akan diawali dengan `(.venv)`.

**Langkah 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

Perintah ini akan menginstall pygame-ce dan pytest secara otomatis.

**Langkah 4: Verifikasi Instalasi**
```bash
python -c "import pygame; print(pygame.__version__)"
python -m pytest --version
```

Kedua perintah di atas harus mencetak versi tanpa error.

**Langkah 5: Jalankan Aplikasi**
```bash
python -m src.main
```

Jendela permainan Quoridor akan terbuka. Selamat bermain!

---

## Algoritma

Minimax dengan Alpha-Beta Pruning, A* Search dan BFS untuk pathfinding,
serta Logical Constraint Engine berbasis BFS Reachability Test.

---

## Cara Bermain

Bawa pion ke baris seberang sebelum lawan. Tiap giliran, pilih satu aksi:
- Klik sel bergaris hijau untuk menggerakkan pion.
- Klik celah antar sel untuk memasang dinding.

**Fitur:**
- **Ghost Step:** menampilkan prediksi balasan AI sebelum langkah dikonfirmasi.
- **Explainable Hint:** memberi saran langkah beserta alasan berupa angka.
- **Dynamic Playstyle:** gaya bermain AI, yaitu Aggressive, Defensive, atau Balanced.
- **Kesulitan 1-5:** level 3, 4, dan 5 berpikir maksimal 3, 5, dan 10 detik per langkah.

| Tombol | Fungsi |
|---|---|
| Enter | Konfirmasi langkah |
| Esc | Batalkan pilihan |
| H | Minta hint |
| U | Undo |
| R | Restart |
| G | Nyalakan atau matikan Ghost Step |
| F1 | Bantuan |

---

## Pengujian

Jalankan seluruh test suite:
```bash
python -m pytest
```

Test suite mencakup:
- **test_rules.py**: 30 kasus Logical Constraint Engine (Bab 2.2 B.1)
- **test_pathfinding.py**: 50 konfigurasi acak untuk verifikasi BFS = A* (Bab 2.2 B.2)
- **test_minimax.py**: Verifikasi Alpha-Beta, zero-sum, dan candidate filtering
- **test_innovations.py**: Dynamic Playstyle, Ghost Step, dan Explainable Hint

---

## Evaluasi (Bab 2.2 Proposal)

Turnamen head-to-head melawan Random Agent, Greedy Shortest-Path Agent, dan
Minimax tanpa Alpha-Beta (50 game per baseline, pemain pertama bergantian):

```bash
python -m experiments.tournament                     # evaluasi penuh
python -m experiments.tournament --games 6 --quick   # uji cepat
```

**Output files** di `experiments/results/`:
- `games.csv` - Detail setiap game
- `moves.csv` - Detail setiap langkah
- `pruning.csv` - Statistik pruning efficiency
- `summary.json` - Ringkasan metrik dalam format JSON
- `summary.md` - Ringkasan metrik dalam format Markdown

**Metrik yang diukur:**
- Win Rate terhadap setiap baseline (Tabel 3 proposal)
- Pruning Efficiency = (Node_Minimax - Node_AlphaBeta) / Node_Minimax
- Wall Effectiveness = Jarak_Lawan_Setelah - Jarak_Lawan_Sebelum
- Kebenaran pathfinding (A* vs BFS) dan nol langkah ilegal

**Baseline tambahan:**
- Minimax murni tersedia lewat `QuoridorAI(max_depth=2, use_pruning=False)`
- Random Agent dan Greedy Agent ada di `src/ai/baselines.py`

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'pygame'"
Pastikan virtual environment aktif (prompt diawali `(.venv)`) dan jalankan:
```bash
python -m pip install -r requirements.txt
```

### Error: Permission denied pada Windows
Gunakan `python -m pip` alih-alih `pip` langsung:
```bash
python -m pip install pygame-ce
```

### GUI tidak muncul
Pastikan Anda menggunakan Python dengan dukungan GUI (bukan versi embedded) dan display driver tersedia.

---

## Lisensi

Proyek ini dikembangkan untuk keperluan akademis mata kuliah Artificial Intelligence (IMT01307503) di Universitas Ciputra Surabaya, tahun akademik 2026.