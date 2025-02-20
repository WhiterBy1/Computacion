import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class Product:
    """Class to represent a product"""
    code: str
    name: str
    price: float
    unit: str


class ProductManager:
    """Handles product loading and searching"""
    
    def __init__(self):
        self.products: List[Product] = self.create_products()
    
    def create_products(self) -> List[Product]:
        """Creates a list of products with prices in COP"""
        return [
            Product("COD1", "Coca-Cola 1L", 4500, "unidad"),
            Product("COD2", "Agua Manantial 600ml", 2500, "unidad"),
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
        """Searches for a product by code or name"""
        search_term = search_term.lower()
        return next(
            (product for product in self.products 
             if search_term in (product.code.lower(), product.name.lower())),
            None
        )


class TaxCalculator:
    """Tax calculation handler"""
    
    TAX_RATE = 0.19  # 19% IVA in Colombia
    
    @staticmethod
    def calculate_tax(amount: float) -> float:
        """Calculates tax for a given amount"""
        return round(amount * TaxCalculator.TAX_RATE, 2)


class InvoiceGenerator:
    """Invoice generator"""
    
    def __init__(self):
        self.items: List[Dict] = []
        self.subtotal = 0.0
    
    def add_item(self, product: Product, quantity: float) -> None:
        """Adds an item to the invoice"""
        total = product.price * quantity
        self.items.append({
            'code': product.code,
            'name': product.name,
            'price': product.price,
            'quantity': quantity,
            'unit': product.unit,
            'total': total
        })
        self.subtotal += total
    
    def generate_invoice(self) -> str:
        """Generates invoice text"""
        tax = TaxCalculator.calculate_tax(self.subtotal)
        total = self.subtotal + tax
        
        invoice = [
            "=== FACTURA DE VENTA ===\n",
            f"{'Código':<8} {'Producto':<25} {'Precio':<12} "
            f"{'Cantidad':<10} {'Unidad':<8} {'Total':<12}"
        ]
        
        invoice.append("-" * 75)
        
        for item in self.items:
            invoice.append(
                f"{item['code']:<8} {item['name'][:24]:<25} "
                f"${item['price']:>9,.0f} {item['quantity']:>9.2f} "
                f"{item['unit']:<8} ${item['total']:>10,.0f}"
            )
        
        invoice.extend([
            "\n" + "=" * 75,
            f"{'Subtotal:':<65} ${self.subtotal:>8,.0f}",
            f"{'IVA (19%):':<65} ${tax:>8,.0f}",
            f"{'TOTAL:':<65} ${total:>8,.0f}",
            "=" * 75
        ])
        
        return '\n'.join(invoice)


class SalesApp(tk.Tk):
    """Sales system graphical interface"""
    
    def __init__(self, product_manager: ProductManager):
        super().__init__()
        
        self.product_manager = product_manager
        self.invoice_generator = InvoiceGenerator()
        
        self.setup_window()
        self.create_frames()
        self.setup_product_selection()
        self.setup_quantity_input()
        self.setup_buttons()
        self.setup_invoice_display()
    
    def setup_window(self) -> None:
        """Configures main window properties"""
        self.title("Sistema de Ventas - Tienda Colombiana")
        self.geometry("800x600")
        self.minsize(800, 600)
        
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
    def create_frames(self) -> None:
        """Creates and configures main layout frames"""
        # Input frame for product selection and quantity
        self.input_frame = ttk.LabelFrame(self, text="Datos de Venta", padding=10)
        self.input_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)
        
        # Invoice frame
        self.invoice_frame = ttk.LabelFrame(self, text="Detalles de la Venta", padding=10)
        self.invoice_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.invoice_frame.grid_columnconfigure(0, weight=1)
        self.invoice_frame.grid_rowconfigure(0, weight=1)
    
    def setup_product_selection(self) -> None:
        """Configures product selection combobox"""
        ttk.Label(self.input_frame, text="Producto:").grid(
            row=0, column=0, padx=(0, 5), pady=5, sticky="w"
        )
        
        self.product_combobox = ttk.Combobox(
            self.input_frame, width=50, state="readonly"
        )
        self.product_combobox.grid(
            row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew"
        )
        
        # Populate combobox
        self.product_combobox['values'] = [
            f"{p.code} - {p.name} (${p.price:,.0f} por {p.unit})" 
            for p in self.product_manager.products
        ]
    
    def setup_quantity_input(self) -> None:
        """Configures quantity input field"""
        ttk.Label(self.input_frame, text="Cantidad:").grid(
            row=1, column=0, padx=(0, 5), pady=5, sticky="w"
        )
        
        self.quantity_entry = ttk.Entry(self.input_frame, width=15)
        self.quantity_entry.grid(
            row=1, column=1, padx=5, pady=5, sticky="w"
        )
    
    def setup_buttons(self) -> None:
        """Configures action buttons"""
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
            text="Finalizar Venta",
            command=self.checkout
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Nueva Venta",
            command=self.reset_sale
        ).pack(side=tk.LEFT, padx=5)
    
    def setup_invoice_display(self) -> None:
        """Configures invoice display area"""
        self.invoice_text = scrolledtext.ScrolledText(
            self.invoice_frame,
            wrap=tk.WORD,
            font=('Courier', 10)
        )
        self.invoice_text.grid(row=0, column=0, sticky="nsew")
        
        # Make text widget read-only
        self.invoice_text.configure(state='disabled')
    
    def add_product(self) -> None:
        """Adds a product to the invoice"""
        product_input = self.product_combobox.get().split(' - ')[0]
        quantity = self.quantity_entry.get()
        
        if not product_input or not quantity:
            messagebox.showerror(
                "Error",
                "Por favor complete todos los campos"
            )
            return
        
        try:
            quantity = float(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Error",
                "La cantidad debe ser un número positivo"
            )
            return
        
        product = self.product_manager.find_product(product_input)
        if not product:
            messagebox.showerror(
                "Error",
                "Producto no encontrado"
            )
            return
        
        self.invoice_generator.add_item(product, quantity)
        self.update_invoice_display()
        self.clear_inputs()
    
    def update_invoice_display(self) -> None:
        """Updates the invoice display area"""
        self.invoice_text.configure(state='normal')
        self.invoice_text.delete(1.0, tk.END)
        self.invoice_text.insert(tk.END, self.invoice_generator.generate_invoice())
        self.invoice_text.configure(state='disabled')
    
    def clear_inputs(self) -> None:
        """Clears input fields"""
        self.product_combobox.set('')
        self.quantity_entry.delete(0, tk.END)
    
    def checkout(self) -> None:
        """Finalizes the sale"""
        if not self.invoice_generator.items:
            messagebox.showerror(
                "Error",
                "No hay productos en la venta"
            )
            return
        
        messagebox.showinfo(
            "Venta Finalizada",
            "Venta procesada exitosamente\n\n" + 
            self.invoice_generator.generate_invoice()
        )
        self.reset_sale()
    
    def reset_sale(self) -> None:
        """Resets the system for a new sale"""
        self.invoice_generator = InvoiceGenerator()
        self.clear_inputs()
        self.update_invoice_display()


def main():
    """Main application entry point"""
    product_manager = ProductManager()
    app = SalesApp(product_manager)
    
    # Configure style
    style = ttk.Style()
    style.configure("Accent.TButton", font=("TkDefaultFont", 9, "bold"))
    
    app.mainloop()


if __name__ == "__main__":
    main()