import tkinter as tk

from ui.dashboard import DashBoard
from ui.theme import COLORS
from .nav_menu import NavMenu
from .settings_view import SettingsView
from .stats_view import StatsView
from .status_bar import StatusBar


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IURISYNC — Descarga Automática de Documentos Legales")
        self.geometry("1100x700")
        self.minsize(920, 600)
        self.state("zoomed")
        self.configure(bg=COLORS["sidebar"])

        # Main container: sidebar | content
        self.container = tk.Frame(self, bg=COLORS["bg"])
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)

        self.nav = NavMenu(self.container, controller=self)
        self.nav.grid(row=0, column=0, sticky="nsew")

        self.content_area = tk.Frame(self.container, bg=COLORS["bg"])
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        self.views = {}
        self.current_view = None

        self.dashboard = DashBoard(self.content_area, self)
        self.register_view("dashboard", "Dashboard", self.dashboard)

        self.settings_view = SettingsView(self.content_area, self)
        self.register_view("configuracion", "Configuración", self.settings_view)

        self.stats_view = StatsView(self.content_area, self, port=None)
        self.register_view("estadisticas", "Estadísticas", self.stats_view)

        self.show_view("dashboard")

        self.status = StatusBar(self)
        self.status.pack(fill="x", side="bottom")

        self._run_callback = None

    def set_stats_port(self, port: int | None) -> None:
        """Recrea StatsView con el puerto del servidor Flask."""
        old = self.views.get("estadisticas")
        if old:
            old.destroy()
        self.stats_view = StatsView(self.content_area, self, port=port)
        self.views["estadisticas"] = self.stats_view

    def register_view(self, name, label, view_widget):
        self.views[name] = view_widget
        self.nav.add_button(name, label, lambda: self.show_view(name))

    def show_view(self, name):
        if name not in self.views:
            return
        if self.current_view and self.current_view in self.views:
            self.views[self.current_view].grid_remove()
        self.views[name].grid(row=0, column=0, sticky="nsew")
        self.current_view = name
        self.nav.set_active(name)

    def set_run_callback(self, cb):
        self._run_callback = cb
        self.dashboard.set_run_callback(cb)

    def set_running(self, running: bool):
        for view in self.views.values():
            if hasattr(view, "set_running"):
                try:
                    view.set_running(running)
                except Exception:
                    pass

    def log(self, msg):
        self.dashboard.log(msg)
        self.status.set_status(msg)

    def update_stats(self, count: int):
        for view in self.views.values():
            if hasattr(view, "update_total"):
                try:
                    view.update_total(count)
                except Exception:
                    pass
