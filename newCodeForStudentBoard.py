import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import re
from abc import ABC, abstractmethod
import uuid
from typing import List, Dict, Optional, Union

# Clase abstracta Estudiante
class Estudiante(ABC):
    def __init__(self, nombre: str, apellido: str, edad: int, id_estudiante: str = None):
        self.__nombre = nombre
        self.__apellido = apellido
        self.__edad = edad
        self.__id = id_estudiante if id_estudiante else str(uuid.uuid4())[:8]
        self.__cursos = []

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, nombre: str) -> None:
        self.__nombre = nombre

    @property
    def apellido(self) -> str:
        return self.__apellido

    @apellido.setter
    def apellido(self, apellido: str) -> None:
        self.__apellido = apellido

    @property
    def edad(self) -> int:
        return self.__edad

    @edad.setter
    def edad(self, edad: int) -> None:
        self.__edad = edad

    @property
    def id(self) -> str:
        return self.__id

    @property
    def cursos(self) -> List[str]:
        return self.__cursos.copy()

    def agregar_curso(self, curso: str) -> None:
        if curso not in self.__cursos:
            self.__cursos.append(curso)

    def eliminar_curso(self, curso: str) -> bool:
        if curso in self.__cursos:
            self.__cursos.remove(curso)
            return True
        return False

    @abstractmethod
    def mostrar_informacion(self) -> str:
        pass

    @abstractmethod
    def get_tipo(self) -> str:
        pass

    def __str__(self) -> str:
        return f"{self.__nombre} {self.__apellido} (ID: {self.__id})"


# Clase concreta EstudiantePregrado
class EstudiantePregrado(Estudiante):
    def __init__(self, nombre: str, apellido: str, edad: int, semestre: int, id_estudiante: str = None):
        super().__init__(nombre, apellido, edad, id_estudiante)
        self.__semestre = semestre
        self.__proyecto_final = None

    @property
    def semestre(self) -> int:
        return self.__semestre

    @semestre.setter
    def semestre(self, semestre: int) -> None:
        self.__semestre = semestre

    @property
    def proyecto_final(self) -> Optional[str]:
        return self.__proyecto_final

    @proyecto_final.setter
    def proyecto_final(self, proyecto: str) -> None:
        self.__proyecto_final = proyecto

    def mostrar_informacion(self) -> str:
        info = f"Estudiante de Pregrado\nNombre: {self.nombre} {self.apellido}\n"
        info += f"ID: {self.id}\nEdad: {self.edad}\nSemestre: {self.__semestre}\n"
        info += f"Proyecto Final: {self.__proyecto_final if self.__proyecto_final else 'No asignado'}\n"
        info += f"Cursos: {', '.join(self.cursos) if self.cursos else 'Ninguno'}"
        return info

    def get_tipo(self) -> str:
        return "Pregrado"


# Clase concreta EstudiantePosgrado
class EstudiantePosgrado(Estudiante):
    def __init__(self, nombre: str, apellido: str, edad: int, programa: str, director_tesis: str = None, id_estudiante: str = None):
        super().__init__(nombre, apellido, edad, id_estudiante)
        self.__programa = programa
        self.__director_tesis = director_tesis
        self.__tema_tesis = None

    @property
    def programa(self) -> str:
        return self.__programa

    @programa.setter
    def programa(self, programa: str) -> None:
        self.__programa = programa

    @property
    def director_tesis(self) -> Optional[str]:
        return self.__director_tesis

    @director_tesis.setter
    def director_tesis(self, director: str) -> None:
        self.__director_tesis = director

    @property
    def tema_tesis(self) -> Optional[str]:
        return self.__tema_tesis

    @tema_tesis.setter
    def tema_tesis(self, tema: str) -> None:
        self.__tema_tesis = tema

    def mostrar_informacion(self) -> str:
        info = f"Estudiante de Posgrado\nNombre: {self.nombre} {self.apellido}\n"
        info += f"ID: {self.id}\nEdad: {self.edad}\nPrograma: {self.__programa}\n"
        info += f"Director de Tesis: {self.__director_tesis if self.__director_tesis else 'No asignado'}\n"
        info += f"Tema de Tesis: {self.__tema_tesis if self.__tema_tesis else 'No asignado'}\n"
        info += f"Cursos: {', '.join(self.cursos) if self.cursos else 'Ninguno'}"
        return info

    def get_tipo(self) -> str:
        return "Posgrado"


