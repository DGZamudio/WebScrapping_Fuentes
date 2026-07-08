import customtkinter as ctk
from ui.theme import COLORS, FONTS, NAV_WIDTH

_ICONS = {
    "dashboard":     "⊞",
    "consola":       "▶",
    "configuracion": "⚙",
    "estadisticas":  "📊",
}


class NavMenu(ctk.CTkFrame):
    """Modern dark sidebar navigation."""

    def __init__(self, parent, controller=None):
        super().__init__(parent, fg_color=COLORS["sidebar"], width=NAV_WIDTH, corner_radius=0)
        self.controller = controller
        self.pack_propagate(False)
        self.buttons = {}
        self.active_button = None
        self._indicators = {}
        self._build_header()

    def _build_header(self):
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(24, 16))

        ctk.CTkLabel(
            logo_frame, text="IURISYNC",
            text_color=COLORS["sidebar_title"], fg_color="transparent",
            font=FONTS["nav_title"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame, text="Sistema de Descarga Legal",
            text_color=COLORS["sidebar_text"], fg_color="transparent",
            font=FONTS["caption"],
        ).pack(anchor="w")

        ctk.CTkFrame(self, fg_color=COLORS["sidebar_section"], height=1, corner_radius=0).pack(
            fill="x", padx=20, pady=(0, 4)
        )

        ctk.CTkLabel(
            self, text="NAVEGACIÓN",
            text_color=COLORS["sidebar_section"], fg_color="transparent",
            font=FONTS["nav_section"],
        ).pack(anchor="w", padx=20, pady=(10, 6))

    def add_button(self, name, label, callback):
        icon = _ICONS.get(name, "•")

        container = ctk.CTkFrame(self, fg_color=COLORS["sidebar"], corner_radius=0)
        container.pack(fill="x", pady=1)

        indicator = ctk.CTkFrame(container, fg_color=COLORS["sidebar"], width=4, height=1, corner_radius=0)
        indicator.pack(side="left", fill="y")

        btn = ctk.CTkButton(
            container,
            text=f"  {icon}   {label}",
            fg_color=COLORS["sidebar"],
            hover_color=COLORS["sidebar_hover"],
            text_color=COLORS["sidebar_text"],
            font=FONTS["nav_item"],
            anchor="w",
            corner_radius=0,
            border_width=0,
            command=lambda n=name, cb=callback: self._on_click(n, cb),
        )
        btn.pack(fill="x", side="left", expand=True, ipady=4)

        self.buttons[name] = btn
        self._indicators[name] = indicator

        if name == "configuracion":
            ctk.CTkFrame(self, fg_color=COLORS["sidebar_section"], height=1, corner_radius=0).pack(
                fill="x", padx=20, pady=(12, 0)
            )
            footer = ctk.CTkFrame(self, fg_color="transparent")
            footer.pack(side="bottom", fill="x", padx=20, pady=14)
            ctk.CTkLabel(
                footer, text="Avance Jurídico  ·  v1.0",
                text_color=COLORS["sidebar_section"], fg_color="transparent",
                font=FONTS["caption"],
            ).pack(anchor="w")

    def _on_click(self, name, callback):
        self.set_active(name)
        callback()

    def set_active(self, name):
        if self.active_button and self.active_button in self.buttons:
            prev = self.active_button
            self.buttons[prev].configure(fg_color=COLORS["sidebar"], text_color=COLORS["sidebar_text"])
            self._indicators[prev].configure(fg_color=COLORS["sidebar"])

        self.active_button = name
        if name in self.buttons:
            self.buttons[name].configure(
                fg_color=COLORS["sidebar_active"], text_color=COLORS["sidebar_text_active"]
            )
            self._indicators[name].configure(fg_color=COLORS["sidebar_active_bar"])
