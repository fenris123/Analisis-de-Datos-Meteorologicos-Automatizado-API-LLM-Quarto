# pip install python-dotenv requests pandas matplotlib

import os
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import time
import calendar

from time import sleep
from datetime import datetime
from dotenv import load_dotenv


# =========================
# INICIO DEL CRONÓMETRO
# =========================
inicio_proceso = time.time()




# =========================
# CONFIG TOKEN
# =========================

TOKEN = INSERTAR TOKEN AQUI

headers = {
    "accept": "application/json",
    "api_key": TOKEN
}

URL_BASE = "https://opendata.aemet.es/opendata"


# =========================
# INPUT
# =========================
mes = int(input("Introduce mes (1-12): "))
estacion = input("Introduce idema (ENTER = 5783): ")
if estacion.strip() == "":
    estacion = "5783"


# =========================
# DESCARGA AEMET
# =========================
def descargar_datos(año, mes, estacion):

    # Calculamos el último día real del mes
    ultimo_dia = calendar.monthrange(año, mes)[1]

    fecha_ini = f"{año}-{mes:02d}-01T00:00:00UTC"
    fecha_fin = f"{año}-{mes:02d}-{ultimo_dia:02d}T23:59:59UTC"

    endpoint = f"/api/valores/climatologicos/diarios/datos/fechaini/{fecha_ini}/fechafin/{fecha_fin}/estacion/{estacion}"

    try:
        r = requests.get(URL_BASE + endpoint, headers=headers, timeout=10)
    except:
        return []

    if r.status_code != 200:
        return []

    meta = r.json()
    datos_url = meta.get("datos")

    if not datos_url:
        return []

    r2 = requests.get(datos_url)

    try:
        return json.loads(r2.text)
    except:
        return []


# =========================
# DESCARGA HISTÓRICA
# =========================
año_actual = datetime.utcnow().year
datos_totales = []

print("\nDescargando histórico...\n")

for año in range(año_actual - 50, año_actual):

    datos = descargar_datos(año, mes, estacion)

    if datos:
        datos_totales.extend(datos)

    sleep(1)


# =========================
# AÑO ACTUAL
# =========================
sleep(10)
datos_totales.extend(descargar_datos(año_actual, mes, estacion))


# =========================
# DATAFRAME
# =========================
df = pd.DataFrame(datos_totales)

df = df[["fecha", "tmax", "tmin"]]
df["fecha"] = pd.to_datetime(df["fecha"])

# Conversión a numérico y limpieza de NaNs
df["tmax"] = pd.to_numeric(df["tmax"].astype(str).str.replace(",", "."), errors="coerce")
df["tmin"] = pd.to_numeric(df["tmin"].astype(str).str.replace(",", "."), errors="coerce")

# Eliminamos filas que no tengan datos térmicos (si la API devuelve días vacíos)
df = df.dropna(subset=["tmax", "tmin"])

df["dia"] = df["fecha"].dt.day
df["anio"] = df["fecha"].dt.year


# =========================
# FEATURES HISTÓRICAS
# =========================
df_hist = df[df["anio"] < año_actual]

hist = df_hist.groupby("dia").agg({
    "tmax": ["mean", "min", "max"],
    "tmin": ["mean", "min", "max"]
})

hist.columns = ["_".join(c) for c in hist.columns]
hist = hist.reset_index()


# =========================
# FEATURES AÑO ACTUAL
# =========================
df_act = df[df["anio"] == año_actual]

act = df_act.groupby("dia").agg({
    "tmax": ["mean", "min", "max"],
    "tmin": ["mean", "min", "max"]
})

act.columns = ["_".join(c) for c in act.columns]
act = act.reset_index()


# =========================
# LLM PROMPT
# =========================
prompt = f"""
Eres un analista meteorológico.

Compara clima histórico (50 años) vs año actual.

HISTÓRICO (por día del mes):
{hist.to_string(index=False)}

AÑO ACTUAL:
{act.to_string(index=False)}

Genera:
1. Resumen general del comportamiento del mes
2. Anomalías térmicas relevantes
3. Días más extremos
4. Conclusión clara en lenguaje natural
"""


def ask_llama(prompt):
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1:8b",
            "prompt": prompt,
            "stream": False
        }
    )
    return r.json()["response"]


print("\nConsultando LLM...\n")
resumen = ask_llama(prompt)


# =========================
# GUARDAR OUTPUTS
# =========================
df.to_csv("datos.csv", index=False)

with open("resumen_llm.md", "w", encoding="utf-8") as f:
    f.write(resumen)






# =========================
# GRÁFICO 1 (SCATTER)
# =========================
plt.figure(figsize=(12,6))

plt.scatter(df_hist["dia"], df_hist["tmax"], facecolors="none", edgecolors="red", label="Tmax hist")
plt.scatter(df_hist["dia"], df_hist["tmin"], facecolors="none", edgecolors="blue", label="Tmin hist")

plt.scatter(df_act["dia"], df_act["tmax"], color="black", marker="^", label="Tmax actual")
plt.scatter(df_act["dia"], df_act["tmin"], color="black", marker="v", label="Tmin actual")

plt.legend()
plt.title(f"Temperaturas mes {mes}")
plt.grid()

plt.savefig("scatter.png", dpi=150, bbox_inches="tight")
plt.close()




# =========================
# GRÁFICO 2
# =========================
plt.figure(figsize=(12,6))

