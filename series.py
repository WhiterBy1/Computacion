import tkinter as tk
from tkinter import ttk, messagebox, StringVar
import numpy as np
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from abc import ABC, abstractmethod


class Serie(ABC):
    """Clase base abstracta para todas las series matemáticas"""
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self._validate_indices()
    
    def _validate_indices(self):
        if not isinstance(self.start, int) or not isinstance(self.end, int):
            raise ValueError("Los índices deben ser números enteros")

        if self.start > self.end:
            raise ValueError("El índice inicial debe ser menor o igual al final")

        # For harmonic series, start must be positive
        if isinstance(self, SerieArmonica) and self.start <= 0:
            raise ValueError("El índice inicial para series armónicas debe ser mayor que 0")
    
    @abstractmethod
    def calcular_suma(self):
        """Calcula la suma de los términos de la serie y devuelve (suma, términos)"""
        pass
    
    @abstractmethod
    def get_formula_latex(self, sum_total):
        """Devuelve la representación LaTeX de la fórmula de la serie"""
        pass
    
    @abstractmethod
    def get_summation_latex(self):
        """Devuelve la representación LaTeX de la notación de suma"""
        pass
    
    @abstractmethod
    def get_result_text(self, sum_total):
        """Devuelve el texto descriptivo del resultado"""
        pass
    
    def get_generic_summation_latex(self):
        """Devuelve la representación LaTeX genérica de la suma"""
        pass

class SerieAritmetica(Serie):
    def __init__(self, start, end, a1, d):
        super().__init__(start, end)
        self.a1 = a1
        self.d = d

    def calcular_suma(self):
        suma = 0.0
        terms = []
        for k in range(self.start, self.end + 1):
            term = self.a1 + (k - self.start) * self.d
            terms.append(term)
            suma += term
        return suma, terms
    
    def get_summation_latex(self):
        return f"$\\sum_{{k={self.start}}}^{{{self.end}}} [{self.a1} + (k-{self.start}) \\cdot {self.d}]$"
    
    def get_generic_summation_latex(self):
        return r"$\sum_{k=start}^{end} [a_1 + (k-start) \cdot d]$"
    
    def get_formula_latex(self, sum_total):
        n = self.end - self.start + 1
        return (
            f"S_n = \\frac{{n}}{{2}} \\cdot [2a_1 + (n-1)d] = "
            f"\\frac{{{n}}}{{2}} \\cdot [2\\cdot{self.a1} + ({n-1})\\cdot{self.d}] = {sum_total:.4f}"
        )
    
    def get_result_text(self, sum_total):
        return f"Serie Aritmética\nPrimer término = {self.a1}, d = {self.d}\nRango: k = {self.start} a {self.end}\nSuma total: {sum_total:.4f}"

class SerieGeometrica(Serie):
    def __init__(self, start, end, a1, r):
        super().__init__(start, end)
        self.a1 = a1
        self.r = r

    def calcular_suma(self):
        suma = 0.0
        terms = []
        for k in range(self.start, self.end + 1):
            term = self.a1 * (self.r ** (k - self.start))
            terms.append(term)
            suma += term
        return suma, terms
    
    def get_summation_latex(self):
        return f"$\\sum_{{k={self.start}}}^{{{self.end}}} {self.a1} \\cdot {self.r}^{{k-{self.start}}}$"
    
    def get_generic_summation_latex(self):
        return r"$\sum_{k=start}^{end} a_1 \cdot r^{k-start}$"
    
    def get_formula_latex(self, sum_total):
        n = self.end - self.start + 1
        latex = (
            f"S_n = \\frac{{a_1(1 - r^n)}}{{1 - r}} = "
            f"\\frac{{{self.a1}(1 - {self.r}^{{{n}}})}}{{1 - {self.r}}} = {sum_total:.4f}"
        )
        
        # Agregar suma infinita si |r| < 1
        if abs(self.r) < 1:
            infinite_sum = self.a1 / (1 - self.r)
            latex += f"\\quad S_{{\\infty}} = {infinite_sum:.4f}"
            
        return latex
    
    def get_result_text(self, sum_total):
        return f"Serie Geométrica\nPrimer término = {self.a1}, r = {self.r}\nRango: k = {self.start} a {self.end}\nSuma total: {sum_total:.4f}"

