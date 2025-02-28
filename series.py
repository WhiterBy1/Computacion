import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import re

class SeriesCalculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora de Series Matemáticas")
        self.geometry("1000x800")
        self.configure(bg="#f0f0f0")
        
        # Configuración de estilo
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
        
        # Frame izquierdo para los controles
        left_frame = tk.Frame(control_frame, bg="#f0f0f0")
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
        
        # Frame para parámetros
        self.params_frame = tk.Frame(left_frame, bg="#f0f0f0")
        self.params_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Número de términos
        terms_label = tk.Label(left_frame, text="Número de términos:", bg="#f0f0f0")
        terms_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        self.terms_var = tk.StringVar(value="10")
        terms_entry = ttk.Entry(left_frame, textvariable=self.terms_var, width=10)
        terms_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Botón de cálculo
        calculate_button = ttk.Button(left_frame, text="Calcular", command=self.calculate_series)
        calculate_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)
        
        # Frame para visualización de sumatoria (área verde)
        self.summation_frame = tk.Frame(control_frame, bg="#e0ffe0", borderwidth=2, relief="groove")
        self.summation_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        # Frame para resultados
        self.result_frame = tk.Frame(main_frame, bg="#f0f0f0")
        self.result_frame.pack(fill=tk.Y, expand=True, pady=10)
        
        # Frame para texto
        self.text_frame = tk.Frame(self.result_frame, bg="#f0f0f0")
        self.text_frame.pack(fill=tk.X, pady=5)
        
        # Frame para fórmulas
        self.formula_frame = tk.Frame(self.result_frame, bg="#f0f0f0")
        self.formula_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame para gráfica
        self.plot_frame = tk.Frame(self.result_frame, bg="#f0f0f0")
        self.plot_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Inicializar los campos de entrada
        self.update_input_fields()
        
    def update_input_fields(self, event=None):
        # Limpiar frame de parámetros
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        series_type = self.series_var.get()
        
        if series_type == "Serie Aritmética":
            # Primer término
            a1_label = tk.Label(self.params_frame, text="Primer término (a₁):", bg="#f0f0f0")
            a1_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
            
            self.a1_var = tk.StringVar(value="1")
            a1_entry = ttk.Entry(self.params_frame, textvariable=self.a1_var, width=10)
            a1_entry.grid(row=0, column=1, padx=5, pady=5)
            
            # Diferencia común
            d_label = tk.Label(self.params_frame, text="Diferencia común (d):", bg="#f0f0f0")
            d_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
            
            self.d_var = tk.StringVar(value="2")
            d_entry = ttk.Entry(self.params_frame, textvariable=self.d_var, width=10)
            d_entry.grid(row=1, column=1, padx=5, pady=5)
            
        elif series_type == "Serie Geométrica":
            # Primer término
            a1_label = tk.Label(self.params_frame, text="Primer término (a₁):", bg="#f0f0f0")
            a1_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
            
            self.a1_var = tk.StringVar(value="1")
            a1_entry = ttk.Entry(self.params_frame, textvariable=self.a1_var, width=10)
            a1_entry.grid(row=0, column=1, padx=5, pady=5)
            
            # Razón común
            r_label = tk.Label(self.params_frame, text="Razón común (r):", bg="#f0f0f0")
            r_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
            
            self.r_var = tk.StringVar(value="2")
            r_entry = ttk.Entry(self.params_frame, textvariable=self.r_var, width=10)
            r_entry.grid(row=1, column=1, padx=5, pady=5)
            
        elif series_type == "Serie Armónica":
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
            
        # Actualizar la visualización de la sumatoria genérica al cambiar el tipo de serie
        self.update_summation_display_generic()
    
    def update_summation_display_generic(self, event=None):
        # Limpiar el frame de sumatoria
        for widget in self.summation_frame.winfo_children():
            widget.destroy()
            
        series_type = self.series_var.get()
        summation_latex = ""
        
        if series_type == "Serie Aritmética":
            # Notación de sumatoria genérica para serie aritmética
            summation_latex = r"$\sum_{start}^{end} [a_1 + (k-1) \cdot d]$"
            
        elif series_type == "Serie Geométrica":
            # Notación de sumatoria genérica para serie geométrica
            summation_latex = r"$\sum_{start}^{end} a_1 \cdot r^{k-1}$"
            
        elif series_type == "Serie Armónica":
            harmonic_type = self.harmonic_type.get()
            
            if harmonic_type == "Regular":
                # Notación de sumatoria genérica para serie armónica regular
                summation_latex = r"$\sum_{k = start}^{end} \frac{a}{k}$"
            else:
                # Notación de sumatoria genérica para serie armónica alternante
                summation_latex = r"$\sum_{start}^{end} \frac{(-1)^{k+1}}{k}$"
        
        # Mostrar la notación de sumatoria genérica en el frame verde
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(110,23, 280)
        ax.text(0.5, 0.5, summation_latex, fontsize=20, ha='center', va='center')
        ax.axis('off')
        
        canvas = FigureCanvasTkAgg(fig, master=self.summation_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.Y, expand=True, padx=10, pady=10)
    
    def update_summation_display(self, series_type, n, formula_details):
        # Limpiar el frame de sumatoria
        for widget in self.summation_frame.winfo_children():
            widget.destroy()
            
        summation_latex = ""
        
        if series_type == "Serie Aritmética":
            a1, d = formula_details
            # Notación de sumatoria para serie aritmética
            summation_latex = r"$\sum_{k=1}^{" + str(n) + r"} [" + str(a1) + r" + (k-1) \cdot " + str(d) + r"]$"
            
        elif series_type == "Serie Geométrica":
            a1, r = formula_details
            # Notación de sumatoria para serie geométrica
            summation_latex = r"$\sum_{k=1}^{" + str(n) + r"} " + str(a1) + r" \cdot " + str(r) + r"^{k-1}$"
            
        elif series_type == "Serie Armónica":
            harmonic_type = formula_details
            
            if harmonic_type == "Regular":
                # Notación de sumatoria para serie armónica regular
                summation_latex = r"$\sum_{k=1}^{" + str(n) + r"} \frac{1}{k}$"
            else:
                # Notación de sumatoria para serie armónica alternante
                summation_latex = r"$\sum_{k=1}^{" + str(n) + r"} \frac{(-1)^{k+1}}{k}$"
        
        # Mostrar la notación de sumatoria en el frame verde
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, summation_latex, fontsize=20, ha='center', va='center')
        ax.axis('off')
        
        canvas = FigureCanvasTkAgg(fig, master=self.summation_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
    def plot_series(self, terms, partial_sums):
        # Limpiar frame de gráfica
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        
        # Crear figura
        fig = plt.Figure(figsize=(8, 5), dpi=100)
        fig.subplots_adjust(bottom=0.15)
        
        # Gráfica de términos
        ax1 = fig.add_subplot(121)
        x = list(range(1, len(terms) + 1))
        ax1.plot(x, terms, 'bo-', markersize=4)
        ax1.set_title('Términos de la Serie')
        ax1.set_xlabel('n')
        ax1.set_ylabel('a_n')
        ax1.grid(True)
        
        # Gráfica de sumas parciales
        ax2 = fig.add_subplot(122)
        ax2.plot(x, partial_sums, 'ro-', markersize=4)
        ax2.set_title('Sumas Parciales')
        ax2.set_xlabel('n')
        ax2.set_ylabel('S_n')
        ax2.grid(True)
        
        # Mostrar gráfica en el frame
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def calculate_series(self):
        try:
            n = int(self.terms_var.get())
            if n <= 0:
                messagebox.showerror("Error", "El número de términos debe ser positivo")
                return
                
            series_type = self.series_var.get()
            terms = []
            partial_sums = []
            formula_latex = ""
            result_text = ""
            
            if series_type == "Serie Aritmética":
                a1 = float(self.a1_var.get())
                d = float(self.d_var.get())
                
                # Actualizar la visualización de la sumatoria
                self.update_summation_display(series_type, n, (a1, d))
                
                for i in range(1, n+1):
                    term = a1 + (i-1) * d
                    terms.append(term)
                    partial_sums.append(sum(terms))
                
                formula_latex = (
                    r"S_n = \frac{n}{2} \cdot [2a_1 + (n-1)d] = "
                    r"\frac{" + str(n) + r"}{2} \cdot [2\cdot" + str(a1) + r" + (" + str(n) + r"-1)\cdot" + str(d) + r"] = " + str(partial_sums[-1])
                )
                result_text = f"Serie Aritmética\na1 = {a1}, d = {d}\nSuma total: {partial_sums[-1]:.4f}"
            
            elif series_type == "Serie Geométrica":
                a1 = float(self.a1_var.get())
                r = float(self.r_var.get())
                
                # Actualizar la visualización de la sumatoria
                self.update_summation_display(series_type, n, (a1, r))
                
                for i in range(1, n+1):
                    term = a1 * (r ** (i-1))
                    terms.append(term)
                    partial_sums.append(sum(terms))
                
                formula_latex = (
                    r"S_n = \frac{a_1(1 - r^n)}{1 - r} = "
                    r"\frac{" + str(a1) + r"(1 - " + str(r) + r"^{" + str(n) + r"})}{1 - " + str(r) + r"} = " + str(partial_sums[-1])
                )
                result_text = f"Serie Geométrica\na1 = {a1}, r = {r}\nSuma total: {partial_sums[-1]:.4f}"
                
                if abs(r) < 1:
                    infinite_sum = a1 / (1 - r)
                    formula_latex += r"\quad S_{\infty} = " + f"{infinite_sum:.4f}"
                else:
                    formula_latex += r"\quad"
            
            elif series_type == "Serie Armónica":
                harmonic_type = self.harmonic_type.get()
                
                # Actualizar la visualización de la sumatoria
                self.update_summation_display(series_type, n, harmonic_type)
                
                if harmonic_type == "Regular":
                    for i in range(1, n+1):
                        term = 1 / i
                        terms.append(term)
                        partial_sums.append(sum(terms))
                    
                    formula_latex = (
                        r"S_n = \sum_{k=1}^n \frac{1}{k} = "
                        r"\sum_{k=1}^{" + str(n) + r"} \frac{1}{k} = " + f"{partial_sums[-1]:.4f}"
                    )
                    result_text = f"Serie Armónica Regular\nSuma total: {partial_sums[-1]:.4f}"
                else:
                    for i in range(1, n+1):
                        term = (-1)**(i+1) / i
                        terms.append(term)
                        partial_sums.append(sum(terms))
                    
                    formula_latex = (
                        r"S_n = \sum_{k=1}^n \frac{(-1)^{k+1}}{k} = "
                        r"\sum_{k=1}^{" + str(n) + r"} \frac{(-1)^{k+1}}{k} = " + f"{partial_sums[-1]:.4f}"
                    )
                    result_text = f"Serie Armónica Alternante\nSuma total: {partial_sums[-1]:.4f}"
            
            # Limpiar frames anteriores
            for widget in self.text_frame.winfo_children():
                widget.destroy()
            for widget in self.formula_frame.winfo_children():
                widget.destroy()
            
            # Mostrar texto simple
            text_label = tk.Label(self.text_frame, text=result_text, 
                                 font=("Arial", 12), bg="#f0f0f0", justify="left")
            text_label.pack(side=tk.LEFT, padx=10)
            
            # Mostrar fórmula renderizada
            fig = Figure(figsize=(8, 2), dpi=100)
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, f"${formula_latex}$", 
                   fontsize=14, ha='center', va='center')
            ax.axis('off')
            
            canvas = FigureCanvasTkAgg(fig, master=self.formula_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Generar gráfica
            self.plot_series(terms, partial_sums)
            
        except ValueError as e:
            messagebox.showerror("Error", "Por favor, ingrese valores numéricos válidos")
            print(f"Error: {e}")

if __name__ == "__main__":
    app = SeriesCalculator()
    app.mainloop()