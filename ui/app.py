import tkinter as tk

from ui.dashboard import DashBoard
from .nav_menu import NavMenu
from .console import Console
from .settings_view import SettingsView
from .status_bar import StatusBar


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Descarga Automática WebScrapping")
        self.geometry("900x600")

        # Contenedor principal nav + content
        self.container = tk.Frame(self, bg="#dde4e6")
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)

        # Menu de navegación a la izquierda
        self.nav = NavMenu(self.container, controller=self)
        self.nav.grid(row=0, column=0, sticky="nsew")

        # Area de contenido a la derecha
        self.content_area = tk.Frame(self.container)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # Diccionario para almacenar las vistas y su estado
        self.views = {}
        self.current_view = None

        # Crear y registrar las vistas principales
        self.dashboard = DashBoard(self.content_area, self)
        self.register_view("dashboard", "Dashboard", self.dashboard)

        self.console = Console(self.content_area, self)
        self.register_view("consola", "Consola", self.console)

        self.settings_view = SettingsView(self.content_area, self)
        self.register_view("configuracion", "Configuración", self.settings_view)

        # Vista por defecto al iniciar la aplicación
        self.show_view("dashboard")

        # Barra de estado en la parte inferior
        self.status = StatusBar(self)
        self.status.pack(fill="x", side="bottom")

        self._run_callback = None

    def register_view(self, name, label, view_widget):
        """Registrar una nueva vista.
        
        Args:
            name: nombre único para la vista (ej. 'home', 'settings')
            label: Nombre a mostrar en el menú de navegación
            view_widget: instancia del widget de la vista (ej. MainFrame, SettingsView)
        """
        self.views[name] = view_widget
        
        # Añadir botón al menú de navegación para esta vista
        self.nav.add_button(name, label, lambda: self.show_view(name))

    def show_view(self, name):
        """Cambiar a otra vista."""
        if name not in self.views:
            return

        # Esconder vista actual
        if self.current_view and self.current_view in self.views:
            self.views[self.current_view].grid_remove()

        # Mostrar nueva vista
        view = self.views[name]
        view.grid(row=0, column=0, sticky="nsew")
        self.current_view = name

        # Encender el botón activo en el menú de navegación
        self.nav.set_active(name)

    def set_run_callback(self, cb):
        self._run_callback = cb
        self.console.set_run_callback(cb)

    def set_running(self, running: bool):
        """Set the app running state; updates console buttons."""
        try:
            self.console.set_running(running)
        except Exception:
            pass

    def log(self, msg):
        self.console.log(msg)
        self.status.set_status(msg)

    def update_stats(self, count: int):
        """Broadcast stats to any view that implements `update_total(count)`.

        This allows views (like `DashBoard`) to be refreshed when the DB changes.
        """
        for view in self.views.values():
            if hasattr(view, "update_total"):
                try:
                    view.update_total(count)
                except Exception:
                    # ignore view update errors to keep UI stable
                    pass
