import tkinter as tk
from tkinter.scrolledtext import ScrolledText


class Console(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self._run_cb = None
        self._build()

    def _build(self):
        top = tk.Frame(self)
        top.pack(fill="x", padx=0, pady=(0, 8))

        self.start_btn = tk.Button(top, text="Ejecutar", command=self._on_start)
        self.start_btn.pack(side="left", padx=4)

        self.stop_btn = tk.Button(top, text="Parar", state="disabled", command=self._on_stop)
        self.stop_btn.pack(side="left", padx=4)

        self.log_area = ScrolledText(self, wrap="word", height=20)
        self.log_area.pack(fill="both", expand=True)

    def set_run_callback(self, cb):
        self._run_cb = cb

    def set_stop_callback(self, cb):
        """Register a callable to be invoked when the Stop button is pressed."""
        self._stop_cb = cb

    def set_running(self, running: bool):
        """Update button states according to running status."""
        if running:
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
        else:
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")

    def _on_start(self):
        if self._run_cb:
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.log("Iniciando...")
            self._run_cb()

    def _on_stop(self):
        self.log("Parando...")
        if hasattr(self, "_stop_cb") and callable(self._stop_cb):
            try:
                self._stop_cb()
            except Exception:
                pass

    def log(self, msg):
        self.log_area.insert("end", msg + "\n")
        self.log_area.see("end")
