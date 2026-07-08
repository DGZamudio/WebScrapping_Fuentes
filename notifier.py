import logging
import sys


class Notifier:
    TITULO = "IURISYNC"

    def notify(self, total: int, fuente: str = None) -> None:
        """Muestra notificación solo si hay documentos nuevos. Nunca lanza excepciones."""
        if total <= 0:
            return
        s = "s" if total != 1 else ""
        if fuente:
            mensaje = f"{fuente}: {total} documento{s} nuevo{s}"
        else:
            mensaje = f"{total} documento{s} nuevo{s} descargado{s}"
        try:
            if self._es_windows_10_o_superior():
                self._toast(mensaje)
            else:
                self._messagebox(mensaje)
        except Exception as e:
            logging.warning(f"Notifier: no se pudo mostrar notificación ({e})")

    def _es_windows_10_o_superior(self) -> bool:
        return sys.getwindowsversion().major >= 10

    def _toast(self, mensaje: str) -> None:
        from winotify import Notification
        Notification(app_id=self.TITULO, title=self.TITULO, msg=mensaje).show()

    def _messagebox(self, mensaje: str) -> None:
        import ctypes
        MB_ICONINFORMATION = 0x40
        ctypes.windll.user32.MessageBoxW(None, mensaje, self.TITULO, MB_ICONINFORMATION)
