import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy import create_engine, Column, Integer, String, Float, or_, and_, between
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Database configuration
DATABASE_URL = "mysql+pymysql://root:@localhost/computacion"
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class Producto(Base):
    """Model representing products in the database."""
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255))
    precio = Column(Float, nullable=False)
    cantidad_stock = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Producto(id={self.id}, nombre='{self.nombre}', precio={self.precio}, stock={self.cantidad_stock})>"
    
    @classmethod
    def crear(cls, session, nombre: str, descripcion: str, precio: float, cantidad_stock: int) -> 'Producto':
        """Creates a new product in the database."""
        producto = cls(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            cantidad_stock=cantidad_stock
        )
        session.add(producto)
        session.commit()
        return producto
    
    @classmethod
    def obtener_todos(cls, session, order_by: str = None, ascending: bool = True) -> List['Producto']:
        """
        Gets all products from the database.
        
        Args:
            session: SQLAlchemy session
            order_by: Field to order by (id, nombre, precio, cantidad_stock)
            ascending: True for ascending order, False for descending
        
        Returns:
            List of Product objects
        """
        query = session.query(cls)
        
        if order_by:
            column = getattr(cls, order_by)
            if not ascending:
                column = column.desc()
            query = query.order_by(column)
            
        return query.all()
    
    @classmethod
    def obtener_por_id(cls, session, id: int) -> Optional['Producto']:
        """Gets a product by its ID."""
        return session.query(cls).filter(cls.id == id).first()
    
    @classmethod
    def buscar(cls, session, 
               texto: Optional[str] = None, 
               precio_min: Optional[float] = None, 
               precio_max: Optional[float] = None,
               stock_min: Optional[int] = None, 
               stock_max: Optional[int] = None,
               order_by: str = None,
               ascending: bool = True) -> List['Producto']:
        """
        Searches products based on multiple criteria with sorting capabilities.
        
        Args:
            session: SQLAlchemy session
            texto: Text to search in name or description
            precio_min: Minimum price
            precio_max: Maximum price
            stock_min: Minimum stock
            stock_max: Maximum stock
            order_by: Field to order by
            ascending: Sort direction
            
        Returns:
            List of matching products
        """
        consulta = session.query(cls)
        
        filtros = []
        if texto:
            # Search by name/description only (removed ID search)
            filtros.append(cls.nombre.like(f"%{texto}%"))
            filtros.append(cls.descripcion.like(f"%{texto}%"))
        
        if precio_min is not None and precio_max is not None:
            filtros.append(between(cls.precio, precio_min, precio_max))
        elif precio_min is not None:
            filtros.append(cls.precio >= precio_min)
        elif precio_max is not None:
            filtros.append(cls.precio <= precio_max)
            
        if stock_min is not None and stock_max is not None:
            filtros.append(between(cls.cantidad_stock, stock_min, stock_max))
        elif stock_min is not None:
            filtros.append(cls.cantidad_stock >= stock_min)
        elif stock_max is not None:
            filtros.append(cls.cantidad_stock <= stock_max)
            
        if filtros:
            consulta = consulta.filter(or_(*filtros))
        
        # Apply sorting
        if order_by:
            column = getattr(cls, order_by)
            if not ascending:
                column = column.desc()
            consulta = consulta.order_by(column)
            
        return consulta.all()
    
    def actualizar(self, session, nombre: Optional[str] = None, 
                  descripcion: Optional[str] = None, 
                  precio: Optional[float] = None, 
                  cantidad_stock: Optional[int] = None) -> None:
        """Updates product data."""
        if nombre is not None:
            self.nombre = nombre
        if descripcion is not None:
            self.descripcion = descripcion
        if precio is not None:
            self.precio = precio
        if cantidad_stock is not None:
            self.cantidad_stock = cantidad_stock
        session.commit()
    
    def ajustar_stock(self, session, cantidad: int) -> None:
        """
        Adjusts the stock by adding or subtracting units.
        
        Args:
            session: SQLAlchemy session
            cantidad: Amount to add (positive) or subtract (negative)
        """
        nuevo_stock = self.cantidad_stock + cantidad
        if nuevo_stock < 0:
            raise ValueError("El stock no puede ser negativo")
        
        self.cantidad_stock = nuevo_stock
        session.commit()
    
    def eliminar(self, session) -> None:
        """Deletes the product from the database."""
        session.delete(self)
        session.commit()
    
    @classmethod
    def actualizar_precios_masivos(cls, session, porcentaje: float, 
                                  condicion: Optional[Dict[str, Any]] = None) -> int:
        """Updates prices for multiple products by a percentage."""
        consulta = session.query(cls)
        
        if condicion:
            if 'precio_min' in condicion and 'precio_max' in condicion:
                consulta = consulta.filter(
                    between(cls.precio, condicion['precio_min'], condicion['precio_max'])
                )
            if 'stock_min' in condicion and 'stock_max' in condicion:
                consulta = consulta.filter(
                    between(cls.cantidad_stock, condicion['stock_min'], condicion['stock_max'])
                )
        
        productos = consulta.all()
        for producto in productos:
            producto.precio = producto.precio * (1 + porcentaje/100)
        
        session.commit()
        return len(productos)

# Create tables if they don't exist
Base.metadata.create_all(engine)

class Validador:
    """Class for validating user inputs."""
    
    @staticmethod
    def validar_texto(texto: str, campo: str, min_longitud: int = 1, max_longitud: int = 100, ob:bool = True) -> Tuple[bool, str]:
        """Validates that a text has the appropriate length."""
        if ob:
            if not texto or len(texto.strip()) < min_longitud:
                return False, f"El campo {campo} no puede estar vacío y debe tener al menos {min_longitud} caracteres."
        if len(texto) > max_longitud:
            return False, f"El campo {campo} no puede exceder los {max_longitud} caracteres."
        return True, ""
    
    @staticmethod
    def validar_numero(valor: str, campo: str, min_valor: float = 0, 
                      max_valor: float = float('inf'), es_entero: bool = False) -> Tuple[bool, str, Optional[Union[int, float]]]:
        """Validates that a value is numeric and within the specified range."""
        if not valor:
            return False, f"El campo {campo} no puede estar vacío.", None
        
        try:
            if es_entero:
                if not valor.isdigit():
                    return False, f"El campo {campo} debe ser un número entero positivo.", None
                numero = int(valor)
            else:
                # Allow decimal point for floats
                if not re.match(r'^\d+(\.\d+)?$', valor):
                    return False, f"El campo {campo} debe ser un número positivo.", None
                numero = float(valor)
                
            if numero < min_valor:
                return False, f"El campo {campo} debe ser mayor o igual a {min_valor}.", None
            if numero > max_valor:
                return False, f"El campo {campo} debe ser menor o igual a {max_valor}.", None
                
            return True, "", numero
        except ValueError:
            return False, f"El campo {campo} debe ser un número válido.", None
    
    @staticmethod
    def validar_rango(min_valor: str, max_valor: str, campo: str, 
                     es_entero: bool = False) -> Tuple[bool, str, Optional[Tuple[Union[int, float], Union[int, float]]]]:
        """Validates that a range of values is valid."""
        # Validate both values are numbers
        valido_min, msg_min, valor_min = Validador.validar_numero(
            min_valor, f"mínimo de {campo}", es_entero=es_entero
        )
        valido_max, msg_max, valor_max = Validador.validar_numero(
            max_valor, f"máximo de {campo}", es_entero=es_entero
        )
        
        if not valido_min:
            return False, msg_min, None
        if not valido_max:
            return False, msg_max, None
        
        # Validate min <= max
        if valor_min > valor_max:
            return False, f"El valor mínimo de {campo} debe ser menor o igual al valor máximo.", None
            
        return True, "", (valor_min, valor_max)

