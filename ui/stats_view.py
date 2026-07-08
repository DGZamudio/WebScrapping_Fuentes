import webbrowser

import customtkinter as ctk

from ui.theme import COLORS, FONTS, CORNER_RADIUS


class StatsView(ctk.CTkFrame):
    def __init__(self, parent, app, port: int | None = None):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._port = port

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", side="top", padx=20, pady=12)
        ctk.CTkLabel(
            header, text="Estadísticas",
            font=FONTS["h1"], fg_color="transparent", text_color=COLORS["text"],
        ).pack(side="left")

        centro = ctk.CTkFrame(self, fg_color="transparent")
        centro.place(relx=0.5, rely=0.45, anchor="center")

        if port is not None:
            ctk.CTkLabel(
                centro,
                text="El dashboard se abre en tu navegador",
                font=FONTS["body"], fg_color="transparent", text_color=COLORS["text_muted"],
            ).pack(pady=(0, 20))

            ctk.CTkButton(
                centro,
                text="  Abrir dashboard  ",
                font=FONTS["body_bold"],
                fg_color=COLORS["btn_primary"], hover_color=COLORS["btn_primary_hover"],
                text_color=COLORS["btn_text"], corner_radius=CORNER_RADIUS,
                command=self._abrir,
            ).pack()

            ctk.CTkLabel(
                centro,
                text=f"Servidor activo en http://127.0.0.1:{port}",
                font=FONTS["small"], fg_color="transparent", text_color=COLORS["text_muted"],
            ).pack(pady=(14, 0))
        else:
            ctk.CTkLabel(
                centro,
                text="Dashboard no disponible\n(puertos 5050-5052 ocupados)",
                font=FONTS["body"], fg_color="transparent", text_color=COLORS["text_muted"],
                justify="center",
            ).pack()

    def _abrir(self):
        webbrowser.open(f"http://127.0.0.1:{self._port}")
