# =============================================================================
# ACCESSIBILITY MANAGER V2.0 - CON SOPORTE COMPLETO PARA TABS
# Solución específica para pestañas de ttk.Notebook y botones problemáticos
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import time

class AccessibilityManager:
    """
    Gestor de accesibilidad mejorado con soporte completo para tabs y botones
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
        
        # Navegación específica para tabs
        self.root.bind_all("<Control-Tab>", self._handle_next_tab)
        self.root.bind_all("<Control-Shift-Tab>", self._handle_previous_tab)
        self.root.bind_all("<Control-1>", lambda e: self._select_tab(0))
        self.root.bind_all("<Control-2>", lambda e: self._select_tab(1))
        self.root.bind_all("<Control-3>", lambda e: self._select_tab(2))
        self.root.bind_all("<Control-4>", lambda e: self._select_tab(3))
        self.root.bind_all("<Control-5>", lambda e: self._select_tab(4))
        
        # Atajos de aplicación
        self.root.bind_all("<F1>", self._show_help)
        self.root.bind_all("<Control-q>", self._handle_quit)
        self.root.bind_all("<Control-r>", self._handle_refresh)
        
        # Auto-descubrir widgets focusables
        self.root.after(500, self._auto_discover_widgets)
        
        # Configurar eventos especiales para notebooks
        self.root.after(600, self._setup_notebook_navigation)
    
    def _setup_notebook_navigation(self):
        """Configurar navegación específica para notebooks (pestañas)"""
        self.notebooks = []
        self._find_notebooks(self.root)
        
        for notebook in self.notebooks:
            # Configurar eventos específicos del notebook
            notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
            
            # Hacer el notebook focusable
            notebook.focus_set()
            
            # Configurar eventos de teclado específicos
            notebook.bind("<Left>", self._notebook_previous_tab)
            notebook.bind("<Right>", self._notebook_next_tab)
            notebook.bind("<Return>", self._notebook_activate_tab)
            notebook.bind("<space>", self._notebook_activate_tab)
    
    def _find_notebooks(self, widget):
        """Encontrar todos los notebooks recursivamente"""
        if isinstance(widget, ttk.Notebook):
            self.notebooks.append(widget)
            # Hacer el notebook focusable y registrarlo
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
        # Enfocar el primer widget dentro de la pestaña activa
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
        """Seleccionar pestaña por índice (Ctrl+1, Ctrl+2, etc.)"""
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
        notebook = event.widget
        # Refrescar widgets cuando cambia la pestaña
        self.root.after(100, self._refresh_current_tab_widgets)
    
    def _refresh_current_tab_widgets(self):
        """Refrescar widgets de la pestaña actual"""
        self._auto_discover_widgets()
    
    def _handle_tab(self, event):
        """Manejar Tab - siguiente widget"""
        # Si estamos en un notebook, usar navegación especial
        if self._is_focus_in_notebook():
            self._focus_next_widget_in_current_tab()
        else:
            self._focus_next_widget()
        return "break"
    
    def _handle_shift_tab(self, event):
        """Manejar Shift+Tab - widget anterior"""
        if self._is_focus_in_notebook():
            self._focus_previous_widget_in_current_tab()
        else:
            self._focus_previous_widget()
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
            self._focus_next_widget()
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
            self._focus_previous_widget()
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
            # Casos especiales
            if isinstance(current_widget, ttk.Notebook):
                self._notebook_activate_tab(type('Event', (), {'widget': current_widget})())
                return "break"
            
            # Para botones y widgets activables
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
            # Intentar invoke primero
            if hasattr(widget, 'invoke'):
                widget.invoke()
                return
            
            # Para botones que no tienen invoke, simular click
            if isinstance(widget, (tk.Button, ttk.Button)):
                widget.event_generate("<Button-1>")
                widget.event_generate("<ButtonRelease-1>")
                return
            
            # Para Entry, simplemente darle foco
            if isinstance(widget, (tk.Entry, ttk.Entry)):
                widget.focus_set()
                return
            
            # Para Treeview, generar evento de selección
            if isinstance(widget, ttk.Treeview):
                selection = widget.selection()
                if selection:
                    widget.event_generate("<<TreeviewSelect>>")
                return
            
            # Para Combobox, expandir lista
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
        """Mostrar ayuda de teclado mejorada"""
        self.show_keyboard_help_enhanced()
        return "break"
    
    def show_keyboard_help_enhanced(self):
        """Mostrar ventana de ayuda mejorada con soporte para tabs"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Atajos de Teclado - Guía Completa")
        help_window.geometry("700x600")
        help_window.transient(self.root)
        help_window.grab_set()
        help_window.focus_set()
        
        # Contenido de ayuda mejorado
        help_text = """
🎮 GUÍA COMPLETA DE ATAJOS DE TECLADO

📋 NAVEGACIÓN BÁSICA:
• Tab                     → Siguiente control
• Shift + Tab             → Control anterior  
• Enter / Espacio         → Activar control seleccionado
• Escape                  → Cancelar acción

🗂️ NAVEGACIÓN EN PESTAÑAS:
• Ctrl + Tab              → Siguiente pestaña
• Ctrl + Shift + Tab      → Pestaña anterior
• Ctrl + 1,2,3,4,5        → Ir directamente a pestaña (1-5)
• Flechas ←→ (en pestaña) → Cambiar pestaña
• Enter (en pestaña)      → Entrar al contenido de la pestaña

🔧 ATAJOS GLOBALES:
• F1                      → Mostrar esta ayuda
• Ctrl + Q                → Salir de la aplicación
• Ctrl + R                → Actualizar/Refrescar datos

🎯 EN TABLAS Y LISTAS:
• Flechas ↑↓              → Navegar entre elementos
• Enter                   → Seleccionar/Ver detalles
• Letras A-Z              → Búsqueda rápida
• Page Up/Down            → Páginas anterior/siguiente

🎮 EN EL JUEGO:
• Flechas                 → Mover cursor en tablero
• Ctrl + Flechas          → Cambiar entre tableros
• Enter / Espacio         → Hacer movimiento
• Números 1-9             → Selección rápida de celda
• Ctrl + R                → Reiniciar juego

💡 CONSEJOS AVANZADOS:
• Los elementos enfocados se resaltan en azul
• Use Tab dentro de pestañas para navegar contenido
• Use Ctrl+Tab para cambiar entre pestañas rápidamente
• Enter funciona en todos los botones y controles
• Los atajos funcionan desde cualquier lugar

🚀 FLUJO DE TRABAJO RECOMENDADO:
1. Use Ctrl+1,2,3,4 para ir directamente a pestañas
2. Use Tab para navegar dentro del contenido
3. Use Enter para activar botones y controles
4. Use Escape para cancelar o volver atrás
5. Use F1 si necesita ayuda en cualquier momento

⚡ SOLUCIÓN DE PROBLEMAS:
• Si Enter no funciona, pruebe Espacio
• Si no puede navegar, presione Tab varias veces
• Si está perdido, presione Escape y comience de nuevo
• Use F1 para esta ayuda desde cualquier lugar
        """
        
        # Frame para el texto
        text_frame = tk.Frame(help_window)
        text_frame.pack(expand=True, fill="both", padx=15, pady=15)
        
        # Widget de texto con scroll
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
            ttk.Notebook  # Incluir notebooks
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
        """Widget pierde foco"""
        if widget in self.original_styles:
            try:
                original = self.original_styles[widget]
                if 'bg' in original and 'bg' in widget.configure() and not isinstance(widget, ttk.Notebook):
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


