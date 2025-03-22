import tkinter as tk
from tkinter import ttk, messagebox, StringVar, BooleanVar, IntVar
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime, timedelta
import os
import re
from tkinter import font as tkfont
from groq import Groq
import random
import json

# Configuración de la API de Groq
client = Groq(api_key="GROQ_API_KEY")

# Constantes para colores
COLOR_AZUL = "#3498db"
COLOR_VERDE = "#2ecc71"
COLOR_ROJO = "#e74c3c"
COLOR_NARANJA = "#f39c12"
COLOR_GRIS = "#95a5a6"
COLOR_GRIS_CLARO = "#f9f9f9"
COLOR_BLANCO = "#ffffff"

# Clase para validaciones
class Validaciones:
    """
    Clase que proporciona métodos de validación para los diferentes campos de la aplicación.
    """
    @staticmethod
    def validar_texto_no_vacio(texto):
        """
        Valida que un texto no esté vacío.
        
        Args:
            texto (str): El texto a validar
            
        Returns:
            bool: True si el texto no está vacío, False en caso contrario
        """
        return bool(texto and texto.strip())
    
    @staticmethod
    def validar_fecha_futura(fecha):
        """
        Valida que una fecha sea futura.
        
        Args:
            fecha (datetime.date): La fecha a validar
            
        Returns:
            bool: True si la fecha es futura, False en caso contrario
        """
        return fecha >= datetime.now().date()
    
    @staticmethod
    def validar_alfanumerico(texto):
        """
        Valida que un texto solo contenga caracteres alfanuméricos.
        
        Args:
            texto (str): El texto a validar
            
        Returns:
            bool: True si el texto solo contiene caracteres alfanuméricos, False en caso contrario
        """
        return bool(re.match(r'^[a-zA-Z0-9\s,]+$', texto))
    
    @staticmethod
    def validar_tarea_duplicada(crud, titulo, tarea_id=None):
        """
        Valida que no exista una tarea con el mismo título.
        
        Args:
            crud (CRUDExcel): Instancia del gestor de Excel
            titulo (str): El título a validar
            tarea_id (int, optional): ID de la tarea actual (para edición)
            
        Returns:
            bool: True si no existe una tarea con el mismo título, False en caso contrario
        """
        tareas_df = crud.read('Tareas')
        if tareas_df.empty:
            return True
        
        # Filtrar por título (case insensitive)
        tareas_mismo_titulo = tareas_df[tareas_df['Título'].str.lower() == titulo.lower()]
        
        # Si estamos editando, excluir la tarea actual
        if tarea_id is not None:
            tareas_mismo_titulo = tareas_mismo_titulo[tareas_mismo_titulo['ID'] != tarea_id]
        
        return tareas_mismo_titulo.empty

# Clase para crear tooltips mejorada
class ToolTip:
    """
    Clase para crear tooltips en widgets de Tkinter.
    """
    def __init__(self, widget, text):
        """
        Inicializa un tooltip para un widget.
        
        Args:
            widget: El widget al que se asociará el tooltip
            text (str): El texto del tooltip
        """
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        """Muestra el tooltip cuando el cursor entra en el widget."""
        # Obtener la posición del widget
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        
        # Crear una ventana emergente
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tooltip, 
            text=self.text, 
            background="#ffffe0", 
            relief="solid", 
            borderwidth=1,
            font=("Arial", 9),
            padx=5,
            pady=2
        )
        label.pack()
    
    def hide_tooltip(self, event=None):
        """Oculta el tooltip cuando el cursor sale del widget."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

# Clase para gestionar el archivo Excel
class CRUDExcel:
    """
    Clase para gestionar operaciones CRUD en un archivo Excel.
    """
    def __init__(self, file_path):
        """
        Inicializa el gestor de Excel.
        
        Args:
            file_path (str): Ruta del archivo Excel
        """
        self.file_path = file_path
        # Crear el archivo Excel si no existe
        if not os.path.exists(file_path):
            self.create_excel_file()
    
    def create_excel_file(self):
        """Crea un archivo Excel con las hojas y datos iniciales."""
        # Crear un DataFrame vacío para cada hoja
        tareas_df = pd.DataFrame(columns=[
            'ID', 'Título', 'Descripción', 'Fecha de Vencimiento', 
            'Prioridad', 'Categoría', 'Etiquetas', 'Estado',
            'Fecha de Creación', 'Última Actualización'
        ])
        
        categorias_df = pd.DataFrame(columns=['ID', 'Nombre'])
        
        # Agregar algunas categorías por defecto
        categorias_default = [
            {'ID': 1, 'Nombre': 'Trabajo'},
            {'ID': 2, 'Nombre': 'Personal'},
            {'ID': 3, 'Nombre': 'Estudio'}
        ]
        categorias_df = pd.DataFrame(categorias_default)
        
        # Crear un ExcelWriter para guardar los DataFrames en diferentes hojas
        with pd.ExcelWriter(self.file_path) as writer:
            tareas_df.to_excel(writer, sheet_name='Tareas', index=False)
            categorias_df.to_excel(writer, sheet_name='Categorías', index=False)
    
    def read(self, sheet_name, filter_by=None):
        """
        Lee datos de una hoja de Excel con filtros opcionales.
        
        Args:
            sheet_name (str): Nombre de la hoja
            filter_by (dict, optional): Diccionario con filtros {columna: valor}
            
        Returns:
            pandas.DataFrame: DataFrame con los datos leídos
        """
        try:
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)
            
            if filter_by:
                # Aplicar filtros si se proporcionan
                for column, value in filter_by.items():
                    df = df[df[column] == value]
            
            return df
        except Exception as e:
            print(f"Error al leer datos: {e}")
            return pd.DataFrame()
    
    def create(self, sheet_name, data):
        """
        Crea un nuevo registro en una hoja de Excel.
        
        Args:
            sheet_name (str): Nombre de la hoja
            data (dict): Datos a insertar
            
        Returns:
            int: ID del nuevo registro o None si hay error
        """
        try:
            # Leer la hoja existente
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)
            
            # Generar un nuevo ID
            if 'ID' in df.columns and not df.empty:
                new_id = df['ID'].max() + 1
            else:
                new_id = 1
            
            # Agregar el ID al diccionario de datos
            data['ID'] = new_id
            
            # Agregar la nueva fila
            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
            
            # Guardar todas las hojas
            with pd.ExcelWriter(self.file_path, mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return new_id
        except Exception as e:
            print(f"Error al crear datos: {e}")
            return None
    
    def update(self, sheet_name, filter_by, updates):
        """
        Actualiza registros en una hoja de Excel.
        
        Args:
            sheet_name (str): Nombre de la hoja
            filter_by (dict): Diccionario con filtros {columna: valor}
            updates (dict): Diccionario con actualizaciones {columna: nuevo_valor}
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Leer la hoja existente
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)
            
            # Encontrar las filas que coinciden con el filtro
            mask = pd.Series(True, index=df.index)
            for column, value in filter_by.items():
                mask = mask & (df[column] == value)
            
            # Actualizar los valores
            for column, value in updates.items():
                df.loc[mask, column] = value
            
            # Guardar todas las hojas
            with pd.ExcelWriter(self.file_path, mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return True
        except Exception as e:
            print(f"Error al actualizar datos: {e}")
            return False
    
    def delete(self, sheet_name, filter_by):
        """
        Elimina registros de una hoja de Excel.
        
        Args:
            sheet_name (str): Nombre de la hoja
            filter_by (dict): Diccionario con filtros {columna: valor}
            
        Returns:
            bool: True si la eliminación fue exitosa, False en caso contrario
        """
        try:
            # Leer la hoja existente
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)
            
            # Encontrar las filas que coinciden con el filtro
            mask = pd.Series(True, index=df.index)
            for column, value in filter_by.items():
                mask = mask & (df[column] == value)
            
            # Eliminar las filas
            df = df[~mask]
            
            # Guardar todas las hojas
            with pd.ExcelWriter(self.file_path, mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return True
        except Exception as e:
            print(f"Error al eliminar datos: {e}")
            return False

# Clase base para ventanas
class BaseWindow(tk.Toplevel):
    """
    Clase base para todas las ventanas de la aplicación.
    """
    def __init__(self, parent, title, width=600, height=500):  # Aumentado el height por defecto
        """
        Inicializa una ventana base.
        
        Args:
            parent: Ventana padre
            title (str): Título de la ventana
            width (int, optional): Ancho de la ventana
            height (int, optional): Alto de la ventana
        """
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(True, True)
        self.configure(bg=COLOR_BLANCO)
        
        # Centrar la ventana
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"+{x}+{y}")
        
        # Crear un frame para el título
        self.title_frame = tk.Frame(self, bg=COLOR_AZUL, height=50)
        self.title_frame.pack(fill=tk.X)
        
        # Título de la ventana
        self.title_label = tk.Label(
            self.title_frame, 
            text=title, 
            font=("Arial", 16, "bold"), 
            bg=COLOR_AZUL, 
            fg=COLOR_BLANCO,
            pady=10
        )
        self.title_label.pack()
        
        # Frame principal para el contenido
        self.main_frame = tk.Frame(self, bg=COLOR_BLANCO)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    def create_button(self, parent, text, command, bg_color, fg_color=COLOR_BLANCO, width=10):
        """
        Crea un botón con estilo consistente.
        
        Args:
            parent: Widget padre
            text (str): Texto del botón
            command: Función a ejecutar al hacer clic
            bg_color (str): Color de fondo
            fg_color (str, optional): Color del texto
            width (int, optional): Ancho del botón
            
        Returns:
            tk.Button: El botón creado
        """
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=fg_color,
            font=("Arial", 10),
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=5,
            width=width
        )
        return button

