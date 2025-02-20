import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Optional
import re
import unicodedata

class Contact:
    def __init__(self, first_name: str, last_name: str, phones: List[str], emails: List[str], description: str = ""):
        self.first_name = first_name
        self.last_name = last_name
        self.phones = phones
        self.emails = emails
        self.description = description

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def initial(self) -> str:
        return self.first_name[0].upper() if self.first_name else self.last_name[0].upper()

    @property
    def primary_phone(self) -> str:
        return self.phones[0] if self.phones else self.emails[0] if self.emails else "Sin información"

contacts_data_prueba = [
    Contact("Jose David", "Quiñonez Rehenals", ["3127368737", "6051234567"],
            ["Example1@gmail.com", "Example1@utb.edu.co"],
            "Compañero de clases de Computación e interfaces"),
    Contact("Danna Valentina", "Zualaga", ["3256859895", "6057654321"],
            ["danna@email.com"]),
    Contact("Daniel Eduardo", "Rengifo", [],
            ["daniel@email.com"]),
    Contact("David", "Gonzalez", ["3118734541", "6052345678"],
            ["david@email.com"]),
    Contact("Laura Sofia", "Madrid", ["3218528798"],
            ["laura@email.com"]),
    Contact("Juan Jose", "Cuervo", [],
            ["juan@email.com"]),
    Contact("Camila Fernanda", "Gómez Pérez", ["3109876543", "6053456789"],
            ["camila@gmail.com", "cfperez@work.com"], "Amiga del colegio"),
    Contact("Juan Sebastián", "Rodríguez Nieto", ["3165432187"],
            ["juanrodriguez@email.com", "juanse@utb.edu.co"],
            "Compañero de trabajo en desarrollo"),
    Contact("Valeria Sofía", "Martínez López", ["3245678912"],
            ["valeria.martinez@email.com"], "Prima"),
    Contact("Santiago Andrés", "Ramírez Ortega", ["3147896541"],
            ["santi.ramirez@email.com", "sramirez@empresa.com"], "Vecino"),
    Contact("Mariana Alejandra", "Fernández Castro", ["3223344556"],
            ["mariana.fernandez@email.com"], "Compañera de universidad"),
    Contact("Luis Fernando", "Torres Pineda", ["3001122334"],
            ["luis.torres@email.com", "ltorres@trabajo.com"], "Colega de proyectos"),
    Contact("Andrea Carolina", "Hernández Gil", ["3056677889"],
            ["andrea.hernandez@email.com"], "Amiga del gimnasio"),
    Contact("Carlos Eduardo", "Mendoza Ruiz", ["3189988776", "6054567890"],
            ["carlos.mendoza@email.com", "carlos@empresa.com"], "Jefe en el trabajo"),
    Contact("Paula Daniela", "Salazar Mejía", ["3207766554"],
            ["paula.salazar@email.com"], "Compañera de clases"),
    Contact("Felipe Esteban", "Castillo Vargas", ["3125588996"],
            ["felipe.castillo@email.com", "felipecastillo@work.com"], "Hermano de un amigo"),
    Contact("Gabriela Isabel", "López Cárdenas", ["3012244668"],
            ["gabriela.lopez@email.com"], "Prima segunda"),
    Contact("Ricardo Antonio", "Ortega Salas", ["3234455667"],
            ["ricardo.ortega@email.com", "rortega@universidad.edu"], "Profesor de matemáticas"),
    Contact("Natalia Fernanda", "Pérez Ríos", ["3156677880"],
            ["natalia.perez@email.com", "nfernanda@company.com"], "Amiga de la infancia"),
    Contact("Jorge Andrés", "Ramírez Vargas", [],
            ["jorge.ramirez@email.com"], "Colega en el trabajo"),
    Contact("Daniela Sofía", "Gutiérrez Muñoz", ["3114455667"],
            ["daniela.gutierrez@email.com", "daniela@startup.com"], "Excompañera de universidad"),
    Contact("Alejandro Manuel", "Suárez Pacheco", ["3199988771"],
            ["alejandro.suarez@email.com"], "Tío"),
    Contact("Patricia Elena", "Navarro Acosta", ["3025566778"],
            ["patricia.navarro@email.com", "pnavarro@empresa.com"], "Vecina de la familia"),
    Contact("Fernando Javier", "Herrera Rojas", ["3208899776"],
            ["fernando.herrera@email.com"], "Amigo del barrio"),
    Contact("Vanessa María", "Muñoz Delgado", ["3052233445"],
            ["vanessa.munoz@email.com", "vmuñoz@investigacion.edu"], "Colega en investigación"),
    Contact("Miguel Ángel", "Vega López", ["3146677889"],
            ["miguel.vega@email.com", "mvega@soccerclub.com"], "Compañero de equipo de fútbol"),
    Contact("Lucía Alejandra", "Castaño Torres", ["3177788996"],
            ["lucia.castano@email.com"], "Hermana de un amigo"),
    Contact("Raúl Ernesto", "Mendoza Solís", ["3223344551"],
            ["raul.mendoza@email.com", "rmendoza@startup.co"], "Amigo de la universidad"),
    Contact("Tatiana Beatriz", "Ríos Sánchez", ["3031122335"],
            ["tatiana.rios@email.com", "tbeatriz@tech.com"], "Colega en tecnología"),
    Contact("Esteban Julián", "Peña Fuentes", ["3195566778"],
            ["esteban.pena@email.com"], "Primo lejano"),
    Contact("Carolina Andrea", "Montoya León", ["3047788996"],
            ["carolina.montoya@email.com", "cmontoya@fashion.com"], "Amiga diseñadora"),
    Contact("Sofía Camila", "Delgado Ruiz", ["3203344557"],
            ["sofia.delgado@email.com"], "Hermana de un amigo"),
]
class Validator:
    """Clase para validar únicamente el formato de los datos de entrada"""
    
    # Prefijos para números de telefonía móvil en Colombia
    MOBILE_PREFIXES = [
        '300', '301', '302', '303', '304', '305',  # Claro
        '310', '311', '312', '313', '314', '315', '316', '317', '318', '319',  # Claro
        '320', '321', '322', '323',  # Movistar
        '324', '325', '326',  # Movistar (nuevos)
        '330', '331', '332', '333', '334',  # Movistar (expandido)
        '350', '351', '352',  # Wom
        '360', '361', '362', '363', '364',  # Avantel/Wom
        '370', '371', '372', '373',  # Virgin Mobile
    ]

    # Prefijos de líneas fijas válidos en Colombia
    LANDLINE_PREFIXES = ['601', '602', '604', '605', '606', '607', '608']
    
    @staticmethod
    def validate_phone_format(phone: str) -> tuple[bool, str, str]:
        """
        Valida que el teléfono tenga el formato correcto, detectando automáticamente
        si es móvil o fijo.
        \nretornando:
            tuple: (es_válido, mensaje_error, tipo_numero)
        """
        # Limpiar el número de espacios y caracteres especiales
        cleaned = re.sub(r'\D', '', phone)
        
        # Verificar longitud
        if len(cleaned) != 10:
            return False, "El número debe tener 10 dígitos", 'desconocido'
            
        # Obtener prefijo
        prefix = cleaned[:3]
        
        # Verificar si es móvil
        if prefix in Validator.MOBILE_PREFIXES:
            return True, "", 'movil'
            
        # Verificar si es fijo
        if prefix in Validator.LANDLINE_PREFIXES:
            return True, "", 'fijo'
                
        # Si llegamos aquí, el prefijo no es válido
        return False, f"El número {phone} no es válido en Colombia (prefijo {prefix} desconocido)", 'desconocido'

    @staticmethod
    def format_phone_number(phone: str) -> str:
        """
        Da formato al número telefónico para mejor visualización, 
        detectando automáticamente el tipo
        """
        cleaned = re.sub(r'\D', '', phone)
        if len(cleaned) != 10:
            return cleaned
            
        prefix = cleaned[:3]
        # Formato para móviles: XXX XXX XXXX
        if prefix in Validator.MOBILE_PREFIXES:
            return f"{cleaned[:3]} {cleaned[3:6]} {cleaned[6:]}"
        # Formato para fijos: (XXX) XXX XXXX
        elif prefix in Validator.LANDLINE_PREFIXES:
            return f"({cleaned[:3]}) {cleaned[3:6]} {cleaned[6:]}"
        # Si no se reconoce el tipo, retornar sin formato especial
        return cleaned

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
        self.MAX_CONTACTS_FREE_VERSION = 33

    def update_contact(self, contact: Contact, new_data: dict) -> tuple[bool, Optional[str]]:
        """
        Actualiza un contacto existente.
        Retorna: (éxito, mensaje_de_error)
        """
        try:
            for key, value in new_data.items():
                setattr(contact, key, value)
            return True, None
        except Exception as e:
            return False, str(e)

    def add_contact(self, contact_data: dict) -> tuple[bool, Optional[str], Optional[Contact]]:
        """
        Añade un nuevo contacto.
        Retorna: (éxito, mensaje_de_error, contacto_creado)
        """
        try:
            contact = Contact(**contact_data)
            self.contacts.append(contact)
            return True, None, contact
        except Exception as e:
            return False, str(e), None

    def _is_phone_duplicate(self, phone: str, exclude: Optional[Contact] = None) -> bool:
        """Verifica si el teléfono ya existe"""
        cleaned_phone = re.sub(r'\D', '', phone)
        return any(
            contact != exclude and any(re.sub(r'\D', '', p) == cleaned_phone for p in contact.phones)
            for contact in self.contacts
        )

    def _is_name_duplicate(self, first_name: str, last_name: str, exclude: Optional[Contact] = None) -> bool:
        """Verifica si el nombre completo ya existe"""
        full_name = f"{first_name} {last_name}".strip() 
        normalized_full_name = Validator.normalize_text(full_name) 

        # Verificar si el conjunto de nombre y apellido está duplicado
        return any(
            contact != exclude and 
            Validator.normalize_text(f"{contact.first_name} {contact.last_name}") == normalized_full_name
            for contact in self.contacts
        )

    def search_contacts(self, query: str) -> List[Contact]:
        """Busca contactos por nombre, teléfono, correo electrónico o descripción."""
        if not query.strip():
            return sorted(self.contacts, key=lambda x: x.full_name.lower())

        normalized_query = Validator.normalize_text(query)
        filtered_contacts = []

        for contact in self.contacts:
            # Buscar en el nombre completo
            if normalized_query in Validator.normalize_text(contact.full_name):
                filtered_contacts.append(contact)
                continue
            
            # Buscar en los teléfonos
            if any(normalized_query in Validator.normalize_text(phone) for phone in contact.phones):
                filtered_contacts.append(contact)
                continue
            
            # Buscar en los correos electrónicos
            if any(normalized_query in Validator.normalize_text(email) for email in contact.emails):
                filtered_contacts.append(contact)
                continue
            
            # Buscar en la descripción
            if normalized_query in Validator.normalize_text(contact.description):
                filtered_contacts.append(contact)
                continue
            
        return sorted(filtered_contacts, key=lambda x: x.full_name.lower())
class ContactForm(tk.Toplevel):
    """Clase encargada de gestionar los form para añadir y editar contactos"""
    def __init__(self, parent, contact_manager: ContactManager, on_save: Callable, 
                 contact: Optional[Contact] = None):
        super().__init__(parent)
        self.title("Editar Contacto" if contact else "Nuevo Contacto")
        self.geometry("400x600")
        self.contact = contact
        self.contact_manager = contact_manager
        self.on_save = on_save
        
        self.setup_form()
        if contact:
            self.load_contact_data()

    def setup_form(self):
        # Campos de entrada básicos con límite de 30 caracteres
        self.create_labeled_entry("Nombre:", "first_name", 50, pady=(20,0))
        self.create_labeled_entry("Apellido:", "last_name", 50)

        # Configurar Text widgets con validación
        self.setup_phones_text()
        self.setup_emails_text()
        self.setup_description_text()
        
        # Botón de guardar
        ttk.Button(self, text="Guardar", command=self.save_contact).pack(pady=20)
    def setup_phones_text(self):
        ttk.Label(self, text="Teléfonos (uno por línea, max 10):").pack(padx=20, pady=(10,0))
        self.phones_text = tk.Text(self, height=4)
        self.phones_text.pack(padx=20)
        self.phones_text.bind('<Key>', self.on_phone_key)
        self.phones_text.bind('<<Modified>>', self.on_phones_modified)

    def setup_emails_text(self):
        ttk.Label(self, text="Emails (uno por línea, max 50):").pack(padx=20, pady=(10,0))
        self.emails_text = tk.Text(self, height=4)
        self.emails_text.pack(padx=20)
        self.emails_text.bind('<Key>', self.on_email_key)
        self.emails_text.bind('<<Modified>>', self.on_emails_modified)

    def setup_description_text(self):
        ttk.Label(self, text="Descripción (max 200):").pack(padx=20, pady=(10,0))
        self.description_text = tk.Text(self, height=4)
        self.description_text.pack(padx=20)
        self.description_text.bind('<<Modified>>', self.on_description_modified)

    def create_labeled_entry(self, label: str, attr_name: str, max_length: int, **kwargs):
        ttk.Label(self, text=label).pack(padx=20, **kwargs)
        validate_cmd = (self.register(self.validate_entry_length), '%P', str(max_length))
        entry = ttk.Entry(self, validate="key", validatecommand=validate_cmd)
        entry.pack(padx=20)
        setattr(self, f"{attr_name}_entry", entry)

    def validate_entry_length(self, new_text, max_length):
        return len(new_text) <= int(max_length)

    def on_phone_key(self, event):
        # Permitir teclas especiales (Backspace, Delete, flechas, etc.)
        allowed_keys = {'BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Return'}
        if event.keysym in allowed_keys:
            return

        # Validar el carácter ingresado
        char = event.char
        if not re.match(r'^[\d\s\+\-\(\)]$', char): 
            return "break"

        # Validar longitud máxima por línea
        line = self.phones_text.index("insert").split('.')[0]
        current_line = self.phones_text.get(f"{line}.0", f"{line}.end")
        if len(current_line) >= 10:
            return "break"

    def on_email_key(self, event):
        allowed = {'BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Return'}
        if event.keysym in allowed:
            return
        line = self.emails_text.index("insert").split('.')[0]
        current_line = self.emails_text.get(f"{line}.0", f"{line}.end")
        if len(current_line) >= 50:
            return "break"

    def on_description_modified(self, event):
        if self.description_text.edit_modified():
            content = self.description_text.get("1.0", "end-1c")
            if len(content) > 200:
                self.description_text.delete("1.0", "end")
                self.description_text.insert("1.0", content[:200])
                messagebox.showwarning("Límite excedido", "Descripción máxima: 200 caracteres")
            self.description_text.edit_modified(False)

    def on_phones_modified(self, event):
        if self.phones_text.edit_modified():
            lines = self.phones_text.get("1.0", "end-1c").split('\n')
            corrected = [line[:20] for line in lines]
            if any(len(line) > 20 for line in lines):
                self.phones_text.delete("1.0", "end")
                self.phones_text.insert("1.0", '\n'.join(corrected))
                messagebox.showwarning("Límite excedido", "Máximo 20 caracteres por teléfono")
            self.phones_text.edit_modified(False)

    def on_emails_modified(self, event):
        if self.emails_text.edit_modified():
            lines = self.emails_text.get("1.0", "end-1c").split('\n')
            corrected = [line[:50] for line in lines]
            if any(len(line) > 50 for line in lines):
                self.emails_text.delete("1.0", "end")
                self.emails_text.insert("1.0", '\n'.join(corrected))
                messagebox.showwarning("Límite excedido", "Máximo 50 caracteres por email")
            self.emails_text.edit_modified(False)
    
    def load_contact_data(self):
        self.first_name_entry.insert(0, self.contact.first_name)
        self.last_name_entry.insert(0, self.contact.last_name)
        self.phones_text.insert('1.0', '\n'.join(self.contact.phones))
        self.emails_text.insert('1.0', '\n'.join(self.contact.emails))
        self.description_text.insert('1.0', self.contact.description)

    def get_form_data(self):
        return {
            'first_name': self.first_name_entry.get().strip(),
            'last_name': self.last_name_entry.get().strip(),
            'phones': [p.strip() for p in self.phones_text.get('1.0', tk.END).split('\n') if p.strip()],
            'emails': [e.strip() for e in self.emails_text.get('1.0', tk.END).split('\n') if e.strip()],
            'description': self.description_text.get('1.0', tk.END).strip()
        }
    def validate_and_process_data(self, data: dict) -> tuple[bool, Optional[str], List[str]]:
        """
        Valida y procesa los datos del formulario.
        Retorna: (es_válido, mensaje_error, advertencias)
        """
        warnings = []

        # Validaciones críticas que impiden guardar
        if not data['first_name'] and not data['last_name']:
            return False, "Debe ingresar al menos un nombre o un apellido", []

        if not data['phones'] and not data['emails']:
            return False, "Debe ingresar al menos un teléfono o un correo electrónico", []

        # Validar formato de emails (crítico)
        for email in data['emails']:
            if not Validator.validate_email_format(email):
                return False, f"Email inválido: {email}", []

        # Validar formato de teléfonos (advertencia)
        for phone in data['phones']:
            is_valid, error_msg, phone_type = Validator.validate_phone_format(phone)
            if not is_valid:
                warnings.append(error_msg)

        # Verificar duplicados (advertencia)
        if self.contact_manager._is_name_duplicate(data['first_name'], data['last_name'], exclude=self.contact):
            warnings.append("Ya existe un contacto con este nombre y apellido")

        for phone in data['phones']:
            if self.contact_manager._is_phone_duplicate(phone, exclude=self.contact):
                warnings.append(f"El teléfono {phone} ya existe en otro contacto")

        return True, None, warnings
    def save_contact(self):
        # Obtener los datos del formulario
        data = self.get_form_data()

        # Validar y procesar los datos
        is_valid, error_msg, warnings = self.validate_and_process_data(data)

        # Si hay un error crítico, mostrar mensaje y salir
        if not is_valid:
            messagebox.showerror("Error", error_msg)
            return

        # Si hay advertencias, preguntar al usuario si desea continuar
        if warnings:
            warning_message = "\n".join(warnings) + "\n\n¿Desea continuar?"
            if not messagebox.askyesno("Advertencias", warning_message):
                return  # El usuario decidió no continuar

        # Guardar el contacto
        if self.contact:
            # Actualizar contacto existente
            success, error = self.contact_manager.update_contact(self.contact, data)
            if not success:
                messagebox.showerror("Error", error)
                return
        else:
            # Crear nuevo contacto
            success, error, new_contact = self.contact_manager.add_contact(data)
            if not success:
                messagebox.showerror("Error", error)
                return
            self.contact = new_contact

        # Notificar éxito y cerrar el formulario
        self.on_save(self.contact)
        self.destroy()
        messagebox.showinfo("Éxito", "Contacto guardado correctamente")
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
        self.detail_phones_label = ttk.Label(info_frame)
        self.detail_phones_label.pack(anchor=tk.W, padx=20)
        
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
        # Verificar el límite de contactos antes de abrir el formulario
        if len(self.contact_manager.contacts) >= self.contact_manager.MAX_CONTACTS_FREE_VERSION:
            messagebox.showerror("Versión gratuita de prueba", "Ha alcanzado el límite de contactos de la versión gratuita de prueba.")
            return
        ContactForm(self.root, self.contact_manager, self.handle_contact_save)

    def edit_contact(self):
        if not self.selected_contact:
            return
        ContactForm(self.root, self.contact_manager, self.handle_contact_save, self.selected_contact)
    def create_contact_item(self, contact: Contact, parent):
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

        primary_info = Validator.format_phone_number(contact.primary_phone) if contact.phones else contact.emails[0] if contact.emails else "Sin información"
        phone_label = ttk.Label(info_frame,
                              text=primary_info,
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
        
        # Limpiar y actualizar teléfonos
        for widget in self.detail_phones_label.winfo_children():
            widget.destroy()
        for phone in contact.phones:
            ttk.Label(self.detail_phones_label, text=phone).pack(anchor=tk.W)
        
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
        for widget in self.detail_phones_label.winfo_children():
            widget.destroy()
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