# Dashboards Perú — App

Dashboard en Dash con dos pestañas:

1. **Tipo de cambio S/ vs US$** — datos oficiales del BCRP, consumidos en vivo desde su API REST pública.
2. **Empleo por ciudad (INEI - EPEN)** — tasa de desempleo e ingreso promedio por ciudad, calculados a partir de microdatos oficiales de la Encuesta Permanente de Empleo Nacional.

## Cómo correrlo

```bash
cd App
python -m venv .venv
# Windows: .venv\Scripts\activate | Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abre `http://127.0.0.1:8050` en el navegador. La pestaña 1 funciona de inmediato (llama a la API en vivo). La pestaña 2 necesita el paso de datos del INEI de abajo — si no lo hiciste, muestra un mensaje con instrucciones en vez de fallar.

## Pestaña 1 — Tipo de cambio (BCRP)
`app.py` llama a `bcrp_api.py`, que consulta la serie `PN01207PM` (tipo de cambio interbancario promedio, mensual) en la API pública del BCRP. No requiere descargar nada.

## Pestaña 2 — Empleo por ciudad (INEI - EPEN)

Los archivos del INEI no se pueden descargar automáticamente desde acá (no son accesibles por HTTP desde este entorno), así que este paso lo haces tú una vez:

1. Descarga la **"Data de muestra" (CSV)** de la EPEN — es liviana, ideal para probar el dashboard:
   https://www.datosabiertos.gob.pe/sites/default/files/Nacional%20EPEN%20Trim.%20Ene-Feb-Mar%202026_1.csv
   - (Para el dataset completo en vez de la muestra: https://proyectos.inei.gob.pe/iinei/srienaho/descarga/CSV/1034-Modulo76.zip — descomprime el CSV que trae adentro)
2. Guarda el archivo `.csv` dentro de `App/data/raw/` (cualquier nombre, el script toma el primer `.csv` que encuentre).
3. Corre el script de limpieza/ponderación:
   ```bash
   python inei_epen.py
   ```
   Esto genera `data/processed/epen_ciudades.csv` con, por ciudad: PEA, ocupados, desempleo abierto/oculto, tasa de desempleo (%) e ingreso promedio — todo ponderado con el factor de expansión muestral (`FAC_T300`), como corresponde a una encuesta.
4. Corre `python app.py` — la pestaña 2 ya mostrará los gráficos.

Diccionario de variables usado (oficial, trimestre Ene-Feb-Mar 2026):
https://proyectos.inei.gob.pe/iinei/srienaho/Descarga/DocumentosMetodologicos/2026-184/Diccionario.pdf
Variables clave: `OCUP300` (1=Ocupado, 2=Desempleo abierto, 3=Desempleo oculto, 4=Inactivo), `NOMCIUDAD`, `FAC_T300` (ponderación), `INGTOT` (ingreso mensual).

⚠️ El wrangling en `inei_epen.py` fue probado con datos sintéticos que imitan esta estructura, no con el archivo real del INEI — si al correrlo faltan columnas, el error te dirá cuáles espera y cuáles trajo tu CSV, revisa si el trimestre que descargaste cambió algún nombre de variable.

## Estructura
```
App/
├── app.py               # app Dash (2 pestañas + callbacks)
├── bcrp_api.py           # cliente API BCRP (pestaña 1)
├── inei_epen.py          # wrangling de microdatos EPEN (pestaña 2)
├── requirements.txt
├── data/
│   ├── raw/              # coloca aquí el CSV del INEI descargado
│   └── processed/        # salida limpia (epen_ciudades.csv)
```

## Desplegar (opcional)
Dash es una app Flask, así que se despliega en cualquier host que corra Python (Render, Railway, Fly.io tienen tier gratuito). Vercel no corre apps Dash de forma nativa.

## Próximos pasos
- Tercer dashboard con datos del MEF (ejecución presupuestal) o de otro dominio.
- Filtro por trimestre/año en la pestaña del INEI cuando se sumen más trimestres.
