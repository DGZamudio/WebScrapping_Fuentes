import tkinter as tk
import webbrowser

from ui.theme import COLORS, FONTS


class StatsView(tk.Frame):
    def __init__(self, parent, app, port: int | None = None):
        super().__init__(parent, bg=COLORS["bg"])
        self._port = port

        header = tk.Frame(self, bg=COLORS["bg"], pady=12, padx=20)
        header.pack(fill="x", side="top")
        tk.Label(
            header, text="Estadísticas",
            font=FONTS["h1"], bg=COLORS["bg"], fg=COLORS["text"],
        ).pack(side="left")

        centro = tk.Frame(self, bg=COLORS["bg"])
        centro.place(relx=0.5, rely=0.45, anchor="center")

        if port is not None:
            tk.Label(
                centro,
                text="El dashboard se abre en tu navegador",
                font=FONTS["body"], bg=COLORS["bg"], fg=COLORS["text_muted"],
            ).pack(pady=(0, 20))

            tk.Button(
                centro,
                text="  Abrir dashboard  ",
                font=FONTS["body_bold"],
                bg=COLORS["btn_primary"], fg=COLORS["btn_text"],
                relief="flat", padx=20, pady=10,
                cursor="hand2",
                command=self._abrir,
            ).pack()

            tk.Label(
                centro,
                text=f"Servidor activo en http://127.0.0.1:{port}",
                font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text_muted"],
            ).pack(pady=(14, 0))
        else:
            tk.Label(
                centro,
                text="Dashboard no disponible\n(puertos 5050-5052 ocupados)",
                font=FONTS["body"], bg=COLORS["bg"], fg=COLORS["text_muted"],
                justify="center",
            ).pack()

    def _abrir(self):
        webbrowser.open(f"http://127.0.0.1:{self._port}")
