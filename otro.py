import tkinter as tk
from tkinter import ttk, messagebox

class ConversorTemperatura:
    LIMITES = {
        'Celsius': -273.15,
        'Fahrenheit': -459.67,
        'Kelvin': 0
    }

    def __init__(self):
        self.conversiones = {
            'Celsius': {
                'Fahrenheit': lambda c: (c * 9/5) + 32,
                'Kelvin': lambda c: c + 273.15
            },
            'Fahrenheit': {
                'Celsius': lambda f: (f - 32) * 5/9,
                'Kelvin': lambda f: (f - 32) * 5/9 + 273.15
            },
            'Kelvin': {
                'Celsius': lambda k: k - 273.15,
                'Fahrenheit': lambda k: (k - 273.15) * 9/5 + 32
            }
        }

    def validar_temperatura(self, temperatura: float, escala: str) -> bool:
        return temperatura >= self.LIMITES[escala]

    def convertir(self, temperatura: float, escala_origen: str, escala_destino: str) -> float:
        if escala_origen == escala_destino:
            return temperatura
        return self.conversiones[escala_origen][escala_destino](temperatura)

def convertir_temperatura():
    try:
        conversor = ConversorTemperatura()
        temperatura = float(entry_temperatura.get())
        escala_origen = combo_escala_origen.get()
        escala_destino = combo_escala_destino.get()

        if not conversor.validar_temperatura(temperatura, escala_origen):
            limite = conversor.LIMITES[escala_origen]
            messagebox.showerror("Error", 
                f"Temperatura inválida para {escala_origen}. Mínimo permitido: {limite}")
            return

        resultado = conversor.convertir(temperatura, escala_origen, escala_destino)
        label_resultado.config(text=f"Resultado: {resultado:.2f}° {escala_destino}")

    except ValueError:
        messagebox.showerror("Error", "Ingrese un número válido para la temperatura")

# Configuración de la interfaz gráfica
root = tk.Tk()
root.title("Conversor de Temperaturas")
root.geometry("400x350")
root.configure(bg="#f0f0f0")

style = ttk.Style()
style.configure('TFrame', background="#f0f0f0")
style.configure('TLabel', background="#f0f0f0", font=('Arial', 12))
style.configure('TButton', font=('Arial', 12, 'bold'), background="#4CAF50", foreground="black")
style.configure('TEntry', font=('Arial', 12))

frame_principal = ttk.Frame(root)
frame_principal.pack(padx=20, pady=20, fill='both', expand=True)

# Título
label_titulo = ttk.Label(frame_principal, 
                        text="Conversor de Temperaturas",
                        font=('Arial', 16, 'bold'))
label_titulo.pack(pady=10)

# Entrada de temperatura
frame_entrada = ttk.Frame(frame_principal)
frame_entrada.pack(fill='x', pady=5)

ttk.Label(frame_entrada, text="Temperatura a convertir:").pack()
entry_temperatura = ttk.Entry(frame_entrada)
entry_temperatura.pack()

# Selectores de escala
frame_escalas = ttk.Frame(frame_principal)
frame_escalas.pack(fill='x', pady=10)

ttk.Label(frame_entrada, text="Escala origen: \t Escala destino:").pack()
combo_escala_origen = ttk.Combobox(frame_escalas, 
                                  values=['Celsius', 'Fahrenheit', 'Kelvin'],
                                  state='readonly')
combo_escala_origen.current(0)
combo_escala_origen.pack(side='left', padx=10)

combo_escala_destino = ttk.Combobox(frame_escalas, 
                                   values=['Celsius', 'Fahrenheit', 'Kelvin'],
                                   state='readonly')
combo_escala_destino.current(1)
combo_escala_destino.pack(side='left', padx=10)

# Botón de conversión
btn_convertir = ttk.Button(frame_principal, 
                          text="Convertir", 
                          command=convertir_temperatura)
btn_convertir.pack(pady=15)

# Resultado
label_resultado = ttk.Label(frame_principal, 
                           text="Resultado: -",
                           font=('Arial', 14, 'bold'),
                           foreground="#2E7D32")
label_resultado.pack()

root.mainloop()