class SistemaInventario:
    """Class that manages the inventory system logic."""
    
    def __init__(self):
        """Initializes the inventory system."""
        self.session = Session()
    
    def agregar_producto(self, nombre: str, descripcion: str, precio: float, 
                        cantidad_stock: int) -> Tuple[bool, str, Optional[Producto]]:
        """Adds a new product to the inventory."""
        try:
            # Validate data
            valido_nombre, msg_nombre = Validador.validar_texto(nombre, "Nombre")
            if not valido_nombre:
                return False, msg_nombre, None
                
            valido_desc, msg_desc = Validador.validar_texto(descripcion, "Descripción", min_longitud=0, max_longitud=255, ob = False)
            if not valido_desc:
                return False, msg_desc, None
                
            valido_precio, msg_precio, precio_validado = Validador.validar_numero(
                str(precio), "Precio", min_valor=0.01
            )
            if not valido_precio:
                return False, msg_precio, None
                
            valido_stock, msg_stock, stock_validado = Validador.validar_numero(
                str(cantidad_stock), "Cantidad en stock", min_valor=0, es_entero=True
            )
            if not valido_stock:
                return False, msg_stock, None
            
            # Create product
            producto = Producto.crear(
                self.session, 
                nombre=nombre, 
                descripcion=descripcion, 
                precio=precio_validado, 
                cantidad_stock=stock_validado
            )
            return True, f"Producto '{nombre}' agregado correctamente.", producto
            
        except SQLAlchemyError as e:
            self.session.rollback()
            return False, f"Error de base de datos: {str(e)}", None
    
    def editar_producto(self, id: int, nombre: str, descripcion: str, 
                       precio: float, cantidad_stock: int, ajuste_stock: int = 0) -> Tuple[bool, str]:
        """
        Edits an existing product with optional stock adjustment.
        
        Args:
            id: Product ID
            nombre: Product name
            descripcion: Product description
            precio: Product price
            cantidad_stock: Total stock quantity (if ajuste_stock is 0)
            ajuste_stock: Stock adjustment (units to add or subtract)
            
        Returns:
            Tuple with success flag and message
        """
        try:
            producto = Producto.obtener_por_id(self.session, id)
            if not producto:
                return False, f"No se encontró el producto solicitado."
            
            # Validate data
            valido_nombre, msg_nombre = Validador.validar_texto(nombre, "Nombre")
            if not valido_nombre:
                return False, msg_nombre
                
            valido_desc, msg_desc = Validador.validar_texto(descripcion, "Descripción", min_longitud=0, max_longitud=255,  ob = False)
            if not valido_desc:
                return False, msg_desc
                
            valido_precio, msg_precio, precio_validado = Validador.validar_numero(
                str(precio), "Precio", min_valor=0.01
            )
            if not valido_precio:
                return False, msg_precio
            
            # Handle stock adjustment if provided
            if ajuste_stock != 0:
                try:
                    producto.ajustar_stock(self.session, ajuste_stock)
                    stock_validado = producto.cantidad_stock  # Get the updated stock
                except ValueError as e:
                    return False, str(e)
            else:
                # Validate and use the provided total stock
                valido_stock, msg_stock, stock_validado = Validador.validar_numero(
                    str(cantidad_stock), "Cantidad en stock", min_valor=0, es_entero=True
                )
                if not valido_stock:
                    return False, msg_stock
            
            # Update product
            producto.actualizar(
                self.session,
                nombre=nombre,
                descripcion=descripcion,
                precio=precio_validado,
                cantidad_stock=stock_validado
            )
            
            mensaje = f"Producto '{nombre}' actualizado correctamente."
            if ajuste_stock > 0:
                mensaje += f" Se agregaron {ajuste_stock} unidades al stock."
            elif ajuste_stock < 0:
                mensaje += f" Se quitaron {abs(ajuste_stock)} unidades del stock."
                
            return True, mensaje
            
        except SQLAlchemyError as e:
            self.session.rollback()
            return False, f"Error de base de datos: {str(e)}"
    
    def ajustar_stock(self, id: int, cantidad: int) -> Tuple[bool, str]:
        """
        Adjusts product stock by adding or subtracting units.
        
        Args:
            id: Product ID
            cantidad: Amount to add (positive) or subtract (negative)
            
        Returns:
            Tuple with success flag and message
        """
        try:
            producto = Producto.obtener_por_id(self.session, id)
            if not producto:
                return False, f"No se encontró el producto solicitado."
            
            try:
                producto.ajustar_stock(self.session, cantidad)
                
                if cantidad > 0:
                    mensaje = f"Se agregaron {cantidad} unidades al stock de '{producto.nombre}'."
                else:
                    mensaje = f"Se quitaron {abs(cantidad)} unidades del stock de '{producto.nombre}'."
                
                return True, mensaje
            except ValueError as e:
                return False, str(e)
            
        except SQLAlchemyError as e:
            self.session.rollback()
            return False, f"Error de base de datos: {str(e)}"
    
    def eliminar_producto(self, id: int) -> Tuple[bool, str]:
        """Deletes a product from the inventory."""
        try:
            producto = Producto.obtener_por_id(self.session, id)
            if not producto:
                return False, f"No se encontró el producto solicitado."
            
            nombre = producto.nombre
            producto.eliminar(self.session)
            return True, f"Producto '{nombre}' eliminado correctamente."
            
        except SQLAlchemyError as e:
            self.session.rollback()
            return False, f"Error de base de datos: {str(e)}"
    
    def buscar_productos(self, texto: Optional[str] = None, 
                        precio_min: Optional[float] = None, 
                        precio_max: Optional[float] = None,
                        stock_min: Optional[int] = None, 
                        stock_max: Optional[int] = None,
                        order_by: str = None,
                        ascending: bool = True) -> List[Producto]:
        """Searches products based on multiple criteria with sorting."""
        try:
            return Producto.buscar(
                self.session,
                texto=texto,
                precio_min=precio_min,
                precio_max=precio_max,
                stock_min=stock_min,
                stock_max=stock_max,
                order_by=order_by,
                ascending=ascending
            )
        except SQLAlchemyError as e:
            # Mejorado: Mostrar el error en la consola para depuración
            print(f"Error al buscar productos: {str(e)}")
            return []
    
    def obtener_todos_productos(self, order_by: str = None, ascending: bool = True) -> List[Producto]:
        """Gets all products from inventory with optional sorting."""
        try:
            return Producto.obtener_todos(self.session, order_by, ascending)
        except SQLAlchemyError as e:
            # Mejorado: Mostrar el error en la consola para depuración
            print(f"Error al obtener productos: {str(e)}")
            return []
    
    def actualizar_precios_masivos(self, porcentaje: float, 
                                  condiciones: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, int]:
        """Updates prices for multiple products by a percentage."""
        try:
            # Validate percentage
            valido_porc, msg_porc, porc_validado = Validador.validar_numero(
                str(porcentaje), "Porcentaje", min_valor=-90, max_valor=1000
            )
            if not valido_porc:
                return False, msg_porc, 0
            
            # Update prices
            num_actualizados = Producto.actualizar_precios_masivos(
                self.session, porc_validado, condiciones
            )
            
            if num_actualizados == 0:
                return False, "No se encontraron productos que cumplan con los criterios.", 0
                
            return True, f"Se actualizaron los precios de {num_actualizados} productos.", num_actualizados
            
        except SQLAlchemyError as e:
            self.session.rollback()
            return False, f"Error de base de datos: {str(e)}", 0
    
    def sincronizar_con_bd(self) -> Tuple[bool, str]:
        """
        Synchronizes the local database session with the database server.
        
        Returns:
            Tuple with success flag and message
        """
        try:
            # Close current session and create a new one
            self.session.close()
            self.session = Session()
            return True, "Base de datos sincronizada correctamente."
        except SQLAlchemyError as e:
            return False, f"Error al sincronizar con la base de datos: {str(e)}"
    
    def cerrar(self):
        """Closes the database session."""
        self.session.close()

