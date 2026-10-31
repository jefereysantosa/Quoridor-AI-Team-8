from .rules import Rules

class MoveGenerator:
    @staticmethod
    def get_legal_moves(state, player_idx: int):
        """Mengembalikan list semua aksi legal: [('move', (r, c)), ('wall', (r, c, 'H')), ...]"""
        moves = []
        
        # 1. Generate Pawn Moves (Gerak Pion & Lompatan)
        moves.extend(MoveGenerator._get_pawn_moves(state, player_idx))
        
        # 2. Generate Wall Moves (Penempatan Dinding)
        # Hanya generate jika pemain masih punya dinding
        if state.walls_remaining[player_idx] > 0:
            moves.extend(MoveGenerator._get_wall_moves(state, player_idx))
            
        return moves

    @staticmethod
    def _get_pawn_moves(state, player_idx: int):
        moves = []
        r, c = state.pawns[player_idx]
        opp_idx = 1 - player_idx
        opp_r, opp_c = state.pawns[opp_idx]
        
        # Arah: Atas, Bawah, Kiri, Kanan
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 9 and 0 <= nc < 9:
                # Cek apakah terblokir dinding (gunakan logika yang sama dengan BFS)
                blocked = False
                if dr == -1: blocked = state.h_walls[r-1][c] or (c > 0 and state.h_walls[r-1][c-1])
                elif dr == 1: blocked = state.h_walls[r][c] or (c > 0 and state.h_walls[r][c-1])
                elif dc == -1: blocked = state.v_walls[r][c-1] or (r > 0 and state.v_walls[r-1][c-1])
                elif dc == 1: blocked = state.v_walls[r][c] or (r > 0 and state.v_walls[r-1][c])
                
                if not blocked:
                    # Cek apakah ada pion lawan di depan
                    if nr == opp_r and nc == opp_c:
                        # ATURAN LOMPATAN: Coba lompat lurus
                        jump_r, jump_c = nr + dr, nc + dc
                        jump_blocked = False
                        
                        # Cek dinding di belakang pion lawan
                        if dr == -1: jump_blocked = state.h_walls[nr-1][nc] or (nc > 0 and state.h_walls[nr-1][nc-1])
                        elif dr == 1: jump_blocked = state.h_walls[nr][nc] or (nc > 0 and state.h_walls[nr][nc-1])
                        elif dc == -1: jump_blocked = state.v_walls[nr][nc-1] or (nr > 0 and state.v_walls[nr-1][nc-1])
                        elif dc == 1: jump_blocked = state.v_walls[nr][nc] or (nr > 0 and state.v_walls[nr-1][nc])
                        
                        if 0 <= jump_r < 9 and 0 <= jump_c < 9 and not jump_blocked:
                            moves.append(('move', (jump_r, jump_c))) # Lompat Lurus
                        else:
                            # Jika lompat lurus terblokir dinding, boleh lompat DIAGONAL
                            if dr != 0: # Gerakan vertikal, diagonal ke kiri/kanan
                                if nc > 0 and not (state.v_walls[nr][nc-1] or (nr > 0 and state.v_walls[nr-1][nc-1])):
                                    moves.append(('move', (nr, nc - 1)))
                                if nc < 8 and not (state.v_walls[nr][nc] or (nr > 0 and state.v_walls[nr-1][nc])):
                                    moves.append(('move', (nr, nc + 1)))
                            else: # Gerakan horizontal, diagonal ke atas/bawah
                                if nr > 0 and not (state.h_walls[nr-1][nc] or (nc > 0 and state.h_walls[nr-1][nc-1])):
                                    moves.append(('move', (nr - 1, nc)))
                                if nr < 8 and not (state.h_walls[nr][nc] or (nc > 0 and state.h_walls[nr][nc-1])):
                                    moves.append(('move', (nr + 1, nc)))
                    else:
                        moves.append(('move', (nr, nc))) # Jalan biasa
                        
        return moves

    @staticmethod
    def _get_wall_moves(state, player_idx: int):
        moves = []
        # Iterasi semua 64 titik persimpangan (8x8)
        for r in range(8):
            for c in range(8):
                for orientation in ['H', 'V']:
                    if Rules.is_wall_valid(state, r, c, orientation, player_idx):
                        moves.append(('wall', (r, c, orientation)))
        return moves