# Clase SistemaUniversidad para gestionar estudiantes
class SistemaUniversidad:
    def __init__(self):
        self.__estudiantes: Dict[str, Estudiante] = {}

    def agregar_estudiante(self, estudiante: Estudiante) -> bool:
        if estudiante.id not in self.__estudiantes:
            self.__estudiantes[estudiante.id] = estudiante
            return True
        return False

    def buscar_estudiante(self, id_estudiante: str) -> Optional[Estudiante]:
        return self.__estudiantes.get(id_estudiante)

    def buscar_estudiantes_por_nombre(self, nombre: str) -> List[Estudiante]:
        nombre = nombre.lower()
        return [e for e in self.__estudiantes.values() 
                if nombre in e.nombre.lower() or nombre in e.apellido.lower()]

    def editar_estudiante(self, id_estudiante: str, datos: Dict) -> bool:
        estudiante = self.buscar_estudiante(id_estudiante)
        if not estudiante:
            return False

        if "nombre" in datos:
            estudiante.nombre = datos["nombre"]
        if "apellido" in datos:
            estudiante.apellido = datos["apellido"]
        if "edad" in datos:
            estudiante.edad = datos["edad"]

        if isinstance(estudiante, EstudiantePregrado):
            if "semestre" in datos:
                estudiante.semestre = datos["semestre"]
            if "proyecto_final" in datos:
                estudiante.proyecto_final = datos["proyecto_final"]
        elif isinstance(estudiante, EstudiantePosgrado):
            if "programa" in datos:
                estudiante.programa = datos["programa"]
            if "director_tesis" in datos:
                estudiante.director_tesis = datos["director_tesis"]
            if "tema_tesis" in datos:
                estudiante.tema_tesis = datos["tema_tesis"]

        return True

    def eliminar_estudiante(self, id_estudiante: str) -> bool:
        if id_estudiante in self.__estudiantes:
            del self.__estudiantes[id_estudiante]
            return True
        return False

    def get_todos_estudiantes(self) -> List[Estudiante]:
        return list(self.__estudiantes.values())

    def calcular_edad_promedio(self) -> float:
        if not self.__estudiantes:
            return 0
        total_edad = sum(e.edad for e in self.__estudiantes.values())
        return total_edad / len(self.__estudiantes)

class CursosUniversidad:
    def __init__(self):
        self.__cursos = []

    def agregar_curso(self, curso: str) -> bool:
        if curso not in self.__cursos:
            self.__cursos.append(curso)
            return True
        return False

    def eliminar_curso(self, curso: str) -> bool:
        if curso in self.__cursos:
            self.__cursos.remove(curso)
            return True
        return False

    def get_cursos(self) -> List[str]:
        return self.__cursos.copy()

# Instancia global de CursosUniversidad
cursos_universidad = CursosUniversidad()

# Validadores para los campos del formulario
class Validadores:
    @staticmethod
    def validar_nombre(nombre: str) -> bool:
        return bool(re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]{2,30}$', nombre))

    @staticmethod
    def validar_edad(edad: str) -> bool:
        try:
            edad_num = int(edad)
            return 16 <= edad_num <= 100
        except ValueError:
            return False

    @staticmethod
    def validar_semestre(semestre: str) -> bool:
        try:
            semestre_num = int(semestre)
            return 1 <= semestre_num <= 12
        except ValueError:
            return False

    @staticmethod
    def validar_programa(programa: str) -> bool:
        return len(programa) >= 3 and len(programa) <= 50

    @staticmethod
    def validar_director_tesis(director: str) -> bool:
        return director == "" or Validadores.validar_nombre(director)

    @staticmethod
    def validar_tema_tesis(tema: str) -> bool:
        return tema == "" or (len(tema) >= 5 and len(tema) <= 100)

    @staticmethod
    def validar_proyecto_final(proyecto: str) -> bool:
        return proyecto == "" or (len(proyecto) >= 5 and len(proyecto) <= 100)


