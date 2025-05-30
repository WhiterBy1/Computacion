# =============================================================================
# ACCESSIBILITY MANAGER - MÓDULO DE ACCESIBILIDAD PLUG-AND-PLAY
# Para Ultimate Tic Tac Toe
# Versión: 1.0
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import time 



class AccessibilityManager:
    """
    Gestor de accesibilidad que se puede añadir a cualquier aplicación Tkinter
    """
    
    def __init__(self, root_window):
        self.root = root_window
        self.enabled = True
        
        # Estado de navegación
        self.current_focus_widget = None
        self.focus_ring_widgets = []
        self.focus_index = 0
        
        # Configuración visual
        self.focus_color = "#e6f3ff"
        self.active_color = "#cce7ff"
        self.focus_border_color = "#0066cc"
        
        # Widgets originales (para restaurar)
        self.original_styles = {}
        
        # Configurar automáticamente
        self.setup_global_keyboard_navigation()
        
    def setup_global_keyboard_navigation(self):
        """Configurar navegación por teclado global"""
        
        # Atajos globales principales
        self.root.bind_all("<Tab>", self._handle_tab)
        self.root.bind_all("<Shift-Tab>", self._handle_shift_tab)
        self.root.bind_all("<Return>", self._handle_enter)
        self.root.bind_all("<space>", self._handle_space)
        self.root.bind_all("<Escape>", self._handle_escape)
        
        # Atajos de aplicación
        self.root.bind_all("<F1>", self._show_help)
        self.root.bind_all("<Control-q>", self._handle_quit)
        self.root.bind_all("<Control-r>", self._handle_refresh)
        
        # Auto-descubrir widgets focusables
        self.root.after(500, self._auto_discover_widgets)
    
    def _handle_tab(self, event):
        """Manejar Tab - siguiente widget"""
        self._focus_next_widget()
        return "break"
    
    def _handle_shift_tab(self, event):
        """Manejar Shift+Tab - widget anterior"""
        self._focus_previous_widget()
        return "break"
    
    def _handle_enter(self, event):
        """Manejar Enter - activar widget"""
        if self.current_focus_widget:
            self._activate_widget(self.current_focus_widget)
        return "break"
    
    def _handle_space(self, event):
        """Manejar Espacio - activar widget"""
        if self.current_focus_widget:
            self._activate_widget(self.current_focus_widget)
        return "break"
    
    def _handle_escape(self, event):
        """Manejar Escape - cancelar"""
        self._clear_focus()
        return "break"
    
    def _handle_quit(self, event):
        """Manejar Ctrl+Q - salir"""
        app = self._find_app_instance()
        if app and hasattr(app, 'logout'):
            app.logout()
        elif app and hasattr(app, 'quit'):
            app.quit()
        return "break"
    
    def _handle_refresh(self, event):
        """Manejar Ctrl+R - actualizar"""
        app = self._find_app_instance()
        if app and hasattr(app, 'sync_data'):
            app.sync_data()
        return "break"
    
    def _show_help(self, event):
        """Mostrar ayuda de teclado"""
        self.show_keyboard_help()
        return "break"
    
    def _find_app_instance(self):
        """Encontrar la instancia de la aplicación principal"""
        # Buscar en el root window si es una instancia de App
        if hasattr(self.root, 'logout') or hasattr(self.root, 'sync_data'):
            return self.root
        
        # Buscar en widgets hijos
        for widget in self.root.winfo_children():
            if hasattr(widget, 'logout') or hasattr(widget, 'sync_data'):
                return widget
        
        return None
    
    def _auto_discover_widgets(self):
        """Auto-descubrir widgets focusables"""
        self.focus_ring_widgets.clear()
        self._discover_widgets_recursive(self.root)
        
        # Configurar eventos de foco para todos los widgets
        for widget in self.focus_ring_widgets:
            self._setup_widget_focus_events(widget)
    
    def _discover_widgets_recursive(self, widget):
        """Descubrir widgets de forma recursiva"""
        # Tipos de widgets focusables
        focusable_types = (
            tk.Button, ttk.Button,
            tk.Entry, ttk.Entry,
            tk.Listbox, ttk.Treeview,
            tk.Text, tk.Checkbutton, ttk.Checkbutton,
            tk.Radiobutton, ttk.Radiobutton,
            ttk.Combobox, tk.Scale, ttk.Scale
        )
        
        if isinstance(widget, focusable_types):
            # Verificar que el widget esté visible y habilitado
            try:
                if widget.winfo_viewable() and str(widget['state']) != 'disabled':
                    self.focus_ring_widgets.append(widget)
            except (tk.TclError, KeyError):
                # Algunos widgets no tienen 'state'
                if widget.winfo_viewable():
                    self.focus_ring_widgets.append(widget)
        
        # Recurrir a los hijos
        try:
            for child in widget.winfo_children():
                self._discover_widgets_recursive(child)
        except tk.TclError:
            pass
    
    def _setup_widget_focus_events(self, widget):
        """Configurar eventos de foco para un widget"""
        # Guardar estilo original
        if widget not in self.original_styles:
            self.original_styles[widget] = {}
            try:
                if 'bg' in widget.configure():
                    self.original_styles[widget]['bg'] = widget.cget('bg')
                if 'relief' in widget.configure():
                    self.original_styles[widget]['relief'] = widget.cget('relief')
                if 'highlightthickness' in widget.configure():
                    self.original_styles[widget]['highlightthickness'] = widget.cget('highlightthickness')
            except tk.TclError:
                pass
        
        # Configurar eventos
        widget.bind("<FocusIn>", lambda e: self._on_focus_in(e.widget), add="+")
        widget.bind("<FocusOut>", lambda e: self._on_focus_out(e.widget), add="+")
    
    def _on_focus_in(self, widget):
        """Widget recibe foco"""
        self.current_focus_widget = widget
        
        # Aplicar estilo de foco
        try:
            if 'bg' in widget.configure():
                widget.configure(bg=self.focus_color)
            if 'highlightthickness' in widget.configure():
                widget.configure(highlightthickness=2, highlightcolor=self.focus_border_color)
        except tk.TclError:
            pass
    
    def _on_focus_out(self, widget):
        """Widget pierde foco"""
        # Restaurar estilo original
        if widget in self.original_styles:
            try:
                original = self.original_styles[widget]
                if 'bg' in original and 'bg' in widget.configure():
                    widget.configure(bg=original['bg'])
                if 'highlightthickness' in original and 'highlightthickness' in widget.configure():
                    widget.configure(highlightthickness=original['highlightthickness'])
            except tk.TclError:
                pass
    
    def _focus_next_widget(self):
        """Enfocar siguiente widget"""
        if not self.focus_ring_widgets:
            self._auto_discover_widgets()
            
        if not self.focus_ring_widgets:
            return
        
        self.focus_index = (self.focus_index + 1) % len(self.focus_ring_widgets)
        widget = self.focus_ring_widgets[self.focus_index]
        
        if self._is_widget_focusable(widget):
            widget.focus_set()
        else:
            # Si no es focusable, intentar el siguiente
            self._focus_next_widget()
    
    def _focus_previous_widget(self):
        """Enfocar widget anterior"""
        if not self.focus_ring_widgets:
            self._auto_discover_widgets()
            
        if not self.focus_ring_widgets:
            return
        
        self.focus_index = (self.focus_index - 1) % len(self.focus_ring_widgets)
        widget = self.focus_ring_widgets[self.focus_index]
        
        if self._is_widget_focusable(widget):
            widget.focus_set()
        else:
            # Si no es focusable, intentar el anterior
            self._focus_previous_widget()
    
    def _is_widget_focusable(self, widget):
        """Verificar si un widget puede recibir foco"""
        try:
            return (widget.winfo_exists() and 
                   widget.winfo_viewable() and 
                   str(widget['state']) != 'disabled')
        except (tk.TclError, KeyError):
            try:
                return widget.winfo_exists() and widget.winfo_viewable()
            except tk.TclError:
                return False
    
    def _activate_widget(self, widget):
        """Activar un widget (como hacer clic)"""
        try:
            if hasattr(widget, 'invoke'):
                widget.invoke()
            elif isinstance(widget, (tk.Entry, ttk.Entry)):
                # Para Entry, no hacer nada especial, ya tiene foco
                pass
            elif isinstance(widget, (tk.Text,)):
                # Para Text, posicionar cursor al final
                widget.mark_set(tk.INSERT, tk.END)
            elif hasattr(widget, 'selection_set'):
                # Para Listbox y similares
                if widget.size() > 0:
                    widget.selection_set(0)
                    widget.event_generate("<<ListboxSelect>>")
        except (tk.TclError, AttributeError):
            pass
    
    def _clear_focus(self):
        """Limpiar foco actual"""
        if self.current_focus_widget:
            try:
                self.root.focus_set()
            except tk.TclError:
                pass
        self.current_focus_widget = None
    
    def show_keyboard_help(self):
        """Mostrar ventana de ayuda con atajos"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Atajos de Teclado - Ayuda")
        help_window.geometry("650x500")
        help_window.transient(self.root)
        help_window.grab_set()
        help_window.focus_set()
        
        # Contenido de ayuda
        help_text = """