# =============================================================================
# FUNCIONES DE INTEGRACIÓN ACTUALIZADAS
# =============================================================================

def make_accessible(window, game_instance=None):
    """Función simple para hacer accesible cualquier ventana Tkinter"""
    return AccessibilityManager(window)

def add_accessibility_to_app(app_instance):
    """Añadir accesibilidad a una aplicación existente"""
    accessibility_manager = AccessibilityManager(app_instance)
    app_instance.accessibility_manager = accessibility_manager
    return accessibility_manager

def add_game_accessibility(game_window, game_instance):
    """Añadir accesibilidad específica para el juego"""
    # Para el juego, usar el AccessibilityManager base que ya incluye todo
    game_accessibility = AccessibilityManager(game_window)
    game_instance.accessibility_manager = game_accessibility
    return game_accessibility


# =============================================================================
# EJEMPLO DE USO Y TESTING
# =============================================================================

if __name__ == "__main__":
    # Demo con pestañas para probar la funcionalidad
    root = tk.Tk()
    root.title("Demo Accesibilidad con Tabs")
    root.geometry("600x400")
    
    # Crear notebook con pestañas
    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both", padx=10, pady=10)
    
    # Pestaña 1
    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text="Pestaña 1")
    tk.Label(tab1, text="Contenido de Pestaña 1", font=("Arial", 14)).pack(pady=20)
    tk.Button(tab1, text="Botón 1A").pack(pady=5)
    tk.Button(tab1, text="Botón 1B").pack(pady=5)
    
    # Pestaña 2
    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text="Pestaña 2")
    tk.Label(tab2, text="Contenido de Pestaña 2", font=("Arial", 14)).pack(pady=20)
    tk.Button(tab2, text="Botón 2A").pack(pady=5)
    tk.Entry(tab2).pack(pady=5)
    tk.Button(tab2, text="Botón 2B").pack(pady=5)
    
    # Pestaña 3
    tab3 = ttk.Frame(notebook)
    notebook.add(tab3, text="Pestaña 3")
    tk.Label(tab3, text="Contenido de Pestaña 3", font=("Arial", 14)).pack(pady=20)
    tk.Button(tab3, text="Botón 3A").pack(pady=5)
    
    # Hacer accesible
    accessibility = make_accessible(root)
    
    # Instrucciones
    instructions = tk.Label(
        root, 
        text="Prueba: F1=Ayuda, Tab=Navegar, Ctrl+Tab=Cambiar pestañas, Enter=Activar",
        fg="gray"
    )
    instructions.pack(side="bottom", pady=5)
    
    root.mainloop()