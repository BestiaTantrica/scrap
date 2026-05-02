# RADAR ALPHA — Guía de Montaje en Servidor Oracle

## Paso 1 — Conectarse al servidor

Abrí una terminal y conectate por SSH:
```
ssh ubuntu@TU_IP_PUBLICA
```

---

## Paso 2 — Subir el proyecto

Desde tu máquina local (Windows), ejecutá:
```
scp -r "c:\SCRAP\comparador_inmobiliario\radar-inmobiliario" ubuntu@TU_IP_PUBLICA:~/radar-inmobiliario
```

O si ya está en el servidor, ir al directorio:
```
cd ~/radar-inmobiliario
```

---

## Paso 3 — Configurar la URL del servidor

Editá el archivo `.env` y cambiá esta línea con tu IP real:
```
BASE_URL=http://TU_IP_PUBLICA:5000
```

Podés hacerlo automáticamente con:
```
bash radar_control.sh set-url
```
(detecta la IP pública sola)

---

## Paso 4 — Instalar y arrancar todo

Un solo comando instala dependencias, abre el firewall y arranca los servicios:
```
bash deploy_oracle.sh
```

Tarda ~3 minutos. Al final muestra:
```
✅ SISTEMA EN LÍNEA — Radar Alpha monitoreando 24/7
```

---

## Paso 5 — Abrir el puerto en Oracle Cloud (consola web)

1. Ir a: **OCI Console → Networking → Virtual Cloud Networks**
2. Clic en tu VCN → **Security Lists** → **Default Security List**
3. **Add Ingress Rule**:
   - Source CIDR: `0.0.0.0/0`
   - Protocol: TCP
   - Destination Port: `5000`
4. Guardar

---

## Verificar que todo funciona

```bash
# Estado general
bash radar_control.sh status

# Probar Telegram
bash radar_control.sh test-telegram

# Probar MercadoPago
bash radar_control.sh test-mp

# Ver logs en vivo
bash radar_control.sh logs web
bash radar_control.sh logs autonomo
```

---

## URLs del sistema en producción

| Página | URL |
|--------|-----|
| Landing (clientes) | `http://TU_IP:5000` |
| Publicar gratis | `http://TU_IP:5000/publicar` |
| Panel Admin | `http://TU_IP:5000/admin` |
| Análisis interno | `http://TU_IP:5000/lab` |

---

## Comandos de emergencia

```bash
# Reiniciar todo
bash radar_control.sh restart

# Ver logs si algo falla
bash radar_control.sh logs web
bash radar_control.sh logs autonomo

# Reiniciar solo el web
sudo systemctl restart radar-web.service

# Reiniciar solo el circuito autónomo
sudo systemctl restart radar-autonomo.service
```

---

## Qué hace el sistema 24/7

- **radar-web**: Servidor Flask siempre activo. Recibe leads, procesa pagos, muestra la landing.
- **radar-autonomo**: Cada 6 horas barre ZonaProp, ML, Argenprop, BORA y genera PDFs + kits de marketing automáticamente. Notifica por Telegram.

---

## Variables de entorno críticas (.env)

```
TELEGRAM_BOT_TOKEN=   ← Tu bot de Telegram
TELEGRAM_CHAT_ID=     ← Tu chat ID personal
MP_ACCESS_TOKEN=      ← Token de MercadoPago
BASE_URL=             ← URL pública del servidor (IMPORTANTE)
CICLO_HORAS=6         ← Cada cuántas horas corre el radar
```
