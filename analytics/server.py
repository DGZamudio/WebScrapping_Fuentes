import logging
import socket
import threading

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

_port: int | None = None


def _disponible(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.connect_ex(("127.0.0.1", port)) != 0


def start_server() -> int | None:
    global _port
    for candidato in (5050, 5051, 5052):
        if _disponible(candidato):
            _port = candidato
            t = threading.Thread(
                target=lambda: app.run(
                    host="127.0.0.1", port=_port,
                    debug=False, use_reloader=False,
                ),
                daemon=True,
            )
            t.start()
            logging.info(f"Dashboard analytics en http://127.0.0.1:{_port}")
            return _port
    logging.warning("Analytics server: puertos 5050-5052 ocupados — dashboard deshabilitado")
    return None


@app.route("/")
def index():
    return render_template("dashboard.html", port=_port)


@app.route("/api/datos")
def api_datos():
    from analytics.data import SheetsDataLoader
    from analytics.metrics import (
        actividad_diaria,
        distribucion_por_tipo,
        estado_fuentes,
        kpis,
        volumen_por_mes,
    )
    from db.memory import Memory

    fuente = request.args.get("fuente") or None
    desde  = request.args.get("desde")  or None
    hasta  = request.args.get("hasta")  or None

    db = Memory()

    # Sheets (puede no estar disponible)
    df_raw = None
    try:
        df_raw = SheetsDataLoader().load()
    except Exception as e:
        logging.warning(f"api_datos: Sheets no disponible ({e})")

    # df filtrado para gráficas
    df = None
    if df_raw is not None:
        df = df_raw.copy()
        if fuente:
            df = df[df["Fuente"] == fuente]
        if desde:
            df = df[df["Fecha Publicación"] >= desde]
        if hasta:
            df = df[df["Fecha Publicación"] <= hasta]
        if df.empty:
            df = None

    # KPIs (usan df filtrado para pct_drive, memory.db para conteos)
    kpis_data = kpis(db, df=df, fuente=fuente)

    # Actividad diaria (memory.db, rango aplicado)
    act = actividad_diaria(db, desde=desde, hasta=hasta, fuente=fuente)

    # Volumen mensual por fuente (Sheets, df filtrado)
    volumen: dict = {"meses": [], "series": {}}
    if df is not None:
        try:
            vol_df = volumen_por_mes(df)
            volumen["meses"] = list(vol_df.index)
            volumen["series"] = {col: list(map(int, vol_df[col])) for col in vol_df.columns}
        except Exception as e:
            logging.warning(f"api_datos: volumen_por_mes falló ({e})")

    # Top 20 tipos (Sheets, df filtrado)
    top_tipos: list = []
    if df is not None:
        try:
            tipos = distribucion_por_tipo(df).head(20)
            top_tipos = [{"tipo": t, "total": int(c)} for t, c in tipos.items()]
        except Exception as e:
            logging.warning(f"api_datos: distribucion_por_tipo falló ({e})")

    # Estado fuentes (Sheets sin filtro de fuente para mostrar todas)
    estado: list = []
    df_estado = df_raw
    if df_estado is not None:
        if desde:
            df_estado = df_estado[df_estado["Fecha Publicación"] >= desde]
        if hasta:
            df_estado = df_estado[df_estado["Fecha Publicación"] <= hasta]
    if df_estado is not None and not df_estado.empty:
        try:
            est_df = estado_fuentes(df_estado)
            for _, r in est_df.iterrows():
                estado.append({
                    "fuente": r["Fuente"],
                    "ultima_captura": str(r["ultima_captura"]),
                    "dias_inactivo": int(r["dias_inactivo"]),
                    "estado": r["estado"],
                    "total_docs": db.total_docs(r["Fuente"]),
                })
        except Exception as e:
            logging.warning(f"api_datos: estado_fuentes falló ({e})")

    # Lista de fuentes para el filtro (memory.db)
    with db.get_conn() as conn:
        fuentes_lista = [
            r[0] for r in conn.execute(
                "SELECT DISTINCT source FROM downloaded ORDER BY source"
            ).fetchall()
        ]

    return jsonify({
        "kpis": kpis_data,
        "actividad_diaria": act,
        "volumen_mensual": volumen,
        "top_tipos": top_tipos,
        "estado_fuentes": estado,
        "fuentes": fuentes_lista,
    })
