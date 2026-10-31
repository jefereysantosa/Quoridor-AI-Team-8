import copy

class State:
    def __init__(self):
        
        # Posisi pion: Index 0 = Player 0 (Human/Bawah), Index 1 = Player 1 (AI/Atas)
        # Format: (row, col). Papan 9x9 (index 0-8).
        self.pawns = [(0, 4), (8, 4)]
        
        # Sisa dinding: [Player 0, Player 1]. Masing-masing 10 di awal.
        self.walls_remaining = [10, 10]
        
        # Matriks 8x8 untuk dinding. 
        # h_walls[r][c] = True berarti ada dinding Horizontal di persimpangan (r,c) yang memanjang ke (r, c+1)
        # v_walls[r][c] = True berarti ada dinding Vertikal di persimpangan (r,c) yang memanjang ke (r+1, c)
        self.h_walls = [[False for _ in range(8)] for _ in range(8)]
        self.v_walls = [[False for _ in range(8)] for _ in range(8)]
        
        # 0 = Giliran Player 0, 1 = Giliran Player 1
        self.current_player = 0 

    def clone(self):
        """Membuat salinan state yang independen untuk simulasi Minimax."""
        return copy.deepcopy(self)

    def get_pawn_pos(self, player_idx: int):
        return self.pawns[player_idx]

    def is_winner(self, player_idx: int):
        """Cek apakah pemain sudah mencapai garis tujuan."""
        r, _ = self.pawns[player_idx]
        if player_idx == 0:
            return r == 8  # Player 0 mulai di 0, tujuan di 8
        else:
            return r == 0  # Player 1 mulai di 8, tujuan di 0