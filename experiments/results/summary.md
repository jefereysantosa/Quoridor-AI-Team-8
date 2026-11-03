# Hasil Turnamen Evaluasi Quoridor AI

Kedalaman AI: 2 ply | game per baseline: 50 | langkah pembuka acak: 4 ply | seed: 2026

## 1. Win Rate (Tabel 3)

| Baseline | M-K-S | Win Rate | Target | Tercapai | AI jalan 1 | AI jalan 2 |
|---|---|---|---|---|---|---|
| Random Agent | 50-0-0 | 100.0% | >= 90% | ya | 100.0% | 100.0% |
| Greedy Shortest-Path Agent | 50-0-0 | 100.0% | >= 70% | ya | 100.0% | 100.0% |
| Minimax tanpa Alpha-Beta | 25-25-0 | 50.0% | 40-60% | ya | 48.0% | 52.0% |

## 2. Pruning Efficiency

- Sampel state: 20 pada kedalaman 3
- Rata-rata node Alpha-Beta: 1305.9 vs Minimax murni: 34136.8
- **Pruning Efficiency rata-rata: 73.34%**
- Keputusan identik dengan Minimax murni: 100.0% sampel

## 3. Wall Effectiveness

- Dinding dipasang AI: 783
- **Rata-rata selisih jarak lawan: 1.966 langkah**
- Dinding yang memperpanjang jalur lawan: 94.5%
- Dinding yang justru merugikan AI (nilai negatif): 0

## 4. Kebenaran selama turnamen

- Langkah ilegal: **0** (target 0)
- Selisih A* vs BFS pada state permainan nyata: **0** (target 0)

Biaya pencarian AI: rata-rata 223.3 node dan 525.7 ms per langkah.