# Ventana para agregar/editar tarea
class TaskWindow(BaseWindow):
    """
    Ventana para agregar o editar una tarea.
    """
    def __init__(self, parent, crud, categories, task_id=None, callback=None):
        """
        Inicializa la ventana de tarea.
        
        Args:
            parent: Ventana padre
            crud (CRUDExcel): Instancia del gestor de Excel
            categories (list): Lista de categorías disponibles
            task_id (int, optional): ID de la tarea a editar
            callback (function, optional): Función a llamar al guardar
        """
        self.crud = crud
        self.categories = categories
        self.task_id = task_id
        self.callback = callback
        self.validaciones = Validaciones()
        
        # Determinar si es edición o nueva tarea
        is_edit = task_id is not None
        title = "Editar Tarea" if is_edit else "Agregar Nueva Tarea"
        
        super().__init__(parent, title, width=600, height=600)  # Aumentado el height
        
        # Variables para el formulario
        self.title_var = StringVar()
        self.description_var = StringVar()
        self.priority_var = StringVar(value="Media")
        self.category_var = StringVar()
        self.tags_var = StringVar()
        self.status_var = StringVar(value="Pendiente")
        
        # Crear el formulario
        self.create_form()
        
        # Si es edición, cargar los datos de la tarea
        if is_edit:
            self.load_task_data()
    
    def create_form(self):
        """Crea el formulario para agregar o editar una tarea."""
        # Título
        tk.Label(
            self.main_frame, 
            text="Título: *", 
            font=("Arial", 11), 
            bg=COLOR_BLANCO, 
            anchor="w"
        ).pack(fill=tk.X, pady=(0, 5))
        
        title_entry = tk.Entry(
            self.main_frame, 
            textvariable=self.title_var, 
            font=("Arial", 11),
            relief=tk.SOLID,
            borderwidth=1
        )
        title_entry.pack(fill=tk.X, pady=(0, 15), ipady=5)
        ToolTip(title_entry, "Ingrese un título descriptivo para la tarea")
        
        # Descripción
        tk.Label(
            self.main_frame, 
            text="Descripción:", 
            font=("Arial", 11), 
            bg=COLOR_BLANCO, 
            anchor="w"
        ).pack(fill=tk.X, pady=(0, 5))
        
        description_text = tk.Text(
            self.main_frame, 
            height=5, 
            font=("Arial", 11),
            relief=tk.SOLID,
            borderwidth=1
        )
        description_text.pack(fill=tk.X, pady=(0, 15))
        ToolTip(description_text, "Describa los detalles de la tarea (opcional)")
        
        # Vincular Text con StringVar
        def update_description(*args):
            self.description_var.set(description_text.get("1.0", "end-1c"))
        
        description_text.bind("<KeyRelease>", update_description)
        
        # Frame para fecha y prioridad
        date_priority_frame = tk.Frame(self.main_frame, bg=COLOR_BLANCO)
        date_priority_frame.pack(fill=tk.X, pady=(0, 15))
        date_priority_frame.columnconfigure(0, weight=1)
        date_priority_frame.columnconfigure(1, weight=1)
        
        # Fecha de vencimiento
        tk.Label(
            date_priority_frame, 
            text="Fecha de Vencimiento:", 
            font=("Arial", 11), 
            bg=COLOR_BLANCO, 
            anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.due_date = DateEntry(
            date_priority_frame, 
            width=15, 
            background=COLOR_AZUL,
            foreground=COLOR_BLANCO,
            borderwidth=0,
            date_pattern='dd/mm/yyyy',
            font=("Arial", 11)
        )
        self.due_date.grid(row=1, column=0, sticky="w", padx=(0, 10))
        ToolTip(self.due_date, "Seleccione la fecha límite para completar la tarea")
        
        # Checkbox para sin fecha
        self.use_date_var = BooleanVar(value=False)
        no_date_check = tk.Checkbutton(
            date_priority_frame, 
            text="Sin fecha", 
            variable=self.use_date_var, 
            command=self.toggle_date,
            bg=COLOR_BLANCO,
            font=("Arial", 10)
        )
        no_date_check.grid(row=1, column=0, sticky="e", padx=(0, 20))
        ToolTip(no_date_check, "Marque esta opción si la tarea no tiene fecha límite")
        
        # Prioridad
        tk.Label(
            date_priority_frame, 
            text="Prioridad: *", 
            font=("Arial", 11), 
            bg=COLOR_BLANCO, 
            anchor="w"
        ).grid(row=0, column=1, sticky="w", pady=(0, 5))
        
        priority_combo = ttk.Combobox(
            date_priority_frame, 
            textvariable=self.priority_var, 
            values=["Alta", "Media", "Baja"], 
            state="readonly",
            font=("Arial", 11),
            width=18
        )
        priority_combo.grid(row=1, column=1, sticky="w")
        priority_combo.current(1)  # Por defecto "Media"
        ToolTip(priority_combo, "Seleccione la prioridad de la tarea")
        
        # Frame para categoría y etiquetas
        cat_tags_frame = tk.Frame(self.main_frame, bg=COLOR_BLANCO)
        cat_tags_frame.pack(fill=tk.X, pady=(0, 15))
        cat_tags_frame.columnconfigure(0, weight=1)
        cat_tags_frame.columnconfigure(1, weight=1)
        
        # Categoría
        tk.Label(
            cat_tags_frame, 
            text="Categoría: *", 
            font=("Arial", 11), 
            bg=COLOR_BLANCO, 
            anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.category_combo = ttk.Combobox(
            cat_tags_frame, 
            textvariable=self.category_var, 
            values=[cat["Nombre"] for cat in self.categories], 
            state="readonly",
            font=("Arial", 11),
            width=18
        )
        self.category_combo.grid(row=1, column=0, sticky="w", padx=(0, 10))
        ToolTip(self.category_combo, "Seleccione la categoría a la que pertenece la tarea")
        
        # Etiquetas
        tk.Label(
            cat_tags_frame, 
            text="Etiquetas:", 
            font=("Arial", 11), 
            bg=COLOR_BLANCO, 
            anchor="w"
        ).grid(row=0, column=1, sticky="w", pady=(0, 5))
        
        tags_entry = tk.Entry(
            cat_tags_frame, 
            textvariable=self.tags_var, 
            font=("Arial", 11),
            relief=tk.SOLID,
            borderwidth=1
        )
        tags_entry.grid(row=1, column=1, sticky="ew")
        ToolTip(tags_entry, "Ingrese etiquetas separadas por comas (opcional)")
        
        # Estado (solo visible al editar)
        if self.task_id is not None:
            status_frame = tk.Frame(self.main_frame, bg=COLOR_BLANCO)
            status_frame.pack(fill=tk.X, pady=(0, 15))
            
            tk.Label(
                status_frame, 
                text="Estado:", 
                font=("Arial", 11), 
                bg=COLOR_BLANCO, 
                anchor="w"
            ).pack(anchor="w", pady=(0, 5))
            
            status_combo = ttk.Combobox(
                status_frame, 
                textvariable=self.status_var, 
                values=["Pendiente", "En Progreso", "Completada"], 
                state="readonly",
                font=("Arial", 11),
                width=18
            )
            status_combo.pack(anchor="w")
            ToolTip(status_combo, "Seleccione el estado actual de la tarea")
        
        # Campos obligatorios
        tk.Label(
            self.main_frame, 
            text="* Campos obligatorios", 
            font=("Arial", 10), 
            fg=COLOR_ROJO,
            bg=COLOR_BLANCO, 
            anchor="w"
        ).pack(fill=tk.X, pady=(0, 15))
        
        # Botones
        buttons_frame = tk.Frame(self.main_frame, bg=COLOR_BLANCO)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        cancel_button = self.create_button(
            buttons_frame, 
            "Cancelar", 
            self.destroy, 
            COLOR_ROJO
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
        ToolTip(cancel_button, "Cerrar sin guardar cambios")
        
        save_button = self.create_button(
            buttons_frame, 
            "Guardar", 
            self.save_task, 
            COLOR_VERDE
        )
        save_button.pack(side=tk.RIGHT, padx=5)
        ToolTip(save_button, "Guardar la tarea")
    
    def toggle_date(self):
        """Activa o desactiva el selector de fecha según el checkbox."""
        if self.use_date_var.get():
            self.due_date.config(state="disabled")
        else:
            self.due_date.config(state="normal")
    
    def load_task_data(self):
        """Carga los datos de una tarea existente en el formulario."""
        # Obtener la tarea desde Excel
        task_df = self.crud.read('Tareas', {'ID': self.task_id})
        
        if task_df.empty:
            return
        
        # Obtener la primera fila
        task = task_df.iloc[0]
        
        # Llenar el formulario
        self.title_var.set(task['Título'])
        
        # Descripción en el Text widget
        description = task['Descripción'] if pd.notna(task['Descripción']) else ''
        self.main_frame.children['!text'].delete("1.0", tk.END)
        self.main_frame.children['!text'].insert("1.0", description)
        self.description_var.set(description)
        
        # Fecha
        if pd.isna(task['Fecha de Vencimiento']):
            self.use_date_var.set(True)
            self.due_date.config(state="disabled")
        else:
            self.use_date_var.set(False)
            self.due_date.config(state="normal")
            self.due_date.set_date(task['Fecha de Vencimiento'])
        
        self.priority_var.set(task['Prioridad'])
        self.category_var.set(task['Categoría'])
        self.tags_var.set(task['Etiquetas'] if pd.notna(task['Etiquetas']) else '')
        self.status_var.set(task['Estado'])
    
    def validate_form(self):
        """
        Valida el formulario de tarea.

        Returns:
            list: Lista de errores encontrados
        """
        errors = []

        # Validar título
        if not Validaciones.validar_texto_no_vacio(self.title_var.get()):
            errors.append("El título de la tarea es obligatorio.")

        # Validar fecha
        if not self.use_date_var.get():
            selected_date = self.due_date.get_date()
            if not Validaciones.validar_fecha_futura(selected_date):
                errors.append("La fecha debe ser futura.")

        # Validar prioridad
        if not self.priority_var.get():
            errors.append("Por favor, selecciona la prioridad.")

        # Validar categoría
        if not self.category_var.get():
            errors.append("Por favor, selecciona la categoría.")

        # Validar etiquetas (solo caracteres alfanuméricos)
        if self.tags_var.get().strip() and not Validaciones.validar_alfanumerico(self.tags_var.get()):
            errors.append("Las etiquetas solo pueden contener caracteres alfanuméricos.")

        return errors
    
    def save_task(self):
        """Valida y guarda la tarea."""
        # Validar el formulario
        errors = self.validate_form()
        if errors:
            messagebox.showerror("Error", "\n".join(errors))
            return
    
        # Verificar si ya existe una tarea con el mismo título
        if not Validaciones.validar_tarea_duplicada(self.crud, self.title_var.get().strip(), self.task_id):
            # Si existe una tarea con el mismo título, preguntar al usuario si desea continuar
            confirm = messagebox.askyesno(
                "Título Duplicado",
                "Ya existe una tarea con este título. ¿Desea agregarla de todos modos?"
            )
            if not confirm:
                return  # Si el usuario no desea continuar, salir del método
    
        # Preparar los datos
        now = datetime.now()
    
        task_data = {
            'Título': self.title_var.get().strip(),
            'Descripción': self.description_var.get().strip() or None,
            'Fecha de Vencimiento': None if self.use_date_var.get() else self.due_date.get_date(),
            'Prioridad': self.priority_var.get(),
            'Categoría': self.category_var.get(),
            'Etiquetas': self.tags_var.get().strip() or None,
            'Última Actualización': now
        }
    
        if self.task_id is None:
            # Nueva tarea
            task_data['Estado'] = 'Pendiente'
            task_data['Fecha de Creación'] = now
    
            result = self.crud.create('Tareas', task_data)
            message = "Tarea agregada exitosamente."
        else:
            # Actualizar tarea existente
            task_data['Estado'] = self.status_var.get()
    
            result = self.crud.update('Tareas', {'ID': self.task_id}, task_data)
            message = "Tarea actualizada exitosamente."
    
        if result:
            messagebox.showinfo("Éxito", message)
            if self.callback:
                self.callback()
            self.destroy()
        else:
            messagebox.showerror("Error", "No se pudo guardar la tarea.")

# Ventana para gestionar categorías
class CategoryWindow(BaseWindow):
    """
    Ventana para gestionar las categorías de tareas.
    """
    def __init__(self, parent, crud, callback=None):
        """
        Inicializa la ventana de categorías.
        
        Args:
            parent: Ventana padre
            crud (CRUDExcel): Instancia del gestor de Excel
             
            parent: Ventana padre
            crud (CRUDExcel): Instancia del gestor de Excel
            callback (function, optional): Función a llamar al guardar
        """
        super().__init__(parent, "Gestión de Categorías", width=500, height=450)  # Aumentado el height
        self.crud = crud
        self.callback = callback
        
        # Variable para nueva categoría
        self.new_category_var = StringVar()
        self.validaciones = Validaciones()
        
        # Crear la interfaz
        self.create_interface()
        
        # Cargar categorías
        self.load_categories()
    
    def create_interface(self):
        """Crea la interfaz para gestionar categorías."""
        # Frame para agregar categoría
        add_frame = tk.Frame(self.main_frame, bg=COLOR_BLANCO)
        add_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            add_frame, 
            text="Nueva Categoría:", 
            font=("Arial", 11), 
            bg=COLOR_BLANCO
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        category_entry = tk.Entry(
            add_frame, 
            textvariable=self.new_category_var, 
            font=("Arial", 11),
            width=20
        )
        category_entry.pack(side=tk.LEFT, padx=(0, 10))
        ToolTip(category_entry, "Ingrese el nombre de la nueva categoría")
        
        add_button = self.create_button(
            add_frame, 
            "Agregar", 
            self.add_category, 
            COLOR_VERDE,
            width=8
        )
        add_button.pack(side=tk.LEFT)
        ToolTip(add_button, "Agregar la nueva categoría")
        
        # Frame para la lista de categorías
        list_frame = tk.Frame(self.main_frame, bg=COLOR_BLANCO)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            list_frame, 
            text="Categorías Existentes:", 
            font=("Arial", 11, "bold"), 
            bg=COLOR_BLANCO
        ).pack(anchor="w", pady=(0, 10))
        
        # Treeview para categorías
        columns = ("ID", "Nombre")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # Configurar columnas
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        
        self.tree.column("ID", width=50, stretch=False)
        self.tree.column("Nombre", width=300, stretch=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ToolTip(self.tree, "Lista de categorías disponibles")
        
        # Botones de acción
        button_frame = tk.Frame(self.main_frame, bg=COLOR_BLANCO)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        delete_button = self.create_button(
            button_frame, 
            "Eliminar", 
            self.delete_category, 
            COLOR_ROJO
        )
        delete_button.pack(side=tk.LEFT)
        ToolTip(delete_button, "Eliminar la categoría seleccionada")
        
        close_button = self.create_button(
            button_frame, 
            "Cerrar", 
            self.destroy, 
            COLOR_GRIS
        )
        close_button.pack(side=tk.RIGHT)
        ToolTip(close_button, "Cerrar la ventana")
    
    def load_categories(self):
        """Carga las categorías desde Excel al treeview."""
        # Limpiar el treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Cargar categorías desde Excel
        categories_df = self.crud.read('Categorías')
        
        # Llenar el treeview
        for _, row in categories_df.iterrows():
            self.tree.insert('', 'end', values=(row['ID'], row['Nombre']))
    
    def add_category(self):
        """Valida y agrega una nueva categoría."""
        # Obtener el nombre de la categoría
        category_name = self.new_category_var.get().strip()
        
        if not Validaciones.validar_texto_no_vacio(category_name):
            messagebox.showerror("Error", "El nombre de la categoría es obligatorio.")
            return
        
        # Validar que no exista ya
        categories_df = self.crud.read('Categorías')
        if category_name.lower() in categories_df['Nombre'].str.lower().tolist():
            messagebox.showerror("Error", "Esta categoría ya existe.")
            return
        
        # Validar que solo contenga caracteres alfanuméricos
        if not Validaciones.validar_alfanumerico(category_name):
            messagebox.showerror("Error", "Las categorías solo pueden contener caracteres alfanuméricos.")
            return
        
        # Agregar la categoría
        result = self.crud.create('Categorías', {'Nombre': category_name})
        
        if result:
            messagebox.showinfo("Éxito", "Categoría agregada exitosamente.")
            self.new_category_var.set('')
            self.load_categories()
            if self.callback:
                self.callback()
        else:
            messagebox.showerror("Error", "No se pudo agregar la categoría.")
    
    def delete_category(self):
        """Valida y elimina la categoría seleccionada."""
        # Obtener la categoría seleccionada
        selected = self.tree.selection()
        
        if not selected:
            messagebox.showwarning("Advertencia", "Por favor, selecciona una categoría para eliminar.")
            return
        
        # Obtener el ID y nombre de la categoría
        category_id = self.tree.item(selected[0])['values'][0]
        category_name = self.tree.item(selected[0])['values'][1]
        
        # Verificar si la categoría está siendo utilizada
        tasks_df = self.crud.read('Tareas')
        if not tasks_df.empty and category_name in tasks_df['Categoría'].values:
            messagebox.showerror("Error", "No se puede eliminar esta categoría porque está siendo utilizada en una tarea.")
            return
        
        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar", f"¿Estás seguro de que deseas eliminar la categoría '{category_name}'?"):
            return
        
        # Eliminar la categoría
        result = self.crud.delete('Categorías', {'ID': category_id})
        
        if result:
            messagebox.showinfo("Éxito", "Categoría eliminada exitosamente.")
            self.load_categories()
            if self.callback:
                self.callback()
        else:
            messagebox.showerror("Error", "No se pudo eliminar la categoría.")

# Ventana para ver detalles de tarea
class TaskDetailWindow(BaseWindow):
    """
    Ventana para ver los detalles de una tarea.
    """
    def __init__(self, parent, crud, task_id, callback=None):
        """
        Inicializa la ventana de detalle de tarea.
        
        Args:
            parent: Ventana padre
            crud (CRUDExcel): Instancia del gestor de Excel
            task_id (int): ID de la tarea a mostrar
            callback (function, optional): Función a llamar al actualizar
        """
        self.crud = crud
        self.task_id = task_id
        self.callback = callback
        
        super().__init__(parent, "Detalle de Tarea", width=600, height=550)  # Aumentado el height
        
        # Cargar datos de la tarea
        self.task_data = self.load_task_data()
        
        if self.task_data is not None:
            # Crear la interfaz
            self.create_interface()
    
    def load_task_data(self):
        """
        Carga los datos de la tarea desde Excel.
        
        Returns:
            dict: Datos de la tarea o None si hay error
        """
        # Obtener la tarea desde Excel
        task_df = self.crud.read('Tareas', {'ID': self.task_id})
        
        if task_df.empty:
            messagebox.showerror("Error", "No se pudo cargar la tarea.")
            self.destroy()
            return None
        
        # Retornar la primera fila como diccionario
        return task_df.iloc[0].to_dict()
    
    def create_interface(self):
        """Crea la interfaz para mostrar los detalles de la tarea."""
        # Título de la tarea
        title_label = tk.Label(
            self.main_frame, 
            text=self.task_data['Título'], 
            font=("Arial", 16, "bold"), 
            bg=COLOR_BLANCO,
            anchor="w"
        )
        title_label.pack(fill=tk.X, pady=(0, 15))
        
        # Frame para badges (estado, prioridad, categoría)
        badges_frame = tk.Frame(self.main_frame, bg=COLOR_BLANCO)
        badges_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Colores para los badges
        status_colors = {
            "Pendiente": COLOR_NARANJA,
            "En Progreso": COLOR_AZUL,
            "Completada": COLOR_VERDE
        }
        
        priority_colors = {
            "Alta": COLOR_ROJO,
            "Media": COLOR_NARANJA,
            "Baja": COLOR_VERDE
        }
        
        # Crear badges
        status_badge = tk.Label(
            badges_frame,
            text=self.task_data['Estado'],
            bg=status_colors.get(self.task_data['Estado'], COLOR_GRIS),
            fg=COLOR_BLANCO,
            font=("Arial", 10),
            padx=10,
            pady=3,
            relief=tk.FLAT,
            borderwidth=0
        )
        status_badge.pack(side=tk.LEFT, padx=(0, 10))
        ToolTip(status_badge, "Estado actual de la tarea")
        
        priority_badge = tk.Label(
            badges_frame,
            text=self.task_data['Prioridad'],
            bg=priority_colors.get(self.task_data['Prioridad'], COLOR_GRIS),
            fg=COLOR_BLANCO,
            font=("Arial", 10),
            padx=10,
            pady=3,
            relief=tk.FLAT,
            borderwidth=0
        )
        priority_badge.pack(side=tk.LEFT, padx=(0, 10))
        ToolTip(priority_badge, "Nivel de prioridad de la tarea")
        
        category_badge = tk.Label(
            badges_frame,
            text=self.task_data['Categoría'],
            bg=COLOR_AZUL,
            fg=COLOR_BLANCO,
            font=("Arial", 10),
            padx=10,
            pady=3,
            relief=tk.FLAT,
            borderwidth=0
        )
        category_badge.pack(side=tk.LEFT)
        ToolTip(category_badge, "Categoría a la que pertenece la tarea")
        
        # Fecha de vencimiento
        date_frame = tk.Frame(self.main_frame, bg=COLOR_BLANCO)
        date_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            date_frame,
            text="Fecha de vencimiento:",
            font=("Arial", 11, "bold"),
            bg=COLOR_BLANCO
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        date_text = "Sin fecha" if pd.isna(self.task_data['Fecha de Vencimiento']) else self.task_data['Fecha de Vencimiento'].strftime('%d/%m/%Y')
        date_label = tk.Label(
            date_frame,
            text=date_text,
            font=("Arial", 11),
            bg=COLOR_BLANCO
        )
        date_label.pack(side=tk.LEFT)
        ToolTip(date_label, "Fecha límite para completar la tarea")
        
        # Descripción
        tk.Label(
            self.main_frame,
            text="Descripción:",
            font=("Arial", 11, "bold"),
            bg=COLOR_BLANCO,
            anchor="w"
        ).pack(fill=tk.X, pady=(0, 5))
        
        description_frame = tk.Frame(self.main_frame, bg=COLOR_GRIS_CLARO, bd=1, relief=tk.SOLID)
        description_frame.pack(fill=tk.X, pady=(0, 15), ipady=10)
        
        description_text = self.task_data['Descripción'] if pd.notna(self.task_data['Descripción']) else "Sin descripción"
        description_label = tk.Label(
            description_frame,
            text=description_text,
            font=("Arial", 11),
            bg=COLOR_GRIS_CLARO,
            justify=tk.LEFT,
            wraplength=550,
            padx=10
        )
        description_label.pack(fill=tk.X)
        
        # Etiquetas
        tk.Label(
            self.main_frame,
            text="Etiquetas:",
            font=("Arial", 11, "bold"),
            bg=COLOR_BLANCO,
            anchor="w"
        ).pack(fill=tk.X, pady=(0, 5))
        
        tags_frame = tk.Frame(self.main_frame, bg=COLOR_BLANCO)
        tags_frame.pack(fill=tk.X, pady=(0, 15))
        
        if pd.notna(self.task_data['Etiquetas']) and self.task_data['Etiquetas']:
            tags = self.task_data['Etiquetas'].split(',')
            for tag in tags:
                tag = tag.strip()
                if tag:
                    tag_badge = tk.Label(
                        tags_frame,
                        text=tag,
                        bg=COLOR_GRIS,
                        fg=COLOR_BLANCO,
                        font=("Arial", 10),
                        padx=10,
                        pady=3,
                        relief=tk.FLAT,
                        borderwidth=0
                    )
                    tag_badge.pack(side=tk.LEFT, padx=(0, 5), pady=(0, 5))
                    ToolTip(tag_badge, f"Etiqueta: {tag}")
        else:
            tk.Label(
                tags_frame,
                text="Sin etiquetas",
                font=("Arial", 11),
                bg=COLOR_BLANCO
            ).pack(anchor="w")
        
        # Fechas de creación y actualización
        dates_frame = tk.Frame(self.main_frame, bg=COLOR_BLANCO)
        dates_frame.pack(fill=tk.X, pady=(0, 15))
        
        created_date = self.task_data['Fecha de Creación'].strftime('%d/%m/%Y') if pd.notna(self.task_data.get('Fecha de Creación')) else "Desconocido"
        updated_date = self.task_data['Última Actualización'].strftime('%d/%m/%Y') if pd.notna(self.task_data.get('Última Actualización')) else "Desconocido"
        
        created_label = tk.Label(
            dates_frame,
            text=f"Creado: {created_date}",
            font=("Arial", 10),
            bg=COLOR_BLANCO
        )
        created_label.pack(side=tk.LEFT)
        ToolTip(created_label, "Fecha en que se creó la tarea")
        
        updated_label = tk.Label(
            dates_frame,
            text=f"Última actualización: {updated_date}",
            font=("Arial", 10),
            bg=COLOR_BLANCO
        )
        updated_label.pack(side=tk.LEFT, padx=(20, 0))
        ToolTip(updated_label, "Fecha de la última modificación")
        
        # Botones
        buttons_frame = tk.Frame(self.main_frame, bg=COLOR_BLANCO)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        edit_button = self.create_button(
            buttons_frame,
            "Editar",
            self.edit_task,
            COLOR_NARANJA
        )
        edit_button.pack(side=tk.RIGHT, padx=5)
        ToolTip(edit_button, "Editar esta tarea")
        
        close_button = self.create_button(
            buttons_frame,
            "Cerrar",
            self.destroy,
            COLOR_GRIS
        )
        close_button.pack(side=tk.RIGHT, padx=5)
        ToolTip(close_button, "Cerrar esta ventana")
        
        # Botón para marcar como completada (si no está completada)
        if self.task_data['Estado'] != 'Completada':
            complete_button = self.create_button(
                buttons_frame,
                "Marcar como Completada",
                self.mark_as_completed,
                COLOR_VERDE,
                width=20
            )
            complete_button.pack(side=tk.LEFT)
            ToolTip(complete_button, "Marcar esta tarea como completada")
    
    def edit_task(self):
        """Abre la ventana de edición para la tarea actual."""
        # Obtener categorías
        categories_df = self.crud.read('Categorías')
        categories = categories_df.to_dict('records')
        
        # Abrir ventana de edición
        TaskWindow(self.parent, self.crud, categories, self.task_id, self.on_task_updated)
    
    def mark_as_completed(self):
        """Marca la tarea actual como completada."""
        # Actualizar el estado de la tarea
        result = self.crud.update('Tareas', {'ID': self.task_id}, {
            'Estado': 'Completada',
            'Última Actualización': datetime.now()
        })
        
        if result:
            messagebox.showinfo("Éxito", "Tarea marcada como completada.")
            if self.callback:
                self.callback()
            self.destroy()
        else:
            messagebox.showerror("Error", "No se pudo actualizar el estado de la tarea.")
    
    def on_task_updated(self):
        """Callback que se ejecuta cuando la tarea es actualizada."""
        # Recargar datos de la tarea
        self.task_data = self.load_task_data()
        
        # Actualizar la interfaz
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        self.create_interface()
        
        # Llamar al callback si existe
        if self.callback:
            self.callback()

# Aplicación principal
class TaskManagerApp:
    """
    Clase principal de la aplicación de gestión de tareas.
    """
    def __init__(self, root:tk.Tk):
        """
        Inicializa la aplicación principal.
        
        Args:
            root: Ventana raíz de Tkinter
        """
        self.root = root
        self.root.title("Gestor de Tareas - Panel Principal")
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)
        self.validaciones = Validaciones()

        # Configurar estilo
        self.configure_style()

        # Inicializar el gestor de Excel
        self.excel_file = "tareasT00083600.xlsx"
        self.crud = CRUDExcel(self.excel_file)

        # Preguntar al usuario si desea inyectar datos aleatorios
        self.ask_to_inject_data()

        # Variables para ordenamiento
        self.sort_by = "fecha"  # Opciones: fecha, prioridad, titulo
        self.sort_ascending = True

        # Variables para filtrado
        self.filter_estado_var = StringVar(value="Todas")
        self.filter_categoria_var = StringVar(value="Todas")
        self.filter_prioridad_var = StringVar(value="Todas")

        # Crear la interfaz
        self.create_interface()

        # Cargar datos iniciales
        self.load_data()

    def ask_to_inject_data(self):
        """Pregunta al usuario si desea inyectar datos aleatorios."""
        confirm = messagebox.askyesno(
            "Inyectar Datos Aleatorios",
            "¿Desea inyectar datos aleatorios en la base de datos?"
        )

        if confirm:
            # Generar datos de tareas
            tasks = self.generate_task_data()

            if tasks:
                # Inyectar datos en el archivo Excel
                self.inject_data_into_excel(tasks)
                messagebox.showinfo("Éxito", "Datos aleatorios inyectados exitosamente.")
            else:
                messagebox.showwarning("Advertencia", "No se generaron tareas para inyectar.")
        else:
            print("No se inyectaron datos aleatorios.")

    def generate_task_data(self):
        """Genera datos de tareas utilizando la API de Groq."""
        prompt = """
        Genera una lista de 50 tareas con los siguientes campos en formato JSON:
        - Título: Un título breve para la tarea.
        - Descripción: Una descripción detallada de la tarea.
        - Prioridad: Alta, Media o Baja.
        - Categoría: Trabajo, Personal o Estudio.
        - Etiquetas: Dos etiquetas separadas por comas (por ejemplo, "Urgente, Importante").
        Asegúrate de que los nombres de los campos sean exactamente: Título, Descripción, Prioridad, Categoría, Etiquetas.
        Devuelve la lista de tareas en una clave llamada "tareas".
        """

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente útil que genera datos de tareas en formato JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},  # Asegura que la respuesta sea en formato JSON
            )

            # Extraer el contenido de la respuesta
            response_content = chat_completion.choices[0].message.content

            # Convertir la respuesta JSON en un diccionario de Python
            tasks = json.loads(response_content)
            return tasks.get("tareas", [])  # Asume que la respuesta tiene una clave "tareas"
        except Exception as e:
            print(f"Error al procesar la respuesta de la API: {e}")
            return []

    def inject_data_into_excel(self, tasks):
        """Inyecta datos de tareas en el archivo Excel."""
        # Crear categorías si no existen
        categorias_df = self.crud.read('Categorías')
        if categorias_df.empty:
            categorias = [
                {"ID": 1, "Nombre": "Trabajo"},
                {"ID": 2, "Nombre": "Personal"},
                {"ID": 3, "Nombre": "Estudio"}
            ]
            for categoria in categorias:
                self.crud.create('Categorías', categoria)

        for task in tasks:
            # Añadir campos adicionales requeridos
            task["ID"] = None  # El ID se generará automáticamente en el método create
            task["Fecha de Vencimiento"] = (datetime(2026, 1, 1) + timedelta(days=random.randint(1, 365 * 2)) ) # Fechas en 2026-2027
            task["Estado"] = "Pendiente"
            task["Fecha de Creación"] = datetime.now()
            task["Última Actualización"] = datetime.now()

            # Insertar la tarea en el archivo Excel
            self.crud.create('Tareas', task)

        print(f"{len(tasks)} tareas inyectadas exitosamente.")
        
    
    def configure_style(self):
        """Configura el estilo visual de la aplicación."""
        # Configurar el estilo de la aplicación
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        
        # Configurar colores
        self.root.configure(bg=COLOR_BLANCO)
    
    def create_interface(self):
        """Crea la interfaz principal de la aplicación."""
        # Crear el menú
        self.create_menu()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg=COLOR_BLANCO)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título y filtro
        header_frame = tk.Frame(main_frame, bg=COLOR_BLANCO)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            header_frame, 
            text="Todas las Tareas", 
            font=("Arial", 14, "bold"), 
            bg=COLOR_BLANCO
        ).pack(side=tk.LEFT)
        
        # Frame para filtros
        self.create_filters(main_frame)
        
        # Botones de acción
        buttons_frame = tk.Frame(main_frame, bg=COLOR_BLANCO)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        new_task_button = tk.Button(
            buttons_frame,
            text="Nueva Tarea",
            command=self.open_new_task_window,
            bg=COLOR_AZUL,
            fg=COLOR_BLANCO,
            font=("Arial", 10),
            relief=tk.FLAT,
            borderwidth=0,
            padx=15,
            pady=5
        )
        new_task_button.pack(side=tk.LEFT, padx=(0, 10))
        ToolTip(new_task_button, "Crear una nueva tarea")
        
        categories_button = tk.Button(
            buttons_frame,
            text="Categorías",
            command=self.open_categories_window,
            bg=COLOR_VERDE,
            fg=COLOR_BLANCO,
            font=("Arial", 10),
            relief=tk.FLAT,
            borderwidth=0,
            padx=15,
            pady=5
        )
        categories_button.pack(side=tk.LEFT, padx=(0, 10))
        ToolTip(categories_button, "Gestionar las categorías")
        
        # Botones de ordenamiento
        sort_frame = tk.Frame(buttons_frame, bg=COLOR_BLANCO)
        sort_frame.pack(side=tk.RIGHT)
        
        tk.Label(
            sort_frame,
            text="Ordenar por:",
            font=("Arial", 10),
            bg=COLOR_BLANCO
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.sort_var = StringVar(value="Fecha")
        sort_combo = ttk.Combobox(
            sort_frame,
            textvariable=self.sort_var,
            values=["Fecha", "Prioridad", "Título"],
            state="readonly",
            width=10
        )
        sort_combo.pack(side=tk.LEFT, padx=(0, 5))
        sort_combo.bind("<<ComboboxSelected>>", self.change_sort)
        ToolTip(sort_combo, "Seleccione el criterio de ordenamiento")
        
        # Botón para cambiar dirección de ordenamiento
        self.sort_direction_var = StringVar(value="↓")
        sort_direction_button = tk.Button(
            sort_frame,
            textvariable=self.sort_direction_var,
            command=self.toggle_sort_direction,
            bg=COLOR_GRIS_CLARO,
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            borderwidth=0,
            padx=5,
            pady=0,
            width=2
        )
        sort_direction_button.pack(side=tk.LEFT)
        ToolTip(sort_direction_button, "Cambiar dirección de ordenamiento (ascendente/descendente)")
        
        # Frame para la tabla de tareas
        table_frame = tk.Frame(main_frame, bg=COLOR_BLANCO)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Crear la tabla de tareas con checkboxes
        self.create_task_table(table_frame)
        
        # Barra de estado
        self.status_bar = tk.Label(
            self.root, 
            text="", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            font=("Arial", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Botón para eliminar tareas completadas
        delete_completed_button = tk.Button(
            main_frame,
            text="Eliminar Tareas Completadas",
            command=self.delete_completed_tasks,
            bg=COLOR_ROJO,
            fg=COLOR_BLANCO,
            font=("Arial", 10),
            relief=tk.FLAT,
            borderwidth=0,
            padx=15,
            pady=5
        )
        delete_completed_button.pack(side=tk.BOTTOM, anchor=tk.E, pady=(10, 0))
        ToolTip(delete_completed_button, "Eliminar todas las tareas marcadas como completadas")
    
    def create_filters(self, parent):
        """
        Crea la sección de filtros para la aplicación.
        
        Args:
            parent: Widget padre donde se crearán los filtros
        """
        filters_frame = tk.LabelFrame(parent, text="Filtros", bg=COLOR_BLANCO, font=("Arial", 10, "bold"))
        filters_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Filtro por estado
        estado_frame = tk.Frame(filters_frame, bg=COLOR_BLANCO)
        estado_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(
            estado_frame,
            text="Estado:",
            font=("Arial", 10),
            bg=COLOR_BLANCO
        ).pack(anchor="w")
        
        estado_combo = ttk.Combobox(
            estado_frame,
            textvariable=self.filter_estado_var,
            values=["Todas", "Pendientes", "En Progreso", "Completadas"],
            state="readonly",
            width=12
        )
        estado_combo.pack(pady=(2, 0))
        estado_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())
        ToolTip(estado_combo, "Filtrar tareas por estado")
        
        # Filtro por categoría
        categoria_frame = tk.Frame(filters_frame, bg=COLOR_BLANCO)
        categoria_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(
            categoria_frame,
            text="Categoría:",
            font=("Arial", 10),
            bg=COLOR_BLANCO
        ).pack(anchor="w")
        
        # Obtener categorías
        categorias_df = self.crud.read('Categorías')
        categorias = ["Todas"] + categorias_df['Nombre'].tolist()
        
        categoria_combo = ttk.Combobox(
            categoria_frame,
            textvariable=self.filter_categoria_var,
            values=categorias,
            state="readonly",
            width=12
        )
        categoria_combo.pack(pady=(2, 0))
        categoria_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())
        ToolTip(categoria_combo, "Filtrar tareas por categoría")
        
        # Filtro por prioridad
        prioridad_frame = tk.Frame(filters_frame, bg=COLOR_BLANCO)
        prioridad_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(
            prioridad_frame,
            text="Prioridad:",
            font=("Arial", 10),
            bg=COLOR_BLANCO
        ).pack(anchor="w")
        
        prioridad_combo = ttk.Combobox(
            prioridad_frame,
            textvariable=self.filter_prioridad_var,
            values=["Todas", "Alta", "Media", "Baja"],
            state="readonly",
            width=12
        )
        prioridad_combo.pack(pady=(2, 0))
        prioridad_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())
        ToolTip(prioridad_combo, "Filtrar tareas por prioridad")
        
        # Botón para limpiar filtros
        clear_button = tk.Button(
            filters_frame,
            text="Limpiar Filtros",
            command=self.clear_filters,
            bg=COLOR_GRIS,
            fg=COLOR_BLANCO,
            font=("Arial", 9),
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=2
        )
        clear_button.pack(side=tk.RIGHT, padx=10, pady=5)
        ToolTip(clear_button, "Quitar todos los filtros aplicados")
    
    def clear_filters(self):
        """Limpia todos los filtros aplicados."""
        self.filter_estado_var.set("Todas")
        self.filter_categoria_var.set("Todas")
        self.filter_prioridad_var.set("Todas")
        self.apply_filter()
    
    def create_menu(self):
        """Crea el menú principal de la aplicación."""
        menubar = tk.Menu(self.root)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Nueva Tarea", command=self.open_new_task_window)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        
        # Menú Editar
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Editar Tarea Seleccionada", command=self.edit_selected_task)
        edit_menu.add_command(label="Eliminar Tarea Seleccionada", command=self.delete_selected_task)
        edit_menu.add_separator()
        edit_menu.add_command(label="Eliminar Tareas Completadas", command=self.delete_completed_tasks)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        
        # Menú Ver
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Todas las Tareas", command=lambda: self.set_filter("Todas"))
        view_menu.add_command(label="Tareas Pendientes", command=lambda: self.set_filter("Pendientes"))
        view_menu.add_command(label="Tareas En Progreso", command=lambda: self.set_filter("En Progreso"))
        view_menu.add_command(label="Tareas Completadas", command=lambda: self.set_filter("Completadas"))
        view_menu.add_separator()
        view_menu.add_command(label="Ordenar por Fecha", command=lambda: self.set_sort("Fecha"))
        view_menu.add_command(label="Ordenar por Prioridad", command=lambda: self.set_sort("Prioridad"))
        view_menu.add_command(label="Ordenar por Título", command=lambda: self.set_sort("Título"))
        menubar.add_cascade(label="Ver", menu=view_menu)
        
        # Menú Categorías
        categories_menu = tk.Menu(menubar, tearoff=0)
        categories_menu.add_command(label="Gestionar Categorías", command=self.open_categories_window)
        menubar.add_cascade(label="Categorías", menu=categories_menu)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_task_table(self, parent):
        """
        Crea la tabla para mostrar las tareas.
        
        Args:
            parent: Widget padre donde se creará la tabla
        """
        # Frame para la tabla
        table_frame = tk.Frame(parent, bg=COLOR_BLANCO)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Crear encabezados
        headers_frame = tk.Frame(table_frame, bg=COLOR_GRIS_CLARO)
        headers_frame.pack(fill=tk.X)

        # Checkbox en encabezado
        checkbox_header = tk.Frame(headers_frame, width=30, bg=COLOR_GRIS_CLARO)
        checkbox_header.pack(side=tk.LEFT, fill=tk.Y)

        # Encabezados de columnas
        tk.Label(headers_frame, text="Título", width=30, font=("Arial", 10, "bold"), bg=COLOR_GRIS_CLARO).pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
        tk.Label(headers_frame, text="Fecha", width=15, font=("Arial", 10, "bold"), bg=COLOR_GRIS_CLARO).pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(headers_frame, text="     Prioridad", width=10, font=("Arial", 10, "bold"), bg=COLOR_GRIS_CLARO).pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(headers_frame, text="       Categoría", width=15, font=("Arial", 10, "bold"), bg=COLOR_GRIS_CLARO).pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(headers_frame, text="         Estado", width=10, font=("Arial", 10, "bold"), bg=COLOR_GRIS_CLARO).pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(headers_frame, text="Acción", width=10, font=("Arial", 10, "bold"), bg=COLOR_GRIS_CLARO).pack(side=tk.LEFT, fill=tk.Y)

        # Frame para la lista de tareas con scroll
        self.tasks_canvas = tk.Canvas(table_frame, bg=COLOR_BLANCO)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tasks_canvas.yview)
        self.tasks_frame = tk.Frame(self.tasks_canvas, bg=COLOR_BLANCO)

        self.tasks_frame.bind(
            "<Configure>",
            lambda e: self.tasks_canvas.configure(scrollregion=self.tasks_canvas.bbox("all"))
        )

        self.tasks_canvas.create_window((0, 0), window=self.tasks_frame, anchor="nw")
        self.tasks_canvas.configure(yscrollcommand=scrollbar.set)

        self.tasks_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ToolTip(self.tasks_canvas, "Lista de tareas")
    
    def load_data(self):
        """Carga los datos de tareas y actualiza la interfaz."""
        # Cargar tareas
        self.load_tasks()
        
        # Actualizar la barra de estado
        self.update_status_bar()
    
    def load_tasks(self):
        """Carga las tareas desde Excel y aplica filtros y ordenamiento."""
        # Limpiar el frame de tareas
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()
        
        # Cargar tareas desde Excel
        tasks_df = self.crud.read('Tareas')
        
        if tasks_df.empty:
            # Mostrar mensaje si no hay tareas
            tk.Label(
                self.tasks_frame,
                text="No hay tareas. Haga clic en 'Nueva Tarea' para agregar una.",
                font=("Arial", 11),
                bg=COLOR_BLANCO,
                fg=COLOR_GRIS,
                pady=20
            ).pack(fill=tk.X)
            return
        
        # Aplicar filtros
        # Filtro por estado
        estado_filter = self.filter_estado_var.get()
        if estado_filter == "Pendientes":
            tasks_df = tasks_df[tasks_df['Estado'] == 'Pendiente']
        elif estado_filter == "En Progreso":
            tasks_df = tasks_df[tasks_df['Estado'] == 'En Progreso']
        elif estado_filter == "Completadas":
            tasks_df = tasks_df[tasks_df['Estado'] == 'Completada']
        
        # Filtro por categoría
        categoria_filter = self.filter_categoria_var.get()
        if categoria_filter != "Todas":
            tasks_df = tasks_df[tasks_df['Categoría'] == categoria_filter]
        
        # Filtro por prioridad
        prioridad_filter = self.filter_prioridad_var.get()
        if prioridad_filter != "Todas":
            tasks_df = tasks_df[tasks_df['Prioridad'] == prioridad_filter]
        
        # Convertir fechas
        tasks_df['Fecha de Vencimiento'] = pd.to_datetime(tasks_df['Fecha de Vencimiento'], errors='coerce')
        
        # Aplicar ordenamiento
        sort_column = self.sort_var.get().lower()
        if sort_column == "fecha":
            tasks_df = tasks_df.sort_values(
                by=['Fecha de Vencimiento'], 
                ascending=self.sort_ascending,
                na_position='last'
            )
        elif sort_column == "prioridad":
            # Definir orden de prioridades
            priority_order = {'Alta': 0, 'Media': 1, 'Baja': 2}
            tasks_df['PrioridadOrden'] = tasks_df['Prioridad'].map(priority_order)
            tasks_df = tasks_df.sort_values(
                by=['PrioridadOrden'], 
                ascending=self.sort_ascending
            )
        elif sort_column == "título":
            tasks_df = tasks_df.sort_values(
                by=['Título'], 
                ascending=self.sort_ascending
            )
        
        # Separar tareas completadas y no completadas
        completed_tasks = tasks_df[tasks_df['Estado'] == 'Completada']
        incomplete_tasks = tasks_df[tasks_df['Estado'] != 'Completada']
        
        # Concatenar tareas no completadas primero y luego las completadas
        tasks_df = pd.concat([incomplete_tasks, completed_tasks])
        
        # Crear filas para cada tarea
        for index, row in tasks_df.iterrows():
            self.create_task_row(row)
        
        # Si no hay tareas después del filtro
        if len(tasks_df) == 0:
            filter_text = []
            if estado_filter != "Todas":
                filter_text.append(f"estado '{estado_filter}'")
            if categoria_filter != "Todas":
                filter_text.append(f"categoría '{categoria_filter}'")
            if prioridad_filter != "Todas":
                filter_text.append(f"prioridad '{prioridad_filter}'")
            
            filter_description = ", ".join(filter_text) if filter_text else "los filtros aplicados"
            
            tk.Label(
                self.tasks_frame,
                text=f"No hay tareas con {filter_description}.",
                font=("Arial", 11),
                bg=COLOR_BLANCO,
                fg=COLOR_GRIS,
                pady=20
            ).pack(fill=tk.X)
    
    def create_task_row(self, task):
        """
        Crea una fila para una tarea en la tabla.
        
        Args:
            task (pandas.Series): Datos de la tarea
        """
        # Colores según estado
        if task['Estado'] == 'Completada':
            bg_color = COLOR_GRIS_CLARO
            fg_color = COLOR_GRIS
            title_font = ("Arial", 10, "overstrike")
        else:
            bg_color = COLOR_BLANCO
            fg_color = "black"
            title_font = ("Arial", 10)

        # Colores para prioridad
        priority_colors = {
            "Alta": COLOR_ROJO,
            "Media": COLOR_NARANJA,
            "Baja": COLOR_VERDE
        }

        # Colores para estado
        status_colors = {
            "Pendiente": COLOR_NARANJA,
            "En Progreso": COLOR_AZUL,
            "Completada": COLOR_VERDE
        }

        # Frame para la fila
        row_frame = tk.Frame(self.tasks_frame, bg=bg_color, bd=1, relief=tk.SOLID)
        row_frame.pack(fill=tk.X, pady=1)

        # Variable para el checkbox
        check_var = BooleanVar(value=task['Estado'] == 'Completada')

        # Función para manejar el cambio en el checkbox
        def toggle_completed():
            new_status = "Completada" if check_var.get() else "Pendiente"
            self.update_task_status(task['ID'], new_status)

        # Checkbox
        checkbox = tk.Checkbutton(
            row_frame, 
            variable=check_var, 
            command=toggle_completed,
            bg=bg_color,
            activebackground=bg_color
        )
        checkbox.pack(side=tk.LEFT, padx=(5, 0))
        ToolTip(checkbox, "Marcar como completada/pendiente")

        # Título (con evento de clic para editar)
        title = task['Título']
        if len(title) > 20:  # Truncar el título si es muy largo
            title = title[:17] + "..."

        title_label = tk.Label(
            row_frame, 
            text=title, 
            font=title_font,
            bg=bg_color, 
            fg=fg_color,
            width=30,
            anchor="w"
        )
        title_label.pack(side=tk.LEFT, padx=(5, 0))
        title_label.bind("<Button-1>", lambda e, id=task['ID']: self.open_task_detail(id))
        ToolTip(title_label, f"Título: {task['Título']}\nHaga clic para ver detalles")

        # Fecha
        date_str = task['Fecha de Vencimiento'].strftime('%d/%m/%Y') if pd.notna(task['Fecha de Vencimiento']) else "-/-/---"
        date_label = tk.Label(
            row_frame, 
            text=date_str, 
            font=("Arial", 10),
            bg=bg_color, 
            fg=fg_color,
            width=15
        )
        date_label.pack(side=tk.LEFT)
        if pd.notna(task['Fecha de Vencimiento']):
            ToolTip(date_label, f"Fecha de vencimiento: {date_str}")
        else:
            ToolTip(date_label, "Sin fecha de vencimiento")

        # Prioridad (con color)
        priority_frame = tk.Frame(row_frame, bg=bg_color)
        priority_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))

        priority_badge = tk.Label(
            priority_frame,
            text=task['Prioridad'],
            bg=priority_colors.get(task['Prioridad'], COLOR_GRIS),
            fg=COLOR_BLANCO,
            font=("Arial", 9),
            padx=8,
            pady=1,
            relief=tk.FLAT,
            borderwidth=0,
            width=10  # Asegurar que todas las barras de prioridad tengan el mismo ancho
        )
        priority_badge.pack(pady=2)
        ToolTip(priority_badge, f"Prioridad: {task['Prioridad']}")

        # Categoría
        category_label = tk.Label(
            row_frame, 
            text=task['Categoría'], 
            font=("Arial", 10),
            bg=bg_color, 
            fg=COLOR_AZUL,
            width=15
        )
        category_label.pack(side=tk.LEFT)
        ToolTip(category_label, f"Categoría: {task['Categoría']}")

        # Estado (con color)
        status_frame = tk.Frame(row_frame, bg=bg_color)
        status_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))

        status_badge = tk.Label(
            status_frame,
            text=task['Estado'],
            bg=status_colors.get(task['Estado'], COLOR_GRIS),
            fg=COLOR_BLANCO,
            font=("Arial", 9),
            padx=8,
            pady=1,
            relief=tk.FLAT,
            borderwidth=0,
            width=10  # Asegurar que todas las barras de estado tengan el mismo ancho
        )
        status_badge.pack(pady=2)
        ToolTip(status_badge, f"Estado: {task['Estado']}")

        # Botones de acción
        actions_frame = tk.Frame(row_frame, bg=bg_color)
        actions_frame.pack(side=tk.RIGHT, padx=5)

        # Botón editar
        edit_button = tk.Button(
            actions_frame,
            text="✎",
            command=lambda id=task['ID']: self.edit_task(id),
            bg=bg_color,
            relief=tk.FLAT,
            borderwidth=0,
            font=("Arial", 10)
        )
        edit_button.pack(side=tk.LEFT, padx=2)
        ToolTip(edit_button, "Editar esta tarea")

        # Botón eliminar
        delete_button = tk.Button(
            actions_frame,
            text="✖",
            command=lambda id=task['ID']: self.confirm_delete_task(id),
            bg=bg_color,
            relief=tk.FLAT,
            borderwidth=0,
            font=("Arial", 10)
        )
        delete_button.pack(side=tk.LEFT, padx=2)
        ToolTip(delete_button, "Eliminar esta tarea")
    
    def update_task_status(self, task_id, new_status):
        """
        Actualiza el estado de una tarea.
        
        Args:
            task_id (int): ID de la tarea
            new_status (str): Nuevo estado
        """
        # Actualizar el estado de la tarea
        result = self.crud.update('Tareas', {'ID': task_id}, {
            'Estado': new_status,
            'Última Actualización': datetime.now()
        })
        
        if result:
            self.load_data()
        else:
            messagebox.showerror("Error", "No se pudo actualizar el estado de la tarea.")
    
    def update_status_bar(self):
        """Actualiza la barra de estado con información de las tareas."""
        # Contar tareas
        tasks_df = self.crud.read('Tareas')
        
        if tasks_df.empty:
            self.status_bar.config(text="0 tareas")
            return
        
        total = len(tasks_df)
        pending = len(tasks_df[tasks_df['Estado'] == 'Pendiente'])
        in_progress = len(tasks_df[tasks_df['Estado'] == 'En Progreso'])
        completed = len(tasks_df[tasks_df['Estado'] == 'Completada'])
        
        # Actualizar barra de estado
        now = datetime.now().strftime('%d/%m/%Y %H:%M')
        status_text = f"{total} tareas | {pending} pendientes | {in_progress} en progreso | {completed} completadas | Última actualización: {now}"
        self.status_bar.config(text=status_text)
    
    def apply_filter(self):
        """Aplica los filtros seleccionados y recarga las tareas."""
        self.load_data()
    
    def set_filter(self, filter_value):
        """
        Establece el filtro de estado y aplica el filtro.
        
        Args:
            filter_value (str): Valor del filtro
        """
        self.filter_estado_var.set(filter_value)
        self.apply_filter()
    
    def change_sort(self, event):
        """
        Cambia el criterio de ordenamiento.
        
        Args:
            event: Evento que desencadenó el cambio
        """
        self.sort_by = self.sort_var.get().lower()
        self.load_data()
    
    def toggle_sort_direction(self):
        """Cambia la dirección de ordenamiento (ascendente/descendente)."""
        # Cambiar dirección de ordenamiento
        self.sort_ascending = not self.sort_ascending
        self.sort_direction_var.set("↓" if self.sort_ascending else "↑")
        self.load_data()
    
    def set_sort(self, sort_value):
        """
        Establece el criterio de ordenamiento.
        
        Args:
            sort_value (str): Criterio de ordenamiento
        """
        self.sort_var.set(sort_value)
        self.sort_by = sort_value.lower()
        self.load_data()
    
    def open_new_task_window(self):
        """Abre la ventana para crear una nueva tarea."""
        # Obtener categorías
        categories_df = self.crud.read('Categorías')
        categories = categories_df.to_dict('records')
        
        # Abrir ventana de nueva tarea
        TaskWindow(self.root, self.crud, categories, callback=self.load_data)
    
    def open_categories_window(self):
        """Abre la ventana para gestionar categorías."""
        # Abrir ventana de categorías
        CategoryWindow(self.root, self.crud, callback=self.load_data)
    
    def open_task_detail(self, task_id):
        """
        Abre la ventana de detalle de una tarea.
        
        Args:
            task_id (int): ID de la tarea
        """
        # Abrir ventana de detalle de tarea
        TaskDetailWindow(self.root, self.crud, task_id, callback=self.load_data)
    
    def edit_task(self, task_id):
        """
        Abre la ventana para editar una tarea.
        
        Args:
            task_id (int): ID de la tarea
        """
        # Obtener categorías
        categories_df = self.crud.read('Categorías')
        categories = categories_df.to_dict('records')
        
        # Abrir ventana de edición
        TaskWindow(self.root, self.crud, categories, task_id, callback=self.load_data)
    
    def edit_selected_task(self):
        """Muestra un mensaje informativo sobre cómo editar tareas."""
        # Como ahora usamos un sistema personalizado, esta función no es necesaria
        # pero la mantenemos por compatibilidad con el menú
        messagebox.showinfo("Información", "Haga clic en una tarea para editarla.")
    
    def confirm_delete_task(self, task_id):
        """
        Confirma la eliminación de una tarea.
        
        Args:
            task_id (int): ID de la tarea
        """
        # Confirmar eliminación
        if messagebox.askyesno("Confirmar", "¿Estás seguro de que deseas eliminar esta tarea?"):
            self.delete_task(task_id)
    
    def delete_task(self, task_id):
        """
        Elimina una tarea.
        
        Args:
            task_id (int): ID de la tarea
        """
        # Eliminar la tarea
        result = self.crud.delete('Tareas', {'ID': task_id})
        
        if result:
            self.load_data()
        else:
            messagebox.showerror("Error", "No se pudo eliminar la tarea.")
    
    def delete_selected_task(self):
        """Muestra un mensaje informativo sobre cómo eliminar tareas."""
        # Como ahora usamos un sistema personalizado, esta función no es necesaria
        # pero la mantenemos por compatibilidad con el menú
        messagebox.showinfo("Información", "Haga clic en el botón ✖ junto a una tarea para eliminarla.")
    
    def delete_completed_tasks(self):
        """Elimina todas las tareas completadas."""
        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar", "¿Estás seguro de que deseas eliminar todas las tareas completadas?"):
            return
        
        # Obtener tareas completadas
        tasks_df = self.crud.read('Tareas')
        completed_tasks = tasks_df[tasks_df['Estado'] == 'Completada']
        
        if completed_tasks.empty:
            messagebox.showinfo("Información", "No hay tareas completadas para eliminar.")
            return
        
        # Eliminar cada tarea completada
        for task_id in completed_tasks['ID'].values:
            self.crud.delete('Tareas', {'ID': task_id})
        
        messagebox.showinfo("Éxito", f"Se eliminaron {len(completed_tasks)} tareas completadas.")
        self.load_data()
    
    def show_about(self):
        """Muestra información sobre la aplicación."""
        messagebox.showinfo(
            "Acerca de", 
            "Gestor de Tareas v1.0\n\n"
            "Una aplicación para gestionar tus tareas diarias.\n\n"
            "© 2025 Todos los derechos reservados."
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManagerApp(root)
    root.mainloop()