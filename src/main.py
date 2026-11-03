"""
Titik masuk aplikasi Quoridor AI. Jalankan dengan: python -m src.main

Menyusun layout sesuai Gambar 4 proposal: menu di atas, papan di kiri,
panel statistik dan hint di kanan, serta kontrol di bawah.
"""

from __future__ import annotations

import pygame

from src.ai.explain import describe_action
from src.gui.board_view import BoardView, CELL_SIZE, ORIGIN, PLAYER_COLORS
from src.gui.controller import AI_IDX, HUMAN_IDX, MODE_AI, MODE_HUMAN, GameController
from src.gui.innovations import GhostOverlay, HintPanel, PlaystyleButtons
from src.gui.panels import (
    COLOR_ACCENT, COLOR_MUTED, COLOR_TEXT, HELP_PAGES,
    Button, StatsPanel, ToggleGroup, draw_help, draw_panel, wrap_text,
)

WINDOW_SIZE = (1180, 780)
BACKGROUND = (14, 15, 19)
RIGHT_X = 672
RIGHT_W = 476
HINT_GHOST_COLOR = (96, 200, 130)
FPS = 60


class App:
    """Jendela aplikasi: menerjemahkan input pengguna ke GameController."""

    def __init__(self, screen=None):
        pygame.init()
        pygame.display.set_caption("Quoridor AI - Team 8")
        self.screen = screen or pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.show_help = False
        self.help_page = 0

        self.font = pygame.font.SysFont("consolas", 16)
        self.font_small = pygame.font.SysFont("consolas", 14, bold=True)
        self.font_title = pygame.font.SysFont("consolas", 17, bold=True)
        self.font_big = pygame.font.SysFont("consolas", 40, bold=True)

        self.ctrl = GameController()
        self.board = BoardView()
        self.overlay = GhostOverlay(cell_size=CELL_SIZE, origin=ORIGIN)
        self.hover = None

        self.menu_buttons = [
            Button(pygame.Rect(32 + i * 112, 16, 104, 36), label, key)
            for i, (label, key) in enumerate(
                [("New Game", "new"), ("Undo", "undo"), ("Restart", "restart"), ("Help", "help")]
            )
        ]
        self.stats_panel = StatsPanel(pygame.Rect(RIGHT_X, 68, RIGHT_W, 188), self.font_title, self.font)
        self.hint_button = Button(pygame.Rect(RIGHT_X, 264, RIGHT_W, 34), "Minta Hint (H)", "hint")
        self.hint_panel = HintPanel(pygame.Rect(RIGHT_X, 304, RIGHT_W, 278), self.font)

        self.message_rect = pygame.Rect(RIGHT_X, 590, RIGHT_W, 106)
        self.confirm_button = Button(pygame.Rect(RIGHT_X + 14, 660, 216, 30), "Konfirmasi (Enter)", "confirm")
        self.cancel_button = Button(pygame.Rect(RIGHT_X + 246, 660, 216, 30), "Batal (Esc)", "cancel")

        self.playstyle_buttons = PlaystyleButtons(pygame.Rect(140, 706, 390, 30), self.font_small)
        self.level_group = ToggleGroup(
            pygame.Rect(140, 742, 200, 30), [(str(level), level) for level in range(1, 6)]
        )
        self.mode_group = ToggleGroup(
            pygame.Rect(RIGHT_X - 54, 706, 260, 30), [("vs AI", MODE_AI), ("vs Manusia", MODE_HUMAN)]
        )
        self.ghost_button = Button(pygame.Rect(360, 742, 170, 30), "Ghost Step", "ghost")

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(self, event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif self.show_help:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self._advance_help(event)
        elif event.type == pygame.MOUSEMOTION:
            self.hover = self.board.hit_test(event.pos)
        elif event.type == pygame.KEYDOWN:
            self._handle_key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event)

    def _handle_key(self, key) -> None:
        ctrl = self.ctrl
        actions = {
            pygame.K_RETURN: ctrl.confirm,
            pygame.K_KP_ENTER: ctrl.confirm,
            pygame.K_ESCAPE: ctrl.cancel,
            pygame.K_h: ctrl.request_hint,
            pygame.K_u: ctrl.undo,
            pygame.K_r: ctrl.restart,
            pygame.K_g: ctrl.toggle_ghost,
        }
        if key == pygame.K_F1:
            self._open_help()
        elif key in actions:
            actions[key]()

    def _handle_click(self, event) -> None:
        ctrl, pos = self.ctrl, event.pos
        menu_actions = {
            "new": ctrl.new_game,
            "undo": ctrl.undo,
            "restart": ctrl.restart,
            "help": self._open_help,
        }
        for button in self.menu_buttons:
            if button.hit(pos):
                menu_actions[button.key]()
                return

        if self.hint_button.hit(pos):
            ctrl.request_hint()
        elif ctrl.pending is not None and self.confirm_button.hit(pos):
            ctrl.confirm()
        elif ctrl.pending is not None and self.cancel_button.hit(pos):
            ctrl.cancel()
        elif self.ghost_button.hit(pos):
            ctrl.toggle_ghost()
        else:
            self._handle_setting_click(event)

    def _handle_setting_click(self, event) -> None:
        ctrl, pos = self.ctrl, event.pos
        playstyle = self.playstyle_buttons.handle_event(event)
        level = self.level_group.hit(pos)
        mode = self.mode_group.hit(pos)
        if playstyle:
            ctrl.set_playstyle(playstyle)
        elif level:
            ctrl.set_level(level)
        elif mode:
            ctrl.set_mode(mode)
        else:
            action = self.board.hit_test(pos)
            if action:
                ctrl.click(action)

    def _open_help(self) -> None:
        self.show_help = True
        self.help_page = 0

    def _advance_help(self, event) -> None:
        """Lanjut ke halaman berikutnya; Esc atau halaman terakhir menutup bantuan."""
        escape = event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        self.help_page += 1
        if escape or self.help_page >= len(HELP_PAGES):
            self.show_help = False

    # ------------------------------------------------------------------
    # Gambar
    # ------------------------------------------------------------------

    def draw(self) -> None:
        self.screen.fill(BACKGROUND)
        self._draw_menu()
        self._draw_board()
        self._draw_right_column()
        self._draw_controls()
        if self.show_help:
            draw_help(self.screen, self.font_title, self.font, self.help_page)

    def _draw_menu(self) -> None:
        ctrl = self.ctrl
        for button in self.menu_buttons:
            button.draw(self.screen, self.font_small)

        if ctrl.winner is not None:
            text = f"PERMAINAN SELESAI: {ctrl.player_name(ctrl.winner).upper()} MENANG"
        elif ctrl.ai_thinking:
            text = "Giliran: AI (berpikir...)"
        else:
            text = f"Giliran: {ctrl.player_name(ctrl.state.current_player).upper()}"
        color = PLAYER_COLORS[ctrl.state.current_player] if ctrl.winner is None else COLOR_ACCENT
        label = self.font_title.render(text, True, color)
        self.screen.blit(label, label.get_rect(midright=(RIGHT_X + RIGHT_W, 34)))

    def _draw_board(self) -> None:
        ctrl, screen, board = self.ctrl, self.screen, self.board
        board.draw_board(screen)

        if ctrl.human_can_act:
            board.draw_legal_moves(screen, ctrl.legal_pawn_moves(), self.hover)
        board.draw_walls(screen, ctrl.state, ctrl.fresh_wall_alpha())

        if ctrl.human_can_act and self.hover and self.hover[0] == "wall" and self.hover != ctrl.pending:
            board.draw_wall_preview(screen, self.hover[1], ctrl.wall_reason(self.hover) is None)
        if ctrl.rejected_wall:
            board.draw_wall_preview(screen, ctrl.rejected_wall, False)

        if ctrl.hint and ctrl.hint.action:
            self._draw_action_ghost(ctrl.hint.action, HINT_GHOST_COLOR)
        if ctrl.pending:
            self._draw_action_ghost(ctrl.pending, PLAYER_COLORS[ctrl.state.current_player])
        self.overlay.draw_prediction(screen, ctrl.ghost_pred)

        for idx in (HUMAN_IDX, AI_IDX):
            board.draw_pawn(screen, ctrl.pawn_display_pos(idx), idx)

        if ctrl.winner is not None:
            self._draw_game_over()

    def _draw_action_ghost(self, action, color) -> None:
        kind, payload = action
        if kind == "move":
            self.overlay.draw_pawn_ghost(self.screen, payload, color)
        else:
            self.overlay.draw_wall_ghost(self.screen, *payload, color)

    def _draw_game_over(self) -> None:
        rect = self.board.rect
        shade = pygame.Surface(rect.size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        self.screen.blit(shade, rect.topleft)
        title = self.font_big.render(f"{self.ctrl.player_name(self.ctrl.winner)} menang!", True, COLOR_ACCENT)
        self.screen.blit(title, title.get_rect(center=(rect.centerx, rect.centery - 16)))
        sub = self.font.render("Tekan R untuk bermain lagi, atau U untuk undo", True, COLOR_TEXT)
        self.screen.blit(sub, sub.get_rect(center=(rect.centerx, rect.centery + 26)))

    def _draw_right_column(self) -> None:
        ctrl = self.ctrl
        self.stats_panel.draw(self.screen, ctrl.stats, ctrl.ai_thinking)

        enabled = ctrl.human_can_act and not ctrl.hint_loading
        self.hint_button.label = "Menghitung hint..." if ctrl.hint_loading else "Minta Hint (H)"
        self.hint_button.draw(self.screen, self.font_small, enabled=enabled)
        self._sync_hint_panel()
        self.hint_panel.draw(self.screen)

        self._draw_message_panel()

    def _sync_hint_panel(self) -> None:
        ctrl = self.ctrl
        if ctrl.hint is not None:
            if self.hint_panel.hint is not ctrl.hint:
                self.hint_panel.set_hint(ctrl.hint)
        else:
            self.hint_panel.clear()
            self.hint_panel.lines = ["PANEL EXPLAINABLE HINT", "Tekan Minta Hint untuk saran langkah."]

    def _draw_message_panel(self) -> None:
        ctrl = self.ctrl
        rect = self.message_rect
        draw_panel(self.screen, rect)

        if ctrl.notice:
            text, color = ctrl.notice, (240, 130, 130)
        elif ctrl.pending:
            text = f"Pilihan: {describe_action(ctrl.pending)}."
            if ctrl.ghost_loading:
                text += " Menghitung balasan AI..."
            elif ctrl.ghost_pred and ctrl.ghost_pred.ai_response:
                text += f" Prediksi balasan AI: {describe_action(ctrl.ghost_pred.ai_response)}."
            color = COLOR_TEXT
        elif ctrl.winner is not None:
            text, color = f"{ctrl.player_name(ctrl.winner)} mencapai garis tujuan.", COLOR_ACCENT
        elif ctrl.ai_thinking:
            text, color = "AI sedang mencari langkah terbaik...", COLOR_MUTED
        else:
            text, color = "Pilih sel hijau untuk bergerak atau celah untuk memasang dinding.", COLOR_MUTED

        y = rect.top + 8
        for line in wrap_text(text, self.font, rect.width - 28)[:3]:
            self.screen.blit(self.font.render(line, True, color), (rect.left + 14, y))
            y += 19

        if ctrl.pending:
            self.confirm_button.draw(self.screen, self.font_small)
            self.cancel_button.draw(self.screen, self.font_small)

    def _draw_controls(self) -> None:
        ctrl, screen = self.ctrl, self.screen
        screen.blit(self.font_small.render("Playstyle", True, COLOR_MUTED), (32, 713))
        self.playstyle_buttons.draw(screen, ctrl.playstyle)
        screen.blit(self.font_small.render("Kesulitan", True, COLOR_MUTED), (32, 749))
        self.level_group.draw(screen, self.font_small, ctrl.level)
        self.ghost_button.label = f"Ghost Step: {'On' if ctrl.ghost_enabled else 'Off'} (G)"
        self.ghost_button.draw(screen, self.font_small, active=ctrl.ghost_enabled)
        self.mode_group.draw(screen, self.font_small, ctrl.mode)

        walls = ctrl.state.walls_remaining
        text = (
            f"Sisa dinding: {ctrl.player_name(HUMAN_IDX)} {walls[HUMAN_IDX]} | "
            f"{ctrl.player_name(AI_IDX)} {walls[AI_IDX]}"
        )
        screen.blit(self.font.render(text, True, COLOR_TEXT), (RIGHT_X - 54, 749))

    # ------------------------------------------------------------------
    # Loop utama
    # ------------------------------------------------------------------

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.ctrl.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()


def main() -> None:
    App().run()


if __name__ == "__main__":
    main()
