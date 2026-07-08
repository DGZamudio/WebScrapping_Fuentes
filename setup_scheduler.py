"""Registra la tarea de IURISYNC en el Programador de tareas de Windows.

Uso:
    python setup_scheduler.py --hora 06:00

El argumento --hora acepta formato HH:MM en 24 horas.
Para cambiar la hora, vuelve a ejecutar el script con la nueva hora.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def registrar_tarea(hora: str) -> None:
    python_exe = sys.executable
    main_py = str(Path(__file__).parent.resolve() / "main.py")
    nombre_tarea = "IURISYNC - Scraping Diario"

    resultado = subprocess.run(
        [
            "schtasks", "/Create", "/F",
            "/TN", nombre_tarea,
            "/TR", f'"{python_exe}" "{main_py}"',
            "/SC", "DAILY",
            "/ST", hora,
        ],
        capture_output=True,
        text=True,
    )

    if resultado.returncode == 0:
        print(f"Tarea registrada: '{nombre_tarea}' a las {hora} diariamente.")
        print(f"Python: {python_exe}")
        print(f"Script: {main_py}")
    else:
        print("Error al registrar la tarea:")
        print(resultado.stderr or resultado.stdout)
        sys.exit(1)


def _validar_hora(valor: str) -> str:
    partes = valor.split(":")
    if len(partes) != 2:
        raise argparse.ArgumentTypeError("Formato inválido. Use HH:MM (ej: 06:00)")
    hh, mm = partes
    if not (hh.isdigit() and mm.isdigit() and 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59):
        raise argparse.ArgumentTypeError("Hora fuera de rango. Use HH:MM en 24 horas (ej: 06:00)")
    return f"{int(hh):02d}:{int(mm):02d}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Registra IURISYNC en el Programador de tareas de Windows."
    )
    parser.add_argument(
        "--hora",
        required=True,
        type=_validar_hora,
        help="Hora de ejecución diaria en formato HH:MM (ej: 06:00)",
    )
    args = parser.parse_args()
    registrar_tarea(args.hora)