🎮 GUÍA DE ATAJOS DE TECLADO

📋 NAVEGACIÓN BÁSICA:
• Tab                     → Siguiente control
• Shift + Tab             → Control anterior  
• Enter / Espacio         → Activar control seleccionado
• Escape                  → Cancelar acción

🔧 ATAJOS GLOBALES:
• F1                      → Mostrar esta ayuda
• Ctrl + Q                → Salir de la aplicación
• Ctrl + R                → Actualizar/Refrescar datos

🎯 EN TABLAS Y LISTAS:
• Flechas ↑↓              → Navegar entre elementos
• Enter                   → Seleccionar/Ver detalles
• Letras A-Z              → Búsqueda rápida

🎮 EN EL JUEGO:
• Flechas                 → Mover cursor
• Enter / Espacio         → Hacer movimiento
• Ctrl + R                → Reiniciar juego

💡 CONSEJOS:
• Los elementos enfocados se resaltan en azul
• Use Tab para navegación secuencial
• Los atajos funcionan en toda la aplicación
• Presione Escape para cancelar acciones

🚀 PRODUCTIVIDAD:
• Aprenda los atajos principales (Tab, Enter, F1)
• Use Ctrl+R para actualizar datos rápidamente
• El foco visual ayuda a saber dónde está
        """
        
        # Frame para el texto
        text_frame = tk.Frame(help_window)
        text_frame.pack(expand=True, fill="both", padx=15, pady=15)
        
        # Widget de texto con scroll
        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#f8f9fa",
            fg="#212529",
            padx=20,
            pady=20,
            state="disabled"
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Insertar texto
        text_widget.config(state="normal")
        text_widget.insert("1.0", help_text)
        text_widget.config(state="disabled")
        
        scrollbar.pack(side="right", fill="y")
        text_widget.pack(side="left", expand=True, fill="both")
        
        # Botón cerrar
        close_btn = tk.Button(
            help_window,
            text="Cerrar (Escape)",
            command=help_window.destroy,
            font=("Arial", 11),
            bg="#007bff",
            fg="white",
            padx=20,
            pady=8
        )
        close_btn.pack(pady=15)
        close_btn.focus_set()
        
        # Atajos para cerrar
        help_window.bind("<Escape>", lambda e: help_window.destroy())
        help_window.bind("<Return>", lambda e: help_window.destroy())
        help_window.bind("<F1>", lambda e: help_window.destroy())
    
    def refresh_widgets(self):
        """Refrescar lista de widgets (llamar después de cambios en UI)"""
        self._auto_discover_widgets()
    
    def disable(self):
        """Deshabilitar accesibilidad temporalmente"""
        self.enabled = False
    
    def enable(self):
        """Habilitar accesibilidad"""
        self.enabled = True
        self._auto_discover_widgets()


class GameAccessibilityManager(AccessibilityManager):
    """
    Gestor de accesibilidad específico para el juego Ultimate Tic Tac Toe
    """
    
    def __init__(self, root_window, game_instance=None):
        super().__init__(root_window)
        self.game = game_instance
        
        # Variables específicas del juego
        self.board_focus_row = 1
        self.board_focus_col = 1
        self.cell_focus_row = 1
        self.cell_focus_col = 1
        
        # Configurar navegación específica del juego
        self.setup_game_navigation()
    
    def setup_game_navigation(self):
        """Configurar navegación específica para el juego"""
        
        # Navegación con flechas en el tablero
        self.root.bind("<Up>", self._handle_arrow_up)
        self.root.bind("<Down>", self._handle_arrow_down)
        self.root.bind("<Left>", self._handle_arrow_left)
        self.root.bind("<Right>", self._handle_arrow_right)
        
        # Navegación entre tableros con Ctrl
        self.root.bind("<Control-Up>", self._handle_board_up)
        self.root.bind("<Control-Down>", self._handle_board_down)
        self.root.bind("<Control-Left>", self._handle_board_left)
        self.root.bind("<Control-Right>", self._handle_board_right)
        
        # Selección rápida con números
        for i in range(1, 10):
            self.root.bind(f"<Key-{i}>", lambda e, num=i: self._handle_number_key(num))
        
        # Crear indicador de posición si no existe
        self._create_position_indicator()
    
    def _create_position_indicator(self):
        """Crear indicador de posición del cursor"""
        # Buscar si ya existe un label de cursor
        for widget in self._find_all_widgets(self.root):
            if isinstance(widget, tk.Label) and "Cursor:" in str(widget.cget('text')):
                self.cursor_label = widget
                return
        
        # Si no existe, intentar crearlo (esto requiere que el juego tenga una estructura específica)
        self.cursor_label = None
    
    def _find_all_widgets(self, parent):
        """Encontrar todos los widgets recursivamente"""
        widgets = [parent]
        try:
            for child in parent.winfo_children():
                widgets.extend(self._find_all_widgets(child))
        except tk.TclError:
            pass
        return widgets
    
    def _handle_arrow_up(self, event):
        """Manejar flecha arriba"""
        self.cell_focus_row = max(0, self.cell_focus_row - 1)
        self._update_game_focus()
        return "break"
    
    def _handle_arrow_down(self, event):
        """Manejar flecha abajo"""
        self.cell_focus_row = min(2, self.cell_focus_row + 1)
        self._update_game_focus()
        return "break"
    
    def _handle_arrow_left(self, event):
        """Manejar flecha izquierda"""
        self.cell_focus_col = max(0, self.cell_focus_col - 1)
        self._update_game_focus()
        return "break"
    
    def _handle_arrow_right(self, event):
        """Manejar flecha derecha"""
        self.cell_focus_col = min(2, self.cell_focus_col + 1)
        self._update_game_focus()
        return "break"
    
    def _handle_board_up(self, event):
        """Manejar Ctrl+Arriba (cambiar tablero)"""
        self.board_focus_row = max(0, self.board_focus_row - 1)
        self._update_game_focus()
        return "break"
    
    def _handle_board_down(self, event):
        """Manejar Ctrl+Abajo (cambiar tablero)"""
        self.board_focus_row = min(2, self.board_focus_row + 1)
        self._update_game_focus()
        return "break"
    
    def _handle_board_left(self, event):
        """Manejar Ctrl+Izquierda (cambiar tablero)"""
        self.board_focus_col = max(0, self.board_focus_col - 1)
        self._update_game_focus()
        return "break"
    
    def _handle_board_right(self, event):
        """Manejar Ctrl+Derecha (cambiar tablero)"""
        self.board_focus_col = min(2, self.board_focus_col + 1)
        self._update_game_focus()
        return "break"
    
    def _handle_number_key(self, number):
        """Manejar teclas numéricas 1-9"""
        # Convertir número a coordenadas de celda
        number -= 1  # 0-8
        self.cell_focus_row = number // 3
        self.cell_focus_col = number % 3
        self._update_game_focus()
        return "break"
    
    def _update_game_focus(self):
        """Actualizar foco en el juego"""
        # Actualizar indicador de posición si existe
        if hasattr(self, 'cursor_label') and self.cursor_label:
            try:
                self.cursor_label.config(
                    text=f"Cursor: Tablero ({self.board_focus_row + 1},{self.board_focus_col + 1}) - Celda ({self.cell_focus_row + 1},{self.cell_focus_col + 1})"
                )
            except tk.TclError:
                pass
        
        # Intentar enfocar el botón correspondiente si el juego tiene la estructura esperada
        if self.game and hasattr(self.game, 'buttons'):
            try:
                target_button = self.game.buttons[self.board_focus_row][self.board_focus_col][self.cell_focus_row][self.cell_focus_col]
                if target_button and target_button.winfo_exists():
                    target_button.focus_set()
            except (IndexError, AttributeError, tk.TclError):
                pass
    
    def _activate_widget(self, widget):
        """Activar widget en el contexto del juego"""
        # Si es un botón del juego, intentar hacer el movimiento
        if self.game and hasattr(self.game, 'make_move'):
            try:
                self.game.make_move(
                    self.board_focus_row, 
                    self.board_focus_col, 
                    self.cell_focus_row, 
                    self.cell_focus_col
                )
                return
            except Exception:
                pass
        
        # Si no es del juego, usar comportamiento por defecto
        super()._activate_widget(widget)


# =============================================================================
# FUNCIONES DE INTEGRACIÓN FÁCIL
# =============================================================================

def make_accessible(window, game_instance=None):
    """
    Función simple para hacer accesible cualquier ventana Tkinter
    
    Args:
        window: La ventana principal (tk.Tk o tk.Toplevel)
        game_instance: Instancia del juego (opcional, para funcionalidad específica)
    
    Returns:
        AccessibilityManager instance
    """
    if game_instance:
        return GameAccessibilityManager(window, game_instance)
    else:
        return AccessibilityManager(window)


def add_accessibility_to_app(app_instance):
    """
    Añadir accesibilidad a una aplicación existente
    
    Args:
        app_instance: Instancia de la aplicación que hereda de tk.Tk
    
    Returns:
        AccessibilityManager instance
    """
    # Crear el gestor de accesibilidad
    accessibility_manager = AccessibilityManager(app_instance)
    
    # Añadir el gestor como atributo de la aplicación
    app_instance.accessibility_manager = accessibility_manager
    
    return accessibility_manager


def add_game_accessibility(game_window, game_instance):
    """
    Añadir accesibilidad específica para el juego
    
    Args:
        game_window: Ventana del juego
        game_instance: Instancia del juego UltimateTicTacToe
    
    Returns:
        GameAccessibilityManager instance
    """
    game_accessibility = GameAccessibilityManager(game_window, game_instance)
    
    # Añadir como atributo del juego
    game_instance.accessibility_manager = game_accessibility
    
    return game_accessibility


# =============================================================================
# EJEMPLO DE USO SIMPLE
# =============================================================================

if __name__ == "__main__":
    # Demo de uso básico
    root = tk.Tk()
    root.title("Demo Accesibilidad")
    
    # Crear algunos widgets de prueba
    tk.Label(root, text="Demo de Accesibilidad", font=("Arial", 16)).pack(pady=10)
    
    tk.Button(root, text="Botón 1").pack(pady=5)
    tk.Button(root, text="Botón 2").pack(pady=5)
    tk.Entry(root).pack(pady=5)
    tk.Button(root, text="Botón 3").pack(pady=5)
    
    # Hacer accesible
    accessibility = make_accessible(root)
    
    tk.Label(root, text="Presiona F1 para ver la ayuda de teclado", 
             fg="gray").pack(pady=10)
    
    root.mainloop()