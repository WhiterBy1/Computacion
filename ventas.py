#as
from datetime import datetime, timedelta
import random
import re
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from dataclasses import dataclass
from typing import List, Dict, Optional, Literal
from tabulate import tabulate

@dataclass
class Product:
    """Clase que representa un producto."""
    code: str
    name: str
    price: float
    unit: Literal['unidad','libra','kilo']
    stock: float

class ProductManager:
    """Clase que define los productos y abarca la lógica de creación y búsqueda de productos."""

    def __init__(self):
        self.products: List[Product] = self.create_products_test()

    def create_products_test(self) -> List[Product]:
        """Crea una lista de productos con precios en COP."""
        return [
            Product("COD1", "Agua 600ml", 2500, "unidad", 100),
            Product("COD2", "Arroz Diana 1kg", 4000, "kilo", 50),
            Product("COD3", "Carne Molida 1 libra", 18000, "libra", 30),
            Product("COD4", "Café Juan Valdez 500g", 20000, "kilo", 40),
            Product("COD5", "Coca-Cola 1L", 4500, "unidad", 80),
            Product("COD6", "Galletas Saltín Noel", 2500, "unidad", 60),
            Product("COD7", "Huevos x 30 unidades", 15000, "unidad", 25),
            Product("COD8", "Leche Alquería 1L", 3500, "unidad", 70),
            Product("COD9", "Papas Margarita 150g", 3500, "unidad", 45),
            Product("COD10", "Pan Bimbo Integral", 6000, "unidad", 35),
            Product("COD11", "Pechuga de Pollo 1 libra", 10000, "libra", 20),
            Product("COD12", "Queso Campesino 1 libra", 12000, "libra", 15),
        ]

    def find_product(self, search_term: str) -> Optional[Product]:
        """Busca un producto por código o nombre."""
        search_term = search_term.lower()
        return next(
            (product for product in self.products
             if search_term in (product.code.lower(), product.name.lower())),
            None
        )

class Validador:
    """Clase que valida las entradas del usuario."""

    @staticmethod
    def validar_cantidad(cantidad: str, unidad: str) -> Optional[float]:
        """
        Valida que la cantidad ingresada sea un número positivo y coincida con el tipo de unidad.

        Args:
            cantidad (str): La cantidad ingresada por el usuario.
            unidad (str): La unidad del producto ('unidad', 'kilo', 'libra')

        Returns:
            Optional[float]: La cantidad validada como float si es válida, None en caso contrario.
        """
        try:
            cantidad_float = float(cantidad)
            if cantidad_float <= 0:
                return None
                
            if unidad == 'unidad':
                # Para unidades, verificar que sea un número entero
                if not cantidad_float.is_integer():
                    return None
                
            # Para kilos y libras, permitir decimales
            return cantidad_float
            
        except ValueError:
            return None

    @staticmethod
    def validar_producto(producto: str) -> bool:
        """
        Valida que se haya seleccionado un producto.

        Args:
            producto (str): El producto seleccionado por el usuario.

        Returns:
            bool: True si el producto es válido, False en caso contrario.
        """
        return bool(producto.strip())

