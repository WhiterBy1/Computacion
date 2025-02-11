import tkinter as tk
from tkinter import ttk, messagebox
import re
from PIL import Image, ImageTk
import os

class Contacto:
    def __init__(self, nombre, apellido, telefono, email, empresa="", nota="", webpage=""):
        self.nombre = nombre
        self.apellido = apellido
        self.telefono = telefono
        self.email = email
        self.empresa = empresa
        self.nota = nota
        self.webpage = webpage

class AgendaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Contacts")
        self.root.geometry("800x600")
        
        # Configurar el estilo
        self.style = ttk.Style()
        self.style.configure('Listbox.TFrame', background='white')
        self.style.configure('Details.TFrame', background='white')
        self.style.configure('Search.TEntry', padding=5)
        
        # Frame principal con división
        self.main_frame = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel izquierdo (lista de contactos)
        self.left_panel = ttk.Frame(self.main_frame, style='Listbox.TFrame')
        self.main_frame.add(self.left_panel, weight=1)
        
        # Barra de búsqueda
        self.search_frame = ttk.Frame(self.left_panel)
        self.search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, 
                                    textvariable=self.search_var,
                                    style='Search.TEntry')
        self.search_entry.pack(fill=tk.X, padx=5, pady=5)
        self.search_entry.insert(0, "Search Contacts")
        
        # Lista de contactos
        self.contacts_frame = ttk.Frame(self.left_panel)
        self.contacts_frame.pack(fill=tk.BOTH, expand=True)
        
        self.contacts_canvas = tk.Canvas(self.contacts_frame, bg='white')
        scrollbar = ttk.Scrollbar(self.contacts_frame, orient=tk.VERTICAL, 
                                command=self.contacts_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.contacts_canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.contacts_canvas.configure(
                scrollregion=self.contacts_canvas.bbox("all")
            )
        )
        
        self.contacts_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.contacts_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.contacts_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Panel derecho (detalles del contacto)
        self.right_panel = ttk.Frame(self.main_frame, style='Details.TFrame')
        self.main_frame.add(self.right_panel, weight=2)
        
        # Contenido del panel derecho
        # Cabecera con nombre y empresa
        self.header_frame = ttk.Frame(self.right_panel)
        self.header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.name_label = ttk.Label(self.header_frame, text="", font=('Arial', 16, 'bold'))
        self.name_label.pack(anchor=tk.W)
        
        self.company_label = ttk.Label(self.header_frame, text="", font=('Arial', 10))
        self.company_label.pack(anchor=tk.W)
        
        # Sección de emails
        self.email_frame = ttk.LabelFrame(self.right_panel, text="Emails")
        self.email_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Sección de teléfono
        self.phone_frame = ttk.LabelFrame(self.right_panel, text="Telephone")
        self.phone_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Sección de nota
        self.note_frame = ttk.LabelFrame(self.right_panel, text="Note")
        self.note_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Sección de página web
        self.web_frame = ttk.LabelFrame(self.right_panel, text="Webpages")
        self.web_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Agregar algunos contactos de ejemplo
        self.add_sample_contacts()
        
    def create_contact_button(self, contact):
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Crear un círculo con las iniciales como "foto"
        canvas = tk.Canvas(frame, width=30, height=30, bg='#4CAF50', highlightthickness=0)
        canvas.create_text(15, 15, text=contact.nombre[0].upper(), fill='white', font=('Arial', 12, 'bold'))
        canvas.pack(side=tk.LEFT, padx=5)
        
        button = ttk.Label(frame, text=f"{contact.nombre} {contact.apellido}")
        button.pack(side=tk.LEFT, padx=5, fill=tk.X)
        
        frame.bind('<Button-1>', lambda e: self.show_contact_details(contact))
        button.bind('<Button-1>', lambda e: self.show_contact_details(contact))
        
    def show_contact_details(self, contact):
        self.name_label.config(text=f"{contact.nombre} {contact.apellido}")
        self.company_label.config(text=contact.empresa)
        
        # Limpiar frames anteriores
        for widget in self.email_frame.winfo_children():
            widget.destroy()
        for widget in self.phone_frame.winfo_children():
            widget.destroy()
        for widget in self.note_frame.winfo_children():
            widget.destroy()
        for widget in self.web_frame.winfo_children():
            widget.destroy()
            
        # Mostrar emails
        ttk.Label(self.email_frame, text=contact.email).pack(padx=5, pady=2)
        
        # Mostrar teléfono
        ttk.Label(self.phone_frame, text=contact.telefono).pack(padx=5, pady=2)
        
        # Mostrar nota
        ttk.Label(self.note_frame, text=contact.nota).pack(padx=5, pady=2)
        
        # Mostrar página web
        if contact.webpage:
            ttk.Label(self.web_frame, text=contact.webpage).pack(padx=5, pady=2)
    
    def add_sample_contacts(self):
        contacts = [
            Contacto("Jane", "Karloff", "07399 879185", 
                    "mary@wideanglesoftware.com", "Wide Angle Software", 
                    "Main person", "http://www.wideanglesoftware.com"),
            Contacto("James", "King", "555-0102", "james@email.com", 
                    "Tech Corp", "Developer"),
            Contacto("Sarah", "Smith", "555-0103", "sarah@email.com", 
                    "Design Inc", "Designer"),
            Contacto("Mark", "Stanley", "555-0104", "mark@email.com", 
                    "Marketing Pro", "Marketing")
        ]
        
        for contact in contacts:
            self.create_contact_button(contact)

if __name__ == '__main__':
    root = tk.Tk()
    app = AgendaGUI(root)
    root.mainloop()