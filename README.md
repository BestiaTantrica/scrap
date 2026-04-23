# 🏠 COMPARADOR INMOBILIARIO — Protocolo de Arranque

## Estructura
```
comparador_inmobiliario/
├── app.py               ← Backend Flask (Panel Web + API)
├── bot.py               ← Bot de Telegram
├── scrapers/
│   ├── zonaprop.py
│   ├── mercadolibre.py
│   ├── olx.py
│   ├── argenprop.py
│   └── infocasas.py
├── templates/index.html ← Panel Web (abre en browser)
├── resultados/          ← Excel generados automáticamente
└── requirements.txt
```

## Arranque (2 terminales)

### Terminal 1 — Panel Web:
```powershell
cd C:\SCRAP\comparador_inmobiliario
python app.py
# Abrí http://localhost:5000 en el navegador
```

### Terminal 2 — Bot Telegram:
```powershell
cd C:\SCRAP\comparador_inmobiliario
python bot.py
```

## Comandos Telegram
- `/buscar palermo` — busca en todas las plataformas
- `/buscar lujan venta casas` — búsqueda personalizada
- `/buscar belgrano alquiler departamentos`
- `/status` — estado del servidor
- `/ayuda` — lista de comandos

## Plataformas soportadas
| Plataforma    | Color  | Estado |
|---------------|--------|--------|
| ZonaProp      | 🔵     | Activo |
| MercadoLibre  | 🟡     | Activo |
| OLX           | 🟣     | Activo |
| Argenprop     | 🟢     | Activo |
| Infocasas     | 🟠     | Activo |

## LOG
- 2026-04-23: Sistema creado. 5 plataformas operativas.
