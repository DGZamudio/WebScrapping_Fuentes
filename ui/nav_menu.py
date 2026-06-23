import tkinter as tk
from ui.theme import COLORS, FONTS, NAV_WIDTH

_ICONS = {
    "dashboard":    "⊞",
    "consola":      "▶",
    "configuracion": "⚙",
}


class NavMenu(tk.Frame):
    """Modern dark sidebar navigation."""

    def __init__(self, parent, controller=None):
        super().__init__(parent, bg=COLORS["sidebar"], width=NAV_WIDTH)
        self.controller = controller
        self.pack_propagate(False)
        self.buttons = {}
        self.active_button = None
        self._containers = {}
        self._indicators = {}
        self._build_header()

    def _build_header(self):
        logo_frame = tk.Frame(self, bg=COLORS["sidebar"])
        logo_frame.pack(fill="x", padx=20, pady=(24, 16))

        tk.Label(
            logo_frame,
            text="IURISYNC",
            bg=COLORS["sidebar"],
            fg=COLORS["sidebar_title"],
            font=FONTS["nav_title"],
        ).pack(anchor="w")

        tk.Label(
            logo_frame,
            text="Sistema de Descarga Legal",
            bg=COLORS["sidebar"],
            fg=COLORS["sidebar_text"],
            font=FONTS["caption"],
        ).pack(anchor="w")

        tk.Frame(self, bg=COLORS["sidebar_section"], height=1).pack(
            fill="x", padx=20, pady=(0, 4)
        )

        tk.Label(
            self,
            text="NAVEGACIÓN",
            bg=COLORS["sidebar"],
            fg=COLORS["sidebar_section"],
            font=FONTS["nav_section"],
        ).pack(anchor="w", padx=20, pady=(10, 6))

    def add_button(self, name, label, callback):
        icon = _ICONS.get(name, "•")

        container = tk.Frame(self, bg=COLORS["sidebar"])
        container.pack(fill="x", pady=1)

        indicator = tk.Frame(container, bg=COLORS["sidebar"], width=4)
        indicator.pack(side="left", fill="y")

        btn = tk.Label(
            container,
            text=f"  {icon}   {label}",
            bg=COLORS["sidebar"],
            fg=COLORS["sidebar_text"],
            font=FONTS["nav_item"],
            anchor="w",
            cursor="hand2",
            padx=10,
            pady=11,
        )
        btn.pack(fill="x", side="left", expand=True)

        btn.bind("<Enter>",    lambda e, b=btn, n=name: self._on_hover(b, n))
        btn.bind("<Leave>",    lambda e, b=btn, n=name: self._on_leave(b, n))
        btn.bind("<Button-1>", lambda e, n=name, cb=callback: self._on_click(n, cb))
        container.bind("<Button-1>", lambda e, n=name, cb=callback: self._on_click(n, cb))

        self.buttons[name] = btn
        self._containers[name] = container
        self._indicators[name] = indicator

        # Version footer after the last known nav item
        if name == "configuracion":
            tk.Frame(self, bg=COLORS["sidebar_section"], height=1).pack(
                fill="x", padx=20, pady=(12, 0)
            )
            footer = tk.Frame(self, bg=COLORS["sidebar"])
            footer.pack(side="bottom", fill="x", padx=20, pady=14)
            tk.Label(
                footer,
                text="Avance Jurídico  ·  v1.0",
                bg=COLORS["sidebar"],
                fg=COLORS["sidebar_section"],
                font=FONTS["caption"],
            ).pack(anchor="w")

    def _on_hover(self, btn, name):
        if name != self.active_button:
            btn.config(bg=COLORS["sidebar_hover"], fg=COLORS["sidebar_text_active"])
            self._containers[name].config(bg=COLORS["sidebar_hover"])

    def _on_leave(self, btn, name):
        if name != self.active_button:
            btn.config(bg=COLORS["sidebar"], fg=COLORS["sidebar_text"])
            self._containers[name].config(bg=COLORS["sidebar"])

    def _on_click(self, name, callback):
        self.set_active(name)
        callback()

    def set_active(self, name):
        if self.active_button and self.active_button in self.buttons:
            prev = self.active_button
            self.buttons[prev].config(bg=COLORS["sidebar"], fg=COLORS["sidebar_text"])
            self._containers[prev].config(bg=COLORS["sidebar"])
            self._indicators[prev].config(bg=COLORS["sidebar"])

        self.active_button = name
        if name in self.buttons:
            self.buttons[name].config(
                bg=COLORS["sidebar_active"], fg=COLORS["sidebar_text_active"]
            )
            self._containers[name].config(bg=COLORS["sidebar_active"])
            self._indicators[name].config(bg=COLORS["sidebar_active_bar"])