class ToolTip:
    """Class for displaying tooltips on widgets."""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.text, background="#FFFFDD", 
                         relief="solid", borderwidth=1, padx=5, pady=2)
        label.pack()
    
    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class EstiloUI:
    """Class for handling interface styles."""
    
    COLOR_PRIMARIO = "#3498db"
    COLOR_SECUNDARIO = "#2980b9"
    COLOR_FONDO = "#ecf0f1"
    COLOR_TEXTO = "#2c3e50"
    COLOR_EXITO = "#2ecc71"
    COLOR_ERROR = "#e74c3c"
    COLOR_ADVERTENCIA = "#f39c12"
    COLOR_INFO = "#3498db"
    
    @staticmethod
    def aplicar_estilo(root):
        """Applies style to the main window."""
        style = ttk.Style()
        style.theme_use('default')
        
        # Configure styles for ttk widgets
        style.configure("TFrame", background=EstiloUI.COLOR_FONDO)
        style.configure("TLabel", background=EstiloUI.COLOR_FONDO, foreground=EstiloUI.COLOR_TEXTO)
        style.configure("TButton", 
                        background=EstiloUI.COLOR_PRIMARIO, 
                        foreground="white", 
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor=EstiloUI.COLOR_SECUNDARIO)
        style.map("TButton",
                 background=[("active", EstiloUI.COLOR_SECUNDARIO), ("disabled", "#bdc3c7")],
                 foreground=[("disabled", "#7f8c8d")])
        
        style.configure("Encabezado.TLabel", 
                       font=("Helvetica", 14, "bold"), 
                       foreground=EstiloUI.COLOR_PRIMARIO)
        
        style.configure("Titulo.TLabel", 
                       font=("Helvetica", 16, "bold"), 
                       foreground=EstiloUI.COLOR_PRIMARIO)
        
        # Estilos para mensajes de estado
        style.configure("Exito.TLabel", 
                       foreground=EstiloUI.COLOR_EXITO)
        style.configure("Error.TLabel", 
                       foreground=EstiloUI.COLOR_ERROR)
        style.configure("Info.TLabel", 
                       foreground=EstiloUI.COLOR_INFO)
        style.configure("Advertencia.TLabel", 
                       foreground=EstiloUI.COLOR_ADVERTENCIA)
        
        # Configure main window
        root.configure(background=EstiloUI.COLOR_FONDO)
        root.option_add("*TCombobox*Listbox*Background", EstiloUI.COLOR_FONDO)
        root.option_add("*TCombobox*Listbox*Foreground", EstiloUI.COLOR_TEXTO)
        
        # Configure Treeview
        style.configure("Treeview", 
                       background=EstiloUI.COLOR_FONDO,
                       foreground=EstiloUI.COLOR_TEXTO,
                       rowheight=25,
                       fieldbackground=EstiloUI.COLOR_FONDO)
        style.configure("Treeview.Heading", 
                       background=EstiloUI.COLOR_PRIMARIO,
                       foreground="white",
                       font=("Helvetica", 10, "bold"))
        style.map("Treeview.Heading",
                 background=[("active", EstiloUI.COLOR_SECUNDARIO)])
        style.map("Treeview",
                 background=[("selected", EstiloUI.COLOR_PRIMARIO)],
                 foreground=[("selected", "white")])
    
    @staticmethod
    def crear_marco_con_borde(parent, titulo=None):
        """Creates a frame with border and optional title."""
        marco_exterior = ttk.Frame(parent, style="TFrame")
        
        if titulo:
            lbl_titulo = ttk.Label(marco_exterior, text=titulo, style="Encabezado.TLabel")
            lbl_titulo.pack(anchor="w", padx=10, pady=(10, 5))
        
        marco = ttk.Frame(marco_exterior, style="TFrame", relief="solid", borderwidth=1)
        marco.pack(fill="both", expand=True, padx=10, pady=10)
        
        return marco_exterior, marco
    
    @staticmethod
    def mostrar_mensaje(label, mensaje, tipo="info"):
        """
        Muestra un mensaje en un label con el estilo correspondiente al tipo.
        
        Args:
            label: Label donde mostrar el mensaje
            mensaje: Texto del mensaje
            tipo: Tipo de mensaje (exito, error, info, advertencia)
        """
        estilos = {
            "exito": "Exito.TLabel",
            "error": "Error.TLabel",
            "info": "Info.TLabel",
            "advertencia": "Advertencia.TLabel"
        }
        
        estilo = estilos.get(tipo.lower(), "TLabel")
        label.config(text=mensaje, style=estilo)

class MensajeError(tk.Toplevel):
    """Ventana emergente para mostrar errores detallados."""
    
    def __init__(self, parent, titulo, mensaje, detalles=None):
        super().__init__(parent)
        self.title(titulo)
        self.geometry("400x300")
        self.minsize(400, 200)
        self.transient(parent)
        self.grab_set()
        
        # Configurar estilo
        self.configure(background=EstiloUI.COLOR_FONDO)
        
        # Icono de error
        frame_icono = ttk.Frame(self, style="TFrame")
        frame_icono.pack(fill="x", padx=20, pady=10)
        
        lbl_icono = ttk.Label(frame_icono, text="⚠", font=("Helvetica", 24), 
                             foreground=EstiloUI.COLOR_ERROR, style="TLabel")
        lbl_icono.pack(side="left", padx=(0, 10))
        
        lbl_mensaje = ttk.Label(frame_icono, text=mensaje, wraplength=300, 
                               justify="left", style="TLabel")
        lbl_mensaje.pack(side="left", fill="x", expand=True)
        
        # Detalles (opcional)
        if detalles:
            frame_detalles = ttk.Frame(self, style="TFrame")
            frame_detalles.pack(fill="both", expand=True, padx=20, pady=10)
            
            lbl_detalles = ttk.Label(frame_detalles, text="Detalles:", 
                                    anchor="w", style="TLabel")
            lbl_detalles.pack(anchor="w")
            
            txt_detalles = tk.Text(frame_detalles, wrap="word", height=8, 
                                  background="white", foreground=EstiloUI.COLOR_TEXTO)
            txt_detalles.insert("1.0", detalles)
            txt_detalles.config(state="disabled")
            
            scrollbar = ttk.Scrollbar(frame_detalles, orient="vertical", 
                                     command=txt_detalles.yview)
            txt_detalles.configure(yscrollcommand=scrollbar.set)
            
            txt_detalles.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        
        # Botón de cerrar
        frame_botones = ttk.Frame(self, style="TFrame")
        frame_botones.pack(fill="x", padx=20, pady=10)
        
        btn_cerrar = ttk.Button(frame_botones, text="Cerrar", 
                               command=self.destroy)
        btn_cerrar.pack(side="right")
        
        # Centrar ventana
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

