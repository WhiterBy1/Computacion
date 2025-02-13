import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
from datetime import datetime
import re
from contactos import contacts_data_prueba

class Contact:
    def __init__(self, first_name: str, last_name: str, phone: str, emails: List[str], description: str = ""):
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.emails = emails
        self.description = description
        self.created_at = datetime.now()
        self.modified_at = datetime.now()

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def initial(self) -> str:
        return self.first_name[0].upper() if self.first_name else "?"

class ContactManagerGUI:
    def __init__(self, root:tk.Tk):
        self.root = root
        self.root.title("Agenda de Contactos")
        
        # Configurar el estilo
        self.setup_styles()
        
        # Crear el frame principal
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Frame izquierdo con borde
        self.left_frame = ttk.Frame(self.main_frame, style='Bordered.TFrame')
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=2, pady=2)
        
        # Frame derecho con borde
        self.right_frame = ttk.Frame(self.main_frame, style='Bordered.TFrame')
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Configurar la búsqueda
        self.setup_search()
        
        # Configurar la lista de contactos
        self.setup_contact_list()
        
        # Configurar el panel de detalles
        self.setup_details_panel()
        
        # Variables de control
        self.selected_contact = None
        self.contacts = []
        
        # Cargar datos de ejemplo
        self.load_sample_data()

    def setup_styles(self):
        style = ttk.Style()
        
        # Estilo para frames con borde
        style.configure('Bordered.TFrame', 
                       borderwidth=1, 
                       relief='solid')
        
        # Estilo para frames seleccionados
        style.configure('Selected.TFrame',
                       background='#e1f5fe')
        
        # Estilo para botones
        style.configure('Edit.TButton',
                       background='#1976d2',
                       foreground='white')
        style.configure('Delete.TButton',
                       background='#d32f2f',
                       foreground='white')

    def setup_search(self):
        search_frame = ttk.Frame(self.left_frame, style='Bordered.TFrame')
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.filter_contacts)
        
        search_entry = ttk.Entry(search_frame, 
                               textvariable=self.search_var,
                               font=('Arial', 10))
        search_entry.pack(fill=tk.X, padx=5, pady=5)

    def setup_contact_list(self):
        self.contacts_canvas = tk.Canvas(self.left_frame)
        scrollbar = ttk.Scrollbar(self.left_frame, 
                                orient="vertical", 
                                command=self.contacts_canvas.yview)
        self.contacts_frame = ttk.Frame(self.contacts_canvas)
        
        self.contacts_frame.bind(
            "<Configure>",
            lambda e: self.contacts_canvas.configure(
                scrollregion=self.contacts_canvas.bbox("all")
            )
        )
        
        self.contacts_canvas.create_window((0, 0), 
                                         window=self.contacts_frame, 
                                         anchor="nw", 
                                         width=280)
        self.contacts_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.contacts_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_details_panel(self):
        # Avatar y nombre
        self.detail_avatar_frame = ttk.Frame(self.right_frame)
        self.detail_avatar_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.detail_avatar_label = tk.Label(self.detail_avatar_frame,
                                          width=4,
                                          height=2,
                                          font=('Arial', 24, 'bold'),
                                          bg='#2ECC71',
                                          fg='white')
        self.detail_avatar_label.pack()
        
        self.detail_name_label = ttk.Label(self.detail_avatar_frame,
                                         font=('Arial', 14, 'bold'))
        self.detail_name_label.pack(pady=10)
        
        # Botones de acción
        btn_frame = ttk.Frame(self.right_frame)
        btn_frame.pack(fill=tk.X, padx=20)
        
        self.edit_btn = ttk.Button(btn_frame, 
                                 text="Editar",
                                 style='Edit.TButton',
                                 command=self.edit_contact)
        self.edit_btn.pack(side=tk.RIGHT, padx=5)
        
        self.delete_btn = ttk.Button(btn_frame,
                                   text="Eliminar",
                                   style='Delete.TButton',
                                   command=self.delete_contact)
        self.delete_btn.pack(side=tk.RIGHT, padx=5)
        
        # Información de contacto
        info_frame = ttk.Frame(self.right_frame, style='Bordered.TFrame')
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Teléfono
        ttk.Label(info_frame,
                 text="Teléfono:",
                 font=('Arial', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10,0))
        self.detail_phone_label = ttk.Label(info_frame)
        self.detail_phone_label.pack(anchor=tk.W, padx=20)
        
        # Emails
        ttk.Label(info_frame,
                 text="Emails:",
                 font=('Arial', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10,0))
        self.detail_emails_frame = ttk.Frame(info_frame)
        self.detail_emails_frame.pack(fill=tk.X, padx=20)
        
        # Descripción
        ttk.Label(info_frame,
                 text="Descripción:",
                 font=('Arial', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10,0))
        self.detail_description_label = ttk.Label(info_frame, wraplength=300)
        self.detail_description_label.pack(anchor=tk.W, padx=20, pady=(0,10))

    def create_contact_item(self, contact, parent):
        frame = ttk.Frame(parent, style='Bordered.TFrame')
        frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Avatar
        avatar_label = tk.Label(frame,
                              text=contact.initial,
                              width=2,
                              font=('Arial', 12, 'bold'),
                              bg='#2ECC71',
                              fg='white')
        avatar_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Información
        info_frame = ttk.Frame(frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        name_label = ttk.Label(info_frame,
                             text=contact.full_name,
                             font=('Arial', 10))
        name_label.pack(anchor=tk.W)
        
        phone_label = ttk.Label(info_frame,
                              text=contact.phone,
                              font=('Arial', 9),
                              foreground='gray')
        phone_label.pack(anchor=tk.W)
        
        # Vincular eventos de clic
        for widget in [frame, avatar_label, info_frame, name_label, phone_label]:
            widget.bind('<Button-1>', lambda e, c=contact: self.select_contact(c))
            
        return frame

    def select_contact(self, contact:Contact):
        # Deseleccionar el contacto anterior
        if self.selected_contact:
            self.refresh_contacts_list()
            
        self.selected_contact = contact
        self.refresh_contacts_list()
        self.update_details_panel(contact)

    def update_details_panel(self, contact:Contact):
        # Avatar y nombre
        self.detail_avatar_label.configure(text=contact.initial)
        self.detail_name_label.configure(text=contact.full_name)
        
        # Teléfono
        self.detail_phone_label.configure(text=contact.phone)
        
        # Limpiar y actualizar emails
        for widget in self.detail_emails_frame.winfo_children():
            widget.destroy()
        
        for email in contact.emails:
            ttk.Label(self.detail_emails_frame, text=email).pack(anchor=tk.W)
        
        # Descripción
        self.detail_description_label.configure(text=contact.description)

    def refresh_contacts_list(self):
        # Limpiar lista actual
        for widget in self.contacts_frame.winfo_children():
            widget.destroy()
        
        # Filtrar y ordenar contactos
        search_text = self.search_var.get().lower()
        filtered_contacts = [
            c for c in self.contacts
            if search_text in c.full_name.lower() or search_text in c.phone
        ]
        
        sorted_contacts = sorted(filtered_contacts, key=lambda x: x.full_name.lower())
        
        # Recrear lista
        for contact in sorted_contacts:
            item_frame = self.create_contact_item(contact, self.contacts_frame)
            if contact == self.selected_contact:
                item_frame.configure(style='Selected.TFrame')

    def filter_contacts(self, *args):
        self.refresh_contacts_list()

    def load_sample_data(self):
        self.contacts = contacts_data_prueba
        self.refresh_contacts_list()

    def edit_contact(self):
        if not self.selected_contact:
            return
        
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Editar Contacto")
        edit_window.geometry("400x500")
        
        # Campos de edición
        ttk.Label(edit_window, text="Nombre:").pack(padx=20, pady=(20,0))
        first_name_entry = ttk.Entry(edit_window)
        first_name_entry.insert(0, self.selected_contact.first_name)
        first_name_entry.pack(padx=20)
        
        ttk.Label(edit_window, text="Apellido:").pack(padx=20, pady=(10,0))
        last_name_entry = ttk.Entry(edit_window)
        last_name_entry.insert(0, self.selected_contact.last_name)
        last_name_entry.pack(padx=20)
        
        ttk.Label(edit_window, text="Teléfono:").pack(padx=20, pady=(10,0))
        phone_entry = ttk.Entry(edit_window)
        phone_entry.insert(0, self.selected_contact.phone)
        phone_entry.pack(padx=20)
        
        ttk.Label(edit_window, text="Emails (uno por línea):").pack(padx=20, pady=(10,0))
        emails_text = tk.Text(edit_window, height=4)
        emails_text.insert('1.0', '\n'.join(self.selected_contact.emails))
        emails_text.pack(padx=20)
        
        ttk.Label(edit_window, text="Descripción:").pack(padx=20, pady=(10,0))
        description_text = tk.Text(edit_window, height=4)
        description_text.insert('1.0', self.selected_contact.description)
        description_text.pack(padx=20)
        
        def save_changes():
            self.selected_contact.first_name = first_name_entry.get()
            self.selected_contact.last_name = last_name_entry.get()
            self.selected_contact.phone = phone_entry.get()
            self.selected_contact.emails = [
                e.strip() for e in emails_text.get('1.0', tk.END).split('\n')
                if e.strip()
            ]
            self.selected_contact.description = description_text.get('1.0', tk.END).strip()
            self.selected_contact.modified_at = datetime.now()
            
            self.refresh_contacts_list()
            self.update_details_panel(self.selected_contact)
            edit_window.destroy()
        
        ttk.Button(edit_window,
                  text="Guardar",
                  command=save_changes).pack(pady=20)

    def delete_contact(self):
        if not self.selected_contact:
            return
        
        if messagebox.askyesno("Confirmar eliminación",
                              f"¿Está seguro de eliminar a {self.selected_contact.full_name}?"):
            self.contacts.remove(self.selected_contact)
            self.selected_contact = None
            self.refresh_contacts_list()
            
            # Limpiar panel de detalles
            self.detail_avatar_label.configure(text="")
            self.detail_name_label.configure(text="")
            self.detail_phone_label.configure(text="")
            for widget in self.detail_emails_frame.winfo_children():
                widget.destroy()
            self.detail_description_label.configure(text="")
            
            messagebox.showinfo("Éxito", "Contacto eliminado correctamente")

def main():
    root = tk.Tk()
    root.geometry("800x600")
    root.minsize(1000, 600)  # Tamaño mínimo de ventana
    
    # Configurar el tema y estilos globales
    style = ttk.Style()
    style.theme_use('clam')  # Usar un tema moderno
    
    # Configurar colores personalizados
    root.option_add('*Background', '#f5f5f5')
    root.option_add('*Foreground', '#333333')
    
    app = ContactManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()