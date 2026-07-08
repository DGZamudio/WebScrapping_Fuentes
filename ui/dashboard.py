from tkinter import filedialog
from datetime import datetime, date
import threading
import logging

import customtkinter as ctk
from tkcalendar import DateEntry
from db.memory import Memory
from utils import generate_excel_report
from ui.theme import COLORS, FONTS, CORNER_RADIUS, BORDER_WIDTH
from ui.list_filter import reflow_rows

logger = logging.getLogger(__name__)


def _btn(parent, text, command, style="primary", **kw):
    palettes = {
        "primary":   (COLORS["btn_primary"],   COLORS["btn_primary_hover"]),
        "success":   (COLORS["btn_success"],   COLORS["btn_success_hover"]),
        "danger":    (COLORS["btn_danger"],    COLORS["btn_danger_hover"]),
        "secondary": (COLORS["btn_secondary"], COLORS["btn_secondary_hover"]),
    }
    fg, hover = palettes.get(style, palettes["primary"])
    return ctk.CTkButton(
        parent, text=text, command=command,
        fg_color=fg, hover_color=hover, text_color=COLORS["btn_text"],
        font=FONTS["body_bold"], corner_radius=CORNER_RADIUS,
        **kw,
    )


def _card(parent):
    return ctk.CTkFrame(
        parent, fg_color=COLORS["card"],
        border_color=COLORS["card_border"], border_width=BORDER_WIDTH,
        corner_radius=CORNER_RADIUS,
    )