class SerieArmonica(Serie):
    def __init__(self, start, end, tipo):
        super().__init__(start, end)
        self.tipo = tipo  # 'Regular' o 'Alternante'

    def calcular_suma(self):
        suma = 0.0
        terms = []
        for k in range(self.start, self.end + 1):
            if self.tipo == 'Regular':
                term = 1.0 / k
            else:
                exponent = (k - self.start) + 1
                term = ((-1) ** exponent) / k
            terms.append(term)
            suma += term
        return suma, terms
    
    def get_summation_latex(self):
        if self.tipo == "Regular":
            return f"$\\sum_{{k={self.start}}}^{{{self.end}}} \\frac{{1}}{{k}}$"
        else:
            return f"$\\sum_{{k={self.start}}}^{{{self.end}}} \\frac{{(-1)^{{k-{self.start}+1}}}}{{k}}$"
    
    def get_generic_summation_latex(self):
        if self.tipo == "Regular":
            return r"$\sum_{k=start}^{end} \frac{1}{k}$"
        else:
            return r"$\sum_{k=start}^{end} \frac{(-1)^{k-start+1}}{k}$"
    
    def get_formula_latex(self, sum_total):
        term = "\\frac{1}{k}" if self.tipo == "Regular" else "\\frac{(-1)^{k-" + str(self.start) + "+1}}{k}"
        return f"\\sum_{{k={self.start}}}^{{{self.end}}} {term} = {sum_total:.4f}"
    
    def get_result_text(self, sum_total):
        return f"Serie Armónica {self.tipo}\nRango: k = {self.start} a {self.end}\nSuma total: {sum_total:.4f}"

# Factory para crear las series - Patrón Factory Method
class SerieFactory:
    @staticmethod
    def create_serie(serie_tipo, start, end, **kwargs):
        if serie_tipo == "Serie Aritmética":
            return SerieAritmetica(start, end, kwargs.get('a1'), kwargs.get('d'))
        elif serie_tipo == "Serie Geométrica":
            return SerieGeometrica(start, end, kwargs.get('a1'), kwargs.get('r'))
        elif serie_tipo == "Serie Armónica":
            return SerieArmonica(start, end, kwargs.get('tipo'))
        else:
            raise ValueError(f"Tipo de serie no soportado: {serie_tipo}")

# Componentes UI reutilizables
class MatplotlibFigure:
    """Clase para crear y gestionar figuras de Matplotlib"""
    
    @staticmethod
    def create_text_figure(text, figsize=(8, 4), fontsize=20):
        fig = Figure(figsize=figsize, dpi=100)
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, text, fontsize=fontsize, ha='center', va='center')
        ax.axis('off')
        return fig
    
    @staticmethod
    def create_series_plots(terms, partial_sums, start_idx):
        fig = Figure(figsize=(8, 5), dpi=100)
        fig.subplots_adjust(bottom=0.15)
        
        # Gráfica de términos
        ax1 = fig.add_subplot(121)
        x = list(range(start_idx, start_idx + len(terms)))
        ax1.plot(x, terms, 'bo-', markersize=4)
        ax1.set_title('Términos de la Serie')
        ax1.set_xlabel('k')
        ax1.set_ylabel('a_k')
        ax1.grid(True)
        
        # Gráfica de sumas parciales
        ax2 = fig.add_subplot(122)
        ax2.plot(x, partial_sums, 'ro-', markersize=4)
        ax2.set_title('Sumas Parciales')
        ax2.set_xlabel('n')
        ax2.set_ylabel('S_n')
        ax2.grid(True)
        
        return fig

# Add this class to validate and limit input length
class ValidatedEntry(ttk.Entry):
    """Entry widget with validation for numeric input and max length"""
    def __init__(self, parent, textvariable, max_length=10, allow_float=True, **kwargs):
        self.var = textvariable
        self.max_length = max_length
        self.allow_float = allow_float
        
        # Register validation command
        vcmd = (parent.register(self.validate), '%P')
        
        super().__init__(parent, textvariable=textvariable, validate="key", 
                         validatecommand=vcmd, **kwargs)
        
        # Add tooltip on hover
        self.tooltip = None
        self.bind("<Enter>", self.show_tooltip)
        self.bind("<Leave>", self.hide_tooltip)
    
    def validate(self, new_value):
        # Empty is valid (will be caught when calculating)
        if new_value == "":
            return True
            
        # Check max length
        if len(new_value) > self.max_length:
            return False
            
        # Check if it's a valid number format
        if self.allow_float:
            # Allow digits, one decimal point, and one minus sign at the start
            pattern = r'^-?\d*\.?\d*$'
        else:
            # Allow digits and one minus sign at the start for integers
            pattern = r'^-?\d*$'
            
        return bool(re.match(pattern, new_value))
    
    def show_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
        
        x, y, _, _ = self.bbox("insert")
        x += self.winfo_rootx() + 25
        y += self.winfo_rooty() + 25
        
        # Create tooltip window
        self.tooltip = tw = tk.Toplevel(self)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Determine message based on validation type
        if self.allow_float:
            msg = f"Ingrese un número (máx. {self.max_length} caracteres)"
        else:
            msg = f"Ingrese un número entero (máx. {self.max_length} caracteres)"
            
        label = tk.Label(tw, text=msg, background="#ffffe0", relief="solid", borderwidth=1)
        label.pack()
    
    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
class SeriesCalculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora de Series Matemáticas")
        self.geometry("1000x800")
        self.configure(bg="#f0f0f0")
        
        # Configuración de estilo
        self._setup_styles()
        
        # Inicializar UI
        self._init_ui()
        
        # Inicializar los campos de entrada
        self.update_input_fields()
        
    def _setup_styles(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 12), background="#f0f0f0")
        style.configure("TButton", font=("Arial", 12))
        style.configure("TEntry", font=("Arial", 12))
        style.configure("TCombobox", font=("Arial", 12))
        
        # Configurar matplotlib para usar fuentes básicas sin LaTeX
        plt.rcParams.update({
            "text.usetex": False,
            "font.family": "serif"
        })
    
    def _init_ui(self):
        # Frame principal
        main_frame = tk.Frame(self, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título
        title_label = tk.Label(main_frame, text="Calculadora de Series Matemáticas", 
                              font=("Arial", 16, "bold"), bg="#f0f0f0")
        title_label.pack(pady=10)

        # Frame para los controles y visualización
        control_frame = tk.Frame(main_frame, bg="#f0f0f0")
        control_frame.pack(fill=tk.X, pady=10)

        # Inicializar frames de la interfaz
        self._init_control_frame(control_frame)
        self._init_result_frames(main_frame)

        # Status bar
        self.status_var = tk.StringVar(value="Listo para calcular")
        status_bar = tk.Label(self, textvariable=self.status_var, 
                             bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _init_control_frame(self, parent):
        # Frame izquierdo para los controles
        left_frame = tk.Frame(parent, bg="#f0f0f0")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Selección de serie
        series_label = tk.Label(left_frame, text="Seleccione la serie:", bg="#f0f0f0")
        series_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.series_var = tk.StringVar()
        series_options = ["Serie Aritmética", "Serie Geométrica", "Serie Armónica"]
        series_combo = ttk.Combobox(left_frame, textvariable=self.series_var, 
                                    values=series_options, state="readonly", width=20)
        series_combo.grid(row=0, column=1, padx=5, pady=5)
        series_combo.current(0)
        series_combo.bind("<<ComboboxSelected>>", self.update_input_fields)
        
        # Frame para parámetros dinámicos
        self.params_frame = tk.Frame(left_frame, bg="#f0f0f0")
        self.params_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Frame para índices de la sumatoria
        self._create_index_frame(left_frame)
        
        # Botón de cálculo
        calculate_button = ttk.Button(left_frame, text="Calcular", command=self.calculate_series)
        calculate_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)
        
        # Frame para visualización de sumatoria (área verde)
        self.summation_frame = tk.Frame(parent, bg="#e0ffe0", borderwidth=2, relief="groove")
        self.summation_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
    
    # Modified _create_index_frame method to use ValidatedEntry
    def _create_index_frame(self, parent):
        index_frame = tk.Frame(parent, bg="#f0f0f0")
        index_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        # Índice inicial de la sumatoria
        start_label = tk.Label(index_frame, text="Índice inicial (start):", bg="#f0f0f0")
        start_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.start_var = tk.StringVar(value="1")
        start_entry = ValidatedEntry(index_frame, textvariable=self.start_var, 
                                    allow_float=False, max_length=6, width=10)
        start_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Índice final de la sumatoria
        end_label = tk.Label(index_frame, text="Índice final (end):", bg="#f0f0f0")
        end_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.end_var = tk.StringVar(value="10")
        end_entry = ValidatedEntry(index_frame, textvariable=self.end_var, 
                                  allow_float=False, max_length=6, width=10)
        end_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    
    def _init_result_frames(self, parent):
        # Frame para resultados
        self.result_frame = tk.Frame(parent, bg="#f0f0f0")
        self.result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Frame para texto
        self.text_frame = tk.Frame(self.result_frame, bg="#f0f0f0")
        self.text_frame.pack(fill=tk.X, pady=5)
        
        # Frame para fórmulas
        self.formula_frame = tk.Frame(self.result_frame, bg="#f0f0f0")
        self.formula_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame para gráfica
        self.plot_frame = tk.Frame(self.result_frame, bg="#f0f0f0")
        self.plot_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    def update_input_fields(self, event=None):
        # Limpiar frame de parámetros
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        series_type = self.series_var.get()
        
        if series_type == "Serie Aritmética":
            self._create_arithmetic_inputs()
        elif series_type == "Serie Geométrica":
            self._create_geometric_inputs()
        elif series_type == "Serie Armónica":
            self._create_harmonic_inputs()
            
        # Actualizar la visualización de la sumatoria genérica al cambiar el tipo de serie
        self.update_summation_display_generic()
    
    def _create_arithmetic_inputs(self):
        # Primer término
        a1_label = tk.Label(self.params_frame, text="Primer término (a₁):", bg="#f0f0f0")
        a1_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.a1_var = tk.StringVar(value="1")
        a1_entry = ValidatedEntry(self.params_frame, textvariable=self.a1_var, 
                                 allow_float=True, max_length=8, width=10)
        a1_entry.grid(row=0, column=1, padx=5, pady=5)

        # Diferencia común
        d_label = tk.Label(self.params_frame, text="Diferencia común (d):", bg="#f0f0f0")
        d_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.d_var = tk.StringVar(value="2")
        d_entry = ValidatedEntry(self.params_frame, textvariable=self.d_var, 
                                allow_float=True, max_length=8, width=10)
        d_entry.grid(row=1, column=1, padx=5, pady=5)
    
    def _create_geometric_inputs(self):
        # Primer término
        a1_label = tk.Label(self.params_frame, text="Primer término (a₁):", bg="#f0f0f0")
        a1_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.a1_var = tk.StringVar(value="1")
        a1_entry = ValidatedEntry(self.params_frame, textvariable=self.a1_var, 
                                 allow_float=True, max_length=8, width=10)
        a1_entry.grid(row=0, column=1, padx=5, pady=5)

        # Razón común
        r_label = tk.Label(self.params_frame, text="Razón común (r):", bg="#f0f0f0")
        r_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.r_var = tk.StringVar(value="2")
        r_entry = ValidatedEntry(self.params_frame, textvariable=self.r_var, 
                                allow_float=True, max_length=8, width=10)
        r_entry.grid(row=1, column=1, padx=5, pady=5)
    
    def _create_harmonic_inputs(self):
        # Tipo de serie armónica
        type_label = tk.Label(self.params_frame, text="Tipo:", bg="#f0f0f0")
        type_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.harmonic_type = tk.StringVar(value="Regular")
        types = ["Regular", "Alternante"]
        type_combo = ttk.Combobox(self.params_frame, textvariable=self.harmonic_type, 
                                  values=types, state="readonly", width=15)
        type_combo.grid(row=0, column=1, padx=5, pady=5)
        type_combo.current(0)
        type_combo.bind("<<ComboboxSelected>>", self.update_summation_display_generic)
    
    def update_summation_display_generic(self, event=None):
        # Crear la serie temporal para obtener la representación genérica
        series_type = self.series_var.get()

        # Utilizar el Factory para crear una instancia temporal de la serie
        serie_temp = None
        if series_type == "Serie Aritmética":
            serie_temp = SerieFactory.create_serie(series_type, 0, 0, a1=0, d=0)
        elif series_type == "Serie Geométrica":
            serie_temp = SerieFactory.create_serie(series_type, 0, 0, a1=0, r=0)
        elif series_type == "Serie Armónica":
            serie_temp = SerieFactory.create_serie(series_type, 0, 0, tipo=self.harmonic_type.get())

        # Obtener la notación LaTeX genérica
        summation_latex = serie_temp.get_generic_summation_latex()

        # Crear y mostrar la figura
        self._display_latex_in_frame(summation_latex, self.summation_frame)
    
    def _display_latex_in_frame(self, latex_text, frame, clear=True):
        # Limpiar el frame si es necesario
        if clear:
            for widget in frame.winfo_children():
                widget.destroy()
        
        # Crear la figura con el texto LaTeX
        fig = MatplotlibFigure.create_text_figure(latex_text)
        
        # Mostrar en el frame
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def calculate_series(self):
        try:
            # Validate specific fields first
            try:
                start = int(self.start_var.get())
                if start <= 0 and self.series_var.get() == "Serie Armónica":
                    messagebox.showerror("Error", "El índice inicial para series armónicas debe ser mayor que 0")
                    return
            except ValueError:
                messagebox.showerror("Error", "El índice inicial debe ser un número entero válido")
                return

            try:
                end = int(self.end_var.get())
                if end < start:
                    messagebox.showerror("Error", "El índice final debe ser mayor o igual al índice inicial")
                    return
                if end - start > 1000:
                    response = messagebox.askquestion("Advertencia", 
                        "Calcular una serie con muchos términos puede llevar tiempo. ¿Desea continuar?")
                    if response != 'yes':
                        return
            except ValueError:
                messagebox.showerror("Error", "El índice final debe ser un número entero válido")
                return

            series_type = self.series_var.get()

            # Validate series-specific parameters
            if series_type == "Serie Aritmética":
                try:
                    a1 = float(self.a1_var.get())
                except ValueError:
                    messagebox.showerror("Error", "El primer término (a₁) debe ser un número válido")
                    return

                try:
                    d = float(self.d_var.get())
                except ValueError:
                    messagebox.showerror("Error", "La diferencia común (d) debe ser un número válido")
                    return

                serie = SerieFactory.create_serie(series_type, start, end, a1=a1, d=d)

            elif series_type == "Serie Geométrica":
                try:
                    a1 = float(self.a1_var.get())
                except ValueError:
                    messagebox.showerror("Error", "El primer término (a₁) debe ser un número válido")
                    return

                try:
                    r = float(self.r_var.get())
                    if r == 1.0 and start != end:
                        response = messagebox.askokcancel("Advertencia", 
                            "Una serie geométrica con r=1 es simplemente a₁ repetido n veces. ¿Continuar?")
                        if not response:
                            return
                    if abs(r) > 10 and end - start > 20:
                        response = messagebox.askquestion("Advertencia", 
                            "Valores altos de r pueden producir resultados muy grandes. ¿Desea continuar?")
                        if response != 'yes':
                            return
                except ValueError:
                    messagebox.showerror("Error", "La razón común (r) debe ser un número válido")
                    return

                serie = SerieFactory.create_serie(series_type, start, end, a1=a1, r=r)

            elif series_type == "Serie Armónica":
                harmonic_type = self.harmonic_type.get()
                serie = SerieFactory.create_serie(series_type, start, end, tipo=harmonic_type)

            # Calcular la suma y obtener los términos
            try:
                sum_total, terms = serie.calcular_suma()

                # Verificar si los resultados son válidos
                if any(not np.isfinite(term) for term in terms):
                    messagebox.showwarning("Advertencia", 
                        "Algunos términos de la serie contienen valores infinitos o indefinidos.")

                if not np.isfinite(sum_total):
                    messagebox.showwarning("Advertencia", 
                        "La suma de la serie es infinita o indefinida. Se mostrarán los términos pero el resultado total puede no ser preciso.")

            except Exception as e:
                messagebox.showerror("Error de cálculo", 
                    f"No se pudo calcular la serie: {str(e)}")
                return

            # Calculate partial sums (handle potential overflow)
            try:
                partial_sums = []
                running_sum = 0
                for term in terms:
                    running_sum += term
                    partial_sums.append(running_sum)
            except Exception as e:
                messagebox.showerror("Error", f"Error al calcular sumas parciales: {str(e)}")
                return

            # Update the display
            try:
                self._display_latex_in_frame(serie.get_summation_latex(), self.summation_frame)
                self._update_results_display(serie, sum_total, terms, partial_sums)
                messagebox.showinfo("Éxito", "Cálculo completado correctamente")
            except Exception as e:
                messagebox.showerror("Error de visualización", 
                    f"No se pudieron mostrar los resultados: {str(e)}")

        except Exception as e:
            messagebox.showerror("Error inesperado", 
                f"Ha ocurrido un error inesperado: {str(e)}")
            print(f"Error inesperado: {e}")
    
    def _update_results_display(self, serie, sum_total, terms, partial_sums):
        # Limpiar frames anteriores
        for widget in self.text_frame.winfo_children():
            widget.destroy()
        for widget in self.formula_frame.winfo_children():
            widget.destroy()
        
        # Mostrar texto simple
        text_label = tk.Label(self.text_frame, text=serie.get_result_text(sum_total), 
                             font=("Arial", 12), bg="#f0f0f0", justify="left")
        text_label.pack(side=tk.LEFT, padx=10)
        
        # Mostrar fórmula renderizada
        formula_latex = serie.get_formula_latex(sum_total)
        self._display_latex_in_frame(f"${formula_latex}$", self.formula_frame, clear=True)
        
        # Generar gráfica
        self._display_series_plot(terms, partial_sums, serie.start)
    
    def _display_series_plot(self, terms, partial_sums, start_idx):
        # Limpiar frame de gráfica
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        
        # Crear la figura con los gráficos
        fig = MatplotlibFigure.create_series_plots(terms, partial_sums, start_idx)
        
        # Mostrar gráfica en el frame
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    app = SeriesCalculator()
    app.mainloop()