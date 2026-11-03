from src.ai import QuoridorAI, predict_response, generate_hint, clear_ghost_cache
from src.gui.innovations import GhostOverlay, HintPanel, PlaystyleButtons

ai = QuoridorAI(max_depth=3)
overlay = GhostOverlay(cell_size=CELL, origin=ORIGIN)
hint_panel = HintPanel(pygame.Rect(800, 40, 380, 230))
playstyle_buttons = PlaystyleButtons(pygame.Rect(800, 285, 380, 36))
active_playstyle = "balanced"
ghost_pred = None
selected_action = None

# --- di dalam event loop ---
key = playstyle_buttons.handle_event(event)
if key:
    active_playstyle = key
    ai.set_playstyle(key)
    clear_ghost_cache()

# saat pemain KLIK kandidat langkah (sebelum konfirmasi):
# selected_action = hasil hit-test papan milik Jason
if selected_action is not None:
    ghost_pred = predict_response(
        state, selected_action, state.current_player,
        depth=1, playstyle=ai.playstyle,
    )

# saat tombol Hint ditekan:
hint_panel.set_hint(
    generate_hint(state, state.current_player, depth=ai.max_depth, playstyle=ai.playstyle)
)

# saat pemain KONFIRMASI langkah:
state.apply_move(selected_action, state.current_player)
clear_ghost_cache()
ghost_pred = None
ai_move = ai.get_best_move(state, state.current_player)
state.apply_move(ai_move, state.current_player)

# --- di bagian draw ---
overlay.draw_prediction(screen, ghost_pred)
hint_panel.draw(screen)
playstyle_buttons.draw(screen, active_playstyle)