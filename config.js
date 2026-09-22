/* =============================================================
   LB GAS 23 — configuración de la instancia
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
  REFRESH_MINUTES: 10,
  SEARCH_DEBOUNCE_MS: 180,
  PAGE_SIZE: 25,
  PRICE_MIN: 15,
  PRICE_MAX: 45,
  RADIO_KM: 5,
  MAPA_MAX_PUNTOS: 2500,
  ELASTICIDAD_PCT_POR_10_CENTAVOS: 2,
  ESTADO_POR_DEFECTO: "",

  /* ---------- Identidad ---------- */
  TITLE: "LB GAS 23 · Monitor de Precios",
  SUBTITLE: "Servicio Bautista · Precios al Público (SENER / CNE / SAT)",
  LOGO_URL: "logo_lbgas23.png",
  REPO_URL: "",

  /* ---------- Estaciones del cliente ---------- */
  MIS_ESTACIONES: {
    permisos: ["PL/7773/EXP/ES/2015", "PL/138/EXP/ES/2025"],
    patrones: []
  },

  MARCAS_COMPETENCIA: ["BP", "TOTALENERGIES", "REPSOL", "SHELL", "CHEVRON",
                       "EXXONMOBIL", "GULF", "G500", "OXXO GAS", "ARCO NORTE"],

  BENCHMARK: {
    label: "Promedio nacional Profeco",
    regular: 23.68,
    premium: 28.50,
    diesel: 27.00
  },

  METODOLOGIA: "Fuente: Valores estimados por la SENER con información de la CNE y el SAT. " +
               "El precio al público es un promedio de los precios registrados durante el periodo de referencia."
};