class AplicacionInventario:
    """Main application class."""
    
    def __init__(self, root):
        """Initializes the application."""
        self.root = root
        self.root.title("Sistema de Gestión de Inventario")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Initialize inventory system
        self.sistema = SistemaInventario()
        
        # Apply style
        EstiloUI.aplicar_estilo(self.root)
        
        # Create interface
        self.crear_interfaz()
        
        # Current sort state
        self.sort_column = "nombre"  # Cambiado: Default sort column ahora es nombre en lugar de id
        self.sort_ascending = True  # Default sort direction
        
        # Sort column display names and mapping
        self.column_display_names = {
            "nombre": "Nombre",
            "descripcion": "Descripción",
            "precio": "Precio",
            "cantidad_stock": "Stock"
        }
        
        # Column mapping for combobox to database fields
        self.column_mapping = {
            "Nombre": "nombre",
            "Descripción": "descripcion",
            "Precio": "precio",
            "Stock": "cantidad_stock"
        }
        
        # Load initial data
        self.cargar_productos()
    
    def crear_interfaz(self):
        """Creates the user interface."""
        # Main frame
        self.marco_principal = ttk.Frame(self.root, style="TFrame")
        self.marco_principal.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        lbl_titulo = ttk.Label(self.marco_principal, 
                              text="SISTEMA DE GESTIÓN DE INVENTARIO", 
                              style="Titulo.TLabel")
        lbl_titulo.pack(pady=(0, 20))
        
        # Create tabs
        self.notebook = ttk.Notebook(self.marco_principal)
        self.notebook.pack(fill="both", expand=True)
        
        # Listing tab
        self.tab_listado = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_listado, text="Listado de Productos")
        
        # Management tab
        self.tab_gestion = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_gestion, text="Gestión de Productos")
        
        # Search tab
        self.tab_busqueda = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_busqueda, text="Búsqueda Avanzada")
        
        # Bulk operations tab
        self.tab_masivas = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_masivas, text="Operaciones Masivas")
        
        # Configure each tab
        self.configurar_tab_listado()
        self.configurar_tab_gestion()
        self.configurar_tab_busqueda()
        self.configurar_tab_masivas()
        
        # Status bar
        self.marco_estado = ttk.Frame(self.marco_principal, style="TFrame", relief="solid", borderwidth=1)
        self.marco_estado.pack(fill="x", pady=(10, 0))
        
        self.lbl_estado = ttk.Label(self.marco_estado, text="Listo", style="TLabel")
        self.lbl_estado.pack(padx=10, pady=5)
    
    def configurar_tab_listado(self):
        """Configures the product listing tab."""
        # Frame for sorting options
        marco_ordenar = ttk.Frame(self.tab_listado, style="TFrame")
        marco_ordenar.pack(fill="x", padx=10, pady=(10, 0))
        
        # Sort options
        lbl_ordenar = ttk.Label(marco_ordenar, text="Ordenar por:", style="TLabel")
        lbl_ordenar.pack(side="left", padx=(0, 5))
        
        # Sort column combobox - Eliminado ID de las opciones
        self.var_ordenar_columna = tk.StringVar(value="Nombre")
        combo_ordenar = ttk.Combobox(marco_ordenar, textvariable=self.var_ordenar_columna, width=15, state="readonly")
        combo_ordenar['values'] = ["Nombre", "Precio", "Stock"]
        combo_ordenar.pack(side="left", padx=5)
        combo_ordenar.bind("<<ComboboxSelected>>", self.cambiar_ordenamiento)
        
        # Sort direction button
        self.var_ordenar_direccion = tk.BooleanVar(value=True)
        self.btn_direccion = ttk.Button(marco_ordenar, text="↑", width=3, 
                                       command=self.cambiar_direccion_ordenamiento)
        self.btn_direccion.pack(side="left", padx=5)
        
        # Frame for the table
        marco_ext, marco = EstiloUI.crear_marco_con_borde(self.tab_listado, "Listado de Productos")
        marco_ext.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create table - Eliminada la columna ID
        columnas = ("nombre", "descripcion", "precio", "stock")
        self.tabla_productos = ttk.Treeview(marco, columns=columnas, show="headings")
        
        # Configure headers
        self.tabla_productos.heading("nombre", text="Nombre")
        self.tabla_productos.heading("descripcion", text="Descripción")
        self.tabla_productos.heading("precio", text="Precio")
        self.tabla_productos.heading("stock", text="Stock")
        
        # Configure columns
        self.tabla_productos.column("nombre", width=150)
        self.tabla_productos.column("descripcion", width=300)
        self.tabla_productos.column("precio", width=100, anchor="e")
        self.tabla_productos.column("stock", width=80, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(marco, orient="vertical", command=self.tabla_productos.yview)
        self.tabla_productos.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.tabla_productos.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Action buttons
        marco_botones = ttk.Frame(self.tab_listado, style="TFrame")
        marco_botones.pack(fill="x", padx=10, pady=10)
        
        btn_actualizar = ttk.Button(marco_botones, text="Actualizar Lista", 
                                   command=self.sincronizar_bd)
        btn_actualizar.pack(side="left", padx=5)
        
        btn_editar = ttk.Button(marco_botones, text="Editar Producto", 
                               command=self.editar_producto_seleccionado)
        btn_editar.pack(side="left", padx=5)
        
        btn_eliminar = ttk.Button(marco_botones, text="Eliminar Producto", 
                                 command=self.eliminar_producto_seleccionado)
        btn_eliminar.pack(side="left", padx=5)
        
        # Double click to edit
        self.tabla_productos.bind("<Double-1>", lambda e: self.editar_producto_seleccionado())
    
    def cambiar_ordenamiento(self, event=None):
        """Changes the sort column based on combobox selection."""
        seleccion = self.var_ordenar_columna.get()
        columna_db = self.column_mapping.get(seleccion)
        
        if columna_db:
            # If selecting the same column, just refresh with current direction
            if self.sort_column == columna_db:
                self.cargar_productos()
            else:
                # New column, set to ascending by default
                self.sort_column = columna_db
                self.sort_ascending = True
                self.var_ordenar_direccion.set(True)
                self.btn_direccion.config(text="↑")
                self.cargar_productos()
    
    def cambiar_direccion_ordenamiento(self):
        """Toggles the sort direction."""
        self.sort_ascending = not self.sort_ascending
        self.var_ordenar_direccion.set(self.sort_ascending)
        
        # Update button text
        self.btn_direccion.config(text="↑" if self.sort_ascending else "↓")
        
        # Reload data
        self.cargar_productos()
    
    def configurar_tab_gestion(self):
        """Configures the product management tab."""
        # Frame for the form
        marco_ext, marco = EstiloUI.crear_marco_con_borde(self.tab_gestion, "Agregar/Editar Producto")
        marco_ext.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Variables for the form
        self.var_id = tk.StringVar()  # Mantenemos esta variable para uso interno
        self.var_nombre = tk.StringVar()
        self.var_descripcion = tk.StringVar()
        self.var_precio = tk.StringVar()
        self.var_stock = tk.StringVar()
        self.var_ajuste_stock = tk.StringVar()
        self.var_tipo_ajuste = tk.StringVar(value="agregar")
        
        # Create form
        # Eliminado el campo ID visible
        
        # Name
        frame_nombre = ttk.Frame(marco, style="TFrame")
        frame_nombre.pack(fill="x", padx=20, pady=5)
        
        lbl_nombre = ttk.Label(frame_nombre, text="Nombre:", width=15, anchor="e", style="TLabel")
        lbl_nombre.pack(side="left", padx=(0, 5))
        
        entry_nombre = ttk.Entry(frame_nombre, textvariable=self.var_nombre, width=40)
        entry_nombre.pack(side="left")
        
        ToolTip(entry_nombre, "Ingrese el nombre del producto (1-100 caracteres)")
        
        # Description
        frame_desc = ttk.Frame(marco, style="TFrame")
        frame_desc.pack(fill="x", padx=20, pady=5)
        
        lbl_desc = ttk.Label(frame_desc, text="Descripción:", width=15, anchor="e", style="TLabel")
        lbl_desc.pack(side="left", padx=(0, 5))
        
        entry_desc = ttk.Entry(frame_desc, textvariable=self.var_descripcion, width=60)
        entry_desc.pack(side="left")
        
        ToolTip(entry_desc, "Ingrese la descripción del producto (0-255 caracteres)")
        
        # Price
        frame_precio = ttk.Frame(marco, style="TFrame")
        frame_precio.pack(fill="x", padx=20, pady=5)
        
        lbl_precio = ttk.Label(frame_precio, text="Precio:", width=15, anchor="e", style="TLabel")
        lbl_precio.pack(side="left", padx=(0, 5))
        
        entry_precio = ttk.Entry(frame_precio, textvariable=self.var_precio, width=15)
        entry_precio.pack(side="left")
        
        ToolTip(entry_precio, "Ingrese el precio del producto (número positivo)")
        
        # Stock
        frame_stock = ttk.Frame(marco, style="TFrame")
        frame_stock.pack(fill="x", padx=20, pady=5)
        
        lbl_stock = ttk.Label(frame_stock, text="Stock actual:", width=15, anchor="e", style="TLabel")
        lbl_stock.pack(side="left", padx=(0, 5))
        
        entry_stock = ttk.Entry(frame_stock, textvariable=self.var_stock, width=10)
        entry_stock.pack(side="left")
        
        ToolTip(entry_stock, "Cantidad actual en stock (número entero positivo)")
        
        # Stock adjustment
        frame_ajuste = ttk.Frame(marco, style="TFrame")
        frame_ajuste.pack(fill="x", padx=20, pady=5)
        
        lbl_ajuste = ttk.Label(frame_ajuste, text="Ajuste de stock:", width=15, anchor="e", style="TLabel")
        lbl_ajuste.pack(side="left", padx=(0, 5))
        
        # Radio buttons for adjustment type
        frame_tipo_ajuste = ttk.Frame(frame_ajuste, style="TFrame")
        frame_tipo_ajuste.pack(side="left")
        
        rb_agregar = ttk.Radiobutton(frame_tipo_ajuste, text="Agregar", 
                                    variable=self.var_tipo_ajuste, value="agregar")
        rb_agregar.pack(side="left")
        
        rb_quitar = ttk.Radiobutton(frame_tipo_ajuste, text="Quitar", 
                                   variable=self.var_tipo_ajuste, value="quitar")
        rb_quitar.pack(side="left", padx=10)
        
        # Entry for adjustment amount
        entry_ajuste = ttk.Entry(frame_ajuste, textvariable=self.var_ajuste_stock, width=10)
        entry_ajuste.pack(side="left", padx=10)
        
        lbl_unidades = ttk.Label(frame_ajuste, text="unidades", style="TLabel")
        lbl_unidades.pack(side="left")
        
        ToolTip(entry_ajuste, "Cantidad de unidades a agregar o quitar (dejar en blanco para no ajustar)")
        
        # Buttons
        frame_botones = ttk.Frame(marco, style="TFrame")
        frame_botones.pack(fill="x", padx=20, pady=15)
        
        btn_limpiar = ttk.Button(frame_botones, text="Limpiar Formulario", 
                                command=self.limpiar_formulario)
        btn_limpiar.pack(side="left", padx=5)
        
        btn_guardar = ttk.Button(frame_botones, text="Guardar Producto", 
                                command=self.guardar_producto)
        btn_guardar.pack(side="left", padx=5)
        
        # Status message
        self.lbl_estado_form = ttk.Label(marco, text="", style="TLabel")
        self.lbl_estado_form.pack(fill="x", padx=20, pady=5)
    
    def configurar_tab_busqueda(self):
        """Configures the advanced search tab."""
        # Frame for search criteria
        marco_ext, marco = EstiloUI.crear_marco_con_borde(self.tab_busqueda, "Criterios de Búsqueda")
        marco_ext.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Variables for search
        self.var_busqueda_texto = tk.StringVar()
        self.var_precio_min = tk.StringVar()
        self.var_precio_max = tk.StringVar()
        self.var_stock_min = tk.StringVar()
        self.var_stock_max = tk.StringVar()
        self.var_busqueda_orden = tk.StringVar(value="nombre")  # Cambiado: Default ahora es nombre
        self.var_busqueda_direccion = tk.BooleanVar(value=True)
        
        # Search text
        frame_texto = ttk.Frame(marco, style="TFrame")
        frame_texto.pack(fill="x", padx=20, pady=5)
        
        lbl_texto = ttk.Label(frame_texto, text="Texto:", width=15, anchor="e", style="TLabel")
        lbl_texto.pack(side="left", padx=(0, 5))
        
        entry_texto = ttk.Entry(frame_texto, textvariable=self.var_busqueda_texto, width=40)
        entry_texto.pack(side="left")
        
        ToolTip(entry_texto, "Buscar por nombre o descripción")  # Actualizado: Eliminada referencia a ID
        
        # Price range
        frame_precio = ttk.Frame(marco, style="TFrame")
        frame_precio.pack(fill="x", padx=20, pady=5)
        
        lbl_precio = ttk.Label(frame_precio, text="Rango de precio:", width=15, anchor="e", style="TLabel")
        lbl_precio.pack(side="left", padx=(0, 5))
        
        entry_precio_min = ttk.Entry(frame_precio, textvariable=self.var_precio_min, width=10)
        entry_precio_min.pack(side="left")
        
        lbl_precio_a = ttk.Label(frame_precio, text="a", style="TLabel")
        lbl_precio_a.pack(side="left", padx=5)
        
        entry_precio_max = ttk.Entry(frame_precio, textvariable=self.var_precio_max, width=10)
        entry_precio_max.pack(side="left")
        
        ToolTip(entry_precio_min, "Precio mínimo (dejar vacío para no establecer límite)")
        ToolTip(entry_precio_max, "Precio máximo (dejar vacío para no establecer límite)")
        
        # Stock range
        frame_stock = ttk.Frame(marco, style="TFrame")
        frame_stock.pack(fill="x", padx=20, pady=5)
        
        lbl_stock = ttk.Label(frame_stock, text="Rango de stock:", width=15, anchor="e", style="TLabel")
        lbl_stock.pack(side="left", padx=(0, 5))
        
        entry_stock_min = ttk.Entry(frame_stock, textvariable=self.var_stock_min, width=10)
        entry_stock_min.pack(side="left")
        
        lbl_stock_a = ttk.Label(frame_stock, text="a", style="TLabel")
        lbl_stock_a.pack(side="left", padx=5)
        
        entry_stock_max = ttk.Entry(frame_stock, textvariable=self.var_stock_max, width=10)
        entry_stock_max.pack(side="left")
        
        ToolTip(entry_stock_min, "Stock mínimo (dejar vacío para no establecer límite)")
        ToolTip(entry_stock_max, "Stock máximo (dejar vacío para no establecer límite)")
        
        # Sort options - Eliminado ID de las opciones
        frame_orden = ttk.Frame(marco, style="TFrame")
        frame_orden.pack(fill="x", padx=20, pady=5)
        
        lbl_orden = ttk.Label(frame_orden, text="Ordenar por:", width=15, anchor="e", style="TLabel")
        lbl_orden.pack(side="left", padx=(0, 5))
        
        combo_orden = ttk.Combobox(frame_orden, textvariable=self.var_busqueda_orden, width=15)
        combo_orden['values'] = ["nombre", "precio", "cantidad_stock"]
        combo_orden['state'] = 'readonly'
        combo_orden.pack(side="left", padx=5)
        
        # Sort direction
        frame_direccion = ttk.Frame(frame_orden, style="TFrame")
        frame_direccion.pack(side="left", padx=10)
        
        rb_asc = ttk.Radiobutton(frame_direccion, text="Ascendente", 
                                variable=self.var_busqueda_direccion, value=True)
        rb_asc.pack(side="left")
        
        rb_desc = ttk.Radiobutton(frame_direccion, text="Descendente", 
                                variable=self.var_busqueda_direccion, value=False)
        rb_desc.pack(side="left", padx=10)
        
        # Buttons
        frame_botones = ttk.Frame(marco, style="TFrame")
        frame_botones.pack(fill="x", padx=20, pady=15)
        
        btn_limpiar = ttk.Button(frame_botones, text="Limpiar Filtros", 
                                command=self.limpiar_busqueda)
        btn_limpiar.pack(side="left", padx=5)
        
        btn_buscar = ttk.Button(frame_botones, text="Buscar", 
                               command=self.buscar_productos)
        btn_buscar.pack(side="left", padx=5)
        
        # Search results
        marco_ext_res, marco_res = EstiloUI.crear_marco_con_borde(self.tab_busqueda, "Resultados de Búsqueda")
        marco_ext_res.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create results table - Eliminada la columna ID
        columnas = ("nombre", "descripcion", "precio", "stock")
        self.tabla_resultados = ttk.Treeview(marco_res, columns=columnas, show="headings")
        
        # Configure headers
        self.tabla_resultados.heading("nombre", text="Nombre")
        self.tabla_resultados.heading("descripcion", text="Descripción")
        self.tabla_resultados.heading("precio", text="Precio")
        self.tabla_resultados.heading("stock", text="Stock")
        
        # Configure columns
        self.tabla_resultados.column("nombre", width=150)
        self.tabla_resultados.column("descripcion", width=300)
        self.tabla_resultados.column("precio", width=100, anchor="e")
        self.tabla_resultados.column("stock", width=80, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(marco_res, orient="vertical", command=self.tabla_resultados.yview)
        self.tabla_resultados.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.tabla_resultados.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def configurar_tab_masivas(self):
        """Configures the bulk operations tab."""
        # Frame for bulk price update
        marco_ext, marco = EstiloUI.crear_marco_con_borde(self.tab_masivas, "Actualización Masiva de Precios")
        marco_ext.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Variables
        self.var_porcentaje = tk.StringVar()
        self.var_precio_min_masivo = tk.StringVar()
        self.var_precio_max_masivo = tk.StringVar()
        self.var_stock_min_masivo = tk.StringVar()
        self.var_stock_max_masivo = tk.StringVar()
        
        # Percentage
        frame_porcentaje = ttk.Frame(marco, style="TFrame")
        frame_porcentaje.pack(fill="x", padx=20, pady=5)
        
        lbl_porcentaje = ttk.Label(frame_porcentaje, text="Porcentaje:", width=15, anchor="e", style="TLabel")
        lbl_porcentaje.pack(side="left", padx=(0, 5))
        
        entry_porcentaje = ttk.Entry(frame_porcentaje, textvariable=self.var_porcentaje, width=10)
        entry_porcentaje.pack(side="left")
        
        lbl_porcentaje_info = ttk.Label(frame_porcentaje, text="% (positivo para aumentar, negativo para disminuir)", style="TLabel")
        lbl_porcentaje_info.pack(side="left", padx=5)
        
        ToolTip(entry_porcentaje, "Ingrese el porcentaje de cambio (-90 a 1000)")
        
        # Filters
        lbl_filtros = ttk.Label(marco, text="Aplicar a productos que cumplan con:", style="TLabel")
        lbl_filtros.pack(anchor="w", padx=20, pady=(10, 5))
        
        # Price range
        frame_precio = ttk.Frame(marco, style="TFrame")
        frame_precio.pack(fill="x", padx=20, pady=5)
        
        lbl_precio = ttk.Label(frame_precio, text="Rango de precio:", width=15, anchor="e", style="TLabel")
        lbl_precio.pack(side="left", padx=(0, 5))
        
        entry_precio_min = ttk.Entry(frame_precio, textvariable=self.var_precio_min_masivo, width=10)
        entry_precio_min.pack(side="left")
        
        lbl_precio_a = ttk.Label(frame_precio, text="a", style="TLabel")
        lbl_precio_a.pack(side="left", padx=5)
        
        entry_precio_max = ttk.Entry(frame_precio, textvariable=self.var_precio_max_masivo, width=10)
        entry_precio_max.pack(side="left")
        
        # Stock range
        frame_stock = ttk.Frame(marco, style="TFrame")
        frame_stock.pack(fill="x", padx=20, pady=5)
        
        lbl_stock = ttk.Label(frame_stock, text="Rango de stock:", width=15, anchor="e", style="TLabel")
        lbl_stock.pack(side="left", padx=(0, 5))
        
        entry_stock_min = ttk.Entry(frame_stock, textvariable=self.var_stock_min_masivo, width=10)
        entry_stock_min.pack(side="left")
        
        lbl_stock_a = ttk.Label(frame_stock, text="a", style="TLabel")
        lbl_stock_a.pack(side="left", padx=5)
        
        entry_stock_max = ttk.Entry(frame_stock, textvariable=self.var_stock_max_masivo, width=10)
        entry_stock_max.pack(side="left")
        
        # Buttons
        frame_botones = ttk.Frame(marco, style="TFrame")
        frame_botones.pack(fill="x", padx=20, pady=15)
        
        btn_aplicar = ttk.Button(frame_botones, text="Aplicar Cambio de Precios", 
                                command=self.actualizar_precios_masivos)
        btn_aplicar.pack(side="left", padx=5)
        
        # Status message
        self.lbl_estado_masivo = ttk.Label(marco, text="", style="TLabel")
        self.lbl_estado_masivo.pack(fill="x", padx=20, pady=5)
    
    def cargar_productos(self):
        """Loads products into the table with current sorting."""
        # Clear table
        for item in self.tabla_productos.get_children():
            self.tabla_productos.delete(item)
        
        # Get products with current sort settings
        productos = self.sistema.obtener_todos_productos(
            order_by=self.sort_column, 
            ascending=self.sort_ascending
        )
        
        # Insert into table - Eliminado el ID de los valores mostrados
        for producto in productos:
            self.tabla_productos.insert("", "end", values=(
                producto.nombre,
                producto.descripcion,
                f"${producto.precio:.2f}",
                producto.cantidad_stock
            ), tags=(str(producto.id),))  # Guardamos el ID como tag para referencia interna
        
        # Update status
        self.actualizar_estado(f"Se cargaron {len(productos)} productos.")
        
        # Update sort combobox to match current sort
        for display_name, db_field in self.column_mapping.items():
            if db_field == self.sort_column:
                self.var_ordenar_columna.set(display_name)
                break
    
    def sincronizar_bd(self):
        """Synchronizes with the database and refreshes the product list."""
        exito, mensaje = self.sistema.sincronizar_con_bd()
        
        if exito:
            self.actualizar_estado(mensaje)
            self.cargar_productos()
        else:
            # Mejorado: Mostrar error detallado
            MensajeError(self.root, "Error de Sincronización", 
                        "No se pudo sincronizar con la base de datos.", mensaje)
    
    def limpiar_formulario(self):
        """Clears the product management form."""
        self.var_id.set("")
        self.var_nombre.set("")
        self.var_descripcion.set("")
        self.var_precio.set("")
        self.var_stock.set("")
        self.var_ajuste_stock.set("")
        self.var_tipo_ajuste.set("agregar")
        self.lbl_estado_form.config(text="")
    
    def guardar_producto(self):
        """Saves a product (new or edited)."""
        # Get form data
        id_producto = self.var_id.get().strip()
        nombre = self.var_nombre.get().strip()
        descripcion = self.var_descripcion.get().strip()
        precio = self.var_precio.get().strip()
        stock = self.var_stock.get().strip()
        ajuste_stock = self.var_ajuste_stock.get().strip()
        tipo_ajuste = self.var_tipo_ajuste.get()
        
        # Validate data
        if not nombre:
            self.mostrar_error_formulario("El nombre del producto es obligatorio.")
            return
        
        try:
            precio_float = float(precio) if precio else 0
            if precio_float <= 0:
                self.mostrar_error_formulario("El precio debe ser mayor que cero.")
                return
        except ValueError:
            self.mostrar_error_formulario("El precio debe ser un número válido.")
            return
        
        try:
            stock_int = int(stock) if stock else 0
            if stock_int < 0:
                self.mostrar_error_formulario("El stock no puede ser negativo.")
                return
        except ValueError:
            self.mostrar_error_formulario("El stock debe ser un número entero.")
            return
        
        # Process stock adjustment if provided
        ajuste_int = 0
        if ajuste_stock:
            try:
                ajuste_int = int(ajuste_stock)
                if ajuste_int <= 0:
                    self.mostrar_error_formulario("El ajuste de stock debe ser un número positivo.")
                    return
                    
                # Apply sign based on adjustment type
                if tipo_ajuste == "quitar":
                    ajuste_int = -ajuste_int
            except ValueError:
                self.mostrar_error_formulario("El ajuste de stock debe ser un número entero.")
                return
        
        # Save product
        if id_producto:  # Edit existing product
            exito, mensaje = self.sistema.editar_producto(
                int(id_producto), nombre, descripcion, precio_float, stock_int, ajuste_int
            )
        else:  # New product
            exito, mensaje, _ = self.sistema.agregar_producto(
                nombre, descripcion, precio_float, stock_int
            )
        
        # Show result
        if exito:
            # Mejorado: Usar el método de EstiloUI para mostrar mensajes
            EstiloUI.mostrar_mensaje(self.lbl_estado_form, mensaje, "exito")
            self.cargar_productos()
            if not id_producto:  # If it was a new product, clear the form
                self.limpiar_formulario()
        else:
            # Mejorado: Mostrar error detallado
            EstiloUI.mostrar_mensaje(self.lbl_estado_form, mensaje, "error")
    
    def mostrar_error_formulario(self, mensaje):
        """Shows an error message in the form."""
        EstiloUI.mostrar_mensaje(self.lbl_estado_form, mensaje, "error")
    
    def editar_producto_seleccionado(self):
        """Loads data from the selected product into the form."""
        seleccion = self.tabla_productos.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Por favor, seleccione un producto para editar.")
            return
        
        # Get data from selected product
        item = self.tabla_productos.item(seleccion[0])
        valores = item["values"]
        
        # Obtener el ID del producto desde los tags
        id_producto = item["tags"][0] if item["tags"] else None
        
        if not id_producto:
            messagebox.showerror("Error", "No se pudo identificar el producto seleccionado.")
            return
        
        # Load data into form
        self.var_id.set(id_producto)  # Guardamos el ID internamente
        self.var_nombre.set(valores[0])  # Nombre ahora es el primer valor
        self.var_descripcion.set(valores[1])  # Descripción ahora es el segundo valor
        self.var_precio.set(valores[2].replace("$", ""))  # Precio ahora es el tercer valor
        self.var_stock.set(valores[3])  # Stock ahora es el cuarto valor
        self.var_ajuste_stock.set("")  # Clear adjustment field
        
        # Switch to management tab
        self.notebook.select(self.tab_gestion)
    
    def eliminar_producto_seleccionado(self):
        """Deletes the selected product."""
        seleccion = self.tabla_productos.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Por favor, seleccione un producto para eliminar.")
            return
        
        # Get data from selected product
        item = self.tabla_productos.item(seleccion[0])
        valores = item["values"]
        id_producto = item["tags"][0] if item["tags"] else None
        nombre_producto = valores[0]  # Nombre ahora es el primer valor
        
        if not id_producto:
            messagebox.showerror("Error", "No se pudo identificar el producto seleccionado.")
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Confirmar Eliminación", 
                                  f"¿Está seguro de eliminar el producto '{nombre_producto}'?"):
            return
        
        # Delete product
        exito, mensaje = self.sistema.eliminar_producto(int(id_producto))
        
        # Show result
        if exito:
            self.actualizar_estado(mensaje)
            self.cargar_productos()
        else:
            # Mejorado: Mostrar error detallado
            MensajeError(self.root, "Error al Eliminar", 
                        "No se pudo eliminar el producto.", mensaje)
    
    def limpiar_busqueda(self):
        """Clears search criteria."""
        self.var_busqueda_texto.set("")
        self.var_precio_min.set("")
        self.var_precio_max.set("")
        self.var_stock_min.set("")
        self.var_stock_max.set("")
        self.var_busqueda_orden.set("nombre")  # Cambiado: Default ahora es nombre
        self.var_busqueda_direccion.set(True)
        
        # Clear results
        for item in self.tabla_resultados.get_children():
            self.tabla_resultados.delete(item)
    
    def buscar_productos(self):
        """Searches products according to specified criteria."""
        # Get search criteria
        texto = self.var_busqueda_texto.get().strip()
        precio_min_str = self.var_precio_min.get().strip()
        precio_max_str = self.var_precio_max.get().strip()
        stock_min_str = self.var_stock_min.get().strip()
        stock_max_str = self.var_stock_max.get().strip()
        order_by = self.var_busqueda_orden.get()
        ascending = self.var_busqueda_direccion.get()
        
        # Convert to appropriate types
        precio_min = None
        precio_max = None
        stock_min = None
        stock_max = None
        
        try:
            if precio_min_str:
                precio_min = float(precio_min_str)
            if precio_max_str:
                precio_max = float(precio_max_str)
            if stock_min_str:
                stock_min = int(stock_min_str)
            if stock_max_str:
                stock_max = int(stock_max_str)
        except ValueError:
            # Mejorado: Mostrar error detallado
            MensajeError(self.root, "Error de Validación", 
                        "Los valores numéricos ingresados no son válidos.",
                        "Asegúrese de ingresar números válidos para los rangos de precio y stock.")
            return
        
        # Validate ranges
        if precio_min is not None and precio_max is not None and precio_min > precio_max:
            # Mejorado: Mostrar error detallado
            MensajeError(self.root, "Error de Validación", 
                        "El precio mínimo no puede ser mayor que el precio máximo.",
                        "Por favor, corrija el rango de precios.")
            return
        
        if stock_min is not None and stock_max is not None and stock_min > stock_max:
            # Mejorado: Mostrar error detallado
            MensajeError(self.root, "Error de Validación", 
                        "El stock mínimo no puede ser mayor que el stock máximo.",
                        "Por favor, corrija el rango de stock.")
            return
        
        # Perform search
        resultados = self.sistema.buscar_productos(
            texto=texto if texto else None,
            precio_min=precio_min,
            precio_max=precio_max,
            stock_min=stock_min,
            stock_max=stock_max,
            order_by=order_by,
            ascending=ascending
        )
        
        # Clear results table
        for item in self.tabla_resultados.get_children():
            self.tabla_resultados.delete(item)
        
        # Show results - Eliminado el ID de los valores mostrados
        for producto in resultados:
            self.tabla_resultados.insert("", "end", values=(
                producto.nombre,
                producto.descripcion,
                f"${producto.precio:.2f}",
                producto.cantidad_stock
            ), tags=(str(producto.id),))  # Guardamos el ID como tag para referencia interna
        
        # Update status
        self.actualizar_estado(f"Se encontraron {len(resultados)} productos.")
    
    def actualizar_precios_masivos(self):
        """Updates prices for multiple products by a percentage."""
        # Get data
        porcentaje_str = self.var_porcentaje.get().strip()
        precio_min_str = self.var_precio_min_masivo.get().strip()
        precio_max_str = self.var_precio_max_masivo.get().strip()
        stock_min_str = self.var_stock_min_masivo.get().strip()
        stock_max_str = self.var_stock_max_masivo.get().strip()
        
        # Validate percentage
        if not porcentaje_str:
            # Mejorado: Usar el método de EstiloUI para mostrar mensajes
            EstiloUI.mostrar_mensaje(self.lbl_estado_masivo, "Debe ingresar un porcentaje.", "error")
            return
        
        try:
            porcentaje = float(porcentaje_str)
            if porcentaje < -90 or porcentaje > 1000:
                EstiloUI.mostrar_mensaje(self.lbl_estado_masivo, 
                                        "El porcentaje debe estar entre -90 y 1000.", "error")
                return
        except ValueError:
            EstiloUI.mostrar_mensaje(self.lbl_estado_masivo, 
                                    "El porcentaje debe ser un número válido.", "error")
            return
        
        # Convert criteria to appropriate types
        condiciones = {}
        
        try:
            if precio_min_str and precio_max_str:
                precio_min = float(precio_min_str)
                precio_max = float(precio_max_str)
                if precio_min > precio_max:
                    EstiloUI.mostrar_mensaje(self.lbl_estado_masivo, 
                                           "El precio mínimo no puede ser mayor que el precio máximo.", "error")
                    return
                condiciones["precio_min"] = precio_min
                condiciones["precio_max"] = precio_max
            
            if stock_min_str and stock_max_str:
                stock_min = int(stock_min_str)
                stock_max = int(stock_max_str)
                if stock_min > stock_max:
                    EstiloUI.mostrar_mensaje(self.lbl_estado_masivo, 
                                           "El stock mínimo no puede ser mayor que el stock máximo.", "error")
                    return
                condiciones["stock_min"] = stock_min
                condiciones["stock_max"] = stock_max
        except ValueError:
            EstiloUI.mostrar_mensaje(self.lbl_estado_masivo, 
                                    "Los valores numéricos ingresados no son válidos.", "error")
            return
        
        # Confirm operation
        if not messagebox.askyesno("Confirmar Actualización", 
                                  f"¿Está seguro de actualizar los precios en un {porcentaje}%?"):
            return
        
        # Perform update
        exito, mensaje, num_actualizados = self.sistema.actualizar_precios_masivos(
            porcentaje, condiciones
        )
        
        # Show result
        if exito:
            EstiloUI.mostrar_mensaje(self.lbl_estado_masivo, mensaje, "exito")
            self.cargar_productos()
        else:
            EstiloUI.mostrar_mensaje(self.lbl_estado_masivo, mensaje, "error")
    
    def actualizar_estado(self, mensaje):
        """Updates the status bar message."""
        self.lbl_estado.config(text=mensaje)
    
    def cerrar(self):
        """Closes the application."""
        self.sistema.cerrar()
        self.root.destroy()

# Entry point
if __name__ == "__main__":
    try:
        # Create main window
        root = tk.Tk()
        app = AplicacionInventario(root)
        
        # Configure application close
        root.protocol("WM_DELETE_WINDOW", app.cerrar)
        
        # Start event loop
        root.mainloop()
    except Exception as e:
        # Mejorado: Mostrar error detallado
        messagebox.showerror("Error Fatal", 
                            f"Ha ocurrido un error inesperado: {str(e)}\n\n"
                            f"Por favor, contacte al soporte técnico.")
        print(f"Error fatal: {str(e)}")