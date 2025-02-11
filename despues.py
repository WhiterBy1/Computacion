import tkinter as tk
from tkinter import ttk, messagebox
import re

class Contacto:
    def __init__(self, nombre, apellido, telefono, email):
        self.nombre = nombre
        self.apellido = apellido
        self.telefono = telefono
        self.email = email

class Agenda:
    def __init__(self):
        self.contactos = []
    
    def agregar_contacto(self, contacto):
        self.contactos.append(contacto)
        
    def eliminar_contacto(self, indice):
        if 0 <= indice < len(self.contactos):
            del self.contactos[indice]
            return True
        return False
    
    def buscar_contacto(self, texto):
        return [i for i, c in enumerate(self.contactos) 
                if texto.lower() in c.nombre.lower() or 
                texto.lower() in c.apellido.lower()]

class AgendaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Agenda de Contactos")
        self.agenda = Agenda()
        
        # Estilo
        self.style = ttk.Style()
        self.style.configure('TButton', padding=5)
        self.style.configure('TEntry', padding=5)
        self.style.configure('TLabel', padding=5)
        
        # Frame principal
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Formulario
        ttk.Label(self.main_frame, text="Nombre:").grid(row=0, column=0, sticky=tk.W)
        self.nombre_var = tk.StringVar()
        self.nombre_entry = ttk.Entry(self.main_frame, textvariable=self.nombre_var)
        self.nombre_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.main_frame, text="Apellido:").grid(row=1, column=0, sticky=tk.W)
        self.apellido_var = tk.StringVar()
        self.apellido_entry = ttk.Entry(self.main_frame, textvariable=self.apellido_var)
        self.apellido_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(self.main_frame, text="Teléfono:").grid(row=2, column=0, sticky=tk.W)
        self.telefono_var = tk.StringVar()
        self.telefono_entry = ttk.Entry(self.main_frame, textvariable=self.telefono_var)
        self.telefono_entry.grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Label(self.main_frame, text="Email:").grid(row=3, column=0, sticky=tk.W)
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(self.main_frame, textvariable=self.email_var)
        self.email_entry.grid(row=3, column=1, padx=5, pady=2)
        
        # Botones
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Agregar", command=self.agregar_contacto).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Eliminar", command=self.eliminar_contacto).grid(row=0, column=1, padx=5)
        
        # Búsqueda
        ttk.Label(self.main_frame, text="Buscar:").grid(row=5, column=0, sticky=tk.W)
        self.buscar_var = tk.StringVar()
        self.buscar_entry = ttk.Entry(self.main_frame, textvariable=self.buscar_var)
        self.buscar_entry.grid(row=5, column=1, padx=5, pady=2)
        self.buscar_var.trace('w', self.buscar_contacto)
        
        # Lista de contactos
        self.tree = ttk.Treeview(self.main_frame, columns=('Nombre', 'Apellido', 'Teléfono', 'Email'), 
                                show='headings', height=10)
        self.tree.grid(row=6, column=0, columnspan=2, pady=10)
        
        self.tree.heading('Nombre', text='Nombre')
        self.tree.heading('Apellido', text='Apellido')
        self.tree.heading('Teléfono', text='Teléfono')
        self.tree.heading('Email', text='Email')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=6, column=2, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)

    def validar_datos(self, nombre, apellido, telefono, email):
        if not nombre or not apellido:
            messagebox.showerror("Error", "Nombre y apellido son obligatorios")
            return False
            
        if not re.match(r'^\d{9}$', telefono):
            messagebox.showerror("Error", "El teléfono debe tener 9 dígitos")
            return False
            
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messagebox.showerror("Error", "Email inválido")
            return False
            
        return True
        
    def agregar_contacto(self):
        nombre = self.nombre_var.get().strip()
        apellido = self.apellido_var.get().strip()
        telefono = self.telefono_var.get().strip()
        email = self.email_var.get().strip()
        
        if self.validar_datos(nombre, apellido, telefono, email):
            contacto = Contacto(nombre, apellido, telefono, email)
            self.agenda.agregar_contacto(contacto)
            self.tree.insert('', tk.END, values=(nombre, apellido, telefono, email))
            self.limpiar_campos()
            messagebox.showinfo("Éxito", "Contacto agregado correctamente")
    
    def eliminar_contacto(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Aviso", "Por favor seleccione un contacto")
            return
            
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar el contacto?"):
            for item in seleccion:
                indice = self.tree.index(item)
                if self.agenda.eliminar_contacto(indice):
                    self.tree.delete(item)
            messagebox.showinfo("Éxito", "Contacto(s) eliminado(s) correctamente")
    
    def buscar_contacto(self, *args):
        texto = self.buscar_var.get().strip()
        self.tree.delete(*self.tree.get_children())
        
        if texto:
            indices = self.agenda.buscar_contacto(texto)
            for i in indices:
                c = self.agenda.contactos[i]
                self.tree.insert('', tk.END, values=(c.nombre, c.apellido, c.telefono, c.email))
        else:
            for c in self.agenda.contactos:
                self.tree.insert('', tk.END, values=(c.nombre, c.apellido, c.telefono, c.email))
    
    def limpiar_campos(self):
        self.nombre_var.set('')
        self.apellido_var.set('')
        self.telefono_var.set('')
        self.email_var.set('')

if __name__ == '__main__':
    root = tk.Tk()
    app = AgendaGUI(root)
    root.mainloop()