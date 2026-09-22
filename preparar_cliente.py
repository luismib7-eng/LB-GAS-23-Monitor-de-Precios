#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de instancias por cliente — Monitor de Precios
========================================================

Arma la carpeta lista para publicar de un cliente concreto: su marca, sus
estaciones, su radio de competencia y —si se indica— solo los datos de su
estado, de modo que una copia filtrada valga poco fuera de su plaza.

Uso
---
    python3 preparar_cliente.py \
        --origen . \
        --slug lbgas23 \
        --nombre "LB GAS 23" \
        --subtitulo "Servicio Bautista · Precios al Público (SENER / CNE / SAT)" \
        --permisos "PL/7773/EXP/ES/2015,PL/12668/EXP/ES/2015" \
        --estado Jalisco \
        --radio 5 \
        --logo logo_lbgas23.png \
        --salida clientes/lbgas23

El resultado es una carpeta autónoma que se sube a su propio hosting (o a una
subcarpeta del repositorio). Los datos nacionales se regeneran una vez al día;
este script solo recorta y reetiqueta, así que correrlo cuesta segundos.
"""

import argparse
import csv
import io
import os
import re
import shutil
import sys

# Archivos que toda instancia necesita. config.js NO va aquí: se escribe aparte.
ARCHIVOS_APP = [
    "index.html", "styles.css", "app.js", "sw.js", "manifest.json",
    "leaflet.js", "leaflet.css", "papaparse.min.js", "chart.umd.min.js",
    "favicon.png", "apple-touch-icon.png",
    "icono-192.png", "icono-512.png", "icono-512-maskable.png",
    ".nojekyll",
]

DATOS = ["fallback.csv", "historico.csv", "catalogo_estaciones.csv", "reporte_mercado.csv"]


def normaliza_permiso(p):
    k = "".join(str(p or "").split()).upper()
    return k[4:] if k.startswith("CNE/") else k


def filtrar_csv(origen, destino, columna, valor):
    """Copia un CSV conservando solo las filas de un estado. Devuelve (leídas, escritas)."""
    with io.open(origen, encoding="utf-8-sig", newline="") as fh:
        filas = list(csv.DictReader(fh))
    if not filas or columna not in filas[0]:
        shutil.copy(origen, destino)
        return len(filas), len(filas)
    conservadas = [f for f in filas if (f.get(columna) or "").strip().lower() == valor.lower()]
    with io.open(destino, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(conservadas)
    return len(filas), len(conservadas)


def filtrar_historico(origen, destino, estado):
    """El histórico guarda ámbitos: se conservan el nacional y el del estado."""
    with io.open(origen, encoding="utf-8-sig", newline="") as fh:
        filas = list(csv.DictReader(fh))
    if not filas:
        shutil.copy(origen, destino)
        return 0, 0
    conservadas = [f for f in filas
                   if (f.get("Ambito") == "nacional")
                   or ((f.get("Ambito") == "estado") and (f.get("Clave", "").lower() == estado.lower()))]
    with io.open(destino, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(conservadas)
    return len(filas), len(conservadas)


def escribir_config(ruta, args, permisos, logo):
    js = '''/* =============================================================
   %(nombre)s — configuración de la instancia
   Generado por preparar_cliente.py. No editar a mano: los cambios
   se pierden en la siguiente regeneración.
   ============================================================= */

window.APP_CONFIG = {

  /* ---------- Fuentes de datos ---------- */
  SHEET_CSV_URL: "",
  CSV_URL: "",
  XML_URL: "",
  FALLBACK_CSV: "fallback.csv",
  CATALOG_CSV: "catalogo_estaciones.csv",
  HISTORY_CSV: "historico.csv",
  REPORT_CSV: "reporte_mercado.csv",

  /* ---------- Comportamiento ---------- */
  REFRESH_MINUTES: %(refresco)d,
  SEARCH_DEBOUNCE_MS: 180,
  PAGE_SIZE: 25,
  PRICE_MIN: 15,
  PRICE_MAX: 45,
  RADIO_KM: %(radio)s,
  MAPA_MAX_PUNTOS: 2500,
  ELASTICIDAD_PCT_POR_10_CENTAVOS: 2,
  ESTADO_POR_DEFECTO: "",

  /* ---------- Identidad ---------- */
  TITLE: "%(nombre)s · Monitor de Precios",
  SUBTITLE: "%(subtitulo)s",
  LOGO_URL: "%(logo)s",
  REPO_URL: "",

  /* ---------- Estaciones del cliente ---------- */
  MIS_ESTACIONES: {
    permisos: [%(permisos)s],
    patrones: []
  },

  MARCAS_COMPETENCIA: ["BP", "TOTALENERGIES", "REPSOL", "SHELL", "CHEVRON",
                       "EXXONMOBIL", "GULF", "G500", "OXXO GAS", "ARCO NORTE"],

  BENCHMARK: {
    label: "Promedio nacional Profeco",
    regular: %(bench_r)s,
    premium: %(bench_p)s,
    diesel: %(bench_d)s
  },

  METODOLOGIA: "Fuente: Valores estimados por la SENER con información de la CNE y el SAT. " +
               "El precio al público es un promedio de los precios registrados durante el periodo de referencia."
};
''' % {
        "nombre": args.nombre,
        "subtitulo": args.subtitulo,
        "logo": logo,
        "radio": args.radio,
        "refresco": args.refresco,
        "permisos": ", ".join('"%s"' % p for p in permisos),
        "bench_r": args.benchmark_regular,
        "bench_p": args.benchmark_premium,
        "bench_d": args.benchmark_diesel,
    }
    with io.open(ruta, "w", encoding="utf-8") as fh:
        fh.write(js)


def main():
    ap = argparse.ArgumentParser(description="Genera la instancia de un cliente.")
    ap.add_argument("--origen", default=".", help="Carpeta con la aplicación y los datos nacionales")
    ap.add_argument("--salida", required=True, help="Carpeta destino de la instancia")
    ap.add_argument("--slug", required=True, help="Identificador corto del cliente (sin espacios)")
    ap.add_argument("--nombre", required=True, help="Nombre comercial del cliente")
    ap.add_argument("--subtitulo", default="Monitor de precios de combustibles")
    ap.add_argument("--permisos", default="", help="Permisos CRE del cliente, separados por coma")
    ap.add_argument("--estado", default="", help="Recorta los datos a este estado (recomendado)")
    ap.add_argument("--radio", default="5", help="Radio del mercado local en kilómetros")
    ap.add_argument("--logo", default="", help="Archivo de logotipo a copiar en la instancia")
    ap.add_argument("--refresco", type=int, default=10, help="Minutos entre actualizaciones automáticas")
    ap.add_argument("--benchmark-regular", default="23.68")
    ap.add_argument("--benchmark-premium", default="28.50")
    ap.add_argument("--benchmark-diesel", default="27.00")
    args = ap.parse_args()

    if not re.match(r"^[a-z0-9][a-z0-9-]*$", args.slug):
        sys.exit("El slug debe ir en minúsculas, sin espacios ni acentos (ej. lbgas23).")

    os.makedirs(args.salida, exist_ok=True)

    # 1. Aplicación
    faltantes = []
    for archivo in ARCHIVOS_APP:
        origen = os.path.join(args.origen, archivo)
        if not os.path.exists(origen):
            faltantes.append(archivo)
            continue
        shutil.copy(origen, os.path.join(args.salida, archivo))
    if faltantes:
        sys.exit("Faltan archivos en --origen: %s" % ", ".join(faltantes))

    # 2. Logotipo
    logo = ""
    if args.logo:
        origen_logo = args.logo if os.path.exists(args.logo) else os.path.join(args.origen, args.logo)
        if not os.path.exists(origen_logo):
            sys.exit("No se encontró el logotipo: %s" % args.logo)
        logo = os.path.basename(origen_logo)
        shutil.copy(origen_logo, os.path.join(args.salida, logo))

    # 3. Datos, recortados al estado si se indicó
    resumen = []
    for archivo in DATOS:
        origen = os.path.join(args.origen, archivo)
        destino = os.path.join(args.salida, archivo)
        if not os.path.exists(origen):
            resumen.append((archivo, 0, 0, "ausente"))
            continue
        if not args.estado:
            shutil.copy(origen, destino)
            resumen.append((archivo, 0, 0, "completo"))
            continue
        if archivo == "historico.csv":
            leidas, escritas = filtrar_historico(origen, destino, args.estado)
        elif archivo == "reporte_mercado.csv":
            shutil.copy(origen, destino)      # son agregados, no revelan estaciones
            leidas = escritas = 0
        else:
            leidas, escritas = filtrar_csv(origen, destino, "Estado", args.estado)
        resumen.append((archivo, leidas, escritas, "recortado"))

    # 4. Configuración
    permisos = [normaliza_permiso(p) for p in args.permisos.split(",") if p.strip()]
    escribir_config(os.path.join(args.salida, "config.js"), args, permisos, logo)

    # 5. Nota de entrega
    with io.open(os.path.join(args.salida, "INSTANCIA.md"), "w", encoding="utf-8") as fh:
        fh.write("# %s\n\n" % args.nombre)
        fh.write("Instancia generada con `preparar_cliente.py`.\n\n")
        fh.write("- Slug: `%s`\n" % args.slug)
        fh.write("- Estaciones declaradas: %s\n" % (", ".join(permisos) if permisos else "ninguna"))
        fh.write("- Radio de competencia: %s km\n" % args.radio)
        fh.write("- Alcance de datos: %s\n\n" % (args.estado if args.estado else "nacional"))
        fh.write("Para actualizar los datos, vuelve a correr el generador sobre la carpeta\n")
        fh.write("nacional ya actualizada. `config.js` se reescribe: no lo edites a mano.\n")

    print("Instancia creada en: %s" % args.salida)
    print("Cliente:            %s (%s)" % (args.nombre, args.slug))
    print("Estaciones:         %s" % (", ".join(permisos) if permisos else "ninguna declarada"))
    print("Alcance:            %s" % (args.estado if args.estado else "nacional"))
    for archivo, leidas, escritas, modo in resumen:
        if modo == "recortado" and leidas:
            print("  %-24s %6d → %6d filas" % (archivo, leidas, escritas))
        else:
            print("  %-24s %s" % (archivo, modo))


if __name__ == "__main__":
    main()