class Venta:
    """Clase que representa una venta, calcula el total e incluye impuestos."""
    COMPANY_INFO = {
        "nit": "901.234.567-8",
        "nombre": "TIENDA COLOMBIANA SAS",
        "direccion": "Calle 123 # 45-67, Cartagena de Indias D.T. y C.",
        "telefono": "(601) 2345678",
        "email": "ventas@tiendacolombiana.com.co",
        "regimen": "Régimen Común",
        "resolucion_dian": "Resolución DIAN Nº 123456789",
        "fecha_resolucion": "2023-01-01"
    }
    
    _numero_factura = 1  # Contador para numeración consecutiva
    
    def __init__(self):
        self.items: List[Dict] = []
        self.subtotal = 0.0
        self.total_iva = 0.0
        self.numero_factura = Venta._numero_factura
        self.fecha_emision = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
        self.cliente_info = {"nombre": "", "nit": ""}
        self.forma_pago = "Contado"
        self.numero_autorizacion = self.generar_numero_autorizacion()
        Venta._numero_factura += 1

    def generar_numero_autorizacion(self):
        """Genera un numero aleatorio, No se comprueba ya que es una version de prueba de la aplicacion
        para uso practivo se deveria verificar que no exista uno anterior registrado

        Returns:
            int: numero_autorizacion
        """
        return f"{random.randint(100000000000, 999999999999)}"
    
    @staticmethod
    def calcular_descuento(price: float) -> float:
        """
        Calcula el descuento aplicable según el rango de precios.

        Args:
            price (float): Precio del producto.

        Returns:
            float: Descuento aplicable al producto.
        """
        if price < 100000:
            return 0.05  # 5% de descuento
        elif 100000 <= price <= 500000:
            return 0.0  # Sin descuento
        else:
            return 0.10  # 10% de descuento
        
    @staticmethod
    def calculate_tax(amount: float, tax_rate:float) -> float:
        """
        Calcula el impuesto para un monto dado.

        Args:
            amount (float): El monto sobre el cual se calculará el impuesto.
            tax (float): El porcentaje de impuesto sobre el monto.

        Returns:
            float: El impuesto calculado.
        """
        return round(amount * tax_rate, 2)

    def agregar_producto(self, producto: Product, cantidad: float) -> None:
        """
        Añade un producto a la venta.

        Args:
            producto (Product): El producto a añadir.
            cantidad (float): La cantidad del producto.
        """
        
        subtotal_producto = producto.price * cantidad
        iva_producto = self.calculate_tax(subtotal_producto, 0.19)
        descuento = self.calcular_descuento(subtotal_producto)
        descuento_valor = subtotal_producto * descuento
        total_con_descuento = subtotal_producto - descuento_valor + iva_producto
        
        existe_producto = next((item for item in self.items if item['code'] == producto.code), None)
        if not existe_producto:
            self.items.append({
                'code': producto.code,
                'name': producto.name,
                'price': producto.price,
                'quantity': cantidad,
                'unit': producto.unit,
                'subtotal': subtotal_producto,
                'iva': iva_producto,
                'descuento_porcentaje': descuento * 100,
                'descuento_valor': descuento_valor,
                'total': total_con_descuento
            })
            self.subtotal += subtotal_producto
            self.total_iva += iva_producto
        else:
            # Actualizar cantidad y recalcular
            nueva_cantidad = existe_producto['quantity'] + cantidad
            nuevo_subtotal = producto.price * nueva_cantidad
            nuevo_iva = self.calculate_tax(nuevo_subtotal, 0.19)
            nuevo_descuento = self.calcular_descuento(nuevo_subtotal)
            nuevo_descuento_valor = nuevo_subtotal * nuevo_descuento
            nuevo_total = nuevo_subtotal - nuevo_descuento_valor + nuevo_iva
            
            # Restar valores anteriores
            self.subtotal -= existe_producto['subtotal']
            self.total_iva -= existe_producto['iva']
            
            # Actualizar item
            existe_producto.update({
                'quantity': nueva_cantidad,
                'subtotal': nuevo_subtotal,
                'iva': nuevo_iva,
                'descuento_porcentaje': nuevo_descuento * 100,
                'descuento_valor': nuevo_descuento_valor,
                'total': nuevo_total
            })
            
            # Sumar nuevos valores
            self.subtotal += nuevo_subtotal
            self.total_iva += nuevo_iva

    def calcular_total(self) -> float:
        """
        Calcula el total de la venta incluyendo descuentos e IVA.

        Returns:
            float: Total de la venta.
        """
        total_descuentos = sum(item['descuento_valor'] for item in self.items)
        return self.subtotal - total_descuentos + self.total_iva

    def generar_factura(self) -> str:
        """Genera el texto de la factura usando tabulate para un mejor formato."""
        # Encabezado de la factura
        factura_header = f"""{self.COMPANY_INFO['nombre']}
            NIT: {self.COMPANY_INFO['nit']}
            Dirección: {self.COMPANY_INFO['direccion']}
            Tel: {self.COMPANY_INFO['telefono']} - Email: {self.COMPANY_INFO['email']}
            {self.COMPANY_INFO['resolucion_dian']} - Fecha: {self.COMPANY_INFO['fecha_resolucion']}
            {"="*80}
            FACTURA ELECTRÓNICA DE VENTA N° {self.numero_factura}
            Fecha de emisión: {self.fecha_emision}
            Fecha de vencimiento: {self.fecha_vencimiento}
            Número de autorización: {self.numero_autorizacion}
            {"="*80}
            Cliente: {self.cliente_info['nombre']}
            NIT/CC: {self.cliente_info['nit']}
            Forma de pago: {self.forma_pago}
            {"-"*80}
            """

        # Preparar los datos para la tabla
        table_data = []
        total_descuentos = 0
        for item in self.items:
            total_descuentos += item['descuento_valor']
            table_data.append([
                item['code'],
                item['name'],
                f"${item['price']:,.0f}",
                f"{item['quantity']:.2f}",
                item['unit'],
                f"${item['subtotal']:,.0f}",
                f"{item['descuento_porcentaje']:.0f}%",
                f"${item['iva']:,.0f}",
                f"${item['total']:,.0f}"
            ])

        # Definir headers
        headers = [
            'Código', 
            'Producto', 
            'Precio/Unidad', 
            'Cantidad',
            'Unidad',
            'Subtotal',
            'Descuento',
            'iva',
            'Total'
        ]

        # Generar la tabla principal
        tabla_productos = tabulate(
            table_data,
            headers=headers,
            tablefmt='grid',  
            numalign='right',
            stralign='left'
        )

        # Generar tabla de totales
        tabla_totales = tabulate(
            [
                ['Subtotal:', f"${self.subtotal:,.0f}"],
                ['Total IVA:', f"${self.total_iva:,.0f}"],
                ['Total Descuentos:', f"${total_descuentos:,.0f}"],
                ['TOTAL A PAGAR (IVA incluido):', f"${self.calcular_total():,.0f}"]
            ],
            tablefmt='grid',
            numalign='right',
            stralign='left'
        )
        # Pie de factura con datos legales
        factura_footer = (
            "\n" + "="*80 + "\n"
            "IMPORTANTE:\n"
            "Este documento es una representación impresa de un comprobante electrónico\n"
            "Sujeto a revisión y verificación por parte de la DIAN\n"
            f"IVA incluido del 19% - Régimen: {self.COMPANY_INFO['regimen']}\n"
            "Gracias por su compra!"
        )
        # Combinar todo
        factura_completa = (
            "\n=== FACTURA DE VENTA ===\n\n"
            f"{factura_header}\n"
            f"{tabla_productos}\n\n"
            f"{tabla_totales}\n"
            f"\n{factura_footer}"
        )
        return factura_completa
    