# Clase principal de la interfaz gráfica
class AplicacionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Estudiantes")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f0f0")
        self.root.resizable(True, True)

        self.sistema = SistemaUniversidad()
        self.crear_interfaz()
        self.cargar_datos_ejemplo()

    def cargar_datos_ejemplo(self):
        # Datos de ejemplo para mejor visualización
        est1 = EstudiantePregrado("Juan", "Pérez", 20, 4)
        est1.agregar_curso("Programación")
        est1.agregar_curso("Matemáticas")
        self.sistema.agregar_estudiante(est1)

        est2 = EstudiantePosgrado("María", "Gómez", 26, "Maestría en Ciencias")
        est2.agregar_curso("Investigación")
        est2.director_tesis = "Dr. García"
        self.sistema.agregar_estudiante(est2)

        self.actualizar_tabla()

    def crear_interfaz(self):
        # Notebook para diferentes pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Pestaña de lista de estudiantes
        self.tab_lista = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_lista, text="Lista de Estudiantes")

        # Pestaña de estadísticas
        self.tab_estadisticas = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_estadisticas, text="Estadísticas")

        # Configuración de la pestaña de lista
        self.crear_tab_lista()

        # Configuración de la pestaña de estadísticas
        self.crear_tab_estadisticas()

    def crear_tab_lista(self):
        # Frame para la búsqueda
        frame_busqueda = ttk.Frame(self.tab_lista)
        frame_busqueda.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(frame_busqueda, text="Buscar por nombre:").pack(side=tk.LEFT, padx=5)
        self.entry_busqueda = ttk.Entry(frame_busqueda, width=30)
        self.entry_busqueda.pack(side=tk.LEFT, padx=5)
        self.entry_busqueda.bind("<KeyRelease>", self.buscar_estudiantes)

        # Frame para la tabla
        frame_tabla = ttk.Frame(self.tab_lista)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tabla de estudiantes
        columnas = ("ID", "Nombre", "Apellido", "Edad", "Tipo")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        
        # Configurar las columnas
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=100)

        # Scrollbar para la tabla
        scrollbar = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=self.tabla.yview)
        self.tabla.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind para seleccionar un estudiante
        self.tabla.bind("<Double-1>", self.mostrar_detalles_estudiante)

        # Frame para los botones
        frame_botones = ttk.Frame(self.tab_lista)
        frame_botones.pack(fill=tk.X, padx=10, pady=10)

        # Botones de acción
        ttk.Button(frame_botones, text="Agregar Estudiante", command=self.abrir_ventana_agregar).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Editar Estudiante", command=self.abrir_ventana_editar).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Eliminar Estudiante", command=self.eliminar_estudiante).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Gestionar Cursos", command=self.abrir_ventana_cursos).pack(side=tk.LEFT, padx=5)

    def crear_tab_estadisticas(self):
        # Frame para las estadísticas
        frame_estadisticas = ttk.Frame(self.tab_estadisticas)
        frame_estadisticas.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Etiquetas para las estadísticas
        self.lbl_total_estudiantes = ttk.Label(frame_estadisticas, text="Total de Estudiantes: 0")
        self.lbl_total_estudiantes.pack(pady=10, anchor=tk.W)

        self.lbl_edad_promedio = ttk.Label(frame_estadisticas, text="Edad Promedio: 0")
        self.lbl_edad_promedio.pack(pady=10, anchor=tk.W)

        self.lbl_total_pregrado = ttk.Label(frame_estadisticas, text="Estudiantes de Pregrado: 0")
        self.lbl_total_pregrado.pack(pady=10, anchor=tk.W)

        self.lbl_total_posgrado = ttk.Label(frame_estadisticas, text="Estudiantes de Posgrado: 0")
        self.lbl_total_posgrado.pack(pady=10, anchor=tk.W)

        # Botón para actualizar estadísticas
        ttk.Button(frame_estadisticas, text="Actualizar Estadísticas", command=self.actualizar_estadisticas).pack(pady=10)

    def actualizar_tabla(self):
        # Limpiar la tabla
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        # Obtener todos los estudiantes y agregarlos a la tabla
        estudiantes = self.sistema.get_todos_estudiantes()
        for estudiante in estudiantes:
            self.tabla.insert("", tk.END, values=(
                estudiante.id,
                estudiante.nombre,
                estudiante.apellido,
                estudiante.edad,
                estudiante.get_tipo()
            ))

        # Actualizar estadísticas
        self.actualizar_estadisticas()

    def actualizar_estadisticas(self):
        estudiantes = self.sistema.get_todos_estudiantes()
        total_estudiantes = len(estudiantes)
        edad_promedio = self.sistema.calcular_edad_promedio()
        
        # Contar estudiantes por tipo
        pregrado = sum(1 for e in estudiantes if isinstance(e, EstudiantePregrado))
        posgrado = sum(1 for e in estudiantes if isinstance(e, EstudiantePosgrado))

        # Actualizar etiquetas
        self.lbl_total_estudiantes.config(text=f"Total de Estudiantes: {total_estudiantes}")
        self.lbl_edad_promedio.config(text=f"Edad Promedio: {edad_promedio:.1f}")
        self.lbl_total_pregrado.config(text=f"Estudiantes de Pregrado: {pregrado}")
        self.lbl_total_posgrado.config(text=f"Estudiantes de Posgrado: {posgrado}")

    def buscar_estudiantes(self, event=None):
        # Obtener el texto de búsqueda
        busqueda = self.entry_busqueda.get().strip()
        
        # Limpiar la tabla
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        
        # Si no hay texto de búsqueda, mostrar todos los estudiantes
        if not busqueda:
            self.actualizar_tabla()
            return
        
        # Buscar estudiantes por nombre
        estudiantes = self.sistema.buscar_estudiantes_por_nombre(busqueda)
        
        # Agregar resultados a la tabla
        for estudiante in estudiantes:
            self.tabla.insert("", tk.END, values=(
                estudiante.id,
                estudiante.nombre,
                estudiante.apellido,
                estudiante.edad,
                estudiante.get_tipo()
            ))

    def mostrar_detalles_estudiante(self, event=None):
        # Obtener el estudiante seleccionado
        item_seleccionado = self.tabla.selection()
        if not item_seleccionado:
            messagebox.showinfo("Información", "Seleccione un estudiante para ver sus detalles.")
            return

        # Obtener el ID del estudiante
        id_estudiante = self.tabla.item(item_seleccionado[0], "values")[0]
        
        # Buscar el estudiante
        estudiante = self.sistema.buscar_estudiante(id_estudiante)
        if not estudiante:
            messagebox.showerror("Error", "No se pudo encontrar al estudiante.")
            return
        
        # Mostrar los detalles del estudiante
        messagebox.showinfo("Detalles del Estudiante", estudiante.mostrar_informacion())

    def abrir_ventana_agregar(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Agregar Estudiante")
        ventana.geometry("500x500")
        ventana.resizable(False, False)
        ventana.configure(bg="#f0f0f0")
        
        # Hacer que la ventana sea modal
        ventana.transient(self.root)
        ventana.grab_set()
        
        # Frame para el formulario
        frame_formulario = ttk.Frame(ventana)
        frame_formulario.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Variables
        tipo_var = tk.StringVar(value="Pregrado")
        nombre_var = tk.StringVar()
        apellido_var = tk.StringVar()
        edad_var = tk.StringVar()
        semestre_var = tk.StringVar()
        programa_var = tk.StringVar()
        proyecto_var = tk.StringVar()
        director_var = tk.StringVar()
        tema_var = tk.StringVar()
        
        # Función para mostrar/ocultar campos según el tipo
        def actualizar_campos(*args):
            if tipo_var.get() == "Pregrado":
                lbl_semestre.grid(row=5, column=0, sticky=tk.W, pady=5)
                entry_semestre.grid(row=5, column=1, sticky=tk.W, pady=5)
                lbl_proyecto.grid(row=6, column=0, sticky=tk.W, pady=5)
                entry_proyecto.grid(row=6, column=1, sticky=tk.W, pady=5)
                
                lbl_programa.grid_forget()
                entry_programa.grid_forget()
                lbl_director.grid_forget()
                entry_director.grid_forget()
                lbl_tema.grid_forget()
                entry_tema.grid_forget()
            else:
                lbl_programa.grid(row=5, column=0, sticky=tk.W, pady=5)
                entry_programa.grid(row=5, column=1, sticky=tk.W, pady=5)
                lbl_director.grid(row=6, column=0, sticky=tk.W, pady=5)
                entry_director.grid(row=6, column=1, sticky=tk.W, pady=5)
                lbl_tema.grid(row=7, column=0, sticky=tk.W, pady=5)
                entry_tema.grid(row=7, column=1, sticky=tk.W, pady=5)
                
                lbl_semestre.grid_forget()
                entry_semestre.grid_forget()
                lbl_proyecto.grid_forget()
                entry_proyecto.grid_forget()
        
        # Validación de campos
        def validar_numeros(P):
            return P == "" or P.isdigit()
        
        def validar_letras(P):
            return bool(re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]*$', P))
        
        # Registro de validaciones
        vcmd_numeros = ventana.register(validar_numeros)
        vcmd_letras = ventana.register(validar_letras)
        
        # Agregar campos del formulario
        ttk.Label(frame_formulario, text="Tipo de Estudiante:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Radiobutton(frame_formulario, text="Pregrado", variable=tipo_var, value="Pregrado", command=actualizar_campos).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(frame_formulario, text="Posgrado", variable=tipo_var, value="Posgrado", command=actualizar_campos).grid(row=0, column=2, sticky=tk.W, pady=5)
        
        ttk.Label(frame_formulario, text="Nombre:").grid(row=1, column=0, sticky=tk.W, pady=5)
        entry_nombre = ttk.Entry(frame_formulario, textvariable=nombre_var, validate="key", validatecommand=(vcmd_letras, '%P'))
        entry_nombre.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame_formulario, text="Apellido:").grid(row=2, column=0, sticky=tk.W, pady=5)
        entry_apellido = ttk.Entry(frame_formulario, textvariable=apellido_var, validate="key", validatecommand=(vcmd_letras, '%P'))
        entry_apellido.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame_formulario, text="Edad:").grid(row=3, column=0, sticky=tk.W, pady=5)
        entry_edad = ttk.Entry(frame_formulario, textvariable=edad_var, width=5, validate="key", validatecommand=(vcmd_numeros, '%P'))
        entry_edad.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Campos específicos para Pregrado
        lbl_semestre = ttk.Label(frame_formulario, text="Semestre:")
        entry_semestre = ttk.Entry(frame_formulario, textvariable=semestre_var, width=5, validate="key", validatecommand=(vcmd_numeros, '%P'))
        
        lbl_proyecto = ttk.Label(frame_formulario, text="Proyecto Final (opcional):")
        entry_proyecto = ttk.Entry(frame_formulario, textvariable=proyecto_var)
        
        # Campos específicos para Posgrado
        lbl_programa = ttk.Label(frame_formulario, text="Programa:")
        entry_programa = ttk.Entry(frame_formulario, textvariable=programa_var)
        
        lbl_director = ttk.Label(frame_formulario, text="Director de Tesis (opcional):")
        entry_director = ttk.Entry(frame_formulario, textvariable=director_var, validate="key", validatecommand=(vcmd_letras, '%P'))
        
        lbl_tema = ttk.Label(frame_formulario, text="Tema de Tesis (opcional):")
        entry_tema = ttk.Entry(frame_formulario, textvariable=tema_var)
        
        # Mostrar los campos iniciales
        actualizar_campos()
        
        # Tooltips para los campos
        self.crear_tooltip(entry_nombre, "Ingrese nombres (solo letras, 2-30 caracteres)")
        self.crear_tooltip(entry_apellido, "Ingrese apellidos (solo letras, 2-30 caracteres)")
        self.crear_tooltip(entry_edad, "Ingrese edad (16-100)")
        self.crear_tooltip(entry_semestre, "Ingrese semestre (1-12)")
        self.crear_tooltip(entry_proyecto, "Ingrese nombre del proyecto (opcional)")
        self.crear_tooltip(entry_programa, "Ingrese programa de posgrado (3-50 caracteres)")
        self.crear_tooltip(entry_director, "Ingrese nombre del director de tesis (opcional)")
        self.crear_tooltip(entry_tema, "Ingrese tema de tesis (opcional)")
        
        # Botones
        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Button(frame_botones, text="Guardar", command=lambda: self.guardar_estudiante(
            tipo_var.get(),
            nombre_var.get(),
            apellido_var.get(),
            edad_var.get(),
            semestre_var.get(),
            programa_var.get(),
            proyecto_var.get(),
            director_var.get(),
            tema_var.get(),
            ventana
        )).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_botones, text="Cancelar", command=ventana.destroy).pack(side=tk.LEFT, padx=5)

    def crear_tooltip(self, widget, text):
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Crear una ventana emergente
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(self.tooltip, text=text, background="#FFFFDD", relief="solid", borderwidth=1)
            label.pack()
            
        def leave(event):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def guardar_estudiante(self, tipo, nombre, apellido, edad, semestre, programa, proyecto, director, tema, ventana):
        # Validar campos comunes
        errores = []
        
        if not Validadores.validar_nombre(nombre):
            errores.append("Nombre: debe contener solo letras y tener entre 2 y 30 caracteres.")
        
        if not Validadores.validar_nombre(apellido):
            errores.append("Apellido: debe contener solo letras y tener entre 2 y 30 caracteres.")
        
        if not Validadores.validar_edad(edad):
            errores.append("Edad: debe ser un número entre 16 y 100.")
        
        # Validar campos específicos
        if tipo == "Pregrado":
            if not Validadores.validar_semestre(semestre):
                errores.append("Semestre: debe ser un número entre 1 y 12.")
            
            if proyecto and not Validadores.validar_proyecto_final(proyecto):
                errores.append("Proyecto Final: debe tener entre 5 y 100 caracteres.")
        else:
            if not Validadores.validar_programa(programa):
                errores.append("Programa: debe tener entre 3 y 50 caracteres.")
            
            if director and not Validadores.validar_director_tesis(director):
                errores.append("Director de Tesis: debe contener solo letras y tener entre 2 y 30 caracteres.")
            
            if tema and not Validadores.validar_tema_tesis(tema):
                errores.append("Tema de Tesis: debe tener entre 5 y 100 caracteres.")
        
        # Si hay errores, mostrarlos y no guardar
        if errores:
            messagebox.showerror("Error de Validación", "\n".join(errores))
            return
        
        # Convertir edad a entero
        edad_int = int(edad)
        
        # Crear el estudiante según el tipo
        if tipo == "Pregrado":
            estudiante = EstudiantePregrado(nombre, apellido, edad_int, int(semestre))
            if proyecto:
                estudiante.proyecto_final = proyecto
        else:
            estudiante = EstudiantePosgrado(nombre, apellido, edad_int, programa)
            if director:
                estudiante.director_tesis = director
            if tema:
                estudiante.tema_tesis = tema
        
        # Agregar cursos seleccionados
        cursos_seleccionados = self.obtener_cursos_seleccionados()  # Implementa esta función
        for curso in cursos_seleccionados:
            estudiante.agregar_curso(curso)
        
        # Agregar el estudiante al sistema
        if self.sistema.agregar_estudiante(estudiante):
            messagebox.showinfo("Éxito", "Estudiante agregado correctamente.")
            ventana.destroy()
            self.actualizar_tabla()
        else:
            messagebox.showerror("Error", "No se pudo agregar al estudiante.")

    def abrir_ventana_editar(self):
        # Obtener el estudiante seleccionado
        item_seleccionado = self.tabla.selection()
        if not item_seleccionado:
            messagebox.showinfo("Información", "Seleccione un estudiante para editar.")
            return

        # Obtener el ID del estudiante
        id_estudiante = self.tabla.item(item_seleccionado[0], "values")[0]
        
        # Buscar el estudiante
        estudiante = self.sistema.buscar_estudiante(id_estudiante)
        if not estudiante:
            messagebox.showerror("Error", "No se pudo encontrar al estudiante.")
            return
        
        # Crear la ventana de edición
        ventana = tk.Toplevel(self.root)
        ventana.title(f"Editar Estudiante - {estudiante.nombre} {estudiante.apellido}")
        ventana.geometry("500x500")
        ventana.resizable(False, False)
        ventana.configure(bg="#f0f0f0")
        
        # Hacer que la ventana sea modal
        ventana.transient(self.root)
        ventana.grab_set()
        
        # Frame para el formulario
        frame_formulario = ttk.Frame(ventana)
        frame_formulario.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Variables
        nombre_var = tk.StringVar(value=estudiante.nombre)
        apellido_var = tk.StringVar(value=estudiante.apellido)
        edad_var = tk.StringVar(value=str(estudiante.edad))
        
        # Validación de campos
        def validar_numeros(P):
            return P == "" or P.isdigit()
        
        def validar_letras(P):
            return bool(re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]*$', P))
        
        # Registro de validaciones
        vcmd_numeros = ventana.register(validar_numeros)
        vcmd_letras = ventana.register(validar_letras)
        
        # Agregar campos comunes
        ttk.Label(frame_formulario, text="Nombre:").grid(row=0, column=0, sticky=tk.W, pady=5)
        entry_nombre = ttk.Entry(frame_formulario, textvariable=nombre_var, validate="key", validatecommand=(vcmd_letras, '%P'))
        entry_nombre.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame_formulario, text="Apellido:").grid(row=1, column=0, sticky=tk.W, pady=5)
        entry_apellido = ttk.Entry(frame_formulario, textvariable=apellido_var, validate="key", validatecommand=(vcmd_letras, '%P'))
        entry_apellido.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame_formulario, text="Edad:").grid(row=2, column=0, sticky=tk.W, pady=5)
        entry_edad = ttk.Entry(frame_formulario, textvariable=edad_var, width=5, validate="key", validatecommand=(vcmd_numeros, '%P'))
        entry_edad.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Campos específicos según el tipo de estudiante
        if isinstance(estudiante, EstudiantePregrado):
            ttk.Label(frame_formulario, text="Tipo de Estudiante:").grid(row=3, column=0, sticky=tk.W, pady=5)
            ttk.Label(frame_formulario, text="Pregrado").grid(row=3, column=1, sticky=tk.W, pady=5)
            
            semestre_var = tk.StringVar(value=str(estudiante.semestre))
            ttk.Label(frame_formulario, text="Semestre:").grid(row=4, column=0, sticky=tk.W, pady=5)
            entry_semestre = ttk.Entry(frame_formulario, textvariable=semestre_var, width=5, validate="key", validatecommand=(vcmd_numeros, '%P'))
            entry_semestre.grid(row=4, column=1, sticky=tk.W, pady=5)
            
            proyecto_var = tk.StringVar(value=estudiante.proyecto_final if estudiante.proyecto_final else "")
            ttk.Label(frame_formulario, text="Proyecto Final (opcional):").grid(row=5, column=0, sticky=tk.W, pady=5)
            entry_proyecto = ttk.Entry(frame_formulario, textvariable=proyecto_var)
            entry_proyecto.grid(row=5, column=1, sticky=tk.W, pady=5)
            
            # Tooltips
            self.crear_tooltip(entry_semestre, "Ingrese semestre (1-12)")
            self.crear_tooltip(entry_proyecto, "Ingrese nombre del proyecto (opcional)")
            
            # Botón para guardar
            ttk.Button(frame_formulario, text="Guardar", command=lambda: self.guardar_edicion_pregrado(
                id_estudiante,
                nombre_var.get(),
                apellido_var.get(),
                edad_var.get(),
                semestre_var.get(),
                proyecto_var.get(),
                ventana
            )).grid(row=6, column=0, pady=20)
        
        elif isinstance(estudiante, EstudiantePosgrado):
            ttk.Label(frame_formulario, text="Tipo de Estudiante:").grid(row=3, column=0, sticky=tk.W, pady=5)
            ttk.Label(frame_formulario, text="Posgrado").grid(row=3, column=1, sticky=tk.W, pady=5)
            
            programa_var = tk.StringVar(value=estudiante.programa)
            ttk.Label(frame_formulario, text="Programa:").grid(row=4, column=0, sticky=tk.W, pady=5)
            entry_programa = ttk.Entry(frame_formulario, textvariable=programa_var)
            entry_programa.grid(row=4, column=1, sticky=tk.W, pady=5)
            
            director_var = tk.StringVar(value=estudiante.director_tesis if estudiante.director_tesis else "")
            ttk.Label(frame_formulario, text="Director de Tesis (opcional):").grid(row=5, column=0, sticky=tk.W, pady=5)
            entry_director = ttk.Entry(frame_formulario, textvariable=director_var, validate="key", validatecommand=(vcmd_letras, '%P'))
            entry_director.grid(row=5, column=1, sticky=tk.W, pady=5)
            
            tema_var = tk.StringVar(value=estudiante.tema_tesis if estudiante.tema_tesis else "")
            ttk.Label(frame_formulario, text="Tema de Tesis (opcional):").grid(row=6, column=0, sticky=tk.W, pady=5)
            entry_tema = ttk.Entry(frame_formulario, textvariable=tema_var)
            entry_tema.grid(row=6, column=1, sticky=tk.W, pady=5)
            
            # Tooltips
            self.crear_tooltip(entry_programa, "Ingrese programa de posgrado (3-50 caracteres)")
            self.crear_tooltip(entry_director, "Ingrese nombre del director de tesis (opcional)")
            self.crear_tooltip(entry_tema, "Ingrese tema de tesis (opcional)")
            
            # Botón para guardar
            ttk.Button(frame_formulario, text="Guardar", command=lambda: self.guardar_edicion_posgrado(
                id_estudiante,
                nombre_var.get(),
                apellido_var.get(),
                edad_var.get(),
                programa_var.get(),
                director_var.get(),
                tema_var.get(),
                ventana
            )).grid(row=7, column=0, pady=20)
        
        # Tooltips para campos comunes
        self.crear_tooltip(entry_nombre, "Ingrese nombres (solo letras, 2-30 caracteres)")
        self.crear_tooltip(entry_apellido, "Ingrese apellidos (solo letras, 2-30 caracteres)")
        self.crear_tooltip(entry_edad, "Ingrese edad (16-100)")
        
        # Botón para cancelar
        ttk.Button(frame_formulario, text="Cancelar", command=ventana.destroy).grid(row=6 if isinstance(estudiante, EstudiantePregrado) else 7, column=1, pady=20)

    def guardar_edicion_pregrado(self, id_estudiante, nombre, apellido, edad, semestre, proyecto, ventana):
        # Validar campos
        errores = []
        
        if not Validadores.validar_nombre(nombre):
            errores.append("Nombre: debe contener solo letras y tener entre 2 y 30 caracteres.")
        
        if not Validadores.validar_nombre(apellido):
            errores.append("Apellido: debe contener solo letras y tener entre 2 y 30 caracteres.")
        
        if not Validadores.validar_edad(edad):
            errores.append("Edad: debe ser un número entre 16 y 100.")
        
        if not Validadores.validar_semestre(semestre):
            errores.append("Semestre: debe ser un número entre 1 y 12.")
        
        if proyecto and not Validadores.validar_proyecto_final(proyecto):
            errores.append("Proyecto Final: debe tener entre 5 y 100 caracteres.")
        
        # Si hay errores, mostrarlos y no guardar
        if errores:
            messagebox.showerror("Error de Validación", "\n".join(errores))
            return
        
        # Preparar datos para la edición
        datos = {
            "nombre": nombre,
            "apellido": apellido,
            "edad": int(edad),
            "semestre": int(semestre),
            "proyecto_final": proyecto
        }
        
        # Editar el estudiante
        if self.sistema.editar_estudiante(id_estudiante, datos):
            messagebox.showinfo("Éxito", "Estudiante editado correctamente.")
            ventana.destroy()
            self.actualizar_tabla()
        else:
            messagebox.showerror("Error", "No se pudo editar al estudiante.")

    def guardar_edicion_posgrado(self, id_estudiante, nombre, apellido, edad, programa, director, tema, ventana):
        # Validar campos
        errores = []
        
        if not Validadores.validar_nombre(nombre):
            errores.append("Nombre: debe contener solo letras y tener entre 2 y 30 caracteres.")
        
        if not Validadores.validar_nombre(apellido):
            errores.append("Apellido: debe contener solo letras y tener entre 2 y 30 caracteres.")
        
        if not Validadores.validar_edad(edad):
            errores.append("Edad: debe ser un número entre 16 y 100.")
        
        if not Validadores.validar_programa(programa):
            errores.append("Programa: debe tener entre 3 y 50 caracteres.")
        
        if director and not Validadores.validar_director_tesis(director):
            errores.append("Director de Tesis: debe contener solo letras y tener entre 2 y 30 caracteres.")
        
        if tema and not Validadores.validar_tema_tesis(tema):
            errores.append("Tema de Tesis: debe tener entre 5 y 100 caracteres.")
        
        # Si hay errores, mostrarlos y no guardar
        if errores:
            messagebox.showerror("Error de Validación", "\n".join(errores))
            return
        
        # Preparar datos para la edición
        datos = {
            "nombre": nombre,
            "apellido": apellido,
            "edad": int(edad),
            "programa": programa,
            "director_tesis": director,
            "tema_tesis": tema
        }
        
        # Editar el estudiante
        if self.sistema.editar_estudiante(id_estudiante, datos):
            messagebox.showinfo("Éxito", "Estudiante editado correctamente.")
            ventana.destroy()
            self.actualizar_tabla()
        else:
            messagebox.showerror("Error", "No se pudo editar al estudiante.")

    def eliminar_estudiante(self):
        # Obtener el estudiante seleccionado
        item_seleccionado = self.tabla.selection()
        if not item_seleccionado:
            messagebox.showinfo("Información", "Seleccione un estudiante para eliminar.")
            return

        # Obtener el ID del estudiante
        id_estudiante = self.tabla.item(item_seleccionado[0], "values")[0]
        nombre_estudiante = self.tabla.item(item_seleccionado[0], "values")[1]
        apellido_estudiante = self.tabla.item(item_seleccionado[0], "values")[2]
        
        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar a {nombre_estudiante} {apellido_estudiante}?"):
            return
        
        # Eliminar el estudiante
        if self.sistema.eliminar_estudiante(id_estudiante):
            messagebox.showinfo("Éxito", "Estudiante eliminado correctamente.")
            self.actualizar_tabla()
        else:
            messagebox.showerror("Error", "No se pudo eliminar al estudiante.")

    def abrir_ventana_cursos(self):
        # Obtener el estudiante seleccionado
        item_seleccionado = self.tabla.selection()
        if not item_seleccionado:
            messagebox.showinfo("Información", "Seleccione un estudiante para gestionar sus cursos.")
            return

        # Obtener el ID del estudiante
        id_estudiante = self.tabla.item(item_seleccionado[0], "values")[0]

        # Buscar el estudiante
        estudiante = self.sistema.buscar_estudiante(id_estudiante)
        if not estudiante:
            messagebox.showerror("Error", "No se pudo encontrar al estudiante.")
            return

        # Crear la ventana de cursos
        ventana = tk.Toplevel(self.root)
        ventana.title(f"Gestionar Cursos - {estudiante.nombre} {estudiante.apellido}")
        ventana.geometry("500x400")
        ventana.resizable(False, False)
        ventana.configure(bg="#f0f0f0")

        # Hacer que la ventana sea modal
        ventana.transient(self.root)
        ventana.grab_set()

        # Frame para la lista de cursos
        frame_cursos = ttk.Frame(ventana)
        frame_cursos.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Lista de cursos
        ttk.Label(frame_cursos, text="Cursos Inscritos:").grid(row=0, column=0, sticky=tk.W, pady=5)

        # Listbox para mostrar cursos
        listbox_cursos = tk.Listbox(frame_cursos, width=40, height=10)
        listbox_cursos.grid(row=1, column=0, sticky=tk.W, pady=5)

        # Scrollbar para la listbox
        scrollbar = ttk.Scrollbar(frame_cursos, orient=tk.VERTICAL, command=listbox_cursos.yview)
        scrollbar.grid(row=1, column=1, sticky=tk.NS)
        listbox_cursos.configure(yscrollcommand=scrollbar.set)

        # Cargar cursos actuales
        cursos = estudiante.cursos
        for curso in cursos:
            listbox_cursos.insert(tk.END, curso)

        # Frame para agregar nuevo curso
        frame_nuevo = ttk.Frame(frame_cursos)
        frame_nuevo.grid(row=2, column=0, sticky=tk.W, pady=15)

        ttk.Label(frame_nuevo, text="Nuevo Curso:").grid(row=0, column=0, sticky=tk.W, pady=5)
        nuevo_curso_var = tk.StringVar()
        entry_nuevo = ttk.Entry(frame_nuevo, textvariable=nuevo_curso_var, width=30)
        entry_nuevo.grid(row=0, column=1, sticky=tk.W, pady=5)

        # Combobox para seleccionar cursos existentes
        ttk.Label(frame_nuevo, text="Seleccionar Curso:").grid(row=1, column=0, sticky=tk.W, pady=5)
        combobox_cursos = ttk.Combobox(frame_nuevo, values=cursos_universidad.get_cursos(), width=27)
        combobox_cursos.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Función para agregar un curso
        def agregar_curso():
            curso = nuevo_curso_var.get().strip()
            if not curso:
                messagebox.showerror("Error", "El nombre del curso no puede estar vacío.")
                return

            if len(curso) < 3 or len(curso) > 50:
                messagebox.showerror("Error", "El nombre del curso debe tener entre 3 y 50 caracteres.")
                return

            if curso in estudiante.cursos:
                messagebox.showerror("Error", "El curso ya está en la lista.")
                return

            estudiante.agregar_curso(curso)
            listbox_cursos.insert(tk.END, curso)
            nuevo_curso_var.set("")
            messagebox.showinfo("Éxito", f"Curso '{curso}' agregado correctamente.")

        # Función para seleccionar un curso existente
        def seleccionar_curso():
            curso = combobox_cursos.get()
            if not curso:
                messagebox.showerror("Error", "Seleccione un curso de la lista.")
                return

            if curso in estudiante.cursos:
                messagebox.showerror("Error", "El curso ya está en la lista.")
                return

            estudiante.agregar_curso(curso)
            listbox_cursos.insert(tk.END, curso)
            messagebox.showinfo("Éxito", f"Curso '{curso}' agregado correctamente.")

        # Función para eliminar un curso
        def eliminar_curso():
            seleccionado = listbox_cursos.curselection()
            if not seleccionado:
                messagebox.showinfo("Información", "Seleccione un curso para eliminar.")
                return

            curso = listbox_cursos.get(seleccionado[0])
            if estudiante.eliminar_curso(curso):
                listbox_cursos.delete(seleccionado[0])
                messagebox.showinfo("Éxito", f"Curso '{curso}' eliminado correctamente.")
            else:
                messagebox.showerror("Error", "No se pudo eliminar el curso.")

        # Botones
        ttk.Button(frame_nuevo, text="Agregar", command=agregar_curso).grid(row=0, column=2, padx=5)
        ttk.Button(frame_nuevo, text="Seleccionar", command=seleccionar_curso).grid(row=1, column=2, padx=5)
        ttk.Button(frame_cursos, text="Eliminar Curso", command=eliminar_curso).grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Button(frame_cursos, text="Cerrar", command=ventana.destroy).grid(row=4, column=0, sticky=tk.W, pady=15)

# Punto de entrada principal
def main():
    root = tk.Tk()
    app = AplicacionGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()