class DashBoard(ctk.CTkFrame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self.controller = controller
        self._run_callback = None
        self._log_callback = None
        self._stop_cb = None
        self._sync_cb = None
        self._upload_pending_cb = None
        self._source_rows = []
        self._source_groups = []
        self._source_entries = []
        self._build()

    # ------------------------------------------------------------------ build

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 0))

        ctk.CTkLabel(
            header, text="Panel de Control",
            text_color=COLORS["text"], fg_color="transparent", font=FONTS["h1"],
        ).pack(side="left")

        ctk.CTkLabel(
            header, text=datetime.now().strftime("Bienvenido  ·  %d %b %Y"),
            text_color=COLORS["text_muted"], fg_color="transparent", font=FONTS["small"],
        ).pack(side="right", pady=(10, 0))

        ctk.CTkFrame(self, fg_color=COLORS["card_border"], height=1, corner_radius=0).pack(
            fill="x", padx=24, pady=(14, 0)
        )

        content = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Stat cards ───────────────────────────────────────────────────────
        stats = ctk.CTkFrame(content, fg_color="transparent")
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

        run_top = ctk.CTkFrame(run_card, fg_color="transparent")
        run_top.pack(fill="x", padx=20, pady=(18, 0))

        ctk.CTkLabel(
            run_top, text="Ejecutar descarga",
            text_color=COLORS["text"], fg_color="transparent", font=FONTS["h3"],
        ).pack(side="left")

        ctk.CTkFrame(run_card, fg_color=COLORS["card_border"], height=1, corner_radius=0).pack(
            fill="x", padx=20, pady=(12, 0)
        )

        run_body = ctk.CTkFrame(run_card, fg_color="transparent")
        run_body.pack(fill="x", padx=20, pady=16)

        dates_row = ctk.CTkFrame(run_body, fg_color="transparent")
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

        start_col = ctk.CTkFrame(dates_row, fg_color="transparent")
        start_col.pack(side="left", padx=(0, 24))

        ctk.CTkLabel(
            start_col, text="Desde",
            text_color=COLORS["text_muted"], fg_color="transparent", font=FONTS["small"],
        ).pack(anchor="w", pady=(0, 4))

        self._run_start = DateEntry(
            start_col, width=13, date_pattern="yyyy-mm-dd",
            relief="flat", borderwidth=1,
            **date_style,
        )
        self._run_start.pack(ipady=4)
        self._prefill_start_date()

        end_col = ctk.CTkFrame(dates_row, fg_color="transparent")
        end_col.pack(side="left")

        ctk.CTkLabel(
            end_col, text="Hasta",
            text_color=COLORS["text_muted"], fg_color="transparent", font=FONTS["small"],
        ).pack(anchor="w", pady=(0, 4))

        self._run_end = DateEntry(
            end_col, width=13, date_pattern="yyyy-mm-dd",
            relief="flat", borderwidth=1,
            **date_style,
        )
        self._run_end.pack(ipady=4)
        self._run_end.set_date(date.today())

        reset_lbl = ctk.CTkLabel(
            dates_row, text="↺  Restablecer",
            text_color=COLORS["accent"], fg_color="transparent",
            font=FONTS["small"], cursor="hand2",
        )
        reset_lbl.pack(side="left", padx=(20, 0), pady=(16, 0))
        reset_lbl.bind("<Button-1>", lambda e: self._reset_dates())

        btn_row = ctk.CTkFrame(run_body, fg_color="transparent")
        btn_row.pack(fill="x")

        self.btn_execute = _btn(
            btn_row, "▶  Ejecutar ahora", self._on_execute, style="success"
        )
        self.btn_execute.pack(side="left")

        self.btn_stop = _btn(btn_row, "■  Parar", self._on_stop, style="danger")
        self.btn_stop.configure(state="disabled", fg_color=COLORS["btn_disabled_bg"], cursor="")
        self.btn_stop.pack(side="left", padx=(10, 0))

        self.btn_sync = _btn(btn_row, "☁  Sincronizar desde Drive", self._on_sync, style="secondary")
        self.btn_sync.pack(side="left", padx=(10, 0))

        self.btn_upload_pending = _btn(btn_row, "⬆  Subir pendientes", self._on_upload_pending, style="secondary")
        self.btn_upload_pending.pack(side="left", padx=(10, 0))

        ctk.CTkLabel(
            btn_row,
            text="Las fuentes activas se configuran en  Configuración →",
            text_color=COLORS["text_muted"], fg_color="transparent", font=FONTS["caption"],
        ).pack(side="left", padx=(16, 0), pady=(2, 0))

        ctk.CTkFrame(run_card, fg_color=COLORS["card_border"], height=1, corner_radius=0).pack(
            fill="x", padx=0, pady=(12, 0)
        )

        console_bar = ctk.CTkFrame(run_card, fg_color="#0f1923", corner_radius=0)
        console_bar.pack(fill="x")

        ctk.CTkLabel(
            console_bar, text="● ● ●",
            fg_color="transparent", text_color="#3d5166",
            font=("Segoe UI", 9),
        ).pack(side="left", padx=10, pady=6)

        ctk.CTkLabel(
            console_bar, text="Terminal",
            fg_color="transparent", text_color="#4a6580",
            font=FONTS["caption"],
        ).pack(side="left")

        self._terminal = ctk.CTkTextbox(
            run_card,
            fg_color="#0f1923", text_color="#c9d1d9",
            font=("Consolas", 9),
            corner_radius=0, border_width=0,
            height=200,
            wrap="word",
            state="disabled",
        )
        self._terminal.pack(fill="x", padx=0, pady=0)

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

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(18, 0))
        ctk.CTkLabel(
            hdr, text="Documentos por Entidad",
            text_color=COLORS["text"], fg_color="transparent", font=FONTS["h3"],
        ).pack(side="left")
        self._sources_count_label = ctk.CTkLabel(
            hdr, text="", text_color=COLORS["text_muted"], fg_color="transparent", font=FONTS["small"],
        )
        self._sources_count_label.pack(side="right", pady=(2, 0))

        ctk.CTkFrame(card, fg_color=COLORS["card_border"], height=1, corner_radius=0).pack(
            fill="x", padx=20, pady=(12, 0)
        )

        search_row = ctk.CTkFrame(card, fg_color="transparent")
        search_row.pack(fill="x", padx=20, pady=(12, 0))

        self._sources_search_var = ctk.StringVar()
        self._sources_search_var.trace_add(
            "write", lambda *_: self._apply_sources_filter(self._sources_search_var.get())
        )
        ctk.CTkEntry(
            search_row, textvariable=self._sources_search_var,
            placeholder_text="Buscar entidad...",
            fg_color=COLORS["bg"], border_color=COLORS["card_border"],
            text_color=COLORS["text"], corner_radius=CORNER_RADIUS,
        ).pack(fill="x")

        wrap = ctk.CTkFrame(card, fg_color="transparent")
        wrap.pack(fill="x", padx=20, pady=(12, 16))

        self._sources_inner = ctk.CTkScrollableFrame(wrap, fg_color=COLORS["card"], height=180)
        self._sources_inner.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self._sources_inner,
            text="Sin datos aún — los conteos aparecerán al descargar documentos.",
            text_color=COLORS["text_muted"], fg_color="transparent", font=FONTS["small"],
        ).pack(anchor="w", pady=8)

        ctk.CTkFrame(card, fg_color=COLORS["card_border"], height=1, corner_radius=0).pack(fill="x", padx=20)
        footer = ctk.CTkFrame(card, fg_color="transparent")
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
        self._source_rows = []
        self._source_groups = []
        self._source_entries = []

        if not groups:
            ctk.CTkLabel(
                self._sources_inner,
                text="Sin datos aún — los conteos aparecerán al descargar documentos.",
                text_color=COLORS["text_muted"], fg_color="transparent", font=FONTS["small"],
            ).pack(anchor="w", pady=8)
            self._sources_count_label.configure(text="")
            return

        n_total = sum(1 + len(c) for _, _, c in groups)
        self._sources_count_label.configure(text=f"{n_total} fuentes")

        max_count = groups[0][1]
        BAR_W = 90

        for name, total, children in groups:
            if children:
                g = self._add_group_row(name, total, children, max_count, BAR_W)
                self._source_groups.append(g)
                self._source_entries.append(("group", name, g))
            else:
                row = self._add_flat_row(self._sources_inner, name, total, max_count, BAR_W, indent=0)
                self._source_rows.append((name, row))
                self._source_entries.append(("flat", name, row))

        self._apply_sources_filter(self._sources_search_var.get())

    def _add_flat_row(self, parent, name, count, max_count, bar_w, indent=0):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)

        if indent:
            ctk.CTkFrame(row, fg_color="transparent", width=indent, height=1).pack(side="left")

        is_child = indent > 0
        disp = name if len(name) <= 35 else name[:33] + "…"
        ctk.CTkLabel(
            row, text=disp, fg_color="transparent",
            text_color=COLORS["text_muted"] if is_child else COLORS["text_secondary"],
            font=FONTS["caption"] if is_child else FONTS["small"],
            anchor="w", width=180,
        ).pack(side="left")

        track = ctk.CTkFrame(
            row, fg_color=COLORS["card_border"], height=7 if is_child else 8, width=bar_w, corner_radius=0,
        )
        track.pack(side="left", padx=(6, 6))
        fill_w = max(2, int(bar_w * count / max_count))
        ctk.CTkFrame(
            track, fg_color=COLORS["info"] if is_child else COLORS["accent"],
            height=8, width=fill_w, corner_radius=0,
        ).place(x=0, y=0)

        ctk.CTkLabel(
            row, text=f"{count:,}", fg_color="transparent",
            text_color=COLORS["text_muted"] if is_child else COLORS["text"],
            font=FONTS["caption"] if is_child else FONTS["body_bold"],
            anchor="e", width=60,
        ).pack(side="left")

        return row

    def _add_group_row(self, name, total, children, max_count, bar_w):
        group = ctk.CTkFrame(self._sources_inner, fg_color="transparent")
        group.pack(fill="x")

        children_frame = ctk.CTkFrame(group, fg_color="transparent")
        expanded = [False]

        hdr = ctk.CTkFrame(group, fg_color="transparent", cursor="hand2")
        hdr.pack(fill="x", pady=2)

        arrow = ctk.CTkLabel(
            hdr, text="▶", text_color=COLORS["accent"], fg_color="transparent",
            font=("Segoe UI", 8, "bold"), width=16, cursor="hand2",
        )
        arrow.pack(side="left")

        disp = name if len(name) <= 33 else name[:31] + "…"
        name_lbl = ctk.CTkLabel(
            hdr, text=disp, text_color=COLORS["text_secondary"], fg_color="transparent",
            font=FONTS["body_bold"], anchor="w", width=170, cursor="hand2",
        )
        name_lbl.pack(side="left")

        track = ctk.CTkFrame(hdr, fg_color=COLORS["card_border"], height=8, width=bar_w, corner_radius=0)
        track.pack(side="left", padx=(6, 6))
        fill_w = max(2, int(bar_w * total / max_count))
        ctk.CTkFrame(track, fg_color=COLORS["success"], height=8, width=fill_w, corner_radius=0).place(
            x=0, y=0
        )

        ctk.CTkLabel(
            hdr, text=f"{total:,}", text_color=COLORS["text"], fg_color="transparent",
            font=FONTS["body_bold"], anchor="e", width=60,
        ).pack(side="left")

        child_rows = []
        for child_name, child_count in children:
            row = self._add_flat_row(children_frame, child_name, child_count, max_count, bar_w, indent=16)
            child_rows.append((child_name, row))

        def toggle(e=None):
            if expanded[0]:
                children_frame.pack_forget()
                arrow.configure(text="▶")
                expanded[0] = False
            else:
                children_frame.pack(fill="x")
                arrow.configure(text="▼")
                expanded[0] = True

        hdr.bind("<Button-1>", toggle)
        arrow.bind("<Button-1>", toggle)
        name_lbl.bind("<Button-1>", toggle)

        return {
            "name": name, "group_frame": group, "children_frame": children_frame,
            "arrow": arrow, "expanded": expanded, "children": child_rows,
        }

    # -------------------------------------------------------------- filtering

    def _apply_sources_filter(self, query: str):
        q = query.strip().lower()

        # Forget every top-level sibling first, then re-pack the visible ones
        # in their original creation order, so flat rows and group headers
        # (interleaved by Memory().get_counts_grouped()'s ordering) never
        # scramble relative to each other while filtering.
        for name, row in self._source_rows:
            row.pack_forget()
        for g in self._source_groups:
            g["group_frame"].pack_forget()

        for kind, name, ref in self._source_entries:
            if kind == "flat":
                if not q or q in name.lower():
                    ref.pack(fill="x", pady=2)
                continue

            g = ref
            has_match = q in g["name"].lower() or any(
                q in c.lower() for c, _ in g["children"]
            )
            reflow_rows(g["children"], query)

            if q:
                if not has_match:
                    continue
                g["group_frame"].pack(fill="x")
                if not g["expanded"][0]:
                    g["children_frame"].pack(fill="x")
                    g["arrow"].configure(text="▼")
                    g["expanded"][0] = True
            else:
                g["group_frame"].pack(fill="x")
                if g["expanded"][0]:
                    g["children_frame"].pack_forget()
                    g["arrow"].configure(text="▶")
                    g["expanded"][0] = False

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
        card = ctk.CTkFrame(
            parent, fg_color=COLORS["card"],
            border_color=COLORS["card_border"], border_width=BORDER_WIDTH,
            corner_radius=CORNER_RADIUS,
        )
        card.grid(row=0, column=col, padx=(0, 12) if col < 2 else 0, sticky="ew")

        ctk.CTkFrame(card, fg_color=color, height=4, corner_radius=0).pack(fill="x")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", padx=18, pady=14)

        ctk.CTkLabel(
            inner, text=title.upper(), fg_color="transparent",
            text_color=COLORS["text_muted"], font=FONTS["stat_label"],
        ).pack(anchor="w")
        val_lbl = ctk.CTkLabel(
            inner, text=value, fg_color="transparent",
            text_color=color, font=FONTS["stat_number"],
        )
        val_lbl.pack(anchor="w", pady=(4, 2))
        ctk.CTkLabel(
            inner, text=subtitle, fg_color="transparent",
            text_color=COLORS["text_muted"], font=FONTS["caption"],
        ).pack(anchor="w")
        return val_lbl

    # ------------------------------------------------------------------- API

    def update_total(self, count: int):
        self._total_docs_label.configure(text=str(count))
        self._refresh_sources_card()

    def set_run_callback(self, cb):
        self._run_callback = cb

    def set_log_callback(self, cb):
        self._log_callback = cb

    def set_running(self, running: bool):
        if running:
            self.btn_execute.configure(
                state="disabled", text="⏳  Ejecutando...",
                fg_color=COLORS["btn_disabled_bg"], cursor="",
            )
            self.btn_stop.configure(
                state="normal", fg_color=COLORS["btn_danger"], cursor="hand2",
            )
        else:
            self.btn_execute.configure(
                state="normal", text="▶  Ejecutar ahora",
                fg_color=COLORS["btn_success"], cursor="hand2",
            )
            self.btn_stop.configure(
                state="disabled", fg_color=COLORS["btn_disabled_bg"], cursor="",
            )

    def log(self, msg: str):
        """Append a colored line to the terminal panel."""
        tag = self._tag(msg)
        ts = datetime.now().strftime("%H:%M:%S")
        self._terminal.configure(state="normal")
        self._terminal.insert("end", f"[{ts}] ", "ts")
        self._terminal.insert("end", msg + "\n", tag)
        self._terminal.see("end")
        self._terminal.configure(state="disabled")
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

    def set_sync_callback(self, cb):
        self._sync_cb = cb

    def set_upload_pending_callback(self, cb):
        self._upload_pending_cb = cb

    def _log(self, msg):
        self.log(msg)

    def _on_upload_pending(self):
        if not self._upload_pending_cb:
            return
        self.btn_upload_pending.configure(
            state="disabled", text="⏳  Subiendo...",
            fg_color=COLORS["btn_disabled_bg"], cursor="",
        )
        def worker():
            try:
                self._upload_pending_cb(on_progress=lambda m: self.after(0, lambda: self.log(m)))
            finally:
                self.after(0, lambda: self.btn_upload_pending.configure(
                    state="normal", text="⬆  Subir pendientes",
                    fg_color=COLORS["btn_secondary"], cursor="hand2",
                ))
        threading.Thread(target=worker, daemon=True).start()

    def _on_sync(self):
        if not self._sync_cb:
            return
        self.btn_sync.configure(
            state="disabled", text="⏳  Sincronizando...",
            fg_color=COLORS["btn_disabled_bg"], cursor="",
        )
        def worker():
            try:
                self._sync_cb(on_progress=lambda m: self.after(0, lambda: self.log(m)))
            finally:
                self.after(0, lambda: self.btn_sync.configure(
                    state="normal", text="☁  Sincronizar desde Drive",
                    fg_color=COLORS["btn_secondary"], cursor="hand2",
                ))
        threading.Thread(target=worker, daemon=True).start()

    def _on_execute(self):
        if self._run_callback:
            self._run_callback()

    def _on_stop(self):
        if self._stop_cb:
            self._stop_cb()
        self.btn_stop.configure(state="disabled", fg_color=COLORS["btn_disabled_bg"], cursor="")

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

        self.btn_download_report.configure(state="disabled", fg_color=COLORS["btn_disabled_bg"], cursor="")
        self._log(f"[Inventario] Generando reporte en {file_path}...")

        def worker():
            try:
                generate_excel_report(file_path, entries, title="Inventario de documentos descargados")
                self._log(f"[Inventario] Reporte guardado en {file_path}")
            except Exception as e:
                self._log(f"[Inventario] Error al generar reporte: {e}")
            finally:
                self.after(0, lambda: self.btn_download_report.configure(
                    state="normal", fg_color=COLORS["btn_primary"], cursor="hand2"
                ))

        threading.Thread(target=worker, daemon=True).start()
