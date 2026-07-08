import subprocess
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import json

from scrappers import SCRAPERS
from setup_scheduler import registrar_tarea, _validar_hora
from ui.theme import COLORS, FONTS

SETTINGS_PATH = Path("config") / "settings.json"


class _CollapsibleSection(tk.Frame):
    """Collapsible group row for grouping related sources."""

    def __init__(self, parent, text, count, label="fuentes", bg=COLORS["card"], **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        self._bg = bg
        self._expanded = False

        # ── Header row ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=bg, cursor="hand2")
        hdr.pack(fill="x", pady=(6, 0))

        self._arrow = tk.Label(
            hdr, text="▶", bg=bg, fg=COLORS["accent"],
            font=("Segoe UI", 8, "bold"), width=2, cursor="hand2",
        )
        self._arrow.pack(side="left")

        tk.Label(
            hdr, text=text, bg=bg, fg=COLORS["text_secondary"],
            font=FONTS["body_bold"], anchor="w", cursor="hand2",
        ).pack(side="left")

        tk.Label(
            hdr, text=f"{count} {label}",
            bg=bg, fg=COLORS["text_muted"], font=FONTS["caption"],
        ).pack(side="left", padx=(8, 0), pady=(1, 0))

        # ── Content frame (hidden by default) ────────────────────────────────
        self.content = tk.Frame(self, bg=bg)

        for widget in (hdr, self._arrow):
            widget.bind("<Button-1>", self._toggle)

    def _toggle(self, _=None):
        if self._expanded:
            self.content.pack_forget()
            self._arrow.config(text="▶")
        else:
            self.content.pack(fill="x", padx=(16, 0), pady=(4, 0))
            self._arrow.config(text="▼")
        self._expanded = not self._expanded


class SettingsView(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller
        self.source_vars: dict[str, tk.BooleanVar] = {}
        self._all_vars: list[tk.BooleanVar] = []        # flat list for select-all
        self._build()
        self.load_settings()

    # ------------------------------------------------------------------ build

    def _build(self):
        # ── Sticky header ─────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", padx=24, pady=(24, 0))

        tk.Label(
            header, text="Configuración",
            bg=COLORS["bg"], fg=COLORS["text"], font=FONTS["h1"],
        ).pack(side="left")

        tk.Label(
            header, text="Fuentes activas y opciones de descarga",
            bg=COLORS["bg"], fg=COLORS["text_muted"], font=FONTS["small"],
        ).pack(side="right", pady=(10, 0))

        tk.Frame(self, bg=COLORS["card_border"], height=1).pack(
            fill="x", padx=24, pady=(14, 0)
        )

        # ── Scrollable body ────────────────────────────────────────────────────
        canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = tk.Frame(canvas, bg=COLORS["bg"])
        win_id = canvas.create_window((0, 0), window=body, anchor="nw")

        def _scroll(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        def _update(e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.update_idletasks()
            if body.winfo_reqheight() > canvas.winfo_height():
                if not scrollbar.winfo_ismapped():
                    scrollbar.pack(side="right", fill="y")
            else:
                scrollbar.pack_forget()

        canvas.bind("<Configure>", lambda e: (canvas.itemconfig(win_id, width=e.width), _update()))
        body.bind("<Configure>", lambda e: _update())
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _scroll))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # ── Scheduler card ────────────────────────────────────────────────────
        self._build_scheduler_card(body)

        # ── Sources card ───────────────────────────────────────────────────────
        card = self._card(body)
        card.pack(fill="x", padx=24, pady=(0, 24))

        # Card header
        card_hdr = tk.Frame(card, bg=COLORS["card"])
        card_hdr.pack(fill="x", padx=20, pady=(18, 0))

        tk.Label(
            card_hdr, text="Fuentes a descargar",
            bg=COLORS["card"], fg=COLORS["text"], font=FONTS["h3"],
        ).pack(side="left")

        # Select-all / none toggle link
        self._sel_all_lbl = tk.Label(
            card_hdr, text="Seleccionar todo",
            bg=COLORS["card"], fg=COLORS["accent"],
            font=FONTS["small"], cursor="hand2",
        )
        self._sel_all_lbl.pack(side="right", pady=(2, 0))
        self._sel_all_lbl.bind("<Button-1>", self._toggle_all)

        tk.Frame(card, bg=COLORS["card_border"], height=1).pack(fill="x", padx=20, pady=(12, 0))

        # Checkbox body
        chk_body = tk.Frame(card, bg=COLORS["card"])
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

        # Non-tribunal sources
        for src in others:
            var = tk.BooleanVar(value=True)
            self._add_checkbox(chk_body, src, var)
            self.source_vars[src] = var
            self._all_vars.append(var)

        # Tribunales Administrativos collapsible
        if trib_adm:
            tk.Frame(chk_body, bg=COLORS["card_border"], height=1).pack(
                fill="x", pady=(10, 4)
            )
            section = _CollapsibleSection(
                chk_body,
                text="Tribunales Administrativos",
                count=len(trib_adm),
                label="tribunales",
                bg=COLORS["card"],
            )
            section.pack(fill="x")

            for src in sorted(trib_adm):
                var = tk.BooleanVar(value=True)
                self._add_checkbox(section.content, src, var, indent=True)
                self.source_vars[src] = var
                self._all_vars.append(var)

        # Tribunales Superiores collapsible
        if trib_sup:
            tk.Frame(chk_body, bg=COLORS["card_border"], height=1).pack(
                fill="x", pady=(10, 4)
            )
            section = _CollapsibleSection(
                chk_body,
                text="Tribunales Superiores",
                count=len(trib_sup),
                label="tribunales",
                bg=COLORS["card"],
            )
            section.pack(fill="x")

            for src in sorted(trib_sup):
                var = tk.BooleanVar(value=True)
                self._add_checkbox(section.content, src, var, indent=True)
                self.source_vars[src] = var
                self._all_vars.append(var)

        # Juzgados collapsible
        if juzgados:
            tk.Frame(chk_body, bg=COLORS["card_border"], height=1).pack(
                fill="x", pady=(10, 4)
            )
            section = _CollapsibleSection(
                chk_body,
                text="Juzgados",
                count=len(juzgados),
                label="juzgados",
                bg=COLORS["card"],
            )
            section.pack(fill="x")

            for src in sorted(juzgados):
                var = tk.BooleanVar(value=True)
                self._add_checkbox(section.content, src, var, indent=True)
                self.source_vars[src] = var
                self._all_vars.append(var)

        # Card footer: save button
        tk.Frame(card, bg=COLORS["card_border"], height=1).pack(fill="x", padx=20, pady=(16, 0))
        footer = tk.Frame(card, bg=COLORS["card"])
        footer.pack(fill="x", padx=20, pady=(10, 16))

        tk.Label(
            footer, text="Los cambios se aplican en la próxima ejecución.",
            bg=COLORS["card"], fg=COLORS["text_muted"], font=FONTS["caption"],
        ).pack(side="left", pady=(2, 0))

        tk.Button(
            footer, text="Guardar configuración",
            command=self._on_save,
            bg=COLORS["btn_primary"], fg=COLORS["btn_text"],
            activebackground=COLORS["btn_primary_hover"],
            activeforeground=COLORS["btn_text"],
            font=FONTS["body_bold"],
            relief="flat", bd=0, cursor="hand2",
            padx=14, pady=7,
        ).pack(side="right")

    # -------------------------------------------------------- scheduler card

    def _build_scheduler_card(self, parent):
        card = self._card(parent)
        card.pack(fill="x", padx=24, pady=(24, 12))

        hdr = tk.Frame(card, bg=COLORS["card"])
        hdr.pack(fill="x", padx=20, pady=(18, 0))
        tk.Label(
            hdr, text="Automatización",
            bg=COLORS["card"], fg=COLORS["text"], font=FONTS["h3"],
        ).pack(side="left")

        tk.Frame(card, bg=COLORS["card_border"], height=1).pack(fill="x", padx=20, pady=(12, 0))

        body = tk.Frame(card, bg=COLORS["card"])
        body.pack(fill="x", padx=20, pady=(12, 0))

        tk.Label(
            body, text="Hora de ejecución diaria:",
            bg=COLORS["card"], fg=COLORS["text_secondary"], font=FONTS["body"],
        ).pack(side="left")

        hora_actual = self._get_hora_actual()
        hh, mm = hora_actual.split(":")

        self._hora_hh = tk.StringVar(value=hh)
        self._hora_mm = tk.StringVar(value=mm)

        tk.Spinbox(
            body, from_=0, to=23, textvariable=self._hora_hh,
            width=3, format="%02.0f", wrap=True,
            font=FONTS["body"], relief="flat",
            bg=COLORS["bg"], fg=COLORS["text"],
            buttonbackground=COLORS["bg"],
        ).pack(side="left", padx=(10, 2))

        tk.Label(body, text=":", bg=COLORS["card"], fg=COLORS["text"], font=FONTS["body_bold"]).pack(side="left")

        tk.Spinbox(
            body, from_=0, to=59, textvariable=self._hora_mm,
            width=3, format="%02.0f", wrap=True,
            font=FONTS["body"], relief="flat",
            bg=COLORS["bg"], fg=COLORS["text"],
            buttonbackground=COLORS["bg"],
        ).pack(side="left", padx=(2, 10))

        tk.Button(
            body, text="Programar",
            command=self._on_programar,
            bg=COLORS["btn_primary"], fg=COLORS["btn_text"],
            activebackground=COLORS["btn_primary_hover"],
            activeforeground=COLORS["btn_text"],
            font=FONTS["body_bold"],
            relief="flat", bd=0, cursor="hand2",
            padx=14, pady=5,
        ).pack(side="left")

        tk.Frame(card, bg=COLORS["card_border"], height=1).pack(fill="x", padx=20, pady=(12, 0))

        footer = tk.Frame(card, bg=COLORS["card"])
        footer.pack(fill="x", padx=20, pady=(8, 14))

        self._sched_status = tk.Label(
            footer, text=self._estado_tarea(),
            bg=COLORS["card"], fg=COLORS["text_muted"], font=FONTS["caption"],
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
                        # "6:00:00 AM" → "06:00"
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
            self._sched_status.config(
                text=f"Tarea activa: {hora} diariamente",
                fg=COLORS["success"],
            )
            if self.controller:
                self.controller.log(f"✓ Ejecución automática programada a las {hora}")
        except Exception as e:
            self._sched_status.config(text=f"Error: {e}", fg=COLORS["error"])
            if self.controller:
                self.controller.log(f"Error al programar tarea: {e}")

    # ----------------------------------------------------------------- helpers

    def _card(self, parent):
        return tk.Frame(
            parent, bg=COLORS["card"],
            highlightbackground=COLORS["card_border"], highlightthickness=1,
        )

    def _add_checkbox(self, parent, text, var, indent=False):
        row = tk.Frame(parent, bg=COLORS["card"])
        row.pack(fill="x", pady=2)

        if indent:
            tk.Frame(row, bg=COLORS["card"], width=4).pack(side="left")

        chk = tk.Checkbutton(
            row, text=text, variable=var,
            bg=COLORS["card"], fg=COLORS["text"] if not indent else COLORS["text_secondary"],
            activebackground=COLORS["card"],
            selectcolor="#eaf0ff",
            font=FONTS["body"] if not indent else FONTS["small"],
            anchor="w", cursor="hand2",
            relief="flat", bd=0,
        )
        chk.pack(side="left", fill="x")

    def _toggle_all(self, _=None):
        any_off = any(not v.get() for v in self._all_vars)
        new_val = True if any_off else False
        for v in self._all_vars:
            v.set(new_val)
        self._sel_all_lbl.config(
            text="Seleccionar todo" if not new_val else "Deseleccionar todo"
        )

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
        self._sel_all_lbl.config(
            text="Deseleccionar todo" if all_on else "Seleccionar todo"
        )
