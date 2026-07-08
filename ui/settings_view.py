import subprocess
import tkinter as tk
from pathlib import Path
import json

import customtkinter as ctk

from scrappers import SCRAPERS
from setup_scheduler import registrar_tarea, _validar_hora
from ui.theme import COLORS, FONTS, CORNER_RADIUS, BORDER_WIDTH
from ui.list_filter import reflow_rows

SETTINGS_PATH = Path("config") / "settings.json"


class _CollapsibleSection(ctk.CTkFrame):
    """Collapsible group row for grouping related sources."""

    def __init__(self, parent, text, count, label="fuentes", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._expanded = False

        hdr = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        hdr.pack(fill="x", pady=(6, 0))

        self._arrow = ctk.CTkLabel(
            hdr, text="▶", text_color=COLORS["accent"], fg_color="transparent",
            font=("Segoe UI", 8, "bold"), width=16, cursor="hand2",
        )
        self._arrow.pack(side="left")

        ctk.CTkLabel(
            hdr, text=text, text_color=COLORS["text_secondary"], fg_color="transparent",
            font=FONTS["body_bold"], anchor="w", cursor="hand2",
        ).pack(side="left")

        ctk.CTkLabel(
            hdr, text=f"{count} {label}",
            text_color=COLORS["text_muted"], fg_color="transparent",
            font=FONTS["caption"],
        ).pack(side="left", padx=(8, 0), pady=(1, 0))

        self.content = ctk.CTkFrame(self, fg_color="transparent")

        for widget in (hdr, self._arrow):
            widget.bind("<Button-1>", self._toggle)

    def _toggle(self, _=None):
        if self._expanded:
            self._force_collapse()
        else:
            self._force_expand()

    def _force_expand(self):
        if not self._expanded:
            self.content.pack(fill="x", padx=(16, 0), pady=(4, 0))
            self._arrow.configure(text="▼")
            self._expanded = True

    def _force_collapse(self):
        if self._expanded:
            self.content.pack_forget()
            self._arrow.configure(text="▶")
            self._expanded = False


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self.controller = controller
        self.source_vars: dict[str, tk.BooleanVar] = {}
        self._all_vars: list[tk.BooleanVar] = []
        self._sections: list[dict] = []
        self._flat_rows: list[tuple[str, ctk.CTkFrame]] = []
        self._build()
        self.load_settings()

    # ------------------------------------------------------------------ build

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 0))

        ctk.CTkLabel(
            header, text="Configuración",
            text_color=COLORS["text"], fg_color="transparent", font=FONTS["h1"],
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="Fuentes activas y opciones de descarga",
            text_color=COLORS["text_muted"], fg_color="transparent", font=FONTS["small"],
        ).pack(side="right", pady=(10, 0))

        ctk.CTkFrame(self, fg_color=COLORS["card_border"], height=1, corner_radius=0).pack(
            fill="x", padx=24, pady=(14, 0)
        )

        body = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=0, pady=0)

        self._build_scheduler_card(body)

        card = self._card(body)
        card.pack(fill="x", padx=24, pady=(0, 24))

        card_hdr = ctk.CTkFrame(card, fg_color="transparent")
        card_hdr.pack(fill="x", padx=20, pady=(18, 0))

        ctk.CTkLabel(
            card_hdr, text="Fuentes a descargar",
            text_color=COLORS["text"], fg_color="transparent", font=FONTS["h3"],
        ).pack(side="left")

        self._sel_all_lbl = ctk.CTkLabel(
            card_hdr, text="Seleccionar todo",
            text_color=COLORS["accent"], fg_color="transparent",
            font=FONTS["small"], cursor="hand2",
        )
        self._sel_all_lbl.pack(side="right", pady=(2, 0))
        self._sel_all_lbl.bind("<Button-1>", self._toggle_all)

        ctk.CTkFrame(card, fg_color=COLORS["card_border"], height=1, corner_radius=0).pack(
            fill="x", padx=20, pady=(12, 0)
        )

        search_row = ctk.CTkFrame(card, fg_color="transparent")
        search_row.pack(fill="x", padx=20, pady=(12, 0))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter(self._search_var.get()))
        ctk.CTkEntry(
            search_row, textvariable=self._search_var,
            placeholder_text="Buscar fuente...",
            fg_color=COLORS["bg"], border_color=COLORS["card_border"],
            text_color=COLORS["text"], corner_radius=CORNER_RADIUS,
        ).pack(fill="x")

        chk_body = ctk.CTkFrame(card, fg_color="transparent")
        chk_body.pack(fill="both", expand=True, padx=20, pady=(12, 0))

        trib_adm = {}
        trib_sup = {}
        juzgados = {}
        others = {}
        for src in SCRAPERS:
            if src.startswith("Tribunal Administrativo"):
                trib_adm[src] = SCRAPERS[src]
            elif src.startswith("Tribunal Superior"):
                trib_sup[src] = SCRAPERS[src]
            elif src.startswith("Juzgado"):
                juzgados[src] = SCRAPERS[src]
            else:
                others[src] = SCRAPERS[src]

        for src in others:
            var = tk.BooleanVar(value=True)
            row = self._add_checkbox(chk_body, src, var)
            self.source_vars[src] = var
            self._all_vars.append(var)
            self._flat_rows.append((src, row))

        self._add_section(chk_body, "Tribunales Administrativos", trib_adm, "tribunales")
        self._add_section(chk_body, "Tribunales Superiores", trib_sup, "tribunales")
        self._add_section(chk_body, "Juzgados", juzgados, "juzgados")

        ctk.CTkFrame(card, fg_color=COLORS["card_border"], height=1, corner_radius=0).pack(
            fill="x", padx=20, pady=(16, 0)
        )
        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(10, 16))

        ctk.CTkLabel(
            footer, text="Los cambios se aplican en la próxima ejecución.",
            text_color=COLORS["text_muted"], fg_color="transparent", font=FONTS["caption"],
        ).pack(side="left", pady=(2, 0))

        ctk.CTkButton(
            footer, text="Guardar configuración",
            command=self._on_save,
            fg_color=COLORS["btn_primary"], hover_color=COLORS["btn_primary_hover"],
            text_color=COLORS["btn_text"], font=FONTS["body_bold"],
            corner_radius=CORNER_RADIUS,
        ).pack(side="right")

    def _add_section(self, parent, title, sources: dict, label: str):
        if not sources:
            return
        ctk.CTkFrame(parent, fg_color=COLORS["card_border"], height=1, corner_radius=0).pack(
            fill="x", pady=(10, 4)
        )
        section = _CollapsibleSection(parent, text=title, count=len(sources), label=label)
        section.pack(fill="x")

        rows = []
        for src in sorted(sources):
            var = tk.BooleanVar(value=True)
            row = self._add_checkbox(section.content, src, var, indent=True)
            self.source_vars[src] = var
            self._all_vars.append(var)
            rows.append((src, row))

        self._sections.append({"frame": section, "rows": rows})

    # -------------------------------------------------------- scheduler card

    def _build_scheduler_card(self, parent):
        card = self._card(parent)
        card.pack(fill="x", padx=24, pady=(24, 12))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(18, 0))
        ctk.CTkLabel(
            hdr, text="Automatización",
            text_color=COLORS["text"], fg_color="transparent", font=FONTS["h3"],
        ).pack(side="left")

        ctk.CTkFrame(card, fg_color=COLORS["card_border"], height=1, corner_radius=0).pack(
            fill="x", padx=20, pady=(12, 0)
        )

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=20, pady=(12, 0))

        ctk.CTkLabel(
            body, text="Hora de ejecución diaria:",
            text_color=COLORS["text_secondary"], fg_color="transparent", font=FONTS["body"],
        ).pack(side="left")

        hora_actual = self._get_hora_actual()
        hh, mm = hora_actual.split(":")

        self._hora_hh = tk.StringVar(value=hh)
        self._hora_mm = tk.StringVar(value=mm)

        # CustomTkinter no incluye un Spinbox nativo; se mantiene tk.Spinbox
        # reskineado, igual que tkcalendar.DateEntry en ui/dashboard.py.
        tk.Spinbox(
            body, from_=0, to=23, textvariable=self._hora_hh,
            width=3, format="%02.0f", wrap=True,
            font=FONTS["body"], relief="flat",
            bg=COLORS["bg"], fg=COLORS["text"],
            buttonbackground=COLORS["bg"],
        ).pack(side="left", padx=(10, 2))

        ctk.CTkLabel(
            body, text=":", text_color=COLORS["text"], fg_color="transparent", font=FONTS["body_bold"],
        ).pack(side="left")

        tk.Spinbox(
            body, from_=0, to=59, textvariable=self._hora_mm,
            width=3, format="%02.0f", wrap=True,
            font=FONTS["body"], relief="flat",
            bg=COLORS["bg"], fg=COLORS["text"],
            buttonbackground=COLORS["bg"],
        ).pack(side="left", padx=(2, 10))

        ctk.CTkButton(
            body, text="Programar",
            command=self._on_programar,
            fg_color=COLORS["btn_primary"], hover_color=COLORS["btn_primary_hover"],
            text_color=COLORS["btn_text"], font=FONTS["body_bold"],
            corner_radius=CORNER_RADIUS,
        ).pack(side="left")

        ctk.CTkFrame(card, fg_color=COLORS["card_border"], height=1, corner_radius=0).pack(
            fill="x", padx=20, pady=(12, 0)
        )

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(8, 14))

        self._sched_status = ctk.CTkLabel(
            footer, text=self._estado_tarea(),
            text_color=COLORS["text_muted"], fg_color="transparent", font=FONTS["caption"],
        )
        self._sched_status.pack(side="left")

    def _get_hora_actual(self) -> str:
        try:
            r = subprocess.run(
                ["schtasks", "/Query", "/TN", "IURISYNC - Scraping Diario", "/FO", "LIST"],
                capture_output=True, text=True,
            )
            for line in r.stdout.splitlines():
                if "Hora de inicio" in line or "Start Time" in line:
                    partes = line.split(":", 1)
                    if len(partes) == 2:
                        raw = partes[1].strip()
                        t = raw.split(" ")[0]
                        h, m = t.split(":")[:2]
                        return f"{int(h):02d}:{int(m):02d}"
        except Exception:
            pass
        return "06:00"

    def _estado_tarea(self) -> str:
        try:
            r = subprocess.run(
                ["schtasks", "/Query", "/TN", "IURISYNC - Scraping Diario", "/FO", "LIST"],
                capture_output=True, text=True,
            )
            if r.returncode == 0:
                hora = self._get_hora_actual()
                return f"Tarea activa: {hora} diariamente"
        except Exception:
            pass
        return "No programada — haz clic en Programar para activar"

    def _on_programar(self):
        try:
            hora = _validar_hora(f"{self._hora_hh.get()}:{self._hora_mm.get()}")
            registrar_tarea(hora)
            self._sched_status.configure(
                text=f"Tarea activa: {hora} diariamente",
                text_color=COLORS["success"],
            )
            if self.controller:
                self.controller.log(f"✓ Ejecución automática programada a las {hora}")
        except Exception as e:
            self._sched_status.configure(text=f"Error: {e}", text_color=COLORS["error"])
            if self.controller:
                self.controller.log(f"Error al programar tarea: {e}")

    # ----------------------------------------------------------------- helpers

    def _card(self, parent):
        return ctk.CTkFrame(
            parent, fg_color=COLORS["card"],
            border_color=COLORS["card_border"], border_width=BORDER_WIDTH,
            corner_radius=CORNER_RADIUS,
        )

    def _add_checkbox(self, parent, text, var, indent=False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)

        if indent:
            ctk.CTkFrame(row, fg_color="transparent", width=4, height=1).pack(side="left")

        ctk.CTkCheckBox(
            row, text=text, variable=var,
            text_color=COLORS["text"] if not indent else COLORS["text_secondary"],
            fg_color=COLORS["btn_primary"], hover_color=COLORS["btn_primary_hover"],
            font=FONTS["body"] if not indent else FONTS["small"],
            checkbox_width=18, checkbox_height=18,
        ).pack(side="left", fill="x")

        return row

    def _toggle_all(self, _=None):
        any_off = any(not v.get() for v in self._all_vars)
        new_val = True if any_off else False
        for v in self._all_vars:
            v.set(new_val)
        self._sel_all_lbl.configure(
            text="Seleccionar todo" if not new_val else "Deseleccionar todo"
        )

    # -------------------------------------------------------------- filtering

    def _apply_filter(self, query: str):
        reflow_rows(self._flat_rows, query)
        q = query.strip().lower()
        for section in self._sections:
            has_match = any(q in name.lower() for name, _ in section["rows"])
            reflow_rows(section["rows"], query)
            if q and has_match:
                section["frame"]._force_expand()
            elif not q:
                section["frame"]._force_collapse()

    # -------------------------------------------------------------------- API

    def _on_save(self):
        try:
            self.save_settings()
            if self.controller:
                self.controller.log("✓ Configuración guardada")
        except Exception as e:
            if self.controller:
                self.controller.log(f"Error guardando configuración: {e}")

    def get_dates(self):
        return {}

    def get_enabled_sources(self):
        try:
            return [k for k, v in self.source_vars.items() if v.get()]
        except Exception:
            return list(SCRAPERS.keys())

    def get_source_options(self):
        return {}

    def save_settings(self):
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {"enabled_sources": self.get_enabled_sources()}
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_settings(self):
        try:
            if SETTINGS_PATH.exists():
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                enabled = data.get("enabled_sources")
                if isinstance(enabled, list):
                    for k, var in self.source_vars.items():
                        var.set(k in enabled)
                self._update_sel_all_label()
        except Exception:
            pass

    def _update_sel_all_label(self):
        all_on = all(v.get() for v in self._all_vars)
        self._sel_all_lbl.configure(
            text="Deseleccionar todo" if all_on else "Seleccionar todo"
        )