class InvoiceWindow(tk.Toplevel):
    """Ventana personalizada para mostrar la factura."""
    
    def __init__(self, parent, invoice_text):
        super().__init__(parent)
        
        # Configurar ventana
        self.title("Venta Finalizada")
        self.geometry("1100x600")
        self.minsize(1100, 600)
        self.maxsize(1100, 600)
        
        # Hacer la ventana modal
        self.transient(parent)
        self.grab_set()
        
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Añadir mensaje de éxito
        success_frame = ttk.Frame(self)
        success_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Label(
            success_frame,
            text="Venta procesada exitosamente",
            font=("TkDefaultFont", 10, "bold")
        ).pack(pady=5)
        
        # Crear área de texto para la factura
        self.invoice_text = scrolledtext.ScrolledText(
            self,
            wrap=tk.NONE,  # Desactivar wrap para mantener el formato
            font=('Courier New', 10),
            width=100,
            height=30
        )
        self.invoice_text.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Insertar texto de la factura
        self.invoice_text.insert("1.0", invoice_text)
        self.invoice_text.configure(state="disabled")
        
        # Botón de cerrar
        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, pady=10)
        
        ttk.Button(
            button_frame,
            text="Aceptar",
            command=self.destroy,
            style="Accent.TButton"
        ).pack(padx=5, pady=5)
        
        # Centrar la ventana
        self.center_window()
        
    def center_window(self):
        """Centra la ventana en la pantalla."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

class ProductManagementWindow(tk.Toplevel):
    """Ventana modal para gestionar productos de la venta actual."""
    
    def __init__(self, parent, venta):
        super().__init__(parent)
        
        self.parent = parent
        self.venta = venta
        
        # Configurar ventana
        self.title("Gestionar Productos")
        self.geometry("600x500")
        self.minsize(600, 500)
        self.maxsize(600, 500)
        
        # Hacer la ventana modal
        self.transient(parent)
        self.grab_set()
        
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.setup_ui()
        self.center_window()
        
    def setup_ui(self):
        """Configura la interfaz de usuario de la ventana de gestión."""
        # Frame principal
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Lista de productos
        list_frame = ttk.LabelFrame(main_frame, text="Productos en la venta actual", padding="10")
        list_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Crear Treeview para mostrar los productos
        self.tree = ttk.Treeview(list_frame, columns=("code", "name", "quantity", "unit", "total"), 
                                show="headings", selectmode="browse")
        
        # Configurar las columnas
        self.tree.heading("code", text="Código")
        self.tree.heading("name", text="Nombre")
        self.tree.heading("quantity", text="Cantidad")
        self.tree.heading("unit", text="Unidad")
        self.tree.heading("total", text="Total")
        
        self.tree.column("code", width=80)
        self.tree.column("name", width=200)
        self.tree.column("quantity", width=80)
        self.tree.column("unit", width=80)
        self.tree.column("total", width=100)
        
        # Añadir scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Colocar Treeview y scrollbar
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Frame para modificación
        modify_frame = ttk.LabelFrame(main_frame, text="Modificar producto seleccionado", padding="10")
        modify_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        
        # Entrada para nueva cantidad
        ttk.Label(modify_frame, text="Nueva cantidad:").grid(row=0, column=0, padx=5, pady=5)
        self.quantity_entry = ttk.Entry(modify_frame, width=15)
        self.quantity_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Botones de acción
        button_frame = ttk.Frame(modify_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(
            button_frame,
            text="Actualizar Cantidad",
            command=self.update_quantity,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Eliminar Producto",
            command=self.remove_product,
            style="Danger.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        # Botón de cerrar
        ttk.Button(
            main_frame,
            text="Cerrar",
            command=self.close_window
        ).grid(row=2, column=0, pady=10)
        
        # Cargar productos
        self.load_products()
        
    def load_products(self):
        """Carga los productos en el Treeview."""
        # Limpiar Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Insertar productos
        for item in self.venta.items:
            self.tree.insert("", "end", values=(
                item["code"],
                item["name"],
                f"{item['quantity']:.2f}",
                item["unit"],
                f"${item['total']:,.0f}"
            ))
    
    def update_quantity(self):
        """Actualiza la cantidad del producto seleccionado."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Por favor seleccione un producto")
            return

        item_values = self.tree.item(selected_item)["values"]
        code = item_values[0]
        new_quantity = self.quantity_entry.get()

        product = next((item for item in self.venta.items if item["code"] == code), None)
        if not product:
            return

        original_product = self.parent.product_manager.find_product(code)
        if not original_product:
            return

        cantidad_validada = Validador.validar_cantidad(new_quantity, product["unit"])
        if cantidad_validada is None:
            if product["unit"] == "unidad":
                mensaje = "La cantidad debe ser un número entero positivo para productos vendidos por unidad"
            else:
                mensaje = f"La cantidad debe ser un número positivo para productos vendidos por {product['unit']}"
            messagebox.showerror("Error", mensaje)
            return

        # Calcular diferencia de cantidad
        delta = cantidad_validada - product['quantity']

        # Validar stock si se aumenta la cantidad
        if delta > 0:
            if original_product.stock < delta:
                messagebox.showerror(
                    "Error",
                    f"Stock insuficiente. Ademas de las ingrsadas hay disponibles: f{original_product.stock:.2f}"
                )
                return
            original_product.stock -= delta
        elif delta < 0:
            original_product.stock += abs(delta)


            
        # Restar valores anteriores
        self.venta.subtotal -= product['subtotal']
        self.venta.total_iva -= product['iva']
        
        # Calcular nuevos valores
        nuevo_subtotal = original_product.price * cantidad_validada
        nuevo_iva = self.venta.calculate_tax(nuevo_subtotal, 0.19)
        nuevo_descuento = self.venta.calcular_descuento(nuevo_subtotal)
        nuevo_descuento_valor = nuevo_subtotal * nuevo_descuento
        nuevo_total = nuevo_subtotal - nuevo_descuento_valor + nuevo_iva
        
        # Actualizar producto
        product.update({
            'quantity': cantidad_validada,
            'subtotal': nuevo_subtotal,
            'iva': nuevo_iva,
            'descuento_porcentaje': nuevo_descuento * 100,
            'descuento_valor': nuevo_descuento_valor,
            'total': nuevo_total
        })
        
        # Actualizar totales de la venta
        self.venta.subtotal += nuevo_subtotal
        self.venta.total_iva += nuevo_iva
        
        # Actualizar UI
        self.load_products()
        self.parent.update_invoice_display()
        self.quantity_entry.delete(0, tk.END)
        messagebox.showinfo("Éxito", "Cantidad actualizada correctamente")
    
    def remove_product(self):
        """Elimina el producto seleccionado."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Por favor seleccione un producto")
            return

        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea eliminar este producto?"):
            item_values = self.tree.item(selected_item)["values"]
            code = item_values[0]

            producto_a_eliminar = next((item for item in self.venta.items if item["code"] == code), None)
            if producto_a_eliminar:
                # Restaurar stock
                original_product = self.parent.product_manager.find_product(code)
                if original_product:
                    original_product.stock += producto_a_eliminar['quantity']

                # Restar valores de los totales
                self.venta.subtotal -= producto_a_eliminar['subtotal']
                self.venta.total_iva -= producto_a_eliminar['iva']

                # Eliminar producto
                self.venta.items = [item for item in self.venta.items if item["code"] != code]

            # Actualizar UI
            self.load_products()
            self.parent.update_invoice_display()
            messagebox.showinfo("Éxito", "Producto eliminado correctamente")
    
    def close_window(self):
        """Cierra la ventana de gestión."""
        self.destroy()
    
    def center_window(self):
        """Centra la ventana en la pantalla."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
