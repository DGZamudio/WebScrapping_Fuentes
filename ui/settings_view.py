import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk
import json
from db.memory import Memory
from scrappers import SCRAPERS

SETTINGS_PATH = Path("config") / "settings.json"

class SettingsView(tk.Frame):
    """Example settings view - add your configuration options here."""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.source_vars = {}
        self._build()
        self.load_settings()

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
        self.end_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.end_date.pack(fill="x")

        # Save button
        tk.Button(dates_frame, text="Guardar", command=self._on_save).pack(anchor="w", pady=(10, 0))

        sources_frame = tk.LabelFrame(self, text="Fuentes a Descargar", padx=10, pady=10)
        sources_frame.pack(fill="x", pady=10)

        for source in SCRAPERS.keys():
            var = tk.BooleanVar(value=True)
            chk = tk.Checkbutton(sources_frame, text=source, variable=var)
            chk.pack(anchor="w")
            self.source_vars[source] = var

        tk.Button(sources_frame, text="Guardar", command=self._on_save).pack(anchor="w", pady=(10, 0))

    def _on_save(self):
        try:
            self.save_settings()
            if self.controller:
                self.controller.log("✓ Configuración guardada")
        except Exception as e:
            if self.controller:
                self.controller.log(f"Error guardando configuración: {e}")

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
        
    def save_settings(self):
        """Persist current settings to `config/settings.json`."""
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "start": self.start_date.get(),
            "end": self.end_date.get(),
            "enabled_sources": self.get_enabled_sources(),
        }
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_settings(self):
        """Load persisted settings (if present) and apply to widgets."""
        try:
            if SETTINGS_PATH.exists():
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                start = data.get("start")
                end = data.get("end")
                enabled = data.get("enabled_sources")

                if start:
                    self.start_date.delete(0, "end")
                    self.start_date.insert(0, start)
                if end:
                    self.end_date.delete(0, "end")
                    self.end_date.insert(0, end)
                if enabled and isinstance(enabled, list):
                    for k, var in self.source_vars.items():
                        var.set(k in enabled)
        except Exception:
            # fail silently; UI should still work
            pass