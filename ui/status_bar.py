import tkinter as tk
from ui.theme import COLORS, FONTS


class StatusBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["statusbar"], height=26)
        self.pack_propagate(False)

        self._dot = tk.Label(
            self, text="●",
            bg=COLORS["statusbar"], fg=COLORS["success"],
            font=("Segoe UI", 8),
        )
        self._dot.pack(side="left", padx=(12, 4))

        self.label = tk.Label(
            self, text="Sistema listo",
            bg=COLORS["statusbar"], fg=COLORS["statusbar_text"],
            font=FONTS["small"], anchor="w",
        )
        self.label.pack(side="left", fill="x", expand=True)

        tk.Label(
            self, text="IURISYNC  ",
            bg=COLORS["statusbar"], fg=COLORS["sidebar_section"],
            font=("Segoe UI", 8, "bold"),
        ).pack(side="right")

    def set_status(self, text):
        self.label.config(text=text)
        m = text.lower()
        if any(k in m for k in ["error", "exception", "excepción"]):
            color = COLORS["error"]
        elif any(k in m for k in ["✓", "guardado", "completado"]):
            color = COLORS["success"]
        elif any(k in m for k in ["iniciando", "descargando", "ejecutando"]):
            color = COLORS["warning"]
        else:
            color = COLORS["success"]
        self._dot.config(fg=color)
