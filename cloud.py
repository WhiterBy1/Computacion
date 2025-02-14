import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Optional, Literal
from datetime import datetime
import re
from contactos import contacts_data_prueba
import unicodedata

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

class Validator:
    """Clase para validar únicamente el formato de los datos de entrada"""
    
    @staticmethod
    def validate_phone_format(phone: str, type: Literal['fijo', 'telefonico']) -> bool:
        """Valida que el teléfono tenga 10 dígitos (eliminando caracteres no numéricos)"""
        cleaned = re.sub(r'\D', '', phone)
        return len(cleaned) == 10

    @staticmethod
    def validate_email_format(email: str) -> bool:
        """Valida el formato básico de un email"""
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(pattern, email) is not None

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normaliza texto: elimina acentos, convierte a minúsculas y remueve caracteres especiales"""
        normalized = unicodedata.normalize('NFKD', text.lower()).encode('ascii', 'ignore').decode('ascii')
        return re.sub(r'[^\w\s]', '', normalized).strip()

class ContactManager:
    """Clase para manejar las operaciones con contactos"""
    
    def __init__(self):
        self.contacts: List[Contact] = []

    def add_contact(self, contact_data: dict) -> tuple[bool, Optional[str], Optional[Contact]]:
        """Añade un nuevo contacto verificando duplicados"""
        # Verificar duplicados
        if self._is_phone_duplicate(contact_data['phone']):
            return False, "El teléfono ya existe en otro contacto", None
            
        if self._is_name_duplicate(contact_data['first_name'], contact_data['last_name']):
            return False, "Ya existe un contacto con este nombre y apellido", None

        # Crear y añadir el contacto
        contact = Contact(**contact_data)
        self.contacts.append(contact)
        return True, None, contact

    def update_contact(self, contact: Contact, new_data: dict) -> tuple[bool, Optional[str]]:
        """Actualiza un contacto existente verificando duplicados"""
        # Verificar duplicados excluyendo el contacto actual
        if self._is_phone_duplicate(new_data['phone'], exclude=contact):
            return False, "El teléfono ya existe en otro contacto"
            
        if self._is_name_duplicate(new_data['first_name'], new_data['last_name'], exclude=contact):
            return False, "Ya existe un contacto con este nombre y apellido"

        # Actualizar datos
        for key, value in new_data.items():
            setattr(contact, key, value)
        contact.modified_at = datetime.now()
        return True, None

    def _is_phone_duplicate(self, phone: str, exclude: Optional[Contact] = None) -> bool:
        """Verifica si el teléfono ya existe"""
        cleaned_phone = re.sub(r'\D', '', phone)
        return any(
            contact != exclude and re.sub(r'\D', '', contact.phone) == cleaned_phone
            for contact in self.contacts
        )

    def _is_name_duplicate(self, first_name: str, last_name: str, exclude: Optional[Contact] = None) -> bool:
        """Verifica si el nombre completo ya existe"""
        normalized_first = Validator.normalize_text(first_name)
        normalized_last = Validator.normalize_text(last_name)
        
        return any(
            contact != exclude and 
            Validator.normalize_text(contact.first_name) == normalized_first and 
            Validator.normalize_text(contact.last_name) == normalized_last
            for contact in self.contacts
        )

    def search_contacts(self, query: str) -> List[Contact]:
        """Busca contactos por nombre, teléfono o descripción"""
        if not query.strip():
            return sorted(self.contacts, key=lambda x: x.full_name.lower())
            
        normalized_query = Validator.normalize_text(query)
        filtered_contacts = [
            c for c in self.contacts
            if any(
                normalized_query in Validator.normalize_text(field)
                for field in [c.full_name, c.phone, c.description]
            )
        ]
        return sorted(filtered_contacts, key=lambda x: x.full_name.lower())

class ContactForm(tk.Toplevel):
    
    def __init__(self, parent, contact_manager: ContactManager, on_save: Callable, 
                 contact: Optional[Contact] = None):
        super().__init__(parent)
        self.title("Editar Contacto" if contact else "Nuevo Contacto")
        self.geometry("400x500")
        self.contact = contact
        self.contact_manager = contact_manager
        self.on_save = on_save
        
        self.setup_form()
        if contact:
            self.load_contact_data()

    def setup_form(self):
        # Campos de entrada
        self.create_labeled_entry("Nombre:", "first_name", pady=(20,0))
        self.create_labeled_entry("Apellido:", "last_name")
        self.create_labeled_entry("Teléfono:", "phone")
        
        ttk.Label(self, text="Emails (uno por línea):").pack(padx=20, pady=(10,0))
        self.emails_text = tk.Text(self, height=4)
        self.emails_text.pack(padx=20)
        
        ttk.Label(self, text="Descripción:").pack(padx=20, pady=(10,0))
        self.description_text = tk.Text(self, height=4)
        self.description_text.pack(padx=20)
        
        ttk.Button(self, text="Guardar", command=self.save_contact).pack(pady=20)

    def create_labeled_entry(self, label: str, attr_name: str, **kwargs):
        ttk.Label(self, text=label).pack(padx=20, **kwargs)
        entry = ttk.Entry(self)
        entry.pack(padx=20)
        setattr(self, f"{attr_name}_entry", entry)

    def load_contact_data(self):
        self.first_name_entry.insert(0, self.contact.first_name)
        self.last_name_entry.insert(0, self.contact.last_name)
        self.phone_entry.insert(0, self.contact.phone)
        self.emails_text.insert('1.0', '\n'.join(self.contact.emails))
        self.description_text.insert('1.0', self.contact.description)

    def get_form_data(self):
        return {
            'first_name': self.first_name_entry.get().strip(),
            'last_name': self.last_name_entry.get().strip(),
            'phone': self.phone_entry.get().strip(),
            'emails': [e.strip() for e in self.emails_text.get('1.0', tk.END).split('\n') if e.strip()],
            'description': self.description_text.get('1.0', tk.END).strip()
        }

    def validate_form_data(self, data: dict) -> bool:
        """Valida solo el formato de los datos del formulario"""
        # Validar campos requeridos
        if not all([data['first_name'], data['last_name'], data['phone']]):
            messagebox.showerror("Error", "Todos los campos son requeridos")
            return False

        # Validar formato de teléfono
        if not Validator.validate_phone_format(data['phone'], 'fijo'):
            messagebox.showerror("Error", "El teléfono debe tener 10 dígitos")
            return False

        # Validar formato de emails
        for email in data['emails']:
            if not Validator.validate_email_format(email):
                messagebox.showerror("Error", f"Email inválido: {email}")
                return False

        return True

    def save_contact(self):
        data = self.get_form_data()
        if not self.validate_form_data(data):
            return

        if self.contact:
            # Actualizar contacto existente
            success, error_msg = self.contact_manager.update_contact(self.contact, data)
        else:
            # Crear nuevo contacto
            success, error_msg, self.contact = self.contact_manager.add_contact(data)

        if not success:
            if "Ya existe" in error_msg:
                if messagebox.askyesno("Advertencia", f"{error_msg}. ¿Desea continuar?"):
                    # Forzar la actualización/creación
                    if self.contact:
                        for key, value in data.items():
                            setattr(self.contact, key, value)
                    else:
                        self.contact = Contact(**data)
                        self.contact_manager.contacts.append(self.contact)
                    success = True
                else:
                    return
            else:
                messagebox.showerror("Error", error_msg)
                return

        if success:
            self.on_save(self.contact)
            self.destroy()
            messagebox.showinfo(
                "Éxito", 
                "Contacto actualizado correctamente" if self.contact else "Contacto agregado correctamente"
            )

class ContactManagerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Agenda de Contactos")
        self.contact_manager = ContactManager()
        self.selected_contact = None
        
        self.setup_gui()
        self.load_sample_data()


    def setup_gui(self):
        self.setup_styles()
        self.create_main_layout()
        self.setup_search()
        self.setup_contact_list()
        self.setup_details_panel()

    def create_main_layout(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.left_frame = ttk.Frame(self.main_frame, style='Bordered.TFrame')
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=2, pady=2)
        
        self.right_frame = ttk.Frame(self.main_frame, style='Bordered.TFrame')
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('default')
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
         # Añadir botón de nuevo contacto
        add_button = ttk.Button(search_frame,
                               text="+ Nuevo Contacto",
                               command=self.add_contact)
        
        add_button.pack(side=tk.RIGHT, padx=5, pady=5)
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

        # Ajustar el área de desplazamiento dinámicamente
        self.contacts_frame.bind(
            "<Configure>",
            lambda e: self.contacts_canvas.configure(
                scrollregion=self.contacts_canvas.bbox("all")
            )
        )

        # Crear el frame dentro del canvas
        window_id = self.contacts_canvas.create_window(
            (0, 0), 
            window=self.contacts_frame, 
            anchor="nw"
        )

        # Ajustar el ancho del frame cuando el canvas cambia de tamaño
        def update_frame_width(event):
            canvas_width = event.width  # Obtener el ancho del canvas
            self.contacts_canvas.itemconfig(window_id, width=canvas_width)

        self.contacts_canvas.bind("<Configure>", update_frame_width)

        # Configurar la barra de desplazamiento
        self.contacts_canvas.configure(yscrollcommand=scrollbar.set)

        # Empaquetar widgets
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

    def handle_contact_save(self, contact: Contact):
        if contact not in self.contact_manager.contacts:
            self.contact_manager.contacts.append(contact)
        self.refresh_contacts_list()
        self.select_contact(contact)
    def add_contact(self):
        ContactForm(self.root, self.contact_manager, self.handle_contact_save)

    def edit_contact(self):
        if not self.selected_contact:
            return
        ContactForm(self.root, self.contact_manager, self.handle_contact_save, self.selected_contact)
    def create_contact_item(self, contact, parent):
        # Frame contenedor principal con clip
        frame = ttk.Frame(parent, style='Bordered.TFrame')
        frame.pack(fill=tk.X, padx=5, pady=2)
        frame.pack_propagate(False)  # Evita que el frame se ajuste al contenido
        frame.configure(height=50)  # Altura fija para el frame

        # Frame interno para el contenido
        content_frame = ttk.Frame(frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Avatar
        avatar_label = tk.Label(content_frame,
                              text=contact.initial,
                              width=2,
                              font=('Arial', 12, 'bold'),
                              bg='#2ECC71',
                              fg='white')
        avatar_label.pack(side=tk.LEFT, padx=5, pady=5)

        # Información
        info_frame = ttk.Frame(content_frame)
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
        for widget in [frame, content_frame, avatar_label, info_frame, name_label, phone_label]:
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
        search_text = self.search_var.get().strip()
        contacts = self.contact_manager.search_contacts(search_text)
        
        # Recrear lista
        for contact in contacts:
            item_frame = self.create_contact_item(contact, self.contacts_frame)
            if contact == self.selected_contact:
                item_frame.configure(style='Selected.TFrame')

    def filter_contacts(self, *args):
        self.refresh_contacts_list()

    def load_sample_data(self):
        self.contact_manager.contacts = contacts_data_prueba
        self.refresh_contacts_list()
    def clear_details_panel(self):
        
        self.detail_avatar_label.configure(text="")
        self.detail_name_label.configure(text="")
        self.detail_phone_label.configure(text="")
        for widget in self.detail_emails_frame.winfo_children():
            widget.destroy()
        self.detail_description_label.configure(text="")
    def delete_contact(self):
        if not self.selected_contact:
            return
        
        if messagebox.askyesno("Confirmar eliminación",
                              f"¿Está seguro de eliminar a {self.selected_contact.full_name}?"):
            self.contact_manager.contacts.remove(self.selected_contact)
            self.selected_contact = None
            self.refresh_contacts_list()
            
            # Limpiar panel de detalles
            self.clear_details_panel()
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