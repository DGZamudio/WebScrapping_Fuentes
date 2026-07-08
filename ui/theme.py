import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COLORS = {
    # Sidebar
    "sidebar":             "#1a2332",
    "sidebar_hover":       "#243447",
    "sidebar_active":      "#1e3a5f",
    "sidebar_active_bar":  "#4a9eff",
    "sidebar_text":        "#7a96b0",
    "sidebar_text_active": "#ffffff",
    "sidebar_title":       "#ffffff",
    "sidebar_section":     "#3a5068",

    # Content
    "bg":          "#f0f4f8",
    "card":        "#ffffff",
    "card_border": "#e2e8f0",

    # Text
    "text":             "#1a202c",
    "text_secondary":   "#4a5568",
    "text_muted":       "#718096",

    # Semantic
    "success":  "#38a169",
    "warning":  "#d69e2e",
    "error":    "#e53e3e",
    "info":     "#3182ce",
    "accent":   "#4a9eff",

    # Buttons (bg, hover)
    "btn_primary":        "#4a9eff",
    "btn_primary_hover":  "#2b85f0",
    "btn_success":        "#38a169",
    "btn_success_hover":  "#2f855a",
    "btn_danger":         "#e53e3e",
    "btn_danger_hover":   "#c53030",
    "btn_secondary":      "#718096",
    "btn_secondary_hover":"#4a5568",
    "btn_disabled_bg":    "#e2e8f0",
    "btn_disabled_fg":    "#a0aec0",
    "btn_text":           "#ffffff",

    # Status bar
    "statusbar":      "#111b27",
    "statusbar_text": "#7a96b0",

    # Console / terminal
    "console_bg":      "#0f1923",
    "console_title":   "#0b1520",
    "console_text":    "#cdd9e5",
    "console_success": "#56d364",
    "console_error":   "#ff7b72",
    "console_warning": "#e3b341",
    "console_info":    "#79c0ff",
    "console_muted":   "#4a5568",
    "console_ts":      "#3d5068",
}

FONTS = {
    "app_title":   ("Segoe UI", 13, "bold"),
    "nav_title":   ("Segoe UI", 15, "bold"),
    "nav_item":    ("Segoe UI", 10),
    "nav_section": ("Segoe UI", 7, "bold"),
    "h1":          ("Segoe UI", 18, "bold"),
    "h2":          ("Segoe UI", 14, "bold"),
    "h3":          ("Segoe UI", 11, "bold"),
    "body":        ("Segoe UI", 10),
    "body_bold":   ("Segoe UI", 10, "bold"),
    "small":       ("Segoe UI", 9),
    "caption":     ("Segoe UI", 8),
    "stat_number": ("Segoe UI", 30, "bold"),
    "stat_label":  ("Segoe UI", 8),
    "timer":       ("Segoe UI", 26, "bold"),
    "mono":        ("Consolas", 9),
}

NAV_WIDTH = 220

CORNER_RADIUS = 8
BORDER_WIDTH = 1
