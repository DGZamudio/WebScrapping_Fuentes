import tkinter as tk
from tkinter import ttk
from db.memory import Memory
from scrappers import SCRAPERS


class SettingsView(tk.Frame):
    """Example settings view - add your configuration options here."""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self._build()

    def _build(self):
        title = tk.Label(self, text="Configuración", font=("Arial", 14, "bold"))
        title.pack(anchor="w", pady=10)

        # Date range settings
        dates_frame = tk.LabelFrame(self, text="Rango de Fechas", padx=10, pady=10)
        dates_frame.pack(fill="x", pady=10)

        tk.Label(dates_frame, text="Fecha Inicio (YYYY-MM-DD):").pack(anchor="w")
        self.start_date = tk.Entry(dates_frame, width=30)
        # Prefill start with last inserted date from DB if available
        try:
            last = Memory().get_last_inserted()
        except Exception:
            last = None
        if last:
            self.start_date.insert(0, last)
        else:
            self.start_date.insert(0, "2026-02-01")
        self.start_date.pack(fill="x", pady=(0, 10))

        tk.Label(dates_frame, text="Fecha Fin (YYYY-MM-DD):").pack(anchor="w")
        self.end_date = tk.Entry(dates_frame, width=30)
        # default end to today
        from datetime import datetime
        self.end_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.end_date.pack(fill="x")

        # Save button
        tk.Button(dates_frame, text="Guardar", command=self._on_save).pack(anchor="w", pady=(10, 0))

        sources_frame = tk.LabelFrame(self, text="Fuentes a Descargar", padx=10, pady=10)
        sources_frame.pack(fill="x", pady=10)
        # store BooleanVar for each source so we can read selection later
        self.source_vars = {}
        for source in SCRAPERS.keys():
            var = tk.BooleanVar(value=True)
            chk = tk.Checkbutton(sources_frame, text=source, variable=var)
            chk.pack(anchor="w")
            self.source_vars[source] = var

    def _on_save(self):
        if self.controller:
            self.controller.log(f"✓ Configuración guardada")

    def get_dates(self):
        """Return the configured date range."""
        return {
            "start": self.start_date.get(),
            "end": self.end_date.get(),
        }

    def get_enabled_sources(self):
        """Return list of enabled scraper keys (those checked in the UI)."""
        try:
            return [k for k, v in self.source_vars.items() if v.get()]
        except Exception:
            return list(SCRAPERS.keys())