class ClientInfoWindow(tk.Toplevel):
    def __init__(self, parent, venta):
        super().__init__(parent)
        self.venta = venta
        self.title("Datos del Cliente")
        self.geometry("500x400")
        self.resizable(False, False)
        
        self.validation_errors = {
            "nombre": tk.StringVar(),
            "nit": tk.StringVar(),
            "pago": tk.StringVar()
        }
        
        self.create_widgets()
        self.center_window()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, 
                text="Información Requerida para Facturación", 
                font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Campos del formulario
        self.create_labeled_entry(main_frame, "Nombre completo*:", "nombre", 1, 80, name=True)
        self.create_labeled_entry(main_frame, "NIT/CC*:", "nit", 2, 15, self.validate_nit)
        self.create_payment_combobox(main_frame)
        
        # Nota legal
        legal_text = ("* Campos obligatorios\n"
                     "El NIT debe tener entre 9 y 15 dígitos\n"
                     "Formato aceptado: 123456789-1 o 901.234.567-8")
        ttk.Label(main_frame, text=legal_text, foreground="gray").grid(
            row=5, column=0, columnspan=2, pady=10, sticky="w")
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Aceptar", command=self.guardar_datos).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side=tk.LEFT, padx=10)
    def validate_nit_entry(self, new_value, action, max_length):
        """Valida cada tecla presionada en el campo NIT"""
        max_len = int(max_length)

        # Permitir teclas de control
        if action == '0':  # Borrado
            return True

        # Validar solo dígitos
        if not new_value.isdigit():
            return False

        # Validar longitud máxima
        return len(new_value) <= max_len
    def create_labeled_entry(self, parent, label, field, row, max_length, validation=None, name=None):
        # Configuración común para campos de entrada
        ttk.Label(parent, text=label).grid(row=row, column=0, pady=5, sticky="w")
        if name:
            validate_cmd = (self.register(self.validate_entry_length), '%P', '%d', str(max_length))
        else:
            validate_cmd = (self.register(self.validate_nit_entry), '%P', '%d', str(max_length))
        entry = ttk.Entry(parent, validate="key", validatecommand=validate_cmd)
        entry.grid(row=row, column=1, pady=5, sticky="ew")
        
        if validation:
            entry.bind("<FocusOut>", lambda e, f=field: validation())
        
        # Etiqueta para errores
        error_label = ttk.Label(parent, textvariable=self.validation_errors[field], 
                              foreground="red", wraplength=300)
        error_label.grid(row=row+1, column=1, sticky="w")
        
        setattr(self, f"{field}_entry", entry)
    
    def create_payment_combobox(self, parent):
        ttk.Label(parent, text="Forma de pago*:").grid(row=4, column=0, pady=5, sticky="w")
        
        self.pago_combobox = ttk.Combobox(parent, 
                                       values=["Contado", "Crédito 30 días", "Tarjeta crédito"], 
                                       state="readonly")
        self.pago_combobox.set("Contado")
        self.pago_combobox.grid(row=4, column=1, pady=5, sticky="ew")
        self.pago_combobox.bind("<<ComboboxSelected>>", lambda e: self.validate_payment())
        
        error_label = ttk.Label(parent, textvariable=self.validation_errors["pago"], 
                              foreground="red", wraplength=300)
        error_label.grid(row=5, column=1, sticky="w")
    
    def validate_entry_length(self, new_text, action, max_length):
        max_len = int(max_length)
        if action == '1':  # Inserción
            return len(new_text) <= max_len
        return True
    
    def validate_nit(self):
        nit = self.nit_entry.get().strip()

        if not nit:
            self.show_error("nit", "Este campo es obligatorio")
            return False

        # Validar longitud
        if len(nit) < 5 or len(nit) > 15:
            self.show_error("nit", "Debe tener entre 5 y 15 dígitos")
            return False

        # Validar solo números
        if not nit.isdigit():
            self.show_error("nit", "Solo se permiten números")
            return False

        self.clear_error("nit")
        return True

    def show_error(self, field, message):
        self.validation_errors[field].set(message)
        getattr(self, f"{field}_entry").config(foreground="red")

    def clear_error(self, field):
        self.validation_errors[field].set("")
        getattr(self, f"{field}_entry").config(foreground="black")
    
    def validate_payment(self):
        if not self.pago_combobox.get():
            self.validation_errors["pago"].set("Debe seleccionar una forma de pago")
            return False
        self.validation_errors["pago"].set("")
        return True
    
    def validate_form(self):
        valid = True
        # Validar nombre
        nombre = self.nombre_entry.get().strip()
        if not nombre:
            self.validation_errors["nombre"].set("Debe ingresar el nombre del cliente")
            valid = False
        else:
            self.validation_errors["nombre"].set("")
        
        # Validar NIT
        if not self.validate_nit():
            valid = False
        
        # Validar forma de pago
        if not self.validate_payment():
            valid = False
        
        return valid
    
    def guardar_datos(self):
        if not self.validate_form():
            messagebox.showerror("Error", "Por favor corrija los campos marcados en rojo")
            return

        # Asegurar formato numérico
        raw_nit = self.nit_entry.get().strip()
        clean_nit = ''.join(filter(str.isdigit, raw_nit))  # Filtro adicional de seguridad

        if len(clean_nit) < 5 or len(clean_nit) > 15:
            messagebox.showerror("Error", "NIT/CC inválido")
            return

        self.venta.cliente_info = {
            "nombre": self.nombre_entry.get().strip(),
            "nit": clean_nit
        }
        self.venta.forma_pago = self.pago_combobox.get()
        self.destroy()
    
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
class SalesApp(tk.Tk):
    """Interfaz gráfica de la aplicación de ventas."""

    def __init__(self, product_manager: ProductManager):
        super().__init__()

        self.product_manager = product_manager
        self.venta = Venta()

        self.setup_window()
        self.create_frames()
        self.setup_product_selection()
        self.setup_quantity_input()
        self.setup_buttons()
        self.setup_invoice_display()

    def setup_window(self) -> None:
        """Configura la ventana principal."""
        self.title("Sistema de Ventas - Tienda Colombiana")
        self.geometry("1100x600")
        self.minsize(1100, 600)

        # Configura el peso de las columnas y filas
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def create_frames(self) -> None:
        """Crea y configura los frames."""
        # Frame de entrada para la selección de productos y cantidad
        self.input_frame = ttk.LabelFrame(self, text="Datos de Venta", padding=10)
        self.input_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        # Frame de la factura
        self.invoice_frame = ttk.LabelFrame(self, text="Detalles de la Venta", padding=10)
        self.invoice_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.invoice_frame.grid_columnconfigure(0, weight=1)
        self.invoice_frame.grid_rowconfigure(0, weight=1)

    def setup_product_selection(self) -> None:
        """Configura el combobox de selección de productos."""
        ttk.Label(self.input_frame, text="Producto:").grid(
            row=0, column=0, padx=(0, 5), pady=5, sticky="w"
        )

        self.product_combobox = ttk.Combobox(
            self.input_frame, width=50, state="readonly"
        )
        self.product_combobox.grid(
            row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew"
        )

        # Llena el combobox con los productos
        self.product_combobox['values'] = [
            f"{p.code} - {p.name} (${p.price:,.0f} por {p.unit})"
            for p in self.product_manager.products
        ]

    def setup_quantity_input(self) -> None:
        """Configura los inputs de cantidades."""
        ttk.Label(self.input_frame, text="Cantidad:").grid(
            row=1, column=0, padx=(0, 5), pady=5, sticky="w"
        )

        self.quantity_entry = ttk.Entry(self.input_frame, width=15)
        self.quantity_entry.grid(
            row=1, column=1, padx=5, pady=5, sticky="w"
        )

    
    def setup_buttons(self) -> None:
        """Configura los botones de acción."""
        buttons_frame = ttk.Frame(self.input_frame)
        buttons_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(
            buttons_frame,
            text="Añadir Producto",
            command=self.add_product,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Gestionar Productos",
            command=self.open_management_window
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Finalizar Venta",
            command=self.checkout
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Nueva Venta",
            command=self.reset_sale
        ).pack(side=tk.LEFT, padx=5)
    
    def open_management_window(self):
        """Abre la ventana de gestión de productos."""
        if not self.venta.items:
            messagebox.showwarning(
                "Advertencia",
                "No hay productos en la venta actual"
            )
            return
        
        ProductManagementWindow(self, self.venta)

    def setup_invoice_display(self) -> None:
        """Configura el área de visualización de la factura."""
        self.invoice_text = scrolledtext.ScrolledText(
            self.invoice_frame,
            wrap=tk.WORD,
            font=('Courier', 10)
        )
        self.invoice_text.grid(row=0, column=0, sticky="nsew")

        # Hace que el widget de texto sea de solo lectura
        self.invoice_text.configure(state='disabled')

    def add_product(self) -> None:
        """Añade un producto a la factura."""
        producto_seleccionado = self.product_combobox.get()
        cantidad = self.quantity_entry.get()

        if not Validador.validar_producto(producto_seleccionado):
            messagebox.showerror(
                "Error",
                "Por favor seleccione un producto"
            )
            return

        producto_codigo = producto_seleccionado.split(' - ')[0]
        producto = self.product_manager.find_product(producto_codigo)
        if not producto:
            messagebox.showerror(
                "Error",
                "Producto no encontrado"
            )
            return

        cantidad_validada = Validador.validar_cantidad(cantidad, producto.unit)
        if cantidad_validada is None:
            if producto.unit == 'unidad':
                mensaje = "La cantidad debe ser un número entero positivo para productos vendidos por unidad"
            else:
                mensaje = f"La cantidad debe ser un número positivo para productos vendidos por {producto.unit}"
            messagebox.showerror("Error", mensaje)
            return

        # Validar stock disponible
        if cantidad_validada > producto.stock:
            messagebox.showerror(
                "Error",
                f"Stock insuficiente. Disponible: {producto.stock:.2f} {producto.unit}"
            )
            return

        # Actualizar stock y agregar producto
        producto.stock -= cantidad_validada
        self.venta.agregar_producto(producto, cantidad_validada)
        self.update_invoice_display()
        self.clear_inputs()

    def update_invoice_display(self) -> None:
        """Actualiza el área de visualización de la factura."""
        self.invoice_text.configure(state='normal')
        self.invoice_text.delete(1.0, tk.END)
        self.invoice_text.insert(tk.END, self.venta.generar_factura())
        self.invoice_text.configure(state='disabled')

    def clear_inputs(self) -> None:
        """Limpia los campos de entrada."""
        self.product_combobox.set('')
        self.quantity_entry.delete(0, tk.END)

    def checkout(self) -> None:
        if not self.venta.items:
            messagebox.showerror("Error", "No hay productos en la venta")
            return
        if not messagebox.askyesno("Finalizar venta", "¿Está seguro de que desea finalizar esta venta?"):
                return
        # Abrir ventana de datos del cliente (modal)
        client_window = ClientInfoWindow(self, self.venta)
        self.wait_window(client_window)

        # Verificar si se completó el formulario
        if not self.venta.cliente_info['nombre']: 
            return  # El usuario canceló

        # Validación final antes de generar factura
        if not self.venta.cliente_info['nit']:
            messagebox.showerror("Error", "Debe ingresar un NIT/CC válido")
            return

        # Generar factura
        InvoiceWindow(self, self.venta.generar_factura())
        self.reset_sale(finish=True)

    def reset_sale(self, finish: bool = False) -> None:
        """Reinicia el sistema para una nueva venta."""
        if not finish:
            if not messagebox.askyesno("Nueva venta", "¿Está seguro de que desea borrar esta venta e iniciar otra?"):
                return
            # Restaurar stock de todos los productos
            for item in self.venta.items:
                product = self.product_manager.find_product(item['code'])
                if product:
                    product.stock += item['quantity']
        self.venta = Venta()
        self.clear_inputs()
        self.update_invoice_display()

def main():
    """Punto de entrada principal de la aplicación."""
    product_manager = ProductManager()
    app = SalesApp(product_manager)

    # Configura el estilo
    style = ttk.Style()
    style.configure("Accent.TButton", font=("TkDefaultFont", 9, "bold"))

    app.mainloop()

if __name__ == "__main__":
    main()
