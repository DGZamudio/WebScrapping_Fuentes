import tkinter as tk
from tkinter import ttk
from pathlib import Path
import json

from scrappers import SCRAPERS
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

        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # ── Sources card ───────────────────────────────────────────────────────
        card = self._card(body)
        card.pack(fill="x", padx=24, pady=(24, 24))

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
        others = {}
        for src in SCRAPERS:
            if src.startswith("Tribunal Administrativo"):
                trib_adm[src] = SCRAPERS[src]
            elif src.startswith("Tribunal Superior"):
                trib_sup[src] = SCRAPERS[src]
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
