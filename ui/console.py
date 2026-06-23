import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from datetime import datetime

from ui.theme import COLORS, FONTS


def _btn(parent, text, command, style="primary"):
    palettes = {
        "success":   (COLORS["btn_success"],   COLORS["btn_success_hover"]),
        "danger":    (COLORS["btn_danger"],    COLORS["btn_danger_hover"]),
        "secondary": (COLORS["btn_secondary"], COLORS["btn_secondary_hover"]),
    }
    bg, hover = palettes.get(style, palettes["success"])
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=COLORS["btn_text"],
        activebackground=hover,
        activeforeground=COLORS["btn_text"],
        disabledforeground=COLORS["btn_disabled_fg"],
        font=FONTS["body_bold"],
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=12,
        pady=6,
    )


class Console(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg=COLORS["bg"])
        self.controller = controller
        self._run_cb = None
        self._stop_cb = None
        self._build()

    def _build(self):
        # ── Page header ───────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", padx=24, pady=(24, 0))

        tk.Label(
            header, text="Consola",
            bg=COLORS["bg"], fg=COLORS["text"], font=FONTS["h1"],
        ).pack(side="left")

        btn_area = tk.Frame(header, bg=COLORS["bg"])
        btn_area.pack(side="right")

        self._clear_btn = _btn(btn_area, "✕  Limpiar", self._on_clear, "secondary")
        self._clear_btn.pack(side="right", padx=(8, 0))

        self.stop_btn = _btn(btn_area, "■  Parar", self._on_stop, "danger")
        self.stop_btn.config(
            state="disabled",
            bg=COLORS["btn_disabled_bg"],
            cursor="",
        )
        self.stop_btn.pack(side="right", padx=(8, 0))

        self.start_btn = _btn(btn_area, "▶  Ejecutar", self._on_start, "success")
        self.start_btn.pack(side="right")

        tk.Frame(self, bg=COLORS["card_border"], height=1).pack(
            fill="x", padx=24, pady=(14, 0)
        )

        # ── Terminal window ───────────────────────────────────────────────────
        term_outer = tk.Frame(
            self,
            bg=COLORS["console_bg"],
            highlightbackground=COLORS["card_border"],
            highlightthickness=1,
        )
        term_outer.pack(fill="both", expand=True, padx=24, pady=16)

        # macOS-style title bar
        titlebar = tk.Frame(term_outer, bg=COLORS["console_title"])
        titlebar.pack(fill="x")

        tk.Label(
            titlebar, text="  ● ● ●",
            bg=COLORS["console_title"], fg="#3d5068",
            font=("Segoe UI", 9),
        ).pack(side="left", pady=6)

        tk.Label(
            titlebar, text="Terminal  —  IURISYNC",
            bg=COLORS["console_title"], fg=COLORS["console_muted"],
            font=FONTS["caption"],
        ).pack(side="left", padx=10)

        # Text area
        self.log_area = ScrolledText(
            term_outer,
            wrap="word",
            bg=COLORS["console_bg"],
            fg=COLORS["console_text"],
            font=FONTS["mono"],
            relief="flat",
            padx=16,
            pady=10,
            insertbackground=COLORS["console_text"],
            selectbackground="#1e3a5f",
            selectforeground=COLORS["console_text"],
        )
        self.log_area.pack(fill="both", expand=True)

        # Colour tags
        self.log_area.tag_config("ts",      foreground=COLORS["console_ts"])
        self.log_area.tag_config("success", foreground=COLORS["console_success"])
        self.log_area.tag_config("error",   foreground=COLORS["console_error"])
        self.log_area.tag_config("warning", foreground=COLORS["console_warning"])
        self.log_area.tag_config("info",    foreground=COLORS["console_info"])
        self.log_area.tag_config("muted",   foreground=COLORS["console_muted"])

    # ------------------------------------------------------------------- API

    def set_run_callback(self, cb):
        self._run_cb = cb

    def set_stop_callback(self, cb):
        self._stop_cb = cb

    def set_running(self, running: bool):
        if running:
            self.start_btn.config(
                state="disabled", bg=COLORS["btn_disabled_bg"], cursor=""
            )
            self.stop_btn.config(
                state="normal", bg=COLORS["btn_danger"], cursor="hand2"
            )
        else:
            self.start_btn.config(
                state="normal", bg=COLORS["btn_success"], cursor="hand2"
            )
            self.stop_btn.config(
                state="disabled", bg=COLORS["btn_disabled_bg"], cursor=""
            )

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert("end", f"[{ts}]  ", "ts")
        self.log_area.insert("end", msg + "\n", self._tag(msg))
        self.log_area.see("end")

    # ---------------------------------------------------------------- private

    def _tag(self, msg):
        m = msg.lower()
        if any(k in m for k in ["error", "exception", "excepción", "✗"]):
            return "error"
        if any(k in m for k in ["✓", "guardado", "completado", "éxito", "ok]"]):
            return "success"
        if any(k in m for k in ["advertencia", "warning", "skip", "omitido"]):
            return "warning"
        if any(k in m for k in ["iniciando", "descargando", "[scheduler]", "[inventario]", "ejecutando"]):
            return "info"
        return "muted"

    def _on_start(self):
        if self._run_cb:
            self.start_btn.config(
                state="disabled", bg=COLORS["btn_disabled_bg"], cursor=""
            )
            self.stop_btn.config(
                state="normal", bg=COLORS["btn_danger"], cursor="hand2"
            )
            self.log("Iniciando...")
            self._run_cb()

    def _on_stop(self):
        self.log("Parando...")
        if self._stop_cb and callable(self._stop_cb):
            try:
                self._stop_cb()
            except Exception:
                pass

    def _on_clear(self):
        self.log_area.delete("1.0", "end")
