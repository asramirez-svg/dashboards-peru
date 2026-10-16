"""Cliente mínimo para la API REST pública del BCRP (BCRPData).

Documentación: https://estadisticas.bcrp.gob.pe/estadisticas/series/ayuda/api
No requiere API key.
"""
from __future__ import annotations

import pandas as pd
import requests

BASE_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"


def get_series(codigo: str, periodo_inicial: str, periodo_final: str, idioma: str = "esp") -> pd.DataFrame:
    """Descarga una serie del BCRP y la devuelve como DataFrame con columnas
    ['periodo', 'valor'].

    Parameters
    ----------
    codigo: código de la serie, ej. "PN01207PM" (buscar en
        https://estadisticas.bcrp.gob.pe/estadisticas/series/buscador)
    periodo_inicial / periodo_final: formato "AAAA-M", ej. "2020-1"
    idioma: "esp" o "ing"
    """
    url = f"{BASE_URL}/{codigo}/json/{periodo_inicial}/{periodo_final}/{idioma}"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    payload = resp.json()

    nombre_serie = payload["config"]["series"][0]["name"]
    filas = [
        {"periodo": p["name"], "valor": float(p["values"][0])}
        for p in payload["periods"]
        if p["values"][0] not in (None, "n.d.")
    ]
    df = pd.DataFrame(filas)
    df.attrs["nombre_serie"] = nombre_serie
    return df


if __name__ == "__main__":
    df = get_series("PN01207PM", "2020-1", "2024-6")
    print(df.attrs["nombre_serie"])
    print(df.head())
