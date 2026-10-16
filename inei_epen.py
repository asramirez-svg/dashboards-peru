"""Wrangling de la Encuesta Permanente de Empleo Nacional (EPEN) del INEI.

Fuente: Plataforma Nacional de Datos Abiertos / INEI — microdatos EPEN.
Diccionario de variables (Trim. Ene-Feb-Mar 2026):
https://proyectos.inei.gob.pe/iinei/srienaho/Descarga/DocumentosMetodologicos/2026-184/Diccionario.pdf

Este script NO descarga el archivo (los .csv/.zip del INEI no son accesibles
por HTTP desde este entorno). Descarga tú mismo el CSV y colócalo en
`data/raw/` — ver instrucciones en App/README.md — luego corre:

    python inei_epen.py

Genera `data/processed/epen_ciudades.csv` con, por ciudad:
- pea: Población Económicamente Activa (ponderada)
- ocupados / desempleo_abierto / desempleo_oculto (ponderados)
- tasa_desempleo (%): (desempleo_abierto + desempleo_oculto) / pea
- ingreso_promedio: ingreso mensual promedio ponderado de los ocupados

Variables usadas del microdato (según diccionario oficial):
- OCUP300: nivel de ocupación → 1=Ocupado, 2=Desempleo abierto,
  3=Desempleo oculto, 4=Inactivo
- NOMCIUDAD: nombre de la ciudad
- FAC_T300: factor de expansión (ponderación muestral)
- INGTOT: ingreso mensual total (ocupación principal + secundaria)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "epen_ciudades.csv"

COL_OCUPACION = "OCUP300"
COL_CIUDAD = "NOMCIUDAD"
COL_PESO = "FAC_T300"
COL_INGRESO = "INGTOT"

OCUP_OCUPADO = 1
OCUP_DESEMPLEO_ABIERTO = 2
OCUP_DESEMPLEO_OCULTO = 3
OCUP_INACTIVO = 4


def load_raw(path: Path) -> pd.DataFrame:
    """Lee el CSV crudo del INEI, probando separador/encoding comunes."""
    intentos = [
        {"sep": ";", "encoding": "utf-8"},
        {"sep": ";", "encoding": "latin-1"},
        {"sep": ",", "encoding": "utf-8"},
        {"sep": ",", "encoding": "latin-1"},
    ]
    ultimo_error = None
    for kwargs in intentos:
        try:
            df = pd.read_csv(path, **kwargs, low_memory=False)
            if df.shape[1] > 1:
                return df
        except Exception as e:  # noqa: BLE001 - queremos probar todas las combinaciones
            ultimo_error = e
    raise ValueError(f"No se pudo leer {path} con los separadores/encodings probados: {ultimo_error}")


def wrangle(df: pd.DataFrame) -> pd.DataFrame:
    faltantes = [c for c in (COL_OCUPACION, COL_CIUDAD, COL_PESO) if c not in df.columns]
    if faltantes:
        raise KeyError(
            f"Faltan columnas esperadas {faltantes} en el CSV. "
            f"Columnas disponibles: {list(df.columns)[:20]}... "
            "Revisa el diccionario de variables del trimestre descargado, puede variar la versión."
        )

    df = df.copy()
    df[COL_PESO] = pd.to_numeric(df[COL_PESO], errors="coerce")
    df[COL_OCUPACION] = pd.to_numeric(df[COL_OCUPACION], errors="coerce")
    df = df.dropna(subset=[COL_PESO, COL_OCUPACION, COL_CIUDAD])

    pea_mask = df[COL_OCUPACION].isin([OCUP_OCUPADO, OCUP_DESEMPLEO_ABIERTO, OCUP_DESEMPLEO_OCULTO])
    df_pea = df[pea_mask]

    resumen = (
        df_pea.groupby(COL_CIUDAD)
        .apply(
            lambda g: pd.Series(
                {
                    "pea": g[COL_PESO].sum(),
                    "ocupados": g.loc[g[COL_OCUPACION] == OCUP_OCUPADO, COL_PESO].sum(),
                    "desempleo_abierto": g.loc[g[COL_OCUPACION] == OCUP_DESEMPLEO_ABIERTO, COL_PESO].sum(),
                    "desempleo_oculto": g.loc[g[COL_OCUPACION] == OCUP_DESEMPLEO_OCULTO, COL_PESO].sum(),
                }
            )
        )
        .reset_index()
        .rename(columns={COL_CIUDAD: "ciudad"})
    )
    resumen["tasa_desempleo"] = (
        (resumen["desempleo_abierto"] + resumen["desempleo_oculto"]) / resumen["pea"] * 100
    ).round(2)

    if COL_INGRESO in df.columns:
        ocupados = df[df[COL_OCUPACION] == OCUP_OCUPADO].copy()
        ocupados[COL_INGRESO] = pd.to_numeric(ocupados[COL_INGRESO], errors="coerce")
        ocupados = ocupados.dropna(subset=[COL_INGRESO, COL_PESO])
        ingreso = (
            ocupados.groupby(COL_CIUDAD)
            .apply(lambda g: (g[COL_INGRESO] * g[COL_PESO]).sum() / g[COL_PESO].sum())
            .reset_index(name="ingreso_promedio")
            .rename(columns={COL_CIUDAD: "ciudad"})
        )
        resumen = resumen.merge(ingreso, on="ciudad", how="left")
        resumen["ingreso_promedio"] = resumen["ingreso_promedio"].round(2)

    return resumen.sort_values("tasa_desempleo", ascending=False).reset_index(drop=True)


def main() -> None:
    candidatos = sorted(RAW_DIR.glob("*.csv"))
    if not candidatos:
        raise SystemExit(
            f"No encontré ningún .csv en {RAW_DIR}. "
            "Descarga la data del EPEN (ver App/README.md) y colócala ahí antes de correr este script."
        )
    origen = candidatos[0]
    print(f"Leyendo {origen} ...")
    df_raw = load_raw(origen)
    print(f"{len(df_raw)} filas cargadas. Procesando...")
    df_resumen = wrangle(df_raw)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_resumen.to_csv(OUTPUT_FILE, index=False)
    print(f"Listo → {OUTPUT_FILE}")
    print(df_resumen.head(10))


if __name__ == "__main__":
    main()
