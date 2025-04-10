import tkinter as tk
from tkinter import messagebox
import copy

class UltimateTicTacToe:
    def __init__(self, root):
        self.root = root
        self.root.title("Triqui de Triquis")
        self.root.resizable(False, False)
        
        # Colores
        self.bg_color = "#f0f0f0"
        self.grid_color = "#000000"
        self.active_board_color = "#ffcccc"
        self.player_X_color = "#3498db"  # Azul
        self.player_O_color = "#e74c3c"  # Rojo
        
        # Estado del juego
        self.current_player = "X"
        self.next_board = None  # Puede ser None al principio (cualquier tablero)
        self.game_boards = [[[[None for _ in range(3)] for _ in range(3)] for _ in range(3)] for _ in range(3)]
        self.board_winners = [[None for _ in range(3)] for _ in range(3)]
        self.game_winner = None
        
        # Crear marcos para los tableros
        self.frames = [[None for _ in range(3)] for _ in range(3)]
        self.buttons = [[[[None for _ in range(3)] for _ in range(3)] for _ in range(3)] for _ in range(3)]
        
        # Crear el tablero principal
        self.main_frame = tk.Frame(root, bg=self.grid_color, padx=5, pady=5)
        self.main_frame.pack(padx=10, pady=10)
        
        # Información del juego
        self.info_frame = tk.Frame(root)
        self.info_frame.pack(pady=5)
        
        self.player_label = tk.Label(self.info_frame, text=f"Turno del Jugador: {self.current_player}", font=("Arial", 12))
        self.player_label.grid(row=0, column=0, padx=10)
        
        self.next_board_label = tk.Label(self.info_frame, text="Tablero activo: Cualquiera", font=("Arial", 12))
        self.next_board_label.grid(row=0, column=1, padx=10)
        
        self.restart_button = tk.Button(self.info_frame, text="Reiniciar Juego", command=self.restart_game)
        self.restart_button.grid(row=0, column=2, padx=10)
        
        # Crear los tableros
        self.create_boards()
        
    def create_boards(self):
        for i in range(3):
            for j in range(3):
                # Crear marco para cada tablero 3x3
                self.frames[i][j] = tk.Frame(self.main_frame, bg=self.bg_color, padx=3, pady=3)
                self.frames[i][j].grid(row=i, column=j, padx=5, pady=5)
                
                # Crear botones para cada casilla
                for x in range(3):
                    for y in range(3):
                        self.buttons[i][j][x][y] = tk.Button(
                            self.frames[i][j],
                            text="",
                            width=3,
                            height=1,
                            font=("Arial", 14, "bold"),
                            bg=self.bg_color,
                            command=lambda i=i, j=j, x=x, y=y: self.make_move(i, j, x, y)
                        )
                        self.buttons[i][j][x][y].grid(row=x, column=y)
        
        # Destacar inicialmente todos los tableros como disponibles
        self.highlight_active_board()
    
    def make_move(self, board_i, board_j, cell_i, cell_j):
        # Verificar si el juego ya terminó
        if self.game_winner:
            return
        
        # Verificar si el tablero está disponible para jugar
        if self.next_board is not None and (self.next_board[0] != board_i or self.next_board[1] != board_j):
            messagebox.showinfo("Movimiento inválido", "Debes jugar en el tablero resaltado.")
            return
        
        # Verificar si el tablero ya tiene un ganador
        if self.board_winners[board_i][board_j]:
            messagebox.showinfo("Tablero completado", "Este tablero ya está ganado. Juega en otro tablero disponible.")
            return
        
        # Verificar si la celda ya está ocupada
        if self.game_boards[board_i][board_j][cell_i][cell_j] is not None:
            return
        
        # Realizar el movimiento
        self.game_boards[board_i][board_j][cell_i][cell_j] = self.current_player
        self.buttons[board_i][board_j][cell_i][cell_j].config(
            text=self.current_player,
            bg=self.player_X_color if self.current_player == "X" else self.player_O_color
        )
        
        # Verificar si hay un ganador en este tablero
        if self.check_win(self.game_boards[board_i][board_j]):
            self.board_winners[board_i][board_j] = self.current_player
            self.mark_board_as_won(board_i, board_j)
            
            # Verificar si hay un ganador del juego completo
            if self.check_win(self.board_winners):
                self.game_winner = self.current_player
                messagebox.showinfo("¡Fin del juego!", f"¡El jugador {self.current_player} ha ganado el juego!")
                return
        # Verificar si hay empate en este tablero
        elif self.check_draw(self.game_boards[board_i][board_j]):
            self.board_winners[board_i][board_j] = "Empate"
            self.mark_board_as_draw(board_i, board_j)
        
        # Verificar si el juego completo está empatado
        if self.check_draw(self.board_winners):
            self.game_winner = "Empate"
            messagebox.showinfo("¡Fin del juego!", "¡El juego ha terminado en empate!")
            return
        
        # Cambiar al siguiente jugador
        self.current_player = "O" if self.current_player == "X" else "X"
        self.player_label.config(text=f"Turno del Jugador: {self.current_player}")
        
        # Determinar el siguiente tablero
        if self.board_winners[cell_i][cell_j] is None:
            self.next_board = (cell_i, cell_j)
            self.next_board_label.config(text=f"Tablero activo: ({cell_i+1}, {cell_j+1})")
        else:
            # Si el tablero ya está ganado o empatado, el jugador puede elegir cualquier tablero
            self.next_board = None
            self.next_board_label.config(text="Tablero activo: Cualquiera")
        
        # Actualizar la visualización de los tableros activos
        self.highlight_active_board()
    
    def check_win(self, board):
        # Verificar filas
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] and board[i][0] is not None and board[i][0] != "Empate":
                return True
        
        # Verificar columnas
        for j in range(3):
            if board[0][j] == board[1][j] == board[2][j] and board[0][j] is not None and board[0][j] != "Empate":
                return True
        
        # Verificar diagonales
        if board[0][0] == board[1][1] == board[2][2] and board[0][0] is not None and board[0][0] != "Empate":
            return True
        if board[0][2] == board[1][1] == board[2][0] and board[0][2] is not None and board[0][2] != "Empate":
            return True
        
        return False
    
    def check_draw(self, board):
        # Verificar si todas las celdas están ocupadas y no hay ganador
        for i in range(3):
            for j in range(3):
                if board[i][j] is None:
                    return False
        return True
    
    def mark_board_as_won(self, board_i, board_j):
        # Marcar visualmente que un tablero ha sido ganado
        winner = self.board_winners[board_i][board_j]
        color = self.player_X_color if winner == "X" else self.player_O_color
        
        # Deshabilitar todos los botones en este tablero
        for i in range(3):
            for j in range(3):
                self.buttons[board_i][board_j][i][j].config(state=tk.DISABLED)
        
        # Colorear el fondo del tablero
        self.frames[board_i][board_j].config(bg=color)
        
        # Mostrar quién ganó este tablero
        label = tk.Label(
            self.frames[board_i][board_j],
            text=winner,
            font=("Arial", 36, "bold"),
            fg="white",
            bg=color
        )
        label.place(relx=0.5, rely=0.5, anchor="center")
    
    def mark_board_as_draw(self, board_i, board_j):
        # Marcar visualmente que un tablero ha terminado en empate
        # Deshabilitar todos los botones en este tablero
        for i in range(3):
            for j in range(3):
                self.buttons[board_i][board_j][i][j].config(state=tk.DISABLED)
        
        # Colorear el fondo del tablero
        self.frames[board_i][board_j].config(bg="#999999")  # Gris para empate
    
    def highlight_active_board(self):
        # Quitar el resaltado de todos los tableros
        for i in range(3):
            for j in range(3):
                if self.board_winners[i][j] is None:
                    self.frames[i][j].config(bg=self.bg_color)
        
        # Resaltar el tablero activo
        if self.next_board is not None:
            i, j = self.next_board
            if self.board_winners[i][j] is None:
                self.frames[i][j].config(bg=self.active_board_color)
        else:
            # Si cualquier tablero es válido, resaltar todos los disponibles
            for i in range(3):
                for j in range(3):
                    if self.board_winners[i][j] is None:
                        self.frames[i][j].config(bg=self.active_board_color)
    
    def restart_game(self):
        # Reiniciar el estado del juego
        self.current_player = "X"
        self.next_board = None
        self.game_boards = [[[[None for _ in range(3)] for _ in range(3)] for _ in range(3)] for _ in range(3)]
        self.board_winners = [[None for _ in range(3)] for _ in range(3)]
        self.game_winner = None
        
        # Reiniciar las etiquetas
        self.player_label.config(text=f"Turno del Jugador: {self.current_player}")
        self.next_board_label.config(text="Tablero activo: Cualquiera")
        
        # Destruir todos los widgets y recrear el tablero
        for i in range(3):
            for j in range(3):
                self.frames[i][j].destroy()
        
        self.create_boards()

if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateTicTacToe(root)
    root.mainloop()