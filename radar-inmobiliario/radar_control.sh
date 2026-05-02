#!/bin/bash
# =============================================================
#  RADAR ALPHA — Panel de Control del Servidor
#  Uso: bash radar_control.sh [status|logs|restart|set-url]
# =============================================================

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
CMD="${1:-status}"

case "$CMD" in

  status)
    echo "=============================="
    echo "  RADAR ALPHA — Estado"
    echo "=============================="
    echo ""
    echo "Servicios:"
    systemctl is-active --quiet radar-web.service \
      && echo "  ✅ radar-web:      ACTIVO" \
      || echo "  ❌ radar-web:      INACTIVO"
    systemctl is-active --quiet radar-autonomo.service \
      && echo "  ✅ radar-autonomo: ACTIVO" \
      || echo "  ❌ radar-autonomo: INACTIVO"

    echo ""
    echo "HTTP:"
    CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ 2>/dev/null || echo "000")
    echo "  Landing /        → HTTP $CODE"
    CODE2=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/admin 2>/dev/null || echo "000")
    echo "  Admin /admin     → HTTP $CODE2"

    echo ""
    PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "?")
    echo "  IP Pública: $PUBLIC_IP"
    echo "  URL:        http://$PUBLIC_IP:5000"

    echo ""
    echo "Datos generados:"
    echo "  Leads:        $(wc -l < "$PROJECT_DIR/clientes_b2b/leads_web.csv" 2>/dev/null || echo 0) registros"
    echo "  Reportes PDF: $(ls "$PROJECT_DIR/reportes_generados/" 2>/dev/null | wc -l)"
    echo "  Kits Mktg:    $(ls "$PROJECT_DIR/resultados/marketing_kits/" 2>/dev/null | wc -l)"
    echo "  Publicaciones:$(ls "$PROJECT_DIR/resultados/publicaciones/" 2>/dev/null | wc -l)"
    ;;

  logs)
    TARGET="${2:-web}"
    echo "=== Logs: radar-$TARGET (Ctrl+C para salir) ==="
    tail -f "$PROJECT_DIR/logs/$TARGET.log"
    ;;

  restart)
    echo "Reiniciando servicios..."
    sudo systemctl restart radar-web.service
    sudo systemctl restart radar-autonomo.service
    sleep 2
    bash "$0" status
    ;;

  set-url)
    # Uso: bash radar_control.sh set-url http://1.2.3.4:5000
    NEW_URL="$2"
    if [ -z "$NEW_URL" ]; then
      PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null)
      NEW_URL="http://$PUBLIC_IP:5000"
    fi
    # Actualizar BASE_URL en .env
    if grep -q "^BASE_URL=" "$PROJECT_DIR/.env"; then
      sed -i "s|^BASE_URL=.*|BASE_URL=$NEW_URL|" "$PROJECT_DIR/.env"
    else
      echo "BASE_URL=$NEW_URL" >> "$PROJECT_DIR/.env"
    fi
    echo "  ✅ BASE_URL actualizada: $NEW_URL"
    echo "  Reiniciando para aplicar cambios..."
    sudo systemctl restart radar-web.service
    ;;

  test-telegram)
    echo "Enviando mensaje de prueba a Telegram..."
    source "$PROJECT_DIR/.env"
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d "chat_id=${TELEGRAM_CHAT_ID}" \
      -d "text=✅ RADAR ALPHA online — $(date '+%d/%m/%Y %H:%M')" \
      -d "parse_mode=Markdown" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('ok') else d)"
    ;;

  test-mp)
    echo "Verificando token MercadoPago..."
    source "$PROJECT_DIR/.env"
    RESP=$(curl -s -H "Authorization: Bearer $MP_ACCESS_TOKEN" \
      "https://api.mercadopago.com/users/me")
    echo "$RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d.get('id'):
    print(f'  ✅ MP OK — Usuario: {d.get(\"nickname\",\"?\")} | País: {d.get(\"country_id\",\"?\")}')
else:
    print(f'  ❌ MP Error: {d.get(\"message\",d)}')
"
    ;;

  *)
    echo "Uso: bash radar_control.sh [status|logs [web|autonomo]|restart|set-url [URL]|test-telegram|test-mp]"
    ;;
esac
