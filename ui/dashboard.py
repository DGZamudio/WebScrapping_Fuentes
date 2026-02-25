import tkinter as tk
from datetime import datetime, timedelta
import threading
import time
import logging

logger = logging.getLogger(__name__)


class DashBoard(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.next_run_time = None
        self.scheduler_active = False
        self.scheduler_thread = None
        self.scheduler_interval = 3600  # Default 1 hour in seconds
        self._run_callback = None
        self._log_callback = None
        self._build()

    def _build(self):
        title = tk.Label(self, text="Panel de Control General", font=("Arial", 14, "bold"))
        title.grid(row=0, columnspan=3, padx=10, pady=10)

        # Timer and console message frame
        frame_timer = tk.LabelFrame(self, text="Próximo Scrapeo", width=250, padx=10, pady=10)
        frame_timer.grid(row=1, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.timer_label = tk.Label(frame_timer, text="No programado", font=("Arial", 12, "bold"), fg="#FF9800")
        self.timer_label.pack(anchor="w", pady=5)
        
        console_message = tk.Label(
            frame_timer, 
            text="💡 Para iniciar ahora, usa el comando en la consola",
            font=("Arial", 9, "italic"),
            fg="#666"
        )
        console_message.pack(anchor="w", pady=5)

        # Date range settings
        frame_docs = tk.LabelFrame(self, text="Total descargas", width=250, padx=10, pady=10)
        frame_docs.grid(row=2, column=0, padx=10, pady=10)

        self.total_docs_label = tk.Label(frame_docs, text="Cargando...")
        self.total_docs_label.pack(anchor="w")


        frame_enti = tk.LabelFrame(self, text="Fuentes", width=250, padx=10, pady=10)
        frame_enti.grid(row=2, column=1, padx=10, pady=10)

        self.total_enti_label = tk.Label(frame_enti, text="Cargando...")
        self.total_enti_label.pack(anchor="w")


        frame_estado = tk.LabelFrame(self, text="Estado del sistema", width=250, padx=10, pady=10)
        frame_estado.grid(row=2, column=2, padx=10, pady=10)

        self.estado_label = tk.Label(frame_estado, text="OK ✔")
        self.estado_label.pack(anchor="w")
        
        # Scheduler configuration frame
        frame_scheduler = tk.LabelFrame(self, text="Configurar Scheduler", width=250, padx=10, pady=10)
        frame_scheduler.grid(row=3, columnspan=3, padx=10, pady=10, sticky="ew")
        
        # Interval input
        tk.Label(frame_scheduler, text="Intervalo (segundos):").pack(side=tk.LEFT, padx=5)
        self.interval_var = tk.StringVar(value="3600")
        interval_entry = tk.Entry(frame_scheduler, textvariable=self.interval_var, width=10)
        interval_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame_scheduler, text="(3600=1h, 1800=30m, 300=5m)").pack(side=tk.LEFT, padx=5)
        
        # Start button
        self.btn_start_scheduler = tk.Button(
            frame_scheduler,
            text="Iniciar Scheduler",
            command=self._on_start_scheduler,
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5
        )
        self.btn_start_scheduler.pack(side=tk.LEFT, padx=5)
        
        # Stop button
        self.btn_stop_scheduler = tk.Button(
            frame_scheduler,
            text="Detener",
            command=self.stop_scheduler,
            bg="#F44336",
            fg="white",
            padx=10,
            pady=5,
            state=tk.DISABLED
        )
        self.btn_stop_scheduler.pack(side=tk.LEFT, padx=5)

    def update_total(self, count: int):
        """Update the displayed total documents count."""
        self.total_docs_label.config(text=str(count))
    
    def set_run_callback(self, cb):
        """Set the callback function to call when scraping should run."""
        self._run_callback = cb
    
    def set_log_callback(self, cb):
        """Set the callback function to call for logging."""
        self._log_callback = cb
    
    def _log(self, msg):
        """Log a message using callback or logger."""
        if self._log_callback:
            self._log_callback(msg)
        else:
            logger.info(msg)
    
    def _on_start_scheduler(self):
        """Handle start scheduler button click."""
        try:
            interval = int(self.interval_var.get())
            if interval <= 0:
                raise ValueError("El intervalo debe ser mayor a 0")
            self.start_scheduler(interval)
            self.btn_start_scheduler.config(state=tk.DISABLED)
            self.btn_stop_scheduler.config(state=tk.NORMAL)
        except ValueError as e:
            self._log(f"[Error] {e}")
            self.timer_label.config(text=f"Error: {e}", fg="#F44336")
    
    def start_scheduler(self, interval: int = 3600):
        """Start the automatic scheduler with given interval in seconds."""
        if self.scheduler_active:
            self._log("[Scheduler] Ya está activo")
            return
        
        self.scheduler_interval = interval
        self.scheduler_active = True
        self.next_run_time = datetime.now() + timedelta(seconds=interval)
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self._log(f"[Scheduler] Iniciado con intervalo de {interval} segundos")
        self._update_timer_display()
    
    def stop_scheduler(self):
        """Stop the automatic scheduler."""
        self.scheduler_active = False
        self.next_run_time = None
        self.timer_label.config(text="Programador detenido", fg="#F44336")
        self.btn_start_scheduler.config(state=tk.NORMAL)
        self.btn_stop_scheduler.config(state=tk.DISABLED)
        self._log("[Scheduler] Detenido")
    
    def set_next_run(self, seconds: int):
        """Set the next scraping time (in seconds from now)."""
        self.next_run_time = datetime.now() + timedelta(seconds=seconds)
        self._update_timer_display()
    
    def _scheduler_loop(self):
        """Background thread that handles scheduled scraping."""
        while self.scheduler_active:
            if self.next_run_time:
                now = datetime.now()
                time_until_run = (self.next_run_time - now).total_seconds()
                
                if time_until_run <= 0:
                    # Time to run the scraping
                    self._log("[Scheduler] Ejecutando scrappeo automático")
                    if self._run_callback:
                        self._run_callback()
                    # Schedule next run
                    self.next_run_time = datetime.now() + timedelta(seconds=self.scheduler_interval)
                else:
                    # Sleep for a bit before checking again
                    time.sleep(min(1, time_until_run))
            else:
                time.sleep(1)
    
    def _update_timer_display(self):
        """Update the timer display with countdown."""
        if self.next_run_time:
            now = datetime.now()
            time_diff = self.next_run_time - now
            
            if time_diff.total_seconds() > 0:
                hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                countdown = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.timer_label.config(text=f"Próximo scrapeo en: {countdown}", fg="#FF9800")
                
                # Schedule next update in 1 second
                self.after(1000, self._update_timer_display)
            else:
                self.timer_label.config(text="Ejecutando scrappeo...", fg="#2196F3")
        else:
            self.timer_label.config(text="No programado", fg="#666")