plt.plot(hist["dia"], hist["tmax_mean"], label="Tmax media hist")
plt.plot(act["dia"], act["tmax_mean"], label="Tmax media actual")

plt.legend()
plt.title("Comparación Tmax media")
plt.grid()

plt.savefig("tmax.png", dpi=150, bbox_inches="tight")
plt.close()


# =========================
# GRÁFICO 3
# =========================
plt.figure(figsize=(12,6))

plt.plot(hist["dia"], hist["tmin_mean"], label="Tmin media hist")
plt.plot(act["dia"], act["tmin_mean"], label="Tmin media actual")

plt.legend()
plt.title("Comparación Tmin media")
plt.grid()

plt.savefig("tmin.png", dpi=150, bbox_inches="tight")
plt.close()


# =========================
# CALCULO DE STATS PARA BANDAS
# =========================
stats_max = df_hist.groupby("dia")["tmax"].agg(
    mean="mean",
    std="std"
).reset_index()

stats_max["upper"] = stats_max["mean"] + stats_max["std"]
stats_max["lower"] = stats_max["mean"] - stats_max["std"]


stats_min = df_hist.groupby("dia")["tmin"].agg(
    mean="mean",
    std="std"
).reset_index()

stats_min["upper"] = stats_min["mean"] + stats_min["std"]
stats_min["lower"] = stats_min["mean"] - stats_min["std"]


# =========================
# GRAFICO 4: MAXIMAS CON BANDAS
# =========================
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(stats_max['dia'], stats_max['mean'],
        label='Media Tmax', color='black', linewidth=2)

ax.plot(stats_max['dia'], stats_max['upper'],
        color='red', linestyle='--', linewidth=2)

ax.plot(stats_max['dia'], stats_max['lower'],
        color='red', linestyle='--', linewidth=2)

ax.fill_between(stats_max['dia'],
                stats_max['lower'],
                stats_max['upper'],
                color='red',
                alpha=0.25)

ax.scatter(df_act["dia"], df_act["tmax"],
           color="red",
           edgecolors="black",
           marker="^",
           s=80,
           label="Tmax actual")

ax.legend()
ax.set_title("Temperatura máxima (histórico + actual)")
ax.set_xlabel("Día")
ax.set_ylabel("Temperatura")

plt.savefig("tmax_bandas.png", dpi=150, bbox_inches="tight")
plt.close()


# =========================
# GRAFICO 5: MINIMAS CON BANDAS
# =========================
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(stats_min['dia'], stats_min['mean'],
        label='Media Tmin', color='black', linewidth=2)

ax.plot(stats_min['dia'], stats_min['upper'],
        color='#1f77b4', linestyle='--', linewidth=2)

ax.plot(stats_min['dia'], stats_min['lower'],
        color='#1f77b4', linestyle='--', linewidth=2)

ax.fill_between(stats_min['dia'],
                stats_min['lower'],
                stats_min['upper'],
                color='#1f77b4',
                alpha=0.25)


ax.scatter(df_act["dia"], df_act["tmin"],
           color="blue",
           edgecolors="black",
           marker="v",
           s=80,
           label="Tmin actual")

ax.legend()
ax.set_title("Temperatura mínima (histórico + actual)")
ax.set_xlabel("Día")
ax.set_ylabel("Temperatura")

plt.savefig("tmin_bandas.png", dpi=150, bbox_inches="tight")
plt.close()



# =========================
# GENERAR REPORTE.QMD
# =========================
reporte_content = f"""---
title: "Análisis Meteorológico Histórico vs Actual"
author: "Generado por Gemini & Llama"
date: "{datetime.now().strftime('%Y-%m-%d')}"
format:
  pdf:
    fig-pos: 'H'
    header-includes:
      - \\usepackage{{float}}
---

## Resumen del Analista (LLM)

{resumen}

---

\pagebreak
## Visualización de Datos

### Comparativa de Dispersión
En este gráfico se muestran todos los puntos históricos (círculos) frente a los valores del año actual (triángulos).

![Temperaturas del Mes](scatter.png)

\pagebreak
### Evolución de Temperaturas Máximas
Comparación de la media histórica diaria frente a la media del año actual.

![Tmax Media](tmax.png)

\pagebreak
### Evolución de Temperaturas Mínimas
Comparación de la media histórica diaria frente a la media del año actual.

![Tmin Media](tmin.png)

\pagebreak
### Análisis de Bandas Tmax
Media histórica con bandas de desviación estándar frente a valores actuales.

![Tmax Bandas](tmax_bandas.png)

\pagebreak
### Análisis de Bandas Tmin
Media histórica con bandas de desviación estándar frente a valores actuales.

![Tmin Bandas](tmin_bandas.png)
"""


with open("reporte.qmd", "w", encoding="utf-8") as f:
    f.write(reporte_content)

print("Archivo reporte.qmd generado con éxito.")


# =========================
# QUARTO
# =========================
print("\nLanzando Quarto...\n")

subprocess.run(["quarto", "render", "reporte.qmd"])


# =========================
# FINAL DEL CRONÓMETRO
# =========================
fin_proceso = time.time()
tiempo_total = fin_proceso - inicio_proceso

# Convertir a formato legible (minutos y segundos)
minutos = int(tiempo_total // 60)
segundos = int(tiempo_total % 60)

print(f"\n✅ Proceso finalizado con éxito.")
print(f"⏱️ Tiempo total de ejecución: {minutos} min {segundos} seg")
