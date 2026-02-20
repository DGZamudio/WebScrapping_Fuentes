import tkinter as tk


class DashBoard(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self._build()

    def _build(self):
        title = tk.Label(self, text="Panel de Control General", font=("Arial", 14, "bold"))
        title.grid(row=0, columnspan=3, padx=10, pady=10)

        # Date range settings
        frame_docs = tk.LabelFrame(self, text="Total descargas", width=250, padx=10, pady=10)
        frame_docs.grid(row=1, column=0, padx=10, pady=10)

        self.total_docs_label = tk.Label(frame_docs, text="Cargando...")
        self.total_docs_label.pack(anchor="w")


        frame_enti = tk.LabelFrame(self, text="Fuentes", width=250, padx=10, pady=10)
        frame_enti.grid(row=1, column=1, padx=10, pady=10)

        self.total_enti_label = tk.Label(frame_enti, text="Cargando...")
        self.total_enti_label.pack(anchor="w")


        frame_estado = tk.LabelFrame(self, text="Estado del sistema", width=250, padx=10, pady=10)
        frame_estado.grid(row=1, column=2, padx=10, pady=10)

        self.estado_label = tk.Label(frame_estado, text="OK ✔")
        self.estado_label.pack(anchor="w")

    def update_total(self, count: int):
        """Update the displayed total documents count."""
        self.total_docs_label.config(text=str(count))