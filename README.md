# 🏠 RADAR INMOBILIARIO — El Gerente IA

> **Estado:** Producción Autónoma.
> **Misión:** Detectar oportunidades de arbitraje inmobiliario y vender leads a inmobiliarias (B2B).

## 📂 Estructura del Ecosistema
El proyecto se ha consolidado en la carpeta `radar-inmobiliario/` para mantener el orden y la escalabilidad.

```text
radar-inmobiliario/
├── app.py                   # Dashboard Web + API (Flask)
├── bot.py                   # Interfaz de Telegram para humanos
├── circuito_autonomo.py      # EL GERENTE: Orquestador del ciclo completo
├── cerebro_redactor.py      # Agente de Ventas (Drafting de propuestas)
├── zona_intel.py            # Inteligencia de Mercado (Trends, Eventos, Precios)
├── generador_leads_inmobiliarios.py  # Captación de Inmobiliarias
├── reporte_generador.py     # Generación de PDFs Profesionales
├── scrapers/                # Motores de extracción (ZonaProp, ML, etc.)
└── templates/               # UI del Dashboard
```

## 🚀 Protocolo de Ejecución

### 1. El Motor (API & Dashboard)
```powershell
cd C:\SCRAP\comparador_inmobiliario\radar-inmobiliario
python app.py
```
*Acceso:* `http://localhost:5000`

### 2. El Gerente Autónomo
Este script corre el ciclo completo: Scraping -> Lead Gen -> Redacción.
```powershell
python circuito_autonomo.py
```

### 3. El Interfaz Humana (Telegram)
```powershell
python bot.py
```

## 🧠 Capas de Inteligencia
1. **Scraping Stealth:** Evasión de bloqueos y extracción de data cruda.
2. **Zona Intel:** Análisis de Google Trends, eventos locales y comparativa de precio/m2 real vs publicado.
3. **Lead Gen B2B:** Identificación de inmobiliarias activas en la zona de búsqueda.
4. **Cerebro Redactor:** Creación de propuestas de venta personalizadas (Drafts listos para Groq).

## 🛠️ Tecnologías
- Python + Playwright + BeautifulSoup
- Flask (API)
- Pandas (Procesamiento de datos)
- Pytrends (Google Trends)
- Groq/Gemini (Redacción de ventas - *En integración*)

---
*Mantenido por la Unidad MIGRACION_SCRAPING_CASH*
