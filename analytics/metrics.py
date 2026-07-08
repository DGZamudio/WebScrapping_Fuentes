from datetime import date

import pandas as pd


def volumen_por_mes(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot: índice=mes (YYYY-MM), columnas=Fuente, valores=conteo."""
    tmp = df.copy()
    tmp["Mes"] = tmp["Fecha Publicación"].dt.to_period("M")
    pivot = (
        tmp.groupby(["Mes", "Fuente"])
        .size()
        .unstack(fill_value=0)
    )
    pivot.index = pivot.index.astype(str)
    return pivot


def distribucion_por_tipo(df: pd.DataFrame) -> pd.Series:
    """Conteo por Tipo, ordenado descendente."""
    return df["Tipo"].value_counts()


def estado_fuentes(df: pd.DataFrame) -> pd.DataFrame:
    """Columnas: Fuente, ultima_captura (date), dias_inactivo (int), estado (str)."""
    hoy = date.today()
    df_valido = df.dropna(subset=["Fecha Captura"])
    if df_valido.empty:
        return pd.DataFrame(columns=["Fuente", "ultima_captura", "dias_inactivo", "estado"])
    resultado = (
        df_valido.groupby("Fuente")["Fecha Captura"]
        .max()
        .reset_index()
        .rename(columns={"Fecha Captura": "ultima_captura"})
    )
    resultado["ultima_captura"] = resultado["ultima_captura"].dt.date
    resultado["dias_inactivo"] = resultado["ultima_captura"].apply(
        lambda d: (hoy - d).days
    )
    resultado["estado"] = resultado["dias_inactivo"].apply(
        lambda d: "Activa" if d <= 7 else "Inactiva"
    )
    return resultado


def kpis(db, df=None, fuente: str | None = None) -> dict:
    """KPIs operativos: combina memory.db (siempre) con Sheets (opcional)."""
    from datetime import date, timedelta

    hace7 = (date.today() - timedelta(days=7)).isoformat()

    with db.get_conn() as conn:
        if fuente:
            total = conn.execute(
                "SELECT COUNT(*) FROM downloaded WHERE source = ?", (fuente,)
            ).fetchone()[0]
            esta_semana = conn.execute(
                "SELECT COUNT(*) FROM downloaded WHERE downloaded_at >= ? AND source = ?",
                (hace7, fuente),
            ).fetchone()[0]
        else:
            total = conn.execute("SELECT COUNT(*) FROM downloaded").fetchone()[0]
            esta_semana = conn.execute(
                "SELECT COUNT(*) FROM downloaded WHERE downloaded_at >= ?", (hace7,)
            ).fetchone()[0]

        fuentes_activas = conn.execute(
            "SELECT COUNT(DISTINCT source) FROM downloaded WHERE downloaded_at >= ?", (hace7,)
        ).fetchone()[0]
        fuentes_total = conn.execute(
            "SELECT COUNT(DISTINCT source) FROM downloaded"
        ).fetchone()[0]

    pct_drive = None
    if df is not None and "Enlace Drive" in df.columns and len(df) > 0:
        con_drive = df["Enlace Drive"].astype(str).str.strip().ne("").sum()
        pct_drive = round(100 * int(con_drive) / len(df))

    return {
        "total": total,
        "esta_semana": esta_semana,
        "fuentes_activas": fuentes_activas,
        "fuentes_total": fuentes_total,
        "pct_drive": pct_drive,
    }


def actividad_diaria(db, desde: str | None = None, hasta: str | None = None, fuente: str | None = None) -> list:
    """Documentos descargados por día según memory.db (usa downloaded_at)."""
    from datetime import date, timedelta

    if hasta is None:
        hasta = date.today().isoformat()
    if desde is None:
        desde = (date.today() - timedelta(days=29)).isoformat()

    with db.get_conn() as conn:
        if fuente:
            rows = conn.execute(
                "SELECT DATE(downloaded_at) as fecha, COUNT(*) as total "
                "FROM downloaded "
                "WHERE DATE(downloaded_at) BETWEEN ? AND ? AND source = ? "
                "GROUP BY fecha ORDER BY fecha",
                (desde, hasta, fuente),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT DATE(downloaded_at) as fecha, COUNT(*) as total "
                "FROM downloaded "
                "WHERE DATE(downloaded_at) BETWEEN ? AND ? "
                "GROUP BY fecha ORDER BY fecha",
                (desde, hasta),
            ).fetchall()

    return [{"fecha": r[0], "total": r[1]} for r in rows]
