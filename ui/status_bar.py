import customtkinter as ctk
from ui.theme import COLORS, FONTS


class StatusBar(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["statusbar"], height=26, corner_radius=0)
        self.pack_propagate(False)

        self._dot = ctk.CTkLabel(
            self, text="●",
            text_color=COLORS["success"], fg_color="transparent",
            font=("Segoe UI", 8),
        )
        self._dot.pack(side="left", padx=(12, 4))

        self.label = ctk.CTkLabel(
            self, text="Sistema listo",
            text_color=COLORS["statusbar_text"], fg_color="transparent",
            font=FONTS["small"], anchor="w",
        )
        self.label.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            self, text="IURISYNC  ",
            text_color=COLORS["sidebar_section"], fg_color="transparent",
            font=("Segoe UI", 8, "bold"),
        ).pack(side="right")

    def set_status(self, text):
        self.label.configure(text=text)
        m = text.lower()
        if any(k in m for k in ["error", "exception", "excepción"]):
            color = COLORS["error"]
        elif any(k in m for k in ["✓", "guardado", "completado"]):
            color = COLORS["success"]
        elif any(k in m for k in ["iniciando", "descargando", "ejecutando"]):
            color = COLORS["warning"]
        else:
            color = COLORS["success"]
        self._dot.configure(text_color=color)
