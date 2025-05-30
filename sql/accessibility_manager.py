# =============================================================================
# ACCESSIBILITY MANAGER - VERSIÓN FINAL CORREGIDA
# Soluciona: recursión infinita + preservación de colores de figuras
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import time

class AccessibilityManager:
    """
    Gestor de accesibilidad con navegación segura sin recursión infinita
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
        
        # Cache de notebooks encontrados
        self.notebooks = []
        
        # Control de recursión
        self._navigation_in_progress = False
        self._max_navigation_attempts = 10
        
        # Configurar automáticamente
        self.setup_global_keyboard_navigation()
        
    def setup_global_keyboard_navigation(self):
        """Configurar navegación por teclado global"""
        
        # Atajos globales principales - USAR BIND EN LA VENTANA ESPECÍFICA
        self.root.bind("<Tab>", self._handle_tab)
        self.root.bind("<Shift-Tab>", self._handle_shift_tab)
        self.root.bind("<Return>", self._handle_enter)
        self.root.bind("<space>", self._handle_space)
        self.root.bind("<Escape>", self._handle_escape)
        
        # Navegación específica para tabs
        self.root.bind("<Control-Tab>", self._handle_next_tab)
        self.root.bind("<Control-Shift-Tab>", self._handle_previous_tab)
        self.root.bind("<Control-1>", lambda e: self._select_tab(0))
        self.root.bind("<Control-2>", lambda e: self._select_tab(1))
        self.root.bind("<Control-3>", lambda e: self._select_tab(2))
        self.root.bind("<Control-4>", lambda e: self._select_tab(3))
        self.root.bind("<Control-5>", lambda e: self._select_tab(4))
        
        # Atajos de aplicación
        self.root.bind("<F1>", self._show_help)
        self.root.bind("<Control-q>", self._handle_quit)
        self.root.bind("<Control-r>", self._handle_refresh)
        
        # Hacer que la ventana tenga foco cuando se cree
        self.root.focus_force()
        
        # Auto-descubrir widgets focusables
        self.root.after(500, self._auto_discover_widgets)
        
        # Configurar eventos especiales para notebooks
        self.root.after(600, self._setup_notebook_navigation)
    
    def _setup_notebook_navigation(self):
        """Configurar navegación específica para notebooks (pestañas)"""
        self.notebooks = []
        self._find_notebooks(self.root)
        
        for notebook in self.notebooks:
            notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
            notebook.focus_set()
            notebook.bind("<Left>", self._notebook_previous_tab)
            notebook.bind("<Right>", self._notebook_next_tab)
            notebook.bind("<Return>", self._notebook_activate_tab)
            notebook.bind("<space>", self._notebook_activate_tab)
    
    def _find_notebooks(self, widget):
        """Encontrar todos los notebooks recursivamente"""
        if isinstance(widget, ttk.Notebook):
            self.notebooks.append(widget)
            self.register_focusable_widget(widget)
        
        try:
            for child in widget.winfo_children():
                self._find_notebooks(child)
        except tk.TclError:
            pass
    
    def _notebook_previous_tab(self, event):
        """Ir a la pestaña anterior"""
        notebook = event.widget
        current = notebook.index(notebook.select())
        total = len(notebook.tabs())
        new_index = (current - 1) % total
        notebook.select(new_index)
        return "break"
    
    def _notebook_next_tab(self, event):
        """Ir a la siguiente pestaña"""
        notebook = event.widget
        current = notebook.index(notebook.select())
        total = len(notebook.tabs())
        new_index = (current + 1) % total
        notebook.select(new_index)
        return "break"
    
    def _notebook_activate_tab(self, event):
        """Activar la pestaña actual del notebook"""
        notebook = event.widget
        current_tab = notebook.nametowidget(notebook.select())
        self._focus_first_widget_in_tab(current_tab)
        return "break"
    
    def _focus_first_widget_in_tab(self, tab_widget):
        """Enfocar el primer widget focusable dentro de una pestaña"""
        focusable_widgets = []
        self._find_focusable_in_widget(tab_widget, focusable_widgets)
        
        if focusable_widgets:
            focusable_widgets[0].focus_set()
    
    def _find_focusable_in_widget(self, widget, focusable_list):
        """Encontrar widgets focusables dentro de un widget específico"""
        focusable_types = (
            tk.Button, ttk.Button,
            tk.Entry, ttk.Entry,
            tk.Listbox, ttk.Treeview,
            tk.Text, tk.Checkbutton, ttk.Checkbutton,
            tk.Radiobutton, ttk.Radiobutton,
            ttk.Combobox, tk.Scale, ttk.Scale
        )
        
        if isinstance(widget, focusable_types):
            try:
                if widget.winfo_viewable() and str(widget['state']) != 'disabled':
                    focusable_list.append(widget)
            except (tk.TclError, KeyError):
                if widget.winfo_viewable():
                    focusable_list.append(widget)
        
        try:
            for child in widget.winfo_children():
                self._find_focusable_in_widget(child, focusable_list)
        except tk.TclError:
            pass
    
    def _handle_next_tab(self, event):
        """Manejar Ctrl+Tab - siguiente pestaña"""
        current_notebook = self._find_current_notebook()
        if current_notebook:
            self._notebook_next_tab(type('Event', (), {'widget': current_notebook})())
        return "break"
    
    def _handle_previous_tab(self, event):
        """Manejar Ctrl+Shift+Tab - pestaña anterior"""
        current_notebook = self._find_current_notebook()
        if current_notebook:
            self._notebook_previous_tab(type('Event', (), {'widget': current_notebook})())
        return "break"
    
    def _select_tab(self, tab_index):
        """Seleccionar pestaña por índice"""
        current_notebook = self._find_current_notebook()
        if current_notebook and tab_index < len(current_notebook.tabs()):
            current_notebook.select(tab_index)
            self._focus_first_widget_in_tab(current_notebook.nametowidget(current_notebook.select()))
        return "break"
    
    def _find_current_notebook(self):
        """Encontrar el notebook que está actualmente en foco o visible"""
        for notebook in self.notebooks:
            try:
                if notebook.winfo_viewable():
                    return notebook
            except tk.TclError:
                continue
        return None
    
    def _on_tab_changed(self, event):
        """Callback cuando cambia la pestaña"""
        self.root.after(100, self._refresh_current_tab_widgets)
    
    def _refresh_current_tab_widgets(self):
        """Refrescar widgets de la pestaña actual"""
        self._auto_discover_widgets()
    
    def _handle_tab(self, event):
        """Manejar Tab - siguiente widget"""
        if self._navigation_in_progress:
            return "break"
        
        try:
            self._navigation_in_progress = True
            if self._is_focus_in_notebook():
                self._focus_next_widget_in_current_tab()
            else:
                self._focus_next_widget_safe()
        finally:
            self._navigation_in_progress = False
        return "break"
    
    def _handle_shift_tab(self, event):
        """Manejar Shift+Tab - widget anterior"""
        if self._navigation_in_progress:
            return "break"
        
        try:
            self._navigation_in_progress = True
            if self._is_focus_in_notebook():
                self._focus_previous_widget_in_current_tab()
            else:
                self._focus_previous_widget_safe()
        finally:
            self._navigation_in_progress = False
        return "break"
    
    def _is_focus_in_notebook(self):
        """Verificar si el foco está dentro de un notebook"""
        current_widget = self.root.focus_get()
        if not current_widget:
            return False
        
        for notebook in self.notebooks:
            try:
                if self._is_widget_child_of(current_widget, notebook):
                    return True
            except tk.TclError:
                continue
        return False
    
    def _is_widget_child_of(self, widget, parent):
        """Verificar si un widget es hijo de otro"""
        if widget == parent:
            return True
        
        try:
            widget_parent = widget.winfo_parent()
            if not widget_parent:
                return False
            
            parent_widget = widget.nametowidget(widget_parent)
            return self._is_widget_child_of(parent_widget, parent)
        except tk.TclError:
            return False
    
    def _focus_next_widget_in_current_tab(self):
        """Enfocar siguiente widget en la pestaña actual"""
        current_notebook = self._find_current_notebook()
        if not current_notebook:
            self._focus_next_widget_safe()
            return
        
        current_tab = current_notebook.nametowidget(current_notebook.select())
        tab_widgets = []
        self._find_focusable_in_widget(current_tab, tab_widgets)
        
        if not tab_widgets:
            return
        
        current_widget = self.root.focus_get()
        if current_widget in tab_widgets:
            current_index = tab_widgets.index(current_widget)
            next_index = (current_index + 1) % len(tab_widgets)
            tab_widgets[next_index].focus_set()
        else:
            tab_widgets[0].focus_set()
    
    def _focus_previous_widget_in_current_tab(self):
        """Enfocar widget anterior en la pestaña actual"""
        current_notebook = self._find_current_notebook()
        if not current_notebook:
            self._focus_previous_widget_safe()
            return
        
        current_tab = current_notebook.nametowidget(current_notebook.select())
        tab_widgets = []
        self._find_focusable_in_widget(current_tab, tab_widgets)
        
        if not tab_widgets:
            return
        
        current_widget = self.root.focus_get()
        if current_widget in tab_widgets:
            current_index = tab_widgets.index(current_widget)
            previous_index = (current_index - 1) % len(tab_widgets)
            tab_widgets[previous_index].focus_set()
        else:
            tab_widgets[-1].focus_set()
    
    def _handle_enter(self, event):
        """Manejar Enter - activar widget mejorado"""
        current_widget = self.root.focus_get()
        
        if current_widget:
            if isinstance(current_widget, ttk.Notebook):
                self._notebook_activate_tab(type('Event', (), {'widget': current_widget})())
                return "break"
            
            self._activate_widget_enhanced(current_widget)
        return "break"
    
    def _handle_space(self, event):
        """Manejar Espacio - activar widget"""
        current_widget = self.root.focus_get()
        if current_widget:
            self._activate_widget_enhanced(current_widget)
        return "break"
    
    def _activate_widget_enhanced(self, widget):
        """Activar widget con detección mejorada"""
        try:
            if hasattr(widget, 'invoke'):
                widget.invoke()
                return
            
            if isinstance(widget, (tk.Button, ttk.Button)):
                widget.event_generate("<Button-1>")
                widget.event_generate("<ButtonRelease-1>")
                return
            
            if isinstance(widget, (tk.Entry, ttk.Entry)):
                widget.focus_set()
                return
            
            if isinstance(widget, ttk.Treeview):
                selection = widget.selection()
                if selection:
                    widget.event_generate("<<TreeviewSelect>>")
                return
            
            if isinstance(widget, ttk.Combobox):
                widget.event_generate("<Button-1>")
                return
                
        except (tk.TclError, AttributeError) as e:
            print(f"No se pudo activar widget: {e}")
    
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
    
    def show_keyboard_help(self):
        """Mostrar ventana de ayuda con atajos"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Atajos de Teclado - Ayuda")
        help_window.geometry("650x500")
        help_window.transient(self.root)
        help_window.grab_set()
        help_window.focus_set()
        
        help_text = """
🎮 GUÍA DE ATAJOS DE TECLADO

📋 NAVEGACIÓN BÁSICA:
• Tab                     → Siguiente control
• Shift + Tab             → Control anterior  
• Enter / Espacio         → Activar control seleccionado
• Escape                  → Cancelar acción

🗂️ NAVEGACIÓN EN PESTAÑAS:
• Ctrl + Tab              → Siguiente pestaña
• Ctrl + Shift + Tab      → Pestaña anterior
• Ctrl + 1,2,3,4,5        → Ir directamente a pestaña
• Flechas ←→ (en pestaña) → Cambiar pestaña
• Enter (en pestaña)      → Entrar al contenido

🔧 ATAJOS GLOBALES:
• F1                      → Mostrar esta ayuda
• Ctrl + Q                → Salir de la aplicación
• Ctrl + R                → Actualizar datos

🎯 EN TABLAS:
• Flechas ↑↓              → Navegar entre elementos
• Enter                   → Seleccionar/Ver detalles
• Page Up/Down            → Cambiar páginas

🎮 EN EL JUEGO:
• Flechas                 → Mover cursor
• Enter / Espacio         → Hacer movimiento
• Ctrl + R                → Reiniciar juego

💡 CONSEJOS:
• Los elementos enfocados se resaltan en azul
• Use Tab para navegar dentro de ventanas
• Los atajos funcionan en cada ventana por separado
• Presione F1 para ayuda en cualquier momento
        """
        
        text_frame = tk.Frame(help_window)
        text_frame.pack(expand=True, fill="both", padx=15, pady=15)
        
        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#f8f9fa",
            fg="#212529",
            padx=20,
            pady=20,
            state="disabled"
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.config(state="normal")
        text_widget.insert("1.0", help_text)
        text_widget.config(state="disabled")
        
        scrollbar.pack(side="right", fill="y")
        text_widget.pack(side="left", expand=True, fill="both")
        
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
        
        help_window.bind("<Escape>", lambda e: help_window.destroy())
        help_window.bind("<Return>", lambda e: help_window.destroy())
        help_window.bind("<F1>", lambda e: help_window.destroy())
    
    def register_focusable_widget(self, widget):
        """Registrar widget como focusable"""
        if widget not in self.focus_ring_widgets:
            self.focus_ring_widgets.append(widget)
            self._setup_widget_focus_events(widget)
    
    def _find_app_instance(self):
        """Encontrar la instancia de la aplicación principal"""
        if hasattr(self.root, 'logout') or hasattr(self.root, 'sync_data'):
            return self.root
        
        for widget in self.root.winfo_children():
            if hasattr(widget, 'logout') or hasattr(widget, 'sync_data'):
                return widget
        
        return None
    
    def _auto_discover_widgets(self):
        """Auto-descubrir widgets focusables"""
        self.focus_ring_widgets.clear()
        self._discover_widgets_recursive(self.root)
        
        for widget in self.focus_ring_widgets:
            self._setup_widget_focus_events(widget)
    
    def _discover_widgets_recursive(self, widget):
        """Descubrir widgets de forma recursiva"""
        focusable_types = (
            tk.Button, ttk.Button,
            tk.Entry, ttk.Entry,
            tk.Listbox, ttk.Treeview,
            tk.Text, tk.Checkbutton, ttk.Checkbutton,
            tk.Radiobutton, ttk.Radiobutton,
            ttk.Combobox, tk.Scale, ttk.Scale,
            ttk.Notebook
        )
        
        if isinstance(widget, focusable_types):
            try:
                if widget.winfo_viewable() and str(widget['state']) != 'disabled':
                    self.focus_ring_widgets.append(widget)
            except (tk.TclError, KeyError):
                if widget.winfo_viewable():
                    self.focus_ring_widgets.append(widget)
        
        try:
            for child in widget.winfo_children():
                self._discover_widgets_recursive(child)
        except tk.TclError:
            pass
    
    def _setup_widget_focus_events(self, widget):
        """Configurar eventos de foco para un widget"""
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
        
        widget.bind("<FocusIn>", lambda e: self._on_focus_in(e.widget), add="+")
        widget.bind("<FocusOut>", lambda e: self._on_focus_out(e.widget), add="+")
    
    def _on_focus_in(self, widget):
        """Widget recibe foco"""
        self.current_focus_widget = widget
        
        try:
            if 'bg' in widget.configure() and not isinstance(widget, ttk.Notebook):
                widget.configure(bg=self.focus_color)
            if 'highlightthickness' in widget.configure():
                widget.configure(highlightthickness=2, highlightcolor=self.focus_border_color)
        except tk.TclError:
            pass
    
    def _on_focus_out(self, widget):
        """Widget pierde foco - VERSIÓN MEJORADA QUE PRESERVA COLORES DE JUEGO"""
        if widget not in self.original_styles:
            return
        
        try:
            original = self.original_styles[widget]
            
            # IMPORTANTE: Verificar si el widget tiene un color de juego
            current_bg = widget.cget('bg')
            is_game_piece = (current_bg == "#3498db" or  # Azul (X)
                           current_bg == "#e74c3c" or   # Rojo (O)
                           current_bg == self.focus_color)  # Color de foco
            
            # Solo restaurar el color original si NO es una pieza del juego
            if ('bg' in original and 
                'bg' in widget.configure() and 
                not isinstance(widget, ttk.Notebook) and
                not is_game_piece):
                widget.configure(bg=original['bg'])
            elif (is_game_piece and 
                  current_bg == self.focus_color and
                  'bg' in original):
                # Si está enfocado pero tiene color original, restaurar
                widget.configure(bg=original['bg'])
            
            # Siempre restaurar el highlightthickness
            if ('highlightthickness' in original and 
                'highlightthickness' in widget.configure()):
                widget.configure(highlightthickness=original['highlightthickness'])
                
        except tk.TclError:
            pass
    
    def _focus_next_widget_safe(self):
        """Enfocar siguiente widget de forma segura sin recursión"""
        if not self.focus_ring_widgets:
            self._auto_discover_widgets()

        if not self.focus_ring_widgets:
            return

        attempts = 0
        while attempts < self._max_navigation_attempts:
            self.focus_index = (self.focus_index + 1) % len(self.focus_ring_widgets)
            widget = self.focus_ring_widgets[self.focus_index]

            if self._is_widget_focusable_safe(widget):
                try:
                    widget.focus_set()  # ← PROTEGER CON TRY-CATCH
                    return
                except tk.TclError:
                    # Widget destruido, continuar buscando
                    pass
                
            attempts += 1

        # Si no encuentra ningún widget focusable, refrescar lista
        self._auto_discover_widgets()
        
        # Si no encuentra ningún widget focusable, usar el primero disponible
        if self.focus_ring_widgets:
            self.focus_ring_widgets[0].focus_set()
    
    def _focus_previous_widget_safe(self):
        """Enfocar widget anterior de forma segura sin recursión"""
        if not self.focus_ring_widgets:
            self._auto_discover_widgets()
            
        if not self.focus_ring_widgets:
            return
        
        attempts = 0
        while attempts < self._max_navigation_attempts:
            self.focus_index = (self.focus_index - 1) % len(self.focus_ring_widgets)
            widget = self.focus_ring_widgets[self.focus_index]
            
            if self._is_widget_focusable_safe(widget):
                try:
                    widget.focus_set()  # ← PROTEGER CON TRY-CATCH
                    return
                except tk.TclError:
                    # Widget destruido, continuar buscando
                    pass
                
            attempts += 1
        
        # Si no encuentra ningún widget focusable, refrescar lista
        self._auto_discover_widgets()
    
    def _is_widget_focusable_safe(self, widget):
        """Verificar si un widget puede recibir foco de forma segura"""
        try:
            if not widget.winfo_exists():
                return False
            if not widget.winfo_viewable():
                return False
            
            # Verificar estado solo si el widget lo soporta
            try:
                state = str(widget['state'])
                return state != 'disabled'
            except (tk.TclError, KeyError):
                # Si no tiene estado, asumir que es focusable
                return True
                
        except tk.TclError:
            return False
    
    def _clear_focus(self):
        """Limpiar foco actual"""
        if self.current_focus_widget:
            try:
                self.root.focus_set()
            except tk.TclError:
                pass
        self.current_focus_widget = None
    
    def refresh_widgets(self):
        """Refrescar lista de widgets"""
        self._auto_discover_widgets()
        self._setup_notebook_navigation()
    
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
    CON PRESERVACIÓN DE COLORES DE FIGURAS
    """
    
    def __init__(self, root_window, game_instance=None):
        super().__init__(root_window)
        self.game = game_instance
        
        # Variables específicas del juego
        self.board_focus_row = 1
        self.board_focus_col = 1
        self.cell_focus_row = 1
        self.cell_focus_col = 1
        
        # Colores específicos del juego (para preservarlos)
        self.game_colors = {
            "#3498db": "X",  # Azul para X
            "#e74c3c": "O",  # Rojo para O
        }
        
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
        for widget in self._find_all_widgets(self.root):
            if isinstance(widget, tk.Label) and "Cursor:" in str(widget.cget('text')):
                self.cursor_label = widget
                return
        
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
    
    def _on_focus_out(self, widget):
        """VERSIÓN ESPECIAL PARA JUEGO - Preservar colores de figuras X y O"""
        if widget not in self.original_styles:
            return
        
        try:
            original = self.original_styles[widget]
            current_bg = widget.cget('bg')
            
            # Verificar si es un botón con una figura del juego
            is_game_piece = current_bg in self.game_colors
            is_focus_color = current_bg == self.focus_color
            
            # Solo restaurar si:
            # 1. NO es una pieza del juego (X o O)
            # 2. O si está con color de foco pero originalmente era neutro
            if ('bg' in original and 
                'bg' in widget.configure() and 
                not isinstance(widget, ttk.Notebook)):
                
                if not is_game_piece:
                    # No es pieza del juego, restaurar color original
                    widget.configure(bg=original['bg'])
                elif is_focus_color and original['bg'] not in self.game_colors:
                    # Está enfocado pero originalmente era neutro
                    widget.configure(bg=original['bg'])
                # Si es pieza del juego, NO cambiar el color
            
            # Siempre restaurar el highlightthickness
            if ('highlightthickness' in original and 
                'highlightthickness' in widget.configure()):
                widget.configure(highlightthickness=original['highlightthickness'])
                
        except tk.TclError:
            pass
    
    def _on_focus_in(self, widget):
        """VERSIÓN ESPECIAL PARA JUEGO - No cambiar color si ya es pieza"""
        self.current_focus_widget = widget
        
        try:
            current_bg = widget.cget('bg')
            is_game_piece = current_bg in self.game_colors
            
            # Solo aplicar color de foco si NO es una pieza del juego
            if ('bg' in widget.configure() and 
                not isinstance(widget, ttk.Notebook) and
                not is_game_piece):
                widget.configure(bg=self.focus_color)
            
            # Siempre aplicar el borde de foco
            if 'highlightthickness' in widget.configure():
                widget.configure(highlightthickness=2, highlightcolor=self.focus_border_color)
                
        except tk.TclError:
            pass
    
    def _activate_widget_enhanced(self, widget):
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
        super()._activate_widget_enhanced(widget)


# =============================================================================
# FUNCIONES DE INTEGRACIÓN CORREGIDAS
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
    accessibility_manager = AccessibilityManager(app_instance)
    app_instance.accessibility_manager = accessibility_manager
    return accessibility_manager


def add_game_accessibility(game_window, game_instance):
    """
    Añadir accesibilidad específica para el juego
    
    Args:
        game_window: Ventana del juego (tk.Toplevel)
        game_instance: Instancia del juego UltimateTicTacToe
    
    Returns:
        GameAccessibilityManager instance
    """
    game_accessibility = GameAccessibilityManager(game_window, game_instance)
    game_instance.accessibility_manager = game_accessibility
    
    # Hacer que la ventana del juego tome el foco
    game_window.focus_force()
    game_window.lift()
    
    return game_accessibility


# =============================================================================
# INSTRUCCIONES DE INTEGRACIÓN FINALES
# =============================================================================

"""
🔧 CAMBIOS REALIZADOS PARA SOLUCIONAR LOS PROBLEMAS:

