import os
import random
import re
import unicodedata
import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Union

import pandas as pd
import openpyxl
from tkcalendar import Calendar, DateEntry
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


# Validadores para los campos del formulario
class Validadores:
    @staticmethod
    def validar_nombre(nombre: str) -> bool:
        return bool(re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]{2,30}$', nombre))
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normaliza texto: elimina acentos, convierte a minúsculas y remueve caracteres especiales"""
        normalized = unicodedata.normalize('NFKD', text.lower()).encode('ascii', 'ignore').decode('ascii')
        return re.sub(r'[^\w\s]', '', normalized).strip()
    
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

# Clase abstracta Estudiante
class Estudiante(ABC):
    def __init__(self, nombre: str, programa: str, apellido: str,identificacion: int, fecha_nacimiento: int, id_estudiante: str = None,  edad: int = None):
        self.__nombre = nombre
        self.__apellido = apellido
        self.__nombre_completo = Validadores.normalize_text(nombre + apellido)
        self.__identificacion = identificacion
        self.__fecha_nacimiento = fecha_nacimiento
        self.__id = id_estudiante if id_estudiante else str(uuid.uuid4())[:8]
        self.__cursos = []
        self.__programa = programa

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
    def identificacion(self) -> int:
        return self.__identificacion
    @identificacion.setter
    def identificacion(self, identificacion: int) -> None:
        self.__identificacion = identificacion
        
    @property
    def fecha_nacimiento(self) -> str:
        return self.__fecha_nacimiento

    @fecha_nacimiento.setter
    def fecha_nacimiento(self, value: str) -> None:
        self.__fecha_nacimiento = value

    @property
    def programa(self) -> str:
        return self.__programa
    
    @programa.setter
    def programa(self, programa: str) -> None:
        self.__programa = programa

    @property
    def id(self) -> str:
        return self.__id

    @property
    def cursos(self) -> List[str]:
        return self.__cursos.copy()
    
    @property
    def edad(self) -> int:
        try:
            fecha_nacimiento = datetime.strptime(self.fecha_nacimiento, "%Y-%m-%d").date()
            today = date.today()
            Edad = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            return Edad
        except ValueError:
            return 0
    
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
    def __init__(self, nombre: str, apellido: str, identificacion:int, fecha_nacimiento:str, programa: str, semestre: int, id_estudiante: str = None, edad: int = None):
        super().__init__(nombre, programa, apellido, identificacion, fecha_nacimiento, id_estudiante, edad)
        self.__semestre = semestre

    @property
    def semestre(self) -> int:
        return self.__semestre

    @semestre.setter
    def semestre(self, semestre: int) -> None:
        self.__semestre = semestre


    def mostrar_informacion(self) -> str:
        info = f"Estudiante de Pregrado\nNombre: {self.nombre} {self.apellido}\n"
        info += f"ID: {self.id}\nEdad: {self.edad}\nSemestre: {self.__semestre}\n"
        info += f"Cursos: {', '.join(self.cursos) if self.cursos else 'Ninguno'}"
        return info

    def get_tipo(self) -> str:
        return "Pregrado"


# Clase concreta EstudiantePosgrado
class EstudiantePosgrado(Estudiante):
    def __init__(self, nombre: str, apellido: str, identificacion: int, fecha_nacimiento: str, programa: str, pregrado:str, id_estudiante: str = None, edad: int = None):
        super().__init__(nombre, programa, apellido, identificacion, fecha_nacimiento, id_estudiante, edad)
        self.__pregrado = pregrado
        
    @property
    def pregrado(self) -> str:
        return self.__pregrado
    @pregrado.setter
    def pregrado(self, pregrado: str) -> None:
        self.__pregrado = pregrado
        
    def mostrar_informacion(self) -> str:
        info = f"Estudiante de Posgrado\nNombre: {self.nombre} {self.apellido}\n"
        info += f"ID: {self.id}\nEdad: {self.edad}\nPrograma: {self.__programa}\n"
        info += f"Pregrado: {self.__pregrado}\n"
        info += f"Cursos: {', '.join(self.cursos) if self.cursos else 'Ninguno'}"
        return info

    def get_tipo(self) -> str:
        return "Posgrado"

class CRUDExcel:
    def __init__(self, file_name="data.xlsx"):
        self.file_name = file_name
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_name):
            with pd.ExcelWriter(self.file_name, engine='openpyxl') as writer:
                df = pd.DataFrame()  # Crea un DataFrame vacío
                df.to_excel(writer, sheet_name="Hoja1", index=False)  # Agrega una hoja inicial


    def _get_sheet(self, sheet_name):
        try:
            return pd.read_excel(self.file_name, sheet_name=sheet_name, engine="openpyxl")
        except ValueError:
            return pd.DataFrame()


    def create(self, sheet_name: str, data):
        df = self._get_sheet(sheet_name)

        # Asegurar que data sea una lista de diccionarios
        if isinstance(data, dict):
            data = [data]  # Convertir a lista si es un solo diccionario

        # Convertir listas dentro de los diccionarios a cadenas separadas por comas
        processed_data = []
        for entry in data:
            processed_entry = {k: (", ".join(v) if isinstance(v, list) else v) for k, v in entry.items()}
            processed_data.append(processed_entry)

        df = pd.concat([df, pd.DataFrame(processed_data)], ignore_index=True)

        with pd.ExcelWriter(self.file_name, mode='a', if_sheet_exists='replace', engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)




    def read(self, sheet_name: str, filter_by: dict = None):
        df = self._get_sheet(sheet_name)
        if filter_by:
            for key, value in filter_by.items():
                df = df[df[key] == value]
        return df

    def update(self, sheet_name: str, filter_by: dict, updates: dict):
        df = self._get_sheet(sheet_name)
        index = df
        for key, value in filter_by.items():
            index = index[index[key] == value]
        
        if not index.empty:
            for idx in index.index:
                for key, value in updates.items():
                    df.at[idx, key] = value
            with pd.ExcelWriter(self.file_name, mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, index=False, sheet_name=sheet_name)
            return True
        return False

    def delete(self, sheet_name: str, filter_by: dict):
        df = self._get_sheet(sheet_name)
        for key, value in filter_by.items():
            df = df[df[key] != value]
        with pd.ExcelWriter(self.file_name, mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)


class SistemaUniversidad:
    def __init__(self, db_file="data.xlsx"):
        self.db = CRUDExcel(db_file)
        self._cargar_estudiantes()
        self._cargar_cursos()
        self._cargar_programas()
        self.identificaciones = set(est.identificacion for est in self.estudiantes.values())


    def _cargar_estudiantes(self):
        self.estudiantes = {}
        try:
            df_pregrado = self.db.read("EstudiantesPregrado")
            df_posgrado = self.db.read("EstudiantesPosgrado")
            
            for _, row in df_pregrado.iterrows():
                estudiante = EstudiantePregrado(
                    nombre=row['nombre'],
                    apellido=row['apellido'],
                    programa=row['programa'],
                    identificacion=row['identificacion'],
                    fecha_nacimiento=row['fecha_nacimiento'],
                    semestre=row['semestre'],
                    id_estudiante=row['id']
                )
                if 'cursos' in row and isinstance(row['cursos'], str):
                    for curso in row['cursos'].split(', '):
                        if curso:
                            estudiante.agregar_curso(curso)
                self.estudiantes[row['id']] = estudiante
                
            for _, row in df_posgrado.iterrows():
                estudiante = EstudiantePosgrado(
                    nombre=row['nombre'],
                    apellido=row['apellido'],
                    programa=row['programa'],
                    identificacion=row['identificacion'],
                    fecha_nacimiento=row['fecha_nacimiento'],
                    pregrado=row['pregrado'],
                    id_estudiante=row['id']
                )
                if 'cursos' in row and isinstance(row['cursos'], str):
                    for curso in row['cursos'].split(', '):
                        if curso:
                            estudiante.agregar_curso(curso)
                self.estudiantes[row['id']] = estudiante
        except Exception as e:
            print(f"Error al cargar estudiantes: {e}")
            
    def _cargar_programas(self):
        try:
            df_programas = self.db.read("Programas")
            if not df_programas.empty:
                self.programas = df_programas.to_dict('records')  # Guardar como lista de diccionarios
            else:
                # Programas predeterminados si no existen
                self.programas = [
                    {"nombre": "Ingeniería de Sistemas", "tipo": "Pregrado"},
                    {"nombre": "Ingeniería Civil", "tipo": "Pregrado"},
                    {"nombre": "Medicina", "tipo": "Pregrado"},
                    {"nombre": "Maestría en Ciencias de la Computación", "tipo": "Posgrado"},
                    {"nombre": "Doctorado en Ingeniería", "tipo": "Posgrado"},
                    {"nombre": "Especialización en Gerencia de Proyectos", "tipo": "Posgrado"},
                ]
                self.db.create("Programas", self.programas)

            # Ordenar la lista de programas alfabéticamente
            self.programas.sort(key=lambda x: x["nombre"])
        except Exception as e:
            print(f"Error al cargar programas: {e}")
            self.programas = []

    def _cargar_cursos(self):
        try:
            df_cursos = self.db.read("Cursos")
            if not df_cursos.empty:
                self.cursos = df_cursos.to_dict('records')  # Guardar como lista de diccionarios
            else:
                # Cursos predeterminados si no existen
                self.cursos = [
                    {"nombre": "Introducción a la Programación", "tipo": "Pregrado"},
                    {"nombre": "Matemáticas Discretas", "tipo": "Pregrado"},
                    {"nombre": "Cálculo I", "tipo": "Pregrado"},
                    {"nombre": "Inteligencia Artificial", "tipo": "Posgrado"},
                    {"nombre": "Seguridad Informática", "tipo": "Posgrado"},
                    {"nombre": "Compiladores", "tipo": "Posgrado"},
                ]
                self.db.create("Cursos", self.cursos)

            # Ordenar la lista de cursos alfabéticamente
            self.cursos.sort(key=lambda x: x["nombre"])
        except Exception as e:
            print(f"Error al cargar cursos: {e}")
            self.cursos = []

    def agregar_estudiante(self, estudiante: Estudiante) -> bool:
        if estudiante.identificacion in self.identificaciones:
            messagebox.showwarning("Identificación duplicada", "El número de identificación ya existe.")
            return False
        
        if estudiante.id in self.estudiantes:
            return False
        
        self.estudiantes[estudiante.id] = estudiante
        self.identificaciones.add(estudiante.identificacion)
        
        data = {
            "id": estudiante.id,
            "nombre": estudiante.nombre,
            "apellido": estudiante.apellido,
            "programa": estudiante.programa,
            "identificacion": estudiante.identificacion,
            "fecha_nacimiento": estudiante.fecha_nacimiento,
            "cursos": estudiante.cursos
        }
        
        if estudiante.get_tipo() == "Pregrado":
            data["semestre"] = estudiante.semestre
            self.db.create("EstudiantesPregrado", data)
        else:
            data["pregrado"] = estudiante.pregrado
            self.db.create("EstudiantesPosgrado", data)
        
        return True
    
    def buscar_estudiante(self, id_estudiante: str) -> Optional[Estudiante]:
        return self.estudiantes.get(id_estudiante)
    
    def buscar_estudiantes_por_criterio(self, criterio: str, valor: str) -> List[Estudiante]:
        resultados = []
        valor_normalizado = Validadores.normalize_text(valor)
        
        for estudiante in self.estudiantes.values():
            if criterio == "nombre":
                nombre_completo = Validadores.normalize_text(estudiante.nombre + " " + estudiante.apellido)
                if valor_normalizado in nombre_completo:
                    resultados.append(estudiante)
            elif criterio == "programa" and valor_normalizado in Validadores.normalize_text(estudiante.programa):
                resultados.append(estudiante)
            elif criterio == "id" and valor in estudiante.id:
                resultados.append(estudiante)
        
        return resultados
    
    def editar_estudiante(self, id_estudiante: str, datos: Dict[str, any]) -> bool:
        estudiante = self.buscar_estudiante(id_estudiante)
        if not estudiante:
            return False
        
        # Actualizar atributos del estudiante
        if "nombre" in datos:
            estudiante.nombre = datos["nombre"]
        if "apellido" in datos:
            estudiante.apellido = datos["apellido"]
        if "programa" in datos:
            estudiante.programa = datos["programa"]
        if "fecha_nacimiento" in datos:
            estudiante.fecha_nacimiento = datos["fecha_nacimiento"]
        
        # Atributos específicos según el tipo de estudiante
        if estudiante.get_tipo() == "Pregrado" and "semestre" in datos:
            estudiante.semestre = datos["semestre"]
            self.db.update("EstudiantesPregrado", {"id": id_estudiante}, datos)
        elif estudiante.get_tipo() == "Posgrado" and "pregrado" in datos:
            estudiante.pregrado = datos["pregrado"]
            self.db.update("EstudiantesPosgrado", {"id": id_estudiante}, datos)
        
        return True
    
    def eliminar_estudiante(self, id_estudiante: str) -> bool:
        estudiante = self.buscar_estudiante(id_estudiante)
        if not estudiante:
            return False
        
        if estudiante.get_tipo() == "Pregrado":
            self.db.delete("EstudiantesPregrado", {"id": id_estudiante})
        else:
            self.db.delete("EstudiantesPosgrado", {"id": id_estudiante})
        
        del self.estudiantes[id_estudiante]
        return True
    
    def agregar_curso_a_estudiante(self, id_estudiante: str, curso: str) -> bool:
        estudiante = self.buscar_estudiante(id_estudiante)
        if not estudiante:
            return False
        
        estudiante.agregar_curso(curso)
        
        cursos_str = ", ".join(estudiante.cursos)
        if estudiante.get_tipo() == "Pregrado":
            self.db.update("EstudiantesPregrado", {"id": id_estudiante}, {"cursos": cursos_str})
        else:
            self.db.update("EstudiantesPosgrado", {"id": id_estudiante}, {"cursos": cursos_str})
        
        return True
    
    def eliminar_curso_de_estudiante(self, id_estudiante: str, curso: str) -> bool:
        estudiante = self.buscar_estudiante(id_estudiante)
        if not estudiante:
            return False
        
        if not estudiante.eliminar_curso(curso):
            return False
        
        cursos_str = ", ".join(estudiante.cursos)
        if estudiante.get_tipo() == "Pregrado":
            self.db.update("EstudiantesPregrado", {"id": id_estudiante}, {"cursos": cursos_str})
        else:
            self.db.update("EstudiantesPosgrado", {"id": id_estudiante}, {"cursos": cursos_str})
        
        return True
    
    def calcular_edad_promedio(self) -> float:
        if not self.estudiantes:
            return 0
        
        total_edad = sum(estudiante.edad for estudiante in self.estudiantes.values())
        return total_edad / len(self.estudiantes)
    
    def agregar_programa(self, programa: dict) -> bool:
        if programa in self.programas:
            return False
        
        self.programas.append(programa)
        self.db.create("Programas", {"nombre": programa["nombre"], "tipo": programa["tipo"]})
        return True
    
    def agregar_curso(self, curso: dict) -> bool:
        if curso in self.cursos:
            return False
        
        self.cursos.append(curso)
        self.db.create("Cursos", {"nombre": curso["nombre"], "tipo": curso["tipo"]})
        return True


class InterfazGrafica:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Estudiantes")
        self.root.geometry("1000x600")
        self.root.resizable(True, True)
        
        self.sistema = SistemaUniversidad()
        
        # Configuración de estilos
        self.configurar_estilos()
        
        # Creación del menú principal
        self.crear_menu()
        
        # Creación del área principal
        self.crear_area_principal()
        
        # Inicializar la vista predeterminada
        self.mostrar_listado_estudiantes()
    
    def configurar_estilos(self):
        # Estilo para el menú lateral
        style = ttk.Style()
        style.configure("TButton", padding=5, relief="flat", font=('Arial', 10))
        style.configure("TLabel", padding=5, font=('Arial', 10))
        style.configure("TEntry", padding=5)
        style.configure("TCombobox", padding=5)
        style.configure("Treeview", font=('Arial', 10))
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
    def crear_menu(self):
        # Menú principal (barra superior)
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Exportar datos", command=self.exportar_datos)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        
        # Menú Estudiantes
        students_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Estudiantes", menu=students_menu)
        students_menu.add_command(label="Agregar Estudiante", command=self.mostrar_formulario_agregar)
        students_menu.add_command(label="Buscar Estudiante", command=self.mostrar_busqueda)
        students_menu.add_command(label="Listar Estudiantes", command=self.mostrar_listado_estudiantes)
        
        # Menú Configuración
        config_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Configuración", menu=config_menu)
        config_menu.add_command(label="Gestionar Programas", command=self.mostrar_gestion_programas)
        config_menu.add_command(label="Gestionar Cursos", command=self.mostrar_gestion_cursos)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.mostrar_acerca_de)
        
    def crear_area_principal(self):
        # Panel izquierdo (menú lateral)
        self.panel_izquierdo = ttk.Frame(self.root, width=200, height=600, padding="10")
        self.panel_izquierdo.pack(side=tk.LEFT, fill=tk.Y)
        
        # Botones del menú lateral
        ttk.Button(self.panel_izquierdo, text="Listar Estudiantes", 
                  command=self.mostrar_listado_estudiantes).pack(fill=tk.X, pady=5)
        ttk.Button(self.panel_izquierdo, text="Agregar Estudiante", 
                  command=self.mostrar_formulario_agregar).pack(fill=tk.X, pady=5)
        ttk.Button(self.panel_izquierdo, text="Buscar Estudiante", 
                  command=self.mostrar_busqueda).pack(fill=tk.X, pady=5)
        ttk.Button(self.panel_izquierdo, text="Gestionar Programas", 
                  command=self.mostrar_gestion_programas).pack(fill=tk.X, pady=5)
        ttk.Button(self.panel_izquierdo, text="Gestionar Cursos", 
                  command=self.mostrar_gestion_cursos).pack(fill=tk.X, pady=5)
        
        # Estadísticas
        ttk.Separator(self.panel_izquierdo).pack(fill=tk.X, pady=10)
        
        ttk.Label(self.panel_izquierdo, text="Estadísticas:").pack(anchor=tk.W)
        self.lbl_total_estudiantes = ttk.Label(self.panel_izquierdo, text="Total estudiantes: 0")
        self.lbl_total_estudiantes.pack(anchor=tk.W, pady=2)
        
        self.lbl_edad_promedio = ttk.Label(self.panel_izquierdo, text="Edad promedio: 0")
        self.lbl_edad_promedio.pack(anchor=tk.W, pady=2)
        
        # Panel derecho (contenido principal)
        self.panel_derecho = ttk.Frame(self.root, padding="10")
        self.panel_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Contenedor para las diferentes vistas
        self.contenedor_vistas = ttk.Frame(self.panel_derecho)
        self.contenedor_vistas.pack(fill=tk.BOTH, expand=True)
        
        # Barra de estado
        self.barra_estado = ttk.Label(self.root, text="Listo", relief=tk.SUNKEN, anchor=tk.W)
        self.barra_estado.pack(side=tk.BOTTOM, fill=tk.X)
        
    def actualizar_estadisticas(self):
        total = len(self.sistema.estudiantes)
        edad_promedio = self.sistema.calcular_edad_promedio()
        
        self.lbl_total_estudiantes.config(text=f"Total estudiantes: {total}")
        self.lbl_edad_promedio.config(text=f"Edad promedio: {edad_promedio:.1f}")
    
    def limpiar_contenedor(self):
        # Eliminar todos los widgets del contenedor de vistas
        for widget in self.contenedor_vistas.winfo_children():
            widget.destroy()
            
    # === VISTAS PRINCIPALES ===
    def mostrar_listado_estudiantes(self):
        self.limpiar_contenedor()
        self.actualizar_estadisticas()
        
        # Título
        ttk.Label(self.contenedor_vistas, text="Listado de Estudiantes", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Marco para la tabla
        frame_tabla = ttk.Frame(self.contenedor_vistas)
        frame_tabla.pack(fill=tk.BOTH, expand=True)
        
        # Tabla de estudiantes
        columns = ("ID", "Nombre", "Apellido", "Programa", "Tipo", "Edad")
        self.tabla_estudiantes = ttk.Treeview(frame_tabla, columns=columns, show="headings")
        
        # Configurar encabezados
        for col in columns:
            self.tabla_estudiantes.heading(col, text=col)
            self.tabla_estudiantes.column(col, width=100)
        
        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=self.tabla_estudiantes.yview)
        self.tabla_estudiantes.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabla_estudiantes.pack(fill=tk.BOTH, expand=True)
        # Ordenar estudiantes por nombre antes de mostrarlos
        estudiantes_ordenados = sorted(self.sistema.estudiantes.values(), key=lambda x: x.nombre)
        # Llenar tabla con datos
        for estudiante in estudiantes_ordenados:
            self.tabla_estudiantes.insert("", tk.END, values=(
                estudiante.id,
                estudiante.nombre,
                estudiante.apellido,
                estudiante.programa,
                estudiante.get_tipo(),
                estudiante.edad
            ))
        
        # Agregar evento de doble clic
        self.tabla_estudiantes.bind("<Double-1>", self.ver_detalles_estudiante)
        
        # Botones de acción
        frame_botones = ttk.Frame(self.contenedor_vistas)
        frame_botones.pack(pady=10)
        
        ttk.Button(frame_botones, text="Ver detalles", 
                  command=lambda: self.ver_detalles_estudiante(None)).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Eliminar", 
                  command=self.eliminar_estudiante_seleccionado).pack(side=tk.LEFT, padx=5)
        
        # Actualizar barra de estado
        self.barra_estado.config(text="Mostrando listado de estudiantes")
    
    def mostrar_formulario_agregar(self):
        self.limpiar_contenedor()
        
        # Título
        ttk.Label(self.contenedor_vistas, text="Agregar Nuevo Estudiante", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Marco para el formulario
        frame_form = ttk.Frame(self.contenedor_vistas, padding=10)
        frame_form.pack(fill=tk.BOTH, expand=True)
        
        # Variables para los campos
        self.var_tipo = tk.StringVar(value="Pregrado")
        self.var_nombre = tk.StringVar()
        self.var_apellido = tk.StringVar()
        self.var_identificacion = tk.StringVar()
        self.var_programa = tk.StringVar()
        self.var_semestre = tk.StringVar()
        self.var_pregrado = tk.StringVar()
        
        # Tipo de estudiante
        ttk.Label(frame_form, text="Tipo de estudiante:").grid(row=0, column=0, sticky=tk.W, pady=5)
        frame_tipo = ttk.Frame(frame_form)
        frame_tipo.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(frame_tipo, text="Pregrado", variable=self.var_tipo, 
                       value="Pregrado", command=self.actualizar_formulario_por_tipo).pack(side=tk.LEFT)
        ttk.Radiobutton(frame_tipo, text="Posgrado", variable=self.var_tipo, 
                       value="Posgrado", command=self.actualizar_formulario_por_tipo).pack(side=tk.LEFT)
        
        # Datos comunes
        ttk.Label(frame_form, text="Nombre:").grid(row=1, column=0, sticky=tk.W, pady=5)
        nombre_entry = ttk.Entry(frame_form, textvariable=self.var_nombre, width=30)
        nombre_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame_form, text="Solo letras, 2-30 caracteres", foreground="gray").grid(row=1, column=2, sticky=tk.W, pady=5)
        
        ttk.Label(frame_form, text="Apellido:").grid(row=2, column=0, sticky=tk.W, pady=5)
        apellido_entry = ttk.Entry(frame_form, textvariable=self.var_apellido, width=30)
        apellido_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame_form, text="Solo letras, 2-30 caracteres", foreground="gray").grid(row=2, column=2, sticky=tk.W, pady=5)
        
        ttk.Label(frame_form, text="Identificación:").grid(row=3, column=0, sticky=tk.W, pady=5)
        id_entry = ttk.Entry(frame_form, textvariable=self.var_identificacion, width=30)
        id_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame_form, text="Solo números", foreground="gray").grid(row=3, column=2, sticky=tk.W, pady=5)
        
        # Permitir solo números en el campo de identificación
        def validar_solo_numeros(P):
            return P.isdigit() or P == ""
        vcmd = (self.root.register(validar_solo_numeros), '%P')
        id_entry.config(validate="key", validatecommand=vcmd)
        
        ttk.Label(frame_form, text="Fecha de nacimiento:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.fecha_nacimiento = DateEntry(frame_form, width=12, background='darkblue',
                                          foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.fecha_nacimiento.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame_form, text="Programa:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.combo_programa = ttk.Combobox(frame_form, textvariable=self.var_programa, 
                                          values=self.sistema.programas, state="readonly", width=30)
        self.combo_programa.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Frame para los campos específicos (se actualiza según el tipo)
        self.frame_campos_especificos = ttk.Frame(frame_form)
        self.frame_campos_especificos.grid(row=6, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Botones
        frame_botones = ttk.Frame(frame_form)
        frame_botones.grid(row=7, column=0, columnspan=3, pady=10)
        
        ttk.Button(frame_botones, text="Guardar", command=self.guardar_estudiante).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Cancelar", command=self.mostrar_listado_estudiantes).pack(side=tk.LEFT, padx=5)
        
        # Actualizar campos específicos según el tipo
        self.actualizar_formulario_por_tipo()
        
        # Actualizar barra de estado
        self.barra_estado.config(text="Agregando nuevo estudiante")
    
    def actualizar_formulario_por_tipo(self):
        # Limpiar el frame de campos específicos
        for widget in self.frame_campos_especificos.winfo_children():
            widget.destroy()

        self.var_programa.set("")  
        tipo = self.var_tipo.get()

        # Filtrar programas según el tipo de estudiante
        programas_filtrados = [
            p["nombre"] for p in self.sistema.programas 
            if p["tipo"] == tipo or p["tipo"] == "Ambos"
        ]
        self.combo_programa["values"] = programas_filtrados

        if tipo == "Pregrado":
            ttk.Label(self.frame_campos_especificos, text="Semestre:").grid(row=0, column=0, sticky=tk.W, pady=5)
            semestre_entry = ttk.Entry(self.frame_campos_especificos, textvariable=self.var_semestre, width=5)
            semestre_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
            ttk.Label(self.frame_campos_especificos, text="Número entre 1-12", foreground="gray").grid(row=0, column=2, sticky=tk.W, pady=5)

            # Permitir solo números en el campo de semestre
            def validar_semestre(P):
                if not P:
                    return True
                if not P.isdigit():
                    return False
                val = int(P)
                return 1 <= val <= 12

            vcmd = (self.root.register(validar_semestre), '%P')
            semestre_entry.config(validate="key", validatecommand=vcmd)

        elif tipo == "Posgrado":
            ttk.Label(self.frame_campos_especificos, text="Título de pregrado:").grid(row=0, column=0, sticky=tk.W, pady=5)
            ttk.Entry(self.frame_campos_especificos, textvariable=self.var_pregrado, width=30).grid(row=0, column=1, sticky=tk.W, pady=5)
    
    def guardar_estudiante(self):
        # Validar campos comunes
        nombre = self.var_nombre.get().strip()
        apellido = self.var_apellido.get().strip()
        identificacion = self.var_identificacion.get().strip()
        programa = self.var_programa.get().strip()
        fecha_nacimiento = self.fecha_nacimiento.get_date().strftime("%Y-%m-%d")
        
        # Validaciones
        errores = []
        
        if not nombre or not Validadores.validar_nombre(nombre):
            errores.append("Nombre inválido. Debe contener solo letras y tener entre 2 y 30 caracteres.")
        
        if not apellido or not Validadores.validar_nombre(apellido):
            errores.append("Apellido inválido. Debe contener solo letras y tener entre 2 y 30 caracteres.")
        
        if not identificacion or not identificacion.isdigit():
            errores.append("Identificación inválida. Debe contener solo números.")
            
        if not programa or not Validadores.validar_programa(programa):
            errores.append("Programa inválido. Debe tener entre 3 y 50 caracteres.")
        
        # Calcular edad
        fecha_nac = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()
        edad = (date.today() - fecha_nac).days // 365
        
        if edad < 16 or edad > 100:
            errores.append("La edad debe estar entre 16 y 100 años.")
        
        # Validaciones específicas según el tipo
        tipo = self.var_tipo.get()
        
        if tipo == "Pregrado":
            semestre = self.var_semestre.get().strip()
            if not semestre or not Validadores.validar_semestre(semestre):
                errores.append("Semestre inválido. Debe ser un número entre 1 y 12.")
        elif tipo == "Posgrado":
            pregrado = self.var_pregrado.get().strip()
            if not pregrado or len(pregrado) < 3:
                errores.append("Título de pregrado inválido. Debe tener al menos 3 caracteres.")
        
        # Mostrar errores si existen
        if errores:
            messagebox.showerror("Error de validación", "\n".join(errores))
            return
        
        # Crear el estudiante según el tipo
        try:
            if tipo == "Pregrado":
                estudiante = EstudiantePregrado(
                    nombre=nombre,
                    apellido=apellido,
                    programa=programa,
                    identificacion=int(identificacion),
                    fecha_nacimiento=fecha_nacimiento,
                    semestre=int(self.var_semestre.get())
                )
            else:  # Posgrado
                estudiante = EstudiantePosgrado(
                    nombre=nombre,
                    apellido=apellido,
                    programa=programa,
                    identificacion=int(identificacion),
                    fecha_nacimiento=fecha_nacimiento,
                    pregrado=self.var_pregrado.get()
                )
            
            # Agregar al sistema
            if self.sistema.agregar_estudiante(estudiante):
                messagebox.showinfo("Éxito", f"Estudiante {nombre} {apellido} agregado correctamente")
                self.mostrar_listado_estudiantes()
            else:
                messagebox.showerror("Error", "No se pudo agregar el estudiante")
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear estudiante: {str(e)}")
    
    def mostrar_busqueda(self):
        self.limpiar_contenedor()
        
        # Título
        ttk.Label(self.contenedor_vistas, text="Buscar Estudiantes", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Marco para la búsqueda
        frame_busqueda = ttk.Frame(self.contenedor_vistas, padding=10)
        frame_busqueda.pack(fill=tk.X)
        
        # Criterio de búsqueda
        ttk.Label(frame_busqueda, text="Buscar por:").grid(row=0, column=0, padx=5)
        self.var_criterio = tk.StringVar(value="nombre")
        combo_criterio = ttk.Combobox(frame_busqueda, textvariable=self.var_criterio, 
                                     values=["nombre", "programa", "id"], width=10, state="readonly")
        combo_criterio.grid(row=0, column=1, padx=5)
        
        # Valor de búsqueda
        self.var_busqueda = tk.StringVar()
        ttk.Entry(frame_busqueda, textvariable=self.var_busqueda, width=30).grid(row=0, column=2, padx=5)
        
        # Botón de búsqueda
        ttk.Button(frame_busqueda, text="Buscar", command=self.realizar_busqueda).grid(row=0, column=3, padx=5)
        
        # Marco para los resultados
        self.frame_resultados = ttk.Frame(self.contenedor_vistas)
        self.frame_resultados.pack(fill=tk.BOTH, expand=True)
        
        # Actualizar barra de estado
        self.barra_estado.config(text="Buscar estudiantes")
    
    def realizar_busqueda(self):
        # Limpiar resultados anteriores
        for widget in self.frame_resultados.winfo_children():
            widget.destroy()
        
        criterio = self.var_criterio.get()
        valor = self.var_busqueda.get().strip()
        
        if not valor:
            ttk.Label(self.frame_resultados, text="Ingrese un término de búsqueda", 
                     foreground="red").pack(pady=10)
            return
        
        # Realizar la búsqueda
        resultados = self.sistema.buscar_estudiantes_por_criterio(criterio, valor)
        resultados.sort(key=lambda x: x.nombre)
        if not resultados:
            ttk.Label(self.frame_resultados, text="No se encontraron resultados", 
                     foreground="red").pack(pady=10)
            return
        
        # Mostrar resultados en tabla
        ttk.Label(self.frame_resultados, text=f"Resultados encontrados: {len(resultados)}").pack(pady=5)
        
        # Tabla de resultados
        columns = ("ID", "Nombre", "Apellido", "Programa", "Tipo", "Edad")
        tabla_resultados = ttk.Treeview(self.frame_resultados, columns=columns, show="headings")
        
        # Configurar encabezados
        for col in columns:
            tabla_resultados.heading(col, text=col)
            tabla_resultados.column(col, width=100)
        
        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(self.frame_resultados, orient=tk.VERTICAL, command=tabla_resultados.yview)
        tabla_resultados.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tabla_resultados.pack(fill=tk.BOTH, expand=True)
        
        # Llenar tabla con resultados
        for estudiante in resultados:
            tabla_resultados.insert("", tk.END, values=(
                estudiante.id,
                estudiante.nombre,
                estudiante.apellido,
                estudiante.programa,
                estudiante.get_tipo(),
                estudiante.edad
            ))
        
        # Agregar evento de doble clic
        tabla_resultados.bind("<Double-1>", lambda event: self.ver_detalles_estudiante_desde_tabla(event, tabla_resultados))
        
        # Botones de acción
        frame_botones = ttk.Frame(self.frame_resultados)
        frame_botones.pack(pady=10)
        
        ttk.Button(frame_botones, text="Ver detalles", 
                  command=lambda: self.ver_detalles_estudiante_desde_tabla(None, tabla_resultados)).pack(side=tk.LEFT, padx=5)
        
        # Actualizar barra de estado
        self.barra_estado.config(text=f"Se encontraron {len(resultados)} estudiantes")
    
    def ver_detalles_estudiante(self, event):
        # Obtener el ítem seleccionado en la tabla
        seleccion = self.tabla_estudiantes.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un estudiante para ver sus detalles")
            return
        
        # Obtener el ID del estudiante seleccionado
        item = self.tabla_estudiantes.item(seleccion[0])
        id_estudiante = item["values"][0]
        
        # Abrir ventana de detalles
        self.mostrar_detalle_estudiante(id_estudiante)
    
    def ver_detalles_estudiante_desde_tabla(self, event, tabla):
        # Obtener el ítem seleccionado en la tabla
        seleccion = tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un estudiante para ver sus detalles")
            return
        
        # Obtener el ID del estudiante seleccionado
        item = tabla.item(seleccion[0])
        id_estudiante = item["values"][0]
        
        # Abrir ventana de detalles
        self.mostrar_detalle_estudiante(id_estudiante)
    
    def mostrar_detalle_estudiante(self, id_estudiante):
        estudiante = self.sistema.buscar_estudiante(id_estudiante)
        if not estudiante:
            messagebox.showerror("Error", "No se pudo encontrar al estudiante seleccionado")
            return
        
        # Crear ventana modal
        ventana_detalle = tk.Toplevel(self.root)
        ventana_detalle.title(f"Detalles del Estudiante: {estudiante.nombre} {estudiante.apellido}")
        ventana_detalle.geometry("1000x650")
        # ventana_detalle.resizable(False, False)
        ventana_detalle.transient(self.root)
        ventana_detalle.grab_set()
        
        # Marco para la información general
        frame_info = ttk.LabelFrame(ventana_detalle, text="Información General", padding=10)
        frame_info.pack(fill=tk.X, padx=10, pady=10)
        
        # Información general
        ttk.Label(frame_info, text=f"ID: {estudiante.id}").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(frame_info, text=f"Tipo: {estudiante.get_tipo()}").grid(row=0, column=1, sticky=tk.W, pady=2)
        ttk.Label(frame_info, text=f"Nombre: {estudiante.nombre} {estudiante.apellido}").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(frame_info, text=f"Identificación: {estudiante.identificacion}").grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Label(frame_info, text=f"Fecha de nacimiento: {estudiante.fecha_nacimiento}").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(frame_info, text=f"Edad: {estudiante.edad} años").grid(row=2, column=1, sticky=tk.W, pady=2)
        ttk.Label(frame_info, text=f"Programa: {estudiante.programa}").grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Información específica según tipo
        if estudiante.get_tipo() == "Pregrado":
            ttk.Label(frame_info, text=f"Semestre: {estudiante.semestre}").grid(row=4, column=0, sticky=tk.W, pady=2)
        else:  # Posgrado
            ttk.Label(frame_info, text=f"Pregrado: {estudiante.pregrado}").grid(row=4, column=0, sticky=tk.W, pady=2)
        
        # Marco para los cursos
        frame_cursos = ttk.LabelFrame(ventana_detalle, text="Cursos", padding=10)
        frame_cursos.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Lista de cursos
        self.lista_cursos = ttk.Treeview(frame_cursos, columns=("curso",), show="headings")
        self.lista_cursos.heading("curso", text="Curso")
        self.lista_cursos.column("curso", width=400)
        
        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(frame_cursos, orient=tk.VERTICAL, command=self.lista_cursos.yview)
        self.lista_cursos.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_cursos.pack(fill=tk.BOTH, expand=True)
        
        # Llenar lista de cursos
        for curso in estudiante.cursos:
            self.lista_cursos.insert("", tk.END, values=(curso,))
        
        # Botones para gestionar cursos
        frame_botones_cursos = ttk.Frame(frame_cursos)
        frame_botones_cursos.pack(pady=5)
        
        ttk.Button(frame_botones_cursos, text="Agregar Curso", 
                  command=lambda: self.agregar_curso_a_estudiante(estudiante, ventana_detalle=ventana_detalle)).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones_cursos, text="Eliminar Curso", 
                  command=lambda: self.eliminar_curso_de_estudiante(estudiante, ventana_detalle=ventana_detalle)).pack(side=tk.LEFT, padx=5)
        
        # Botones inferiores
        frame_botones = ttk.Frame(ventana_detalle)
        frame_botones.pack(pady=10)
        
        ttk.Button(frame_botones, text="Editar", 
                  command=lambda: self.editar_estudiante(estudiante, ventana_detalle)).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Eliminar", 
                  command=lambda: self.confirmar_eliminar_estudiante(estudiante, ventana_detalle)).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Cerrar", 
                  command=ventana_detalle.destroy).pack(side=tk.LEFT, padx=5)
    
    def agregar_curso_a_estudiante(self, estudiante: Estudiante, ventana_detalle: tk.Toplevel):
        # Crear una ventana de diálogo para seleccionar curso
        ventana_curso = tk.Toplevel(self.root)
        ventana_curso.title("Agregar Curso")
        ventana_curso.geometry("400x200")
        ventana_curso.resizable(False, False)
        ventana_curso.transient(self.root)
        ventana_curso.grab_set()

        ttk.Label(ventana_curso, text="Seleccione un curso para agregar:", 
                 font=('Arial', 11)).pack(pady=10)

        # Variable para el curso seleccionado
        var_curso = tk.StringVar()

        # Filtrar cursos según el tipo de estudiante
        cursos_filtrados = [
            c["nombre"] for c in self.sistema.cursos 
            if c["tipo"] == estudiante.get_tipo() or c["tipo"] == "Ambos"
        ]

        # Combobox con los cursos disponibles
        combo_cursos = ttk.Combobox(ventana_curso, textvariable=var_curso, values=cursos_filtrados,state="readonly", width=40)
        combo_cursos.pack(pady=10)

        # Botones
        frame_botones = ttk.Frame(ventana_curso)
        frame_botones.pack(pady=10)

        def guardar_curso():
            curso = var_curso.get().strip()
            if not curso:
                messagebox.showwarning("Curso requerido", "Por favor seleccione un curso")
                return

            if curso in estudiante.cursos:
                messagebox.showwarning("Curso duplicado", "El estudiante ya está inscrito en este curso")
                return

            if self.sistema.agregar_curso_a_estudiante(estudiante.id, curso):
                messagebox.showinfo("Éxito", f"Curso '{curso}' agregado correctamente")
                ventana_curso.destroy()
                ventana_detalle.destroy()
                # Actualizar la vista de detalles
                self.mostrar_detalle_estudiante(estudiante.id)
            else:
                messagebox.showerror("Error", "No se pudo agregar el curso")

        ttk.Button(frame_botones, text="Guardar", command=guardar_curso).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Cancelar", command=ventana_curso.destroy).pack(side=tk.LEFT, padx=5)
    
    def eliminar_curso_de_estudiante(self, estudiante: Estudiante, ventana_detalle:tk.Toplevel):
        # Verificar si hay cursos
        if not estudiante.cursos:
            messagebox.showinfo("Sin cursos", "El estudiante no está inscrito en ningún curso")
            return
        
        # Verificar si hay curso seleccionado en la lista
        seleccion = self.lista_cursos.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un curso para eliminar")
            return
        
        # Obtener el curso seleccionado
        item = self.lista_cursos.item(seleccion[0])
        curso = item["values"][0]
        
        # Confirmar eliminación
        respuesta = messagebox.askyesno("Confirmar eliminación", 
                                      f"¿Está seguro de eliminar el curso '{curso}'?")
        if not respuesta:
            return
        
        # Eliminar curso
        if self.sistema.eliminar_curso_de_estudiante(estudiante.id, curso):
            messagebox.showinfo("Éxito", f"Curso '{curso}' eliminado correctamente")
            # Actualizar la vista de detalles
            ventana_detalle.destroy()
            self.mostrar_detalle_estudiante(estudiante.id)
        else:
            messagebox.showerror("Error", "No se pudo eliminar el curso")
    
    def editar_estudiante(self, estudiante, ventana_padre):
        # Cerrar ventana de detalles
        ventana_padre.destroy()
        
        # Crear ventana de edición
        ventana_edicion = tk.Toplevel(self.root)
        ventana_edicion.title(f"Editar Estudiante: {estudiante.nombre} {estudiante.apellido}")
        ventana_edicion.geometry("600x400")
        ventana_edicion.resizable(False, False)
        ventana_edicion.transient(self.root)
        ventana_edicion.grab_set()
        
        # Marco para el formulario
        frame_form = ttk.Frame(ventana_edicion, padding=10)
        frame_form.pack(fill=tk.BOTH, expand=True)
        
        # Variables para los campos
        var_nombre = tk.StringVar(value=estudiante.nombre)
        var_apellido = tk.StringVar(value=estudiante.apellido)
        var_programa = tk.StringVar(value=estudiante.programa)
        
        # Variables específicas según tipo
        var_semestre = tk.StringVar(value=estudiante.semestre if estudiante.get_tipo() == "Pregrado" else "")
        var_pregrado = tk.StringVar(value=estudiante.pregrado if estudiante.get_tipo() == "Posgrado" else "")
        
        # Tipo de estudiante (solo lectura)
        ttk.Label(frame_form, text="Tipo de estudiante:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(frame_form, text=estudiante.get_tipo()).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Datos comunes
        ttk.Label(frame_form, text="Nombre:").grid(row=1, column=0, sticky=tk.W, pady=5)
        nombre_entry = ttk.Entry(frame_form, textvariable=var_nombre, width=30)
        nombre_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame_form, text="Solo letras, 2-30 caracteres", foreground="gray").grid(row=1, column=2, sticky=tk.W, pady=5)
        
        ttk.Label(frame_form, text="Apellido:").grid(row=2, column=0, sticky=tk.W, pady=5)
        apellido_entry = ttk.Entry(frame_form, textvariable=var_apellido, width=30)
        apellido_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame_form, text="Solo letras, 2-30 caracteres", foreground="gray").grid(row=2, column=2, sticky=tk.W, pady=5)
        
        ttk.Label(frame_form, text="Fecha de nacimiento:").grid(row=3, column=0, sticky=tk.W, pady=5)
        fecha_nacimiento = DateEntry(frame_form, width=12, background='darkblue',
                                     foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        fecha_nacimiento.grid(row=3, column=1, sticky=tk.W, pady=5)
        # Establecer la fecha correcta
        try:
            fecha_dt = datetime.strptime(estudiante.fecha_nacimiento, "%Y-%m-%d").date()
            fecha_nacimiento.set_date(fecha_dt)
        except:
            # En caso de error, usar la fecha actual
            fecha_nacimiento.set_date(date.today())
        
        ttk.Label(frame_form, text="Programa:").grid(row=4, column=0, sticky=tk.W, pady=5)
        combo_programa = ttk.Combobox(frame_form, textvariable=var_programa, 
                                     values=self.sistema.programas,state="readonly", width=30)
        combo_programa.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Campos específicos según tipo
        if estudiante.get_tipo() == "Pregrado":
            ttk.Label(frame_form, text="Semestre:").grid(row=5, column=0, sticky=tk.W, pady=5)
            semestre_entry = ttk.Entry(frame_form, textvariable=var_semestre, width=5)
            semestre_entry.grid(row=5, column=1, sticky=tk.W, pady=5)
            ttk.Label(frame_form, text="Número entre 1-12", foreground="gray").grid(row=5, column=2, sticky=tk.W, pady=5)
            
            # Permitir solo números en el campo de semestre
            def validar_semestre(P):
                if not P:
                    return True
                if not P.isdigit():
                    return False
                val = int(P)
                return 1 <= val <= 12
            
            vcmd = (self.root.register(validar_semestre), '%P')
            semestre_entry.config(validate="key", validatecommand=vcmd)
            
        elif estudiante.get_tipo() == "Posgrado":
            ttk.Label(frame_form, text="Título de pregrado:").grid(row=5, column=0, sticky=tk.W, pady=5)
            ttk.Entry(frame_form, textvariable=var_pregrado, width=30).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Botones
        frame_botones = ttk.Frame(frame_form)
        frame_botones.grid(row=6, column=0, columnspan=3, pady=10)
        
        def guardar_cambios():
            # Validar campos
            nombre = var_nombre.get().strip()
            apellido = var_apellido.get().strip()
            programa = var_programa.get().strip()
            fecha = fecha_nacimiento.get_date().strftime("%Y-%m-%d")
            
            # Validaciones
            errores = []
            
            if not nombre or not Validadores.validar_nombre(nombre):
                errores.append("Nombre inválido. Debe contener solo letras y tener entre 2 y 30 caracteres.")
            
            if not apellido or not Validadores.validar_nombre(apellido):
                errores.append("Apellido inválido. Debe contener solo letras y tener entre 2 y 30 caracteres.")
                
            if not programa or not Validadores.validar_programa(programa):
                errores.append("Programa inválido. Debe tener entre 3 y 50 caracteres.")
            
            # Validaciones específicas según el tipo
            if estudiante.get_tipo() == "Pregrado":
                semestre = var_semestre.get().strip()
                if not semestre or not Validadores.validar_semestre(semestre):
                    errores.append("Semestre inválido. Debe ser un número entre 1 y 12.")
            elif estudiante.get_tipo() == "Posgrado":
                pregrado = var_pregrado.get().strip()
                if not pregrado or len(pregrado) < 3:
                    errores.append("Título de pregrado inválido. Debe tener al menos 3 caracteres.")
            
            # Mostrar errores si existen
            if errores:
                messagebox.showerror("Error de validación", "\n".join(errores))
                return
            
            # Preparar datos para actualización
            datos = {
                "nombre": nombre,
                "apellido": apellido,
                "programa": programa,
                "fecha_nacimiento": fecha
            }
            
            # Datos específicos según tipo
            if estudiante.get_tipo() == "Pregrado":
                datos["semestre"] = int(var_semestre.get())
            elif estudiante.get_tipo() == "Posgrado":
                datos["pregrado"] = var_pregrado.get()
            
            # Actualizar estudiante
            if self.sistema.editar_estudiante(estudiante.id, datos):
                messagebox.showinfo("Éxito", "Estudiante actualizado correctamente")
                ventana_edicion.destroy()
                # Actualizar listado
                self.mostrar_listado_estudiantes()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el estudiante")
        
        ttk.Button(frame_botones, text="Guardar", command=guardar_cambios).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Cancelar", command=ventana_edicion.destroy).pack(side=tk.LEFT, padx=5)
    
    def confirmar_eliminar_estudiante(self, estudiante, ventana_padre=None):
        # Confirmar eliminación
        respuesta = messagebox.askyesno("Confirmar eliminación", 
                                      f"¿Está seguro de eliminar al estudiante {estudiante.nombre} {estudiante.apellido}?")
        if not respuesta:
            return
        
        # Eliminar estudiante
        if self.sistema.eliminar_estudiante(estudiante.id):
            messagebox.showinfo("Éxito", "Estudiante eliminado correctamente")
            
            # Cerrar ventana de detalles si existe
            if ventana_padre:
                ventana_padre.destroy()
            
            # Actualizar listado
            self.mostrar_listado_estudiantes()
        else:
            messagebox.showerror("Error", "No se pudo eliminar el estudiante")
    
    def eliminar_estudiante_seleccionado(self):
        # Obtener el ítem seleccionado en la tabla
        seleccion = self.tabla_estudiantes.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un estudiante para eliminar")
            return
        
        # Obtener el ID del estudiante seleccionado
        item = self.tabla_estudiantes.item(seleccion[0])
        id_estudiante = item["values"][0]
        
        # Buscar el estudiante
        estudiante = self.sistema.buscar_estudiante(id_estudiante)
        if not estudiante:
            messagebox.showerror("Error", "No se pudo encontrar al estudiante seleccionado")
            return
        
        # Confirmar eliminación
        self.confirmar_eliminar_estudiante(estudiante)
    
    def mostrar_gestion_programas(self):
        self.limpiar_contenedor()
        
        # Título
        ttk.Label(self.contenedor_vistas, text="Gestión de Programas Académicos", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Marco para la lista y formulario
        frame_principal = ttk.Frame(self.contenedor_vistas)
        frame_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo - Lista de programas
        frame_lista = ttk.LabelFrame(frame_principal, text="Programas disponibles", padding=10)
        frame_lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Lista de programas
        self.lista_programas = tk.Listbox(frame_lista, width=40, height=15)
        scrollbar = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=self.lista_programas.yview)
        self.lista_programas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_programas.pack(fill=tk.BOTH, expand=True)
        
        # Llenar lista de programas
        for programa in sorted(self.sistema.programas, key=lambda x: x["nombre"]):
            self.lista_programas.insert(tk.END, f"{programa['nombre']} ({programa['tipo']})")
        
        # Panel derecho - Formulario
        frame_form = ttk.LabelFrame(frame_principal, text="Agregar programa", padding=10)
        frame_form.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Variable para el nuevo programa
        self.var_nuevo_programa = tk.StringVar()
        self.var_tipo_programa = tk.StringVar(value="Pregrado")
        
        ttk.Label(frame_form, text="Nombre del programa:").pack(anchor=tk.W, pady=5)
        ttk.Entry(frame_form, textvariable=self.var_nuevo_programa, width=30).pack(fill=tk.X, pady=5)
        ttk.Label(frame_form, text="Tipo de programa:").pack(anchor=tk.W, pady=5)
        ttk.Combobox(frame_form, textvariable=self.var_tipo_programa, 
                values=["Pregrado", "Posgrado", "Ambos"], state="readonly").pack(fill=tk.X, pady=5)
        
        ttk.Button(frame_form, text="Agregar", command=self.agregar_programa).pack(pady=10)
        
        # Botón para eliminar programa
        ttk.Button(frame_lista, text="Eliminar programa seleccionado", 
                  command=self.eliminar_programa).pack(pady=10)
        
        # Actualizar barra de estado
        self.barra_estado.config(text="Gestión de programas académicos")
    
    def agregar_programa(self):
        programa = self.var_nuevo_programa.get().strip()
        tipo = self.var_tipo_programa.get()
        
        if not programa or not Validadores.validar_programa(programa):
            messagebox.showwarning("Programa inválido", 
                                 "El nombre del programa debe tener entre 3 y 50 caracteres")
            return
        
        if programa in self.sistema.programas:
            messagebox.showwarning("Programa duplicado", 
                                 "Este programa ya existe en el sistema")
            return
        nuevo_programa = {"nombre": programa, "tipo": tipo}
        if self.sistema.agregar_programa(nuevo_programa):
            messagebox.showinfo("Éxito", f"Programa '{programa}' agregado correctamente")
            self.var_nuevo_programa.set("")  # Limpiar campo
            
            # Actualizar lista
            self.lista_programas.delete(0, tk.END)
            for prog in sorted(self.sistema.programas, key=lambda x: x["nombre"]):
                self.lista_programas.insert(tk.END, f"{prog['nombre']} ({prog['tipo']})")
        else:
            messagebox.showerror("Error", "No se pudo agregar el programa")
    
    def eliminar_programa(self):
        # Verificar si hay un programa seleccionado
        if not self.lista_programas.curselection():
            messagebox.showwarning("Selección requerida", 
                                 "Por favor seleccione un programa para eliminar")
            return

        # Obtener el índice del programa seleccionado
        index = self.lista_programas.curselection()[0]

        # Obtener el nombre del programa seleccionado
        programa_seleccionado = self.lista_programas.get(index)

        # Extraer solo el nombre del programa (sin el tipo entre paréntesis)
        nombre_programa = programa_seleccionado.split(" (")[0]

        # Verificar si hay estudiantes usando este programa
        estudiantes_con_programa = [
            estudiante for estudiante in self.sistema.estudiantes.values() 
            if estudiante.programa == nombre_programa
        ]

        if estudiantes_con_programa:
            messagebox.showwarning("Programa en uso", 
                                 f"No se puede eliminar el programa '{nombre_programa}' porque está siendo usado por {len(estudiantes_con_programa)} estudiante(s)")
            return

        # Confirmar eliminación
        respuesta = messagebox.askyesno("Confirmar eliminación", 
                                      f"¿Está seguro de eliminar el programa '{nombre_programa}'?")
        if not respuesta:
            return

        # Eliminar el programa de la lista de programas del sistema
        programa_a_eliminar = next(
            (p for p in self.sistema.programas if p["nombre"] == nombre_programa), 
            None
        )

        if programa_a_eliminar:
            self.sistema.programas.remove(programa_a_eliminar)

            # Eliminar el programa de la base de datos
            self.sistema.db.delete("Programas", {"nombre": nombre_programa})

            # Actualizar la lista de programas en la interfaz
            self.lista_programas.delete(index)

            # Actualizar el Combobox de programas en el formulario de agregar estudiante
            if hasattr(self, 'combo_programa'):
                programas_filtrados = [
                    p["nombre"] for p in self.sistema.programas 
                    if p["tipo"] == self.var_tipo.get() or p["tipo"] == "Ambos"
                ]
                self.combo_programa["values"] = programas_filtrados

            messagebox.showinfo("Éxito", f"Programa '{nombre_programa}' eliminado correctamente")
        else:
            messagebox.showerror("Error", "No se pudo eliminar el programa")

    def mostrar_gestion_cursos(self):
        self.limpiar_contenedor()
        
        # Título
        ttk.Label(self.contenedor_vistas, text="Gestión de Cursos", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Marco para la lista y formulario
        frame_principal = ttk.Frame(self.contenedor_vistas)
        frame_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo - Lista de cursos
        frame_lista = ttk.LabelFrame(frame_principal, text="Cursos disponibles", padding=10)
        frame_lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Lista de cursos
        self.lista_cursos = tk.Listbox(frame_lista, width=40, height=15)
        scrollbar = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=self.lista_cursos.yview)
        self.lista_cursos.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_cursos.pack(fill=tk.BOTH, expand=True)
        
        # Llenar lista de cursos
        for curso in sorted(self.sistema.cursos, key=lambda x: x["nombre"]):
            self.lista_cursos.insert(tk.END, f"{curso['nombre']} ({curso['tipo']})")
        
        # Panel derecho - Formulario
        frame_form = ttk.LabelFrame(frame_principal, text="Agregar curso", padding=10)
        frame_form.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Variable para el nuevo curso
        self.var_nuevo_curso = tk.StringVar()
        self.var_tipo_curso = tk.StringVar(value="Pregrado")
        
        ttk.Label(frame_form, text="Nombre del curso:").pack(anchor=tk.W, pady=5)
        ttk.Entry(frame_form, textvariable=self.var_nuevo_curso, width=30).pack(fill=tk.X, pady=5)
        ttk.Label(frame_form, text="Tipo de curso:").pack(anchor=tk.W, pady=5)
        ttk.Combobox(frame_form, textvariable=self.var_tipo_curso, 
                 values=["Pregrado", "Posgrado", "Ambos"], state="readonly").pack(fill=tk.X, pady=5)
        
        ttk.Button(frame_form, text="Agregar", command=self.agregar_curso).pack(pady=10)
        
        # Botón para eliminar curso
        ttk.Button(frame_lista, text="Eliminar curso seleccionado", 
                  command=self.eliminar_curso).pack(pady=10)
        
        # Actualizar barra de estado
        self.barra_estado.config(text="Gestión de cursos")

    def agregar_curso(self):
        nombre_curso = self.var_nuevo_curso.get().strip()
        tipo_curso = self.var_tipo_curso.get()
        
        if not nombre_curso or len(nombre_curso) < 3:
            messagebox.showwarning("Curso inválido", 
                                 "El nombre del curso debe tener al menos 3 caracteres")
            return
        
        if nombre_curso in self.sistema.cursos:
            messagebox.showwarning("Curso duplicado", 
                                 "Este curso ya existe en el sistema")
            return
        nuevo_curso = {"nombre": nombre_curso, "tipo": tipo_curso}
        if self.sistema.agregar_curso(nuevo_curso):
            messagebox.showinfo("Éxito", f"Curso '{nombre_curso}' agregado correctamente")
            self.var_nuevo_curso.set("")  # Limpiar campo
            
            # Actualizar lista
            self.lista_cursos.delete(0, tk.END)
            for cur in self.sistema.cursos:
                self.lista_cursos.insert(tk.END, f"{cur['nombre']} ({cur['tipo']})")
        else:
            messagebox.showerror("Error", "No se pudo agregar el curso")

    def eliminar_curso(self):
        # Verificar selección
        if not self.lista_cursos.curselection():
            messagebox.showwarning("Selección requerida", 
                                 "Por favor seleccione un curso para eliminar")
            return

        # Obtener curso seleccionado
        index = self.lista_cursos.curselection()[0]
        nombre_curso = self.lista_cursos.get(index)

        # Buscar el curso en la lista de cursos
        curso = next((c for c in self.sistema.cursos if c["nombre"] == nombre_curso), None)
        if not curso:
            messagebox.showerror("Error", "No se pudo encontrar el curso seleccionado")
            return

        # Verificar si hay estudiantes usando este curso
        estudiantes_con_curso = [e for e in self.sistema.estudiantes.values() if nombre_curso in e.cursos]
        if estudiantes_con_curso:
            messagebox.showwarning("Curso en uso", 
                                 f"No se puede eliminar el curso '{nombre_curso}' porque está siendo usado por {len(estudiantes_con_curso)} estudiante(s)")
            return

        # Confirmar eliminación
        respuesta = messagebox.askyesno("Confirmar eliminación", 
                                      f"¿Está seguro de eliminar el curso '{nombre_curso}'?")
        if not respuesta:
            return

        # Eliminar curso
        if curso in self.sistema.cursos:
            self.sistema.cursos.remove(curso)
            self.lista_cursos.delete(index)
            self.db.delete("Cursos", {"nombre": nombre_curso})
            messagebox.showinfo("Éxito", f"Curso '{nombre_curso}' eliminado correctamente")
        else:
            messagebox.showerror("Error", "No se pudo eliminar el curso")
    db = CRUDExcel()
    def exportar_datos(self):
        # Crear un archivo Excel con todos los datos
        try:
            with pd.ExcelWriter("exportacion_datos.xlsx", engine="openpyxl") as writer:
                # Exportar estudiantes de pregrado
                df_pregrado = self.db.read("EstudiantesPregrado")
                df_pregrado.to_excel(writer, sheet_name="EstudiantesPregrado", index=False)
                
                # Exportar estudiantes de posgrado
                df_posgrado = self.db.read("EstudiantesPosgrado")
                df_posgrado.to_excel(writer, sheet_name="EstudiantesPosgrado", index=False)
                
                # Exportar programas
                df_programas = self.db.read("Programas")
                df_programas.to_excel(writer, sheet_name="Programas", index=False)
                
                # Exportar cursos
                df_cursos = self.db.read("Cursos")
                df_cursos.to_excel(writer, sheet_name="Cursos", index=False)
            
            messagebox.showinfo("Éxito", "Datos exportados correctamente en 'exportacion_datos.xlsx'")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar los datos: {str(e)}")

    def mostrar_acerca_de(self):
        messagebox.showinfo("Acerca de", 
                           "Sistema de Gestión de Estudiantes\nVersión 1.0\nDesarrollado por Jose David Quiñonez Rehenals")

# Punto de entrada de la aplicación
if __name__ == "__main__":
    respuesta =messagebox.askyesno("Iniciar", "¿Desea hacer una inyeccion de datos?")
    root = tk.Tk()
    app = InterfazGrafica(root)
    root.mainloop()