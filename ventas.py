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

class ProductManager:
    """Clase que define los productos y abarca la lógica de creación y búsqueda de productos."""

    def __init__(self):
        self.products: List[Product] = self.create_products_test()

    def create_products_test(self) -> List[Product]:
        """Crea una lista de productos con precios en COP."""
        return [
            Product("COD1", "Coca-Cola 1L", 4500, "unidad"),
            Product("COD2", "Agua 600ml", 2500, "unidad"),
            Product("COD3", "Queso Campesino 1 libra", 12000, "libra"),
            Product("COD4", "Pechuga de Pollo 1 libra", 10000, "libra"),
            Product("COD5", "Papas Margarita 150g", 3500, "unidad"),
            Product("COD6", "Arroz Diana 1kg", 4000, "kilo"),
            Product("COD7", "Leche Alquería 1L", 3500, "unidad"),
            Product("COD8", "Huevos x 30 unidades", 15000, "unidad"),
            Product("COD9", "Carne Molida 1 libra", 18000, "libra"),
            Product("COD10", "Pan Bimbo Integral", 6000, "unidad"),
            Product("COD11", "Café Juan Valdez 500g", 20000, "kilo"),
            Product("COD12", "Galletas Saltín Noel", 2500, "unidad"),
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
    
    def __init__(self):
        """Inicializa una venta con una lista vacía de productos vendidos."""
        self.items: List[Dict] = []
        self.subtotal = 0.0
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
        
        precio_final = producto.price *  cantidad
        descuento = self.calcular_descuento(precio_final)
        total = precio_final * (1 - descuento) 
        existe_producto = next((item for item in self.items if item['code'] == producto.code), None)
        if not (existe_producto):
            self.items.append({
                'code': producto.code,
                'name': producto.name,
                'price': producto.price,
                'precio_final': precio_final,
                'quantity': cantidad,
                'unit': producto.unit,
                'total': total
            })
            self.subtotal += total
        else:
            existe_producto['quantity'] += cantidad
            existe_producto['total'] = precio_final * existe_producto['quantity']
            self.subtotal += total

    def calcular_impuesto(self) -> float:
        """
        Calcula el impuesto aplicable a la venta.

        Returns:
            float: Impuesto calculado.
        """
        return self.calculate_tax(self.subtotal, tax_rate = 0.19) #TAX_RATE = 0.19  # 19% IVA en Colombia

    def calcular_total(self) -> float:
        """
        Calcula el total de la venta (subtotal + impuesto).

        Returns:
            float: Total de la venta.
        """
        return self.subtotal + self.calcular_impuesto()

    def generar_factura(self) -> str:
        """Genera el texto de la factura usando tabulate para un mejor formato."""
        # Preparar los datos para la tabla
        table_data = []
        for item in self.items:
            table_data.append([
                item['code'],
                item['name'],
                f"${item['price']:,.0f}",
                f"${item['precio_final']:,.0f}",
                f"{item['quantity']:.2f}",
                item['unit'],
                f"${item['total']:,.0f}"
            ])

        # Definir headers
        headers = ['Código', 'Producto', 'Precio', 'Precio Final', 
                  'Cantidad', 'Unidad', 'Total']

        # Generar la tabla principal
        tabla_productos = tabulate(
            table_data,
            headers=headers,
            tablefmt='grid',  # Puedes usar: grid, fancy_grid, pipe, orgtbl, etc.
            numalign='right',
            stralign='left'
        )

        # Calcular totales
        tax = self.calcular_impuesto()
        total = self.calcular_total()

        # Generar tabla de totales
        tabla_totales = tabulate(
            [
                ['Subtotal:', f"${self.subtotal:,.0f}"],
                ['IVA (19%):', f"${tax:,.0f}"],
                ['TOTAL:', f"${total:,.0f}"]
            ],
            tablefmt='grid',
            numalign='right',
            stralign='left'
        )

        # Combinar todo
        factura_completa = (
            "\n=== FACTURA DE VENTA ===\n\n"
            f"{tabla_productos}\n\n"
            f"{tabla_totales}\n"
        )

        return factura_completa

class InvoiceWindow(tk.Toplevel):
    """Ventana personalizada para mostrar la factura."""
    
    def __init__(self, parent, invoice_text):
        super().__init__(parent)
        
        # Configurar ventana
        self.title("Venta Finalizada")
        self.geometry("800x600")
        self.minsize(900, 600)
        self.maxsize(900, 600)
        
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
        
        # Encontrar el producto en la venta
        product = next((item for item in self.venta.items if item["code"] == code), None)
        if not product:
            return
            
        # Validar la nueva cantidad
        cantidad_validada = Validador.validar_cantidad(new_quantity, product["unit"])
        if cantidad_validada is None:
            if product["unit"] == "unidad":
                mensaje = "La cantidad debe ser un número entero positivo para productos vendidos por unidad"
            else:
                mensaje = f"La cantidad debe ser un número positivo para productos vendidos por {product['unit']}"
            messagebox.showerror("Error", mensaje)
            return
            
        # Actualizar cantidad y recalcular totales
        product["quantity"] = cantidad_validada
        product["total"] = product["price"] * cantidad_validada
        self.venta.subtotal = sum(item["total"] for item in self.venta.items)
        
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
            
            # Eliminar producto
            self.venta.items = [item for item in self.venta.items if item["code"] != code]
            self.venta.subtotal = sum(item["total"] for item in self.venta.items)
            
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
        self.geometry("900x600")
        self.minsize(900, 600)

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

        # Obtener el producto primero para conocer su unidad
        producto_codigo = producto_seleccionado.split(' - ')[0]
        producto = self.product_manager.find_product(producto_codigo)
        if not producto:
            messagebox.showerror(
                "Error",
                "Producto no encontrado"
            )
            return

        # Validar la cantidad según la unidad del producto
        cantidad_validada = Validador.validar_cantidad(cantidad, producto.unit)
        if cantidad_validada is None:
            if producto.unit == 'unidad':
                mensaje = "La cantidad debe ser un número entero positivo para productos vendidos por unidad"
            else:
                mensaje = f"La cantidad debe ser un número positivo para productos vendidos por {producto.unit}"
            
            messagebox.showerror("Error", mensaje)
            return

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
        """Finaliza la venta."""
        if not self.venta.items:
            messagebox.showerror(
                "Error",
                "No hay productos en la venta"
            )
            return

        # Crear ventana personalizada para mostrar la factura
        InvoiceWindow(self, self.venta.generar_factura())
        self.reset_sale()

    def reset_sale(self) -> None:
        """Reinicia el sistema para una nueva venta."""
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