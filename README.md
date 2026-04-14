# README

Pipeline automatizado de análisis meteorológico. Descarga datos de la API de AEMET, los procesa con Python y compara  histórico vs mes actual. Genera un resumen con un LLM local y un informe final en HTML/PDF usando Quarto.



## Requisitos

Para ejecutar este proyecto es necesario disponer de lo siguiente:

Software
Python 3.9 o superior
Quarto (para generar el informe final)
Acceso a la API de AEMET (requiere token)
Ollama instalado y en ejecución
Modelo LLM llama3.1:8b descargado en Ollama
Librerías de Python

Instalables con:

pip install python-dotenv requests pandas matplotlib


## Hardware

Este script se ha ejecutado en un entorno doméstico con:

CPU: Intel i5 / i7
RAM: 32 GB

No es necesario disponer de tarjeta gráfica de NVIDIA.
El modelo LLM puede ejecutarse únicamente con CPU, aunque el tiempo de respuesta será mayor en comparación con una GPU.

## Descripción del programa

Este proyecto implementa un pipeline automatizado de análisis meteorológico centrado en:

Un único mes (seleccionado por el usuario), comparandolo con los datos del mismo mes de los ultimos 50 años
Una única estación meteorológica (por defecto, Sevilla - idema 5783)

## El flujo completo realiza los siguientes pasos:

Descarga datos históricos (últimos 50 años) y actuales desde la API de AEMET
Calcula estadísticas diarias (media, mínimo y máximo) separando histórico y año actual
Genera un prompt estructurado para un modelo LLM en local
Obtiene un resumen en lenguaje natural del comportamiento del mes
Genera gráficos comparativos
Construye un informe en formato Quarto (pdf o html) y lo renderiza automáticamente

## El resultado final incluye:

Datos en CSV
Resumen en Markdown
Gráficos en PNG
Informe final en PDF (o HTML si se configura)

Este proyecto es una evolución de trabajos anteriores centrados en la descarga y tratamiento de datos de la API de AEMET, ampliando el flujo para incluir generación automática de texto y creación de informes reproducibles. 

## Configuración del token de AEMET

Para acceder a la API de AEMET es necesario un token.

El script incluye una línea como esta:

TOKEN = "INSERTE TOKEN AQUI"

Debes sustituir ese valor por tu token personal.

Opciones

Opción 1 (no recomendada)
Insertar directamente el token en el código:

TOKEN = "tu_token_aqui"

Opción 2 (recomendada)
Usar un archivo .env:

Crear un archivo .env
Añadir:
TOKEN_AEMET=tu_token_aqui
Cargarlo en el script con python-dotenv

Esta opción evita exponer el token en el repositorio.

## Ejecución

El script solicita por consola:

Mes (1-12)
ID de estación (opcional, por defecto 5783)

Si no se introduce estación, se utiliza automáticamente la de Sevilla.

Una vez introducidos los datos, el proceso se ejecuta de forma completa.

## Notas sobre el LLM

El script está configurado para usar el modelo llama3.1:8b, que debe descargarse

Es posible utilizar otros modelos locales, pero en ese caso será necesario modificar el nombre del modelo en el código.

## Estructura de salida

Al finalizar la ejecución se generan los siguientes archivos:

datos.csv → datos procesados
resumen_llm.md → texto generado por el modelo
scatter.png, tmax.png, tmin.png → gráficos
reporte.qmd → plantilla del informe
Informe renderizado por Quarto (.html o .pdf)

## Notas
El tiempo total de ejecución depende principalmente del modelo LLM. Al estar diseñado para no requerir tarjeta grafica, tardara unos 5 minutos en ejecutarse.
La descarga de datos incluye pausas para evitar sobrecargar la API
El script está pensado para ejecutarse en local y de forma autónoma.

Este script esta hecho unicamente con fines didacticos. 
Sobre el uso de los datos de AEMET, su API etc, recomendamos ver su nota legal:
https://www.aemet.es/es/nota_legal



# IMPORTANTE:  
El script hace 3 intentos para descargar los dato del mes en cada año.
Si no lo logra, pasa al siguiente. 
El año actual por ser el mas importante (sin el no hay datos actuales con los que comparar la media de los anteriores) hemos insertado un sleep de 10 antes de el para minimizar la posibilidad de que falle la descarga. 
Si se observa que faltan en la grafica esos datos, sugerimos esperar un poco antes de volver a lanzar el script.
