#!/bin/bash
# =============================================================
#  RADAR ALPHA — Deploy Script para Oracle Cloud
#  Ejecutar como: bash deploy_oracle.sh
#  Requiere: Ubuntu 22.04 / Oracle Linux 8+
# =============================================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="python3"
PIP="pip3"
SERVICE_USER="$(whoami)"

echo "=============================================="
echo "  RADAR ALPHA — Instalación en Producción"
echo "  Directorio: $PROJECT_DIR"
echo "=============================================="

# ── 1. Dependencias del sistema ───────────────────────────────
echo ""
echo "[1/6] Instalando dependencias del sistema..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv \
    libffi-dev libssl-dev build-essential curl git

# ── 2. Entorno virtual y dependencias Python ─────────────────
echo ""
echo "[2/6] Instalando dependencias Python..."
cd "$PROJECT_DIR"

if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
fi
source venv/bin/activate

pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "  ✅ Dependencias instaladas."

# ── 3. Crear directorios necesarios ──────────────────────────
echo ""
echo "[3/6] Preparando estructura de directorios..."
mkdir -p resultados/marketing_kits
mkdir -p resultados/informes_ia
mkdir -p resultados/publicaciones
mkdir -p reportes_generados
mkdir -p clientes_b2b
mkdir -p static/uploads
mkdir -p logs

echo "  ✅ Directorios listos."

# ── 4. Firewall — abrir puerto 5000 ──────────────────────────
echo ""
echo "[4/6] Configurando firewall (puerto 5000)..."

# UFW (Ubuntu)
if command -v ufw &> /dev/null; then
    sudo ufw allow 5000/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    echo "  ✅ UFW: puertos 5000, 80, 443 abiertos."
fi

# iptables (Oracle Linux / fallback)
if command -v iptables &> /dev/null; then
    sudo iptables -I INPUT -p tcp --dport 5000 -j ACCEPT 2>/dev/null || true
    sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
    echo "  ✅ iptables: puertos abiertos."
fi

# Oracle Cloud: reglas de seguridad VCN (recordatorio)
echo "  ⚠  ORACLE CLOUD: Verificar que el Security Group/VCN tenga"
echo "     el puerto 5000 abierto en la consola web de OCI."

# ── 5. Crear servicios systemd ────────────────────────────────
echo ""
echo "[5/6] Creando servicios systemd..."

VENV_PYTHON="$PROJECT_DIR/venv/bin/python"

# Servicio: app.py (Flask)
sudo tee /etc/systemd/system/radar-web.service > /dev/null <<EOF
[Unit]
Description=Radar Alpha — Servidor Web Flask
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_PYTHON app.py
Restart=always
RestartSec=5
StandardOutput=append:$PROJECT_DIR/logs/web.log
StandardError=append:$PROJECT_DIR/logs/web.log

[Install]
WantedBy=multi-user.target
EOF

# Servicio: circuito_autonomo.py
sudo tee /etc/systemd/system/radar-autonomo.service > /dev/null <<EOF
[Unit]
Description=Radar Alpha — Circuito Autónomo (Scraping + IA + Marketing)
After=network.target radar-web.service

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_PYTHON circuito_autonomo.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/autonomo.log
StandardError=append:$PROJECT_DIR/logs/autonomo.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable radar-web.service
sudo systemctl enable radar-autonomo.service

echo "  ✅ Servicios systemd creados y habilitados."

# ── 6. Arrancar servicios ─────────────────────────────────────
echo ""
echo "[6/6] Arrancando servicios..."
sudo systemctl restart radar-web.service
sleep 3
sudo systemctl restart radar-autonomo.service
sleep 2

# ── Verificación final ────────────────────────────────────────
echo ""
echo "=============================================="
echo "  VERIFICACIÓN FINAL"
echo "=============================================="

WEB_STATUS=$(sudo systemctl is-active radar-web.service)
AUTO_STATUS=$(sudo systemctl is-active radar-autonomo.service)

echo "  radar-web:      $WEB_STATUS"
echo "  radar-autonomo: $AUTO_STATUS"

# Test HTTP local
sleep 2
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ || echo "000")
echo "  HTTP localhost: $HTTP_CODE"

PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo "desconocida")
echo ""
echo "  IP Pública: $PUBLIC_IP"
echo "  Landing:    http://$PUBLIC_IP:5000"
echo "  Admin:      http://$PUBLIC_IP:5000/admin"
echo "  Publicar:   http://$PUBLIC_IP:5000/publicar"
echo ""

if [ "$WEB_STATUS" = "active" ] && [ "$HTTP_CODE" = "200" ]; then
    echo "  ✅ SISTEMA EN LÍNEA — Radar Alpha monitoreando 24/7"
else
    echo "  ❌ Revisar logs: tail -f $PROJECT_DIR/logs/web.log"
fi
echo "=============================================="
