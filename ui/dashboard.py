import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText
from datetime import datetime, date
import threading
import logging

from tkcalendar import DateEntry
from db.memory import Memory
from utils import generate_excel_report
from ui.theme import COLORS, FONTS

logger = logging.getLogger(__name__)


def _btn(parent, text, command, style="primary", **kw):
    palettes = {
        "primary":   (COLORS["btn_primary"],   COLORS["btn_primary_hover"]),
        "success":   (COLORS["btn_success"],   COLORS["btn_success_hover"]),
        "danger":    (COLORS["btn_danger"],    COLORS["btn_danger_hover"]),
        "secondary": (COLORS["btn_secondary"], COLORS["btn_secondary_hover"]),
    }
    bg, hover = palettes.get(style, palettes["primary"])
    return tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=COLORS["btn_text"],
        activebackground=hover, activeforeground=COLORS["btn_text"],
        disabledforeground=COLORS["btn_disabled_fg"],
        font=FONTS["body_bold"], relief="flat", bd=0,
        cursor="hand2", padx=14, pady=7,
        **kw,
    )


def _card(parent):
    return tk.Frame(
        parent, bg=COLORS["card"],
        highlightbackground=COLORS["card_border"], highlightthickness=1,
    )


class DashBoard(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller
        self._run_callback = None
        self._log_callback = None
        self._stop_cb = None
        self._build()

    # ------------------------------------------------------------------ build

    def _build(self):
        # ── Sticky header ────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", padx=24, pady=(24, 0))

        tk.Label(
            header, text="Panel de Control",
            bg=COLORS["bg"], fg=COLORS["text"], font=FONTS["h1"],
        ).pack(side="left")

        tk.Label(
            header, text=datetime.now().strftime("Bienvenido  ·  %d %b %Y"),
            bg=COLORS["bg"], fg=COLORS["text_muted"], font=FONTS["small"],
        ).pack(side="right", pady=(10, 0))

        tk.Frame(self, bg=COLORS["card_border"], height=1).pack(
            fill="x", padx=24, pady=(14, 0)
        )

        # ── Scrollable body ───────────────────────────────────────────────────
        scroll_canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(scroll_canvas, bg=COLORS["bg"])
        win_id = scroll_canvas.create_window((0, 0), window=content, anchor="nw")

        scroll_canvas.bind("<Configure>", lambda e: scroll_canvas.itemconfig(win_id, width=e.width))
        content.bind("<Configure>", lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
        scroll_canvas.bind("<MouseWheel>", lambda e: scroll_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # ── Stat cards ───────────────────────────────────────────────────────
        stats = tk.Frame(content, bg=COLORS["bg"])
        stats.pack(fill="x", padx=24, pady=24)
        stats.columnconfigure((0, 1, 2), weight=1, uniform="stat")

        self._total_docs_label = self._stat_card(
            stats, col=0, title="Total Documentos", value="—",
            subtitle="documentos descargados", color=COLORS["info"],
        )
        self._stat_card(
            stats, col=1, title="Estado del Sistema", value="OK",
            subtitle="funcionando correctamente", color=COLORS["success"],
        )
        self._stat_card(
            stats, col=2, title="Última Actualización",
            value=datetime.now().strftime("%d/%m"),
            subtitle=datetime.now().strftime("%Y"),
            color=COLORS["accent"],
        )

        # ── Execute card ─────────────────────────────────────────────────────
        run_card = _card(content)
        run_card.pack(fill="x", padx=24, pady=(0, 16))

        run_top = tk.Frame(run_card, bg=COLORS["card"])
        run_top.pack(fill="x", padx=20, pady=(18, 0))

        tk.Label(
            run_top, text="Ejecutar descarga",
            bg=COLORS["card"], fg=COLORS["text"], font=FONTS["h3"],
        ).pack(side="left")

        tk.Frame(run_card, bg=COLORS["card_border"], height=1).pack(
            fill="x", padx=20, pady=(12, 0)
        )

        run_body = tk.Frame(run_card, bg=COLORS["card"])
        run_body.pack(fill="x", padx=20, pady=16)

        # Date fields row
        dates_row = tk.Frame(run_body, bg=COLORS["card"])
        dates_row.pack(fill="x", pady=(0, 14))

        date_style = {
            "font": FONTS["body"],
            "background": COLORS["sidebar"],
            "foreground": COLORS["sidebar_text_active"],
            "selectbackground": COLORS["sidebar_active_bar"],
            "selectforeground": "#ffffff",
            "normalbackground": COLORS["card"],
            "normalforeground": COLORS["text"],
            "weekendbackground": COLORS["card"],
            "weekendforeground": COLORS["text"],
            "headersbackground": COLORS["sidebar"],
            "headersforeground": COLORS["sidebar_text_active"],
            "bordercolor": COLORS["card_border"],
            "othermonthforeground": COLORS["text_muted"],
            "othermonthbackground": COLORS["card"],
            "othermonthweforeground": COLORS["text_muted"],
            "othermonthwebackground": COLORS["card"],
            "disableddaybackground": COLORS["card"],
            "disableddayforeground": COLORS["text_muted"],
            "tooltipbackground": COLORS["sidebar"],
            "tooltipforeground": COLORS["sidebar_text_active"],
        }

        # Start date
        start_col = tk.Frame(dates_row, bg=COLORS["card"])
        start_col.pack(side="left", padx=(0, 24))

        tk.Label(
            start_col, text="Desde",
            bg=COLORS["card"], fg=COLORS["text_muted"], font=FONTS["small"],
        ).pack(anchor="w", pady=(0, 4))

        self._run_start = DateEntry(
            start_col, width=13, date_pattern="yyyy-mm-dd",
            relief="flat", borderwidth=1,
            **date_style,
        )
        self._run_start.pack(ipady=4)
        self._prefill_start_date()

        # End date
        end_col = tk.Frame(dates_row, bg=COLORS["card"])
        end_col.pack(side="left")

        tk.Label(
            end_col, text="Hasta",
            bg=COLORS["card"], fg=COLORS["text_muted"], font=FONTS["small"],
        ).pack(anchor="w", pady=(0, 4))

        self._run_end = DateEntry(
            end_col, width=13, date_pattern="yyyy-mm-dd",
            relief="flat", borderwidth=1,
            **date_style,
        )
        self._run_end.pack(ipady=4)
        self._run_end.set_date(date.today())

        # Reset link
        reset_lbl = tk.Label(
            dates_row, text="↺  Restablecer",
            bg=COLORS["card"], fg=COLORS["accent"],
            font=FONTS["small"], cursor="hand2",
        )
        reset_lbl.pack(side="left", padx=(20, 0), pady=(16, 0))
        reset_lbl.bind("<Button-1>", lambda e: self._reset_dates())

        # Execute / Stop buttons
        btn_row = tk.Frame(run_body, bg=COLORS["card"])
        btn_row.pack(fill="x")

        self.btn_execute = _btn(
            btn_row, "▶  Ejecutar ahora", self._on_execute, style="success"
        )
        self.btn_execute.pack(side="left")

        self.btn_stop = _btn(btn_row, "■  Parar", self._on_stop, style="danger")
        self.btn_stop.config(state="disabled", bg=COLORS["btn_disabled_bg"], cursor="")
        self.btn_stop.pack(side="left", padx=(10, 0))

        tk.Label(
            btn_row,
            text="Las fuentes activas se configuran en  Configuración →",
            bg=COLORS["card"], fg=COLORS["text_muted"], font=FONTS["caption"],
        ).pack(side="left", padx=(16, 0), pady=(2, 0))

        # Terminal log area
        tk.Frame(run_card, bg=COLORS["card_border"], height=1).pack(
            fill="x", padx=0, pady=(12, 0)
        )

        console_bar = tk.Frame(run_card, bg="#0f1923")
        console_bar.pack(fill="x")

        tk.Label(
            console_bar, text="● ● ●",
            bg="#0f1923", fg="#3d5166",
            font=("Segoe UI", 9), padx=10,
        ).pack(side="left", pady=6)

        tk.Label(
            console_bar, text="Terminal",
            bg="#0f1923", fg="#4a6580",
            font=FONTS["caption"],
        ).pack(side="left")

        self._terminal = ScrolledText(
            run_card,
            bg="#0f1923", fg="#c9d1d9",
            font=("Consolas", 9),
            relief="flat", bd=0,
            height=12,
            state="disabled",
            wrap="word",
            insertbackground="#c9d1d9",
        )
        self._terminal.pack(fill="x", padx=0, pady=0)

        # Color tags for log classification
        self._terminal.tag_config("success", foreground="#3fb950")
        self._terminal.tag_config("error",   foreground="#f85149")
        self._terminal.tag_config("warning", foreground="#d29922")
        self._terminal.tag_config("info",    foreground="#58a6ff")
        self._terminal.tag_config("muted",   foreground="#4a6580")
        self._terminal.tag_config("ts",      foreground="#3d5166")

        # ── Sources card ─────────────────────────────────────────────────────
        self._sources_card = _card(content)
        self._sources_card.pack(fill="x", padx=24, pady=(0, 16))
        self._build_sources_card()


    # --------------------------------------------------------- sources card

    def _build_sources_card(self):
        card = self._sources_card

        hdr = tk.Frame(card, bg=COLORS["card"])
        hdr.pack(fill="x", padx=20, pady=(18, 0))
        tk.Label(
            hdr, text="Documentos por Entidad",
            bg=COLORS["card"], fg=COLORS["text"], font=FONTS["h3"],
        ).pack(side="left")
        self._sources_count_label = tk.Label(
            hdr, text="", bg=COLORS["card"], fg=COLORS["text_muted"], font=FONTS["small"],
        )
        self._sources_count_label.pack(side="right", pady=(2, 0))

        tk.Frame(card, bg=COLORS["card_border"], height=1).pack(fill="x", padx=20, pady=(12, 0))

        wrap = tk.Frame(card, bg=COLORS["card"])
        wrap.pack(fill="x", padx=20, pady=(0, 16))

        self._sources_canvas = tk.Canvas(wrap, bg=COLORS["card"], highlightthickness=0, height=180)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self._sources_canvas.yview)
        self._sources_canvas.configure(yscrollcommand=sb.set)
        self._sources_canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._sources_inner = tk.Frame(self._sources_canvas, bg=COLORS["card"])
        self._sources_win = self._sources_canvas.create_window((0, 0), window=self._sources_inner, anchor="nw")

        self._sources_inner.bind(
            "<Configure>",
            lambda e: self._sources_canvas.configure(scrollregion=self._sources_canvas.bbox("all")),
        )
        self._sources_canvas.bind(
            "<Configure>",
            lambda e: self._sources_canvas.itemconfig(self._sources_win, width=e.width),
        )
        self._sources_canvas.bind(
            "<MouseWheel>",
            lambda e: self._sources_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        tk.Label(
            self._sources_inner,
            text="Sin datos aún — los conteos aparecerán al descargar documentos.",
            bg=COLORS["card"], fg=COLORS["text_muted"], font=FONTS["small"],
        ).pack(anchor="w", pady=8)

        # Footer: export button
        tk.Frame(card, bg=COLORS["card_border"], height=1).pack(fill="x", padx=20)
        footer = tk.Frame(card, bg=COLORS["card"])
        footer.pack(fill="x", padx=20, pady=(10, 16))
        self.btn_download_report = _btn(
            footer, "⬇  Exportar Excel", self._on_start_downloads, style="primary"
        )
        self.btn_download_report.pack(side="right")

    def _refresh_sources_card(self):
        try:
            groups = Memory().get_counts_grouped()
        except Exception:
            return

        for w in self._sources_inner.winfo_children():
            w.destroy()

        if not groups:
            tk.Label(
                self._sources_inner,
                text="Sin datos aún — los conteos aparecerán al descargar documentos.",
                bg=COLORS["card"], fg=COLORS["text_muted"], font=FONTS["small"],
            ).pack(anchor="w", pady=8)
            self._sources_count_label.config(text="")
            return

        n_total = sum(1 + len(c) for _, _, c in groups)
        self._sources_count_label.config(text=f"{n_total} fuentes")

        max_count = groups[0][1]
        BAR_W = 90

        for name, total, children in groups:
            if children:
                self._add_group_row(name, total, children, max_count, BAR_W)
            else:
                self._add_flat_row(self._sources_inner, name, total, max_count, BAR_W, indent=0)

    def _add_flat_row(self, parent, name, count, max_count, bar_w, indent=0):
        row = tk.Frame(parent, bg=COLORS["card"])
        row.pack(fill="x", pady=2)

        if indent:
            tk.Frame(row, bg=COLORS["card"], width=indent).pack(side="left")

        is_child = indent > 0
        disp = name if len(name) <= 35 else name[:33] + "…"
        tk.Label(
            row, text=disp, bg=COLORS["card"],
            fg=COLORS["text_muted"] if is_child else COLORS["text_secondary"],
            font=FONTS["caption"] if is_child else FONTS["small"],
            anchor="w", width=35,
        ).pack(side="left")

        track = tk.Frame(row, bg=COLORS["card_border"], height=7 if is_child else 8, width=bar_w)
        track.pack(side="left", padx=(6, 6))
        track.pack_propagate(False)
        fill_w = max(2, int(bar_w * count / max_count))
        tk.Frame(track, bg=COLORS["info"] if is_child else COLORS["accent"],
                 height=8, width=fill_w).place(x=0, y=0, height=8)

        tk.Label(
            row, text=f"{count:,}", bg=COLORS["card"],
            fg=COLORS["text_muted"] if is_child else COLORS["text"],
            font=FONTS["caption"] if is_child else FONTS["body_bold"],
            anchor="e", width=7,
        ).pack(side="left")

    def _add_group_row(self, name, total, children, max_count, bar_w):
        group = tk.Frame(self._sources_inner, bg=COLORS["card"])
        group.pack(fill="x")

        children_frame = tk.Frame(group, bg=COLORS["card"])
        expanded = [False]

        hdr = tk.Frame(group, bg=COLORS["card"], cursor="hand2")
        hdr.pack(fill="x", pady=2)

        arrow = tk.Label(hdr, text="▶", bg=COLORS["card"], fg=COLORS["accent"],
                         font=("Segoe UI", 8, "bold"), width=2, cursor="hand2")
        arrow.pack(side="left")

        disp = name if len(name) <= 33 else name[:31] + "…"
        name_lbl = tk.Label(hdr, text=disp, bg=COLORS["card"], fg=COLORS["text_secondary"],
                            font=FONTS["body_bold"], anchor="w", width=33, cursor="hand2")
        name_lbl.pack(side="left")

        track = tk.Frame(hdr, bg=COLORS["card_border"], height=8, width=bar_w)
        track.pack(side="left", padx=(6, 6))
        track.pack_propagate(False)
        fill_w = max(2, int(bar_w * total / max_count))
        tk.Frame(track, bg=COLORS["success"], height=8, width=fill_w).place(x=0, y=0, height=8)

        tk.Label(hdr, text=f"{total:,}", bg=COLORS["card"], fg=COLORS["text"],
                 font=FONTS["body_bold"], anchor="e", width=7).pack(side="left")

        for child_name, child_count in children:
            self._add_flat_row(children_frame, child_name, child_count, max_count, bar_w, indent=16)

        def toggle(e=None):
            if expanded[0]:
                children_frame.pack_forget()
                arrow.config(text="▶")
                expanded[0] = False
            else:
                children_frame.pack(fill="x")
                arrow.config(text="▼")
                expanded[0] = True
            self._sources_inner.update_idletasks()
            self._sources_canvas.configure(scrollregion=self._sources_canvas.bbox("all"))

        hdr.bind("<Button-1>", toggle)
        arrow.bind("<Button-1>", toggle)
        name_lbl.bind("<Button-1>", toggle)

    # ------------------------------------------------------------ date helpers

    def _prefill_start_date(self):
        try:
            last = Memory().get_last_inserted()
            if last:
                d = datetime.strptime(last[:10], "%Y-%m-%d").date()
                self._run_start.set_date(d)
                return
        except Exception:
            pass
        self._run_start.set_date(date.today())

    def _reset_dates(self):
        self._run_end.set_date(date.today())
        self._prefill_start_date()

    def get_dates(self):
        """Return (fini, ffin) as 'YYYY-MM-DD' strings from the DateEntry widgets."""
        fini = self._run_start.get_date().strftime("%Y-%m-%d")
        ffin = self._run_end.get_date().strftime("%Y-%m-%d")
        return fini, ffin

    # ---------------------------------------------------------------- helpers

    def _stat_card(self, parent, col, title, value, subtitle, color):
        card = tk.Frame(parent, bg=COLORS["card"],
                        highlightbackground=COLORS["card_border"], highlightthickness=1)
        card.grid(row=0, column=col, padx=(0, 12) if col < 2 else 0, sticky="ew")

        tk.Frame(card, bg=color, height=4).pack(fill="x")
        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(fill="both", padx=18, pady=14)

        tk.Label(inner, text=title.upper(), bg=COLORS["card"],
                 fg=COLORS["text_muted"], font=FONTS["stat_label"]).pack(anchor="w")
        val_lbl = tk.Label(inner, text=value, bg=COLORS["card"],
                           fg=color, font=FONTS["stat_number"])
        val_lbl.pack(anchor="w", pady=(4, 2))
        tk.Label(inner, text=subtitle, bg=COLORS["card"],
                 fg=COLORS["text_muted"], font=FONTS["caption"]).pack(anchor="w")
        return val_lbl

    # ------------------------------------------------------------------- API

    def update_total(self, count: int):
        self._total_docs_label.config(text=str(count))
        self._refresh_sources_card()

    def set_run_callback(self, cb):
        self._run_callback = cb

    def set_log_callback(self, cb):
        self._log_callback = cb

    def set_running(self, running: bool):
        if running:
            self.btn_execute.config(
                state="disabled", text="⏳  Ejecutando...",
                bg=COLORS["btn_disabled_bg"], cursor="",
            )
            self.btn_stop.config(
                state="normal", bg=COLORS["btn_danger"], cursor="hand2",
            )
        else:
            self.btn_execute.config(
                state="normal", text="▶  Ejecutar ahora",
                bg=COLORS["btn_success"], cursor="hand2",
            )
            self.btn_stop.config(
                state="disabled", bg=COLORS["btn_disabled_bg"], cursor="",
            )

    def log(self, msg: str):
        """Append a colored line to the terminal panel."""
        tag = self._tag(msg)
        ts = datetime.now().strftime("%H:%M:%S")
        self._terminal.config(state="normal")
        self._terminal.insert("end", f"[{ts}] ", "ts")
        self._terminal.insert("end", msg + "\n", tag)
        self._terminal.see("end")
        self._terminal.config(state="disabled")
        if self._log_callback:
            self._log_callback(msg)
        else:
            logger.info(msg)

    def _tag(self, msg: str) -> str:
        ml = msg.lower()
        if any(w in ml for w in ("error", "fallo", "exception", "traceback")):
            return "error"
        if any(w in ml for w in ("✓", "guardado", "completado", "finaliz", "éxito", "exito")):
            return "success"
        if any(w in ml for w in ("advertencia", "warning", "omitido", "skip")):
            return "warning"
        if any(w in ml for w in ("iniciando", "inicio", "start", "descarg", "procesando")):
            return "info"
        return "muted"

    def set_stop_callback(self, cb):
        self._stop_cb = cb

    def _log(self, msg):
        self.log(msg)

    def _on_execute(self):
        if self._run_callback:
            self._run_callback()

    def _on_stop(self):
        if self._stop_cb:
            self._stop_cb()
        self.btn_stop.config(state="disabled", bg=COLORS["btn_disabled_bg"], cursor="")

    def _on_start_downloads(self):
        try:
            self.start_inv_downloads()
        except ValueError as e:
            self._log(f"[Error] {e}")

    def start_inv_downloads(self):
        entries = Memory().get_all_downloaded()
        if not entries:
            self._log("[Inventario] No hay documentos descargados para generar un informe.")
            return

        now = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"inventario_{now}.xlsx",
            title="Guardar inventario como...",
        )
        if not file_path:
            return

        self.btn_download_report.config(state="disabled", bg=COLORS["btn_disabled_bg"], cursor="")
        self._log(f"[Inventario] Generando reporte en {file_path}...")

        def worker():
            try:
                generate_excel_report(file_path, entries, title="Inventario de documentos descargados")
                self._log(f"[Inventario] Reporte guardado en {file_path}")
            except Exception as e:
                self._log(f"[Inventario] Error al generar reporte: {e}")
            finally:
                self.after(0, lambda: self.btn_download_report.config(
                    state="normal", bg=COLORS["btn_primary"], cursor="hand2"
                ))

        threading.Thread(target=worker, daemon=True).start()
