import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk
import json
from db.memory import Memory
from scrappers import SCRAPERS, discover_tribunales

SETTINGS_PATH = Path("config") / "settings.json"


class CollapsibleFrame(tk.Frame):
    """A collapsible frame widget that can expand/collapse its content."""

    def __init__(self, parent, text="", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.show = tk.BooleanVar(value=False)

        # Header button
        self.toggle_button = tk.Button(
            self,
            text=f"▶ {text}",
            command=self.toggle,
            relief="flat",
            bg=self.cget("bg"),
            fg="#466a80",
            font=("Arial", 10, "bold"),
            anchor="w",
            padx=5
        )
        self.toggle_button.pack(fill="x")

        # Content frame
        self.content_frame = tk.Frame(self, bg=self.cget("bg"))
        self.content_frame.pack(fill="x", expand=True)
        self.content_frame.pack_forget()  # Hide initially

    def toggle(self):
        if self.show.get():
            self.content_frame.pack_forget()
            self.toggle_button.config(text=self.toggle_button.cget("text").replace("▼", "▶"))
            self.show.set(False)
        else:
            self.content_frame.pack(fill="x", expand=True, after=self.toggle_button)
            self.toggle_button.config(text=self.toggle_button.cget("text").replace("▶", "▼"))
            self.show.set(True)


class SettingsView(tk.Frame):
    """Example settings view - add your configuration options here."""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.source_vars = {}
        self.ts_details_var = tk.BooleanVar(value=True)
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
        sources_frame.pack(fill="both", expand=True, pady=10)

        # Create a Canvas with Scrollbar for scrollable sources
        canvas = tk.Canvas(sources_frame, height=200, bg=sources_frame.cget("bg"), highlightthickness=0)
        scrollbar = ttk.Scrollbar(sources_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=sources_frame.cget("bg"))

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Discover all available tribunales before showing sources
        try:
            discover_tribunales()
        except Exception as e:
            print(f"Error discovering tribunales: {e}")

        # Separate tribunales from other sources
        tribunales_sources = {}
        other_sources = {}

        for source in SCRAPERS.keys():
            if source.startswith("Tribunal") and source != "Tribunales Superiores":
                tribunales_sources[source] = SCRAPERS[source]
            else:
                other_sources[source] = SCRAPERS[source]

        # Add non-tribunal sources first
        for source in other_sources.keys():
            var = tk.BooleanVar(value=True)
            chk = tk.Checkbutton(scrollable_frame, text=source, variable=var, bg=scrollable_frame.cget("bg"))
            chk.pack(anchor="w")
            self.source_vars[source] = var

            if source == "Tribunales Superiores":
                sub = tk.Checkbutton(
                    scrollable_frame,
                    text="   ↳ Incluir archivos detallados (más lento)",
                    variable=self.ts_details_var,
                    bg=scrollable_frame.cget("bg"),
                    font=("Arial", 9),
                )
                sub.pack(anchor="w", padx=(15, 0))

        # Add collapsible tribunales section
        if tribunales_sources:
            separator = tk.Frame(scrollable_frame, bg="#b2b1b1", height=1)
            separator.pack(fill="x", padx=4, pady=8)

            tribunales_collapsible = CollapsibleFrame(scrollable_frame, text="Tribunales Administrativos", bg=scrollable_frame.cget("bg"))
            tribunales_collapsible.pack(fill="x", pady=(0, 5))

            for source in sorted(tribunales_sources.keys()):
                var = tk.BooleanVar(value=True)
                chk = tk.Checkbutton(
                    tribunales_collapsible.content_frame,
                    text=source.replace("Tribunal - ", ""),
                    variable=var,
                    bg=tribunales_collapsible.content_frame.cget("bg")
                )
                chk.pack(anchor="w", padx=(20, 0))  # Indent slightly
                self.source_vars[source] = var

        button_frame = tk.Frame(sources_frame, bg=sources_frame.cget("bg"))
        button_frame.pack(anchor="w", pady=(10, 0))
        tk.Button(button_frame, text="Guardar", command=self._on_save).pack(anchor="w")

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

    def get_source_options(self):
        """Return per-source configuration options."""
        return {
            "Tribunales Superiores": {
                "include_details": self.ts_details_var.get(),
            }
        }
        
    def save_settings(self):
        """Persist current settings to `config/settings.json`."""
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "start": self.start_date.get(),
            "end": self.end_date.get(),
            "enabled_sources": self.get_enabled_sources(),
            "ts_include_details": self.ts_details_var.get(),
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
                if "ts_include_details" in data:
                    self.ts_details_var.set(data["ts_include_details"])
        except Exception:
            # fail silently; UI should still work
            pass