1. **RECURSIÓN INFINITA SOLUCIONADA:**
   ✅ Añadido control de navegación con _navigation_in_progress
   ✅ Métodos _focus_next_widget_safe() y _focus_previous_widget_safe()
   ✅ Límite máximo de intentos de navegación (_max_navigation_attempts)
   ✅ Verificación segura de widgets focusables

2. **PRESERVACIÓN DE COLORES DE FIGURAS:**
   ✅ Detección de colores de juego (#3498db para X, #e74c3c para O)
   ✅ _on_focus_out() mejorado que NO restaura colores de piezas
   ✅ _on_focus_in() que NO aplica color de foco a piezas existentes
   ✅ Lógica especial en GameAccessibilityManager

3. **GESTIÓN MEJORADA DE ERRORES:**
   ✅ Manejo seguro de widgets destruidos
   ✅ Protección contra errores de Tkinter
   ✅ Verificaciones de existencia de widgets

INSTRUCCIONES DE INTEGRACIÓN:

1. REEMPLAZA tu accessibility_manager.py con este código
2. En tu APLICACION_COMPLETA.PY, asegúrate de tener:

```python
# Al principio del archivo
from accessibility_manager import add_accessibility_to_app, add_game_accessibility

# En App.__init__() - AL FINAL
class App(tk.Tk):
    def __init__(self, session=None):
        # ... todo tu código original ...
        self.show_login()
        self.accessibility_manager = add_accessibility_to_app(self)

# En UltimateTicTacToe.__init__() - AL FINAL  
class UltimateTicTacToe:
    def __init__(self, root, session=None, player1_id=None, player2_id=None):
        # ... todo tu código original ...
        self.create_boards()
        self.accessibility_manager = add_game_accessibility(self.root, self)
```

3. ELIMINA cualquier línea que llame a _update_game_focus() en make_move

RESULTADOS ESPERADOS:
✅ No más errores de recursión en consola
✅ Las figuras X y O mantienen sus colores (azul/rojo)
✅ El foco se ve pero no interfiere con el juego
✅ Navegación fluida sin loops infinitos
✅ Ventanas independientes con navegación separada

¡Esto debería solucionar completamente ambos problemas!
"""

# =============================================================================
# DEMO PARA PROBAR LA PRESERVACIÓN DE COLORES
# =============================================================================

if __name__ == "__main__":
    # Test de preservación de colores en botones
    
    root = tk.Tk()
    root.title("Test Preservación de Colores")
    root.geometry("400x300")
    
    tk.Label(root, text="Test de Preservación de Colores", font=("Arial", 16)).pack(pady=20)
    
    # Crear botones con colores de juego
    frame = tk.Frame(root)
    frame.pack(pady=20)
    
    # Botón X (azul)
    btn_x = tk.Button(frame, text="X", bg="#3498db", fg="white", width=5, height=2, font=("Arial", 14, "bold"))
    btn_x.pack(side="left", padx=5)
    
    # Botón O (rojo)
    btn_o = tk.Button(frame, text="O", bg="#e74c3c", fg="white", width=5, height=2, font=("Arial", 14, "bold"))
    btn_o.pack(side="left", padx=5)
    
    # Botón normal
    btn_normal = tk.Button(frame, text="Normal", width=8, height=2)
    btn_normal.pack(side="left", padx=5)
    
    # Hacer accesible
    accessibility = make_accessible(root)
    
    instructions = tk.Label(
        root, 
        text="Use Tab para navegar. Los botones X y O deben mantener sus colores.",
        fg="gray",
        wraplength=350
    )
    instructions.pack(pady=20)
    
    root.mainloop()