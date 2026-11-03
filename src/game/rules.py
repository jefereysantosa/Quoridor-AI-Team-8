from collections import deque

class Rules:
    @staticmethod
    def is_wall_valid(state, r: int, c: int, orientation: str, player_idx: int):
        """

        Memvalidasi apakah penempatan dinding legal.
        r, c: Koordinat persimpangan (0-7).
        orientation: 'H' (Horizontal) atau 'V' (Vertikal).
        
        """
        # 1. Cek sisa dinding
        if state.walls_remaining[player_idx] <= 0:
            return False

        # 2. Cek batas papan
        if not (0 <= r < 8 and 0 <= c < 8):
            return False

        # 3. Cek Overlap (Tumpang Tindih)
        if orientation == 'H':
            if state.h_walls[r][c]: return False
            # Dinding H memanjang 2 unit. Cek tetangga kiri dan kanan.
            if c > 0 and state.h_walls[r][c-1]: return False
            if c < 7 and state.h_walls[r][c+1]: return False
            if state.v_walls[r][c]: return False   # Dinding V melintasi persimpangan sama
        else: # 'V'
            if state.v_walls[r][c]: return False
            # Dinding V memanjang 2 unit. Cek tetangga atas dan bawah.
            if r > 0 and state.v_walls[r-1][c]: return False
            if r < 7 and state.v_walls[r+1][c]: return False
            if state.h_walls[r][c]: return False   # Dinding H melintasi persimpangan sama

        # 4. Simulasi Penempatan & BFS Reachability Test
        # Simulasi pasang dinding
        if orientation == 'H': state.h_walls[r][c] = True
        else: state.v_walls[r][c] = True

        # Jalankan BFS untuk KEDUA pemain. Target row: Player 0 -> 8, Player 1 -> 0
        p0_path_exists = Rules._bfs_has_path(state, state.pawns[0], 8)
        p1_path_exists = Rules._bfs_has_path(state, state.pawns[1], 0)

        # Backtrack (Lepas dinding simulasi)
        if orientation == 'H': state.h_walls[r][c] = False
        else: state.v_walls[r][c] = False

        # Dinding legal HANYA JIKA kedua pemain masih punya jalan
        return p0_path_exists and p1_path_exists

    @staticmethod
    def _bfs_has_path(state, start_pos: tuple, target_row: int):
        """BFS untuk mengecek apakah ada jalur dari start ke target_row."""
        queue = deque([start_pos])
        visited = set([start_pos])
        
        while queue:
            r, c = queue.popleft()
            
            # Kondisi Menang: Sudah mencapai baris tujuan
            if r == target_row:
                return True
                
            # Cek 4 arah tetangga (Atas, Bawah, Kiri, Kanan)
            # Logika blokir dinding berdasarkan persimpangan 8x8
            neighbors = []
            
            # ATAS (r-1, c)
            if r > 0:
                # Terblokir jika ada H-wall di (r-1, c) atau (r-1, c-1)
                blocked = state.h_walls[r-1][c] or (c > 0 and state.h_walls[r-1][c-1])
                if not blocked: neighbors.append((r-1, c))
                
            # BAWAH (r+1, c)
            if r < 8:
                # Terblokir jika ada H-wall di (r, c) atau (r, c-1)
                blocked = state.h_walls[r][c] or (c > 0 and state.h_walls[r][c-1])
                if not blocked: neighbors.append((r+1, c))
                
            # KIRI (r, c-1)
            if c > 0:
                # Terblokir jika ada V-wall di (r, c-1) atau (r-1, c-1)
                blocked = state.v_walls[r][c-1] or (r > 0 and state.v_walls[r-1][c-1])
                if not blocked: neighbors.append((r, c-1))
                
            # KANAN (r, c+1)
            if c < 8:
                # Terblokir jika ada V-wall di (r, c) atau (r-1, c)
                blocked = state.v_walls[r][c] or (r > 0 and state.v_walls[r-1][c])
                if not blocked: neighbors.append((r, c+1))

            for nxt in neighbors:
                if nxt not in visited:
                    # Cek apakah kotak tujuan tidak ditempati pion lawan (kecuali logic lompatan, tapi untuk pathfinding murni kita anggap pion lawan sebagai blockage sementara atau bisa dilewati? 
                    # ATURAN QUORIDOR: Pion lawan memblokir jalur jalan kaki, tapi bisa dilompati. 
                    # Untuk Reachability Test (BFS), kita abaikan posisi pion lawan karena pion bisa dilompati. 
                    # Yang penting tidak ada DINDIN yang memblokir total.
                    visited.add(nxt)
                    queue.append(nxt)
                    
        return False