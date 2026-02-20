import tkinter as tk


class NavMenu(tk.Frame):
    """Barra de navegación para cambiar entre vistas."""

    def __init__(self, parent, controller=None):
        super().__init__(parent, bg="#fff", width=180)
        self.controller = controller
        self.pack_propagate(False)
        self.pack(fill="y", side="left")

        self.buttons = {}
        self.active_button = None
        self._build()

    def _build(self):
        """Construir la barra de navegación."""
        title = tk.Label(
            self, text="IURISYNC", bg="#fff", fg="#466a80", font=("Arial", 14, "bold")
        )
        title.pack(fill="x", padx=8, pady=12)

        separator = tk.Frame(self, bg="#b2b1b1", height=1)
        separator.pack(fill="x", padx=4, pady=4)

    def add_button(self, name, label, callback):
        """Añadir un botón de navegación.
        
        Args:
            name: nombre único para la vista (ej. 'home', 'settings')
            label: Texto a mostrar en el botón
            callback: Función a llamar cuando se hace clic en el botón
        """
        btn = tk.Button(
            self,
            text=label,
            bg="#fff",
            fg="#466a80",
            activebackground="#363c40",
            activeforeground="#fff",
            border=0,
            font=("Arial", 11),
            padx=8,
            pady=10,
            command=lambda: self._on_button_click(name, callback),
        )
        btn.pack(fill="x", padx=4, pady=2)
        self.buttons[name] = btn

    def set_active(self, name):
        """Cambia el botón activo en la barra de navegación."""
        if self.active_button:
            self.buttons[self.active_button].config(bg="#fff", fg="#466a80")
        self.active_button = name
        if name in self.buttons:
            self.buttons[name].config(bg="#363c40", fg="#fff")

    def _on_button_click(self, name, callback):
        """Función para cuando se hace click en el botón."""
        self.set_active(name)
        callback()
