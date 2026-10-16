"""Dashboards Perú — panel con 2 pestañas.

1. Tipo de cambio S/ vs US$ (BCRP, API pública en vivo).
2. Empleo por ciudad (INEI - EPEN, dataset procesado localmente).

Corre con: python app.py  →  http://127.0.0.1:8050
"""
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html

from bcrp_api import get_series

CODIGO_SERIE_BCRP = "PN01207PM"  # Tipo de cambio interbancario promedio, mensual
ANIO_MIN = 2010
ANIO_MAX = date.today().year

EPEN_PROCESADO = Path(__file__).parent / "data" / "processed" / "epen_ciudades.csv"

app = Dash(__name__)
app.title = "Dashboards Perú"

# --- Pestaña 1: Tipo de cambio (BCRP) -----------------------------------
tab_tipo_cambio = html.Div(
    [
        html.P(
            "Fuente: Banco Central de Reserva del Perú (BCRP) — serie PN01207PM, "
            "tipo de cambio interbancario promedio mensual. Datos oficiales, consultados en vivo."
        ),
        html.Label("Rango de años"),
        dcc.RangeSlider(
            id="rango-anios",
            min=ANIO_MIN,
            max=ANIO_MAX,
            step=1,
            value=[ANIO_MAX - 5, ANIO_MAX],
            marks={a: str(a) for a in range(ANIO_MIN, ANIO_MAX + 1, 2)},
        ),
        dcc.Graph(id="grafico-tipo-cambio"),
    ],
    style={"padding": "20px 0"},
)


@app.callback(Output("grafico-tipo-cambio", "figure"), Input("rango-anios", "value"))
def actualizar_grafico_tipo_cambio(rango_anios):
    anio_ini, anio_fin = rango_anios
    df = get_series(CODIGO_SERIE_BCRP, f"{anio_ini}-1", f"{anio_fin}-12")
    fig = px.line(
        df,
        x="periodo",
        y="valor",
        labels={"periodo": "Período", "valor": "S/ por US$"},
        title="Tipo de cambio interbancario promedio mensual",
    )
    fig.update_layout(template="plotly_white")
    return fig


# --- Pestaña 2: Empleo por ciudad (INEI - EPEN) --------------------------
def _cargar_epen():
    if EPEN_PROCESADO.exists():
        return pd.read_csv(EPEN_PROCESADO)
    return None


def _tab_epen_layout():
    df = _cargar_epen()
    if df is None:
        return html.Div(
            [
                html.P(
                    "Todavía no hay datos procesados del INEI. Descarga el CSV de la EPEN "
                    "(ver App/README.md → sección INEI) y guárdalo en data/raw/, luego corre:"
                ),
                html.Pre("python inei_epen.py", style={"background": "#f4f4f4", "padding": "10px"}),
                html.P("Después recarga esta página."),
            ]
        )
    fig_tasa = px.bar(
        df.sort_values("tasa_desempleo", ascending=True),
        x="tasa_desempleo",
        y="ciudad",
        orientation="h",
        labels={"tasa_desempleo": "Tasa de desempleo (%)", "ciudad": "Ciudad"},
        title="Tasa de desempleo por ciudad (EPEN, INEI)",
    )
    fig_tasa.update_layout(template="plotly_white")

    children = [
        html.P(
            "Fuente: INEI — Encuesta Permanente de Empleo Nacional (EPEN), microdatos "
            "procesados con ponderación muestral (factor de expansión)."
        ),
        dcc.Graph(figure=fig_tasa),
    ]

    if "ingreso_promedio" in df.columns:
        fig_ingreso = px.bar(
            df.sort_values("ingreso_promedio", ascending=True),
            x="ingreso_promedio",
            y="ciudad",
            orientation="h",
            labels={"ingreso_promedio": "Ingreso mensual promedio (S/)", "ciudad": "Ciudad"},
            title="Ingreso mensual promedio de ocupados por ciudad (EPEN, INEI)",
        )
        fig_ingreso.update_layout(template="plotly_white")
        children.append(dcc.Graph(figure=fig_ingreso))

    return html.Div(children, style={"padding": "20px 0"})


tab_epen = html.Div(id="contenido-epen", children=_tab_epen_layout())

# --- Layout general -------------------------------------------------------
app.layout = html.Div(
    style={"fontFamily": "Inter, Arial, sans-serif", "maxWidth": "960px", "margin": "40px auto"},
    children=[
        html.H1("Dashboards Perú"),
        dcc.Tabs(
            [
                dcc.Tab(label="Tipo de cambio (BCRP)", children=[tab_tipo_cambio]),
                dcc.Tab(label="Empleo por ciudad (INEI)", children=[tab_epen]),
            ]
        ),
    ],
)


if __name__ == "__main__":
    app.run(debug=True)
