import json
from curl_cffi import requests
from bs4 import BeautifulSoup
import time

def parse_ml():
    url = "https://inmuebles.mercadolibre.com.ar/departamentos/venta/capital-federal/dueno-directo/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"🔍 Scrapeando MercadoLibre (Modo Ultra-Rápido)...")
    
    try:
        # Usamos curl-cffi para saltar protecciones imitando a Chrome
        response = requests.get(url, headers=headers, impersonate="chrome110")
        if response.status_code != 200:
            print(f"❌ Error: Status {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('.poly-card')
        
        resultados = []
        for item in items[:40]:  # Tomamos los primeros 40
            try:
                # Titulo y link
                a_tag = item.select_one('.poly-component__title-wrapper a')
                if not a_tag: continue
                titulo = a_tag.text.strip()
                link = a_tag.get('href', '')
                
                # Precio y moneda
                precio_tag = item.select_one('.poly-price__current .andes-money-amount__fraction')
                moneda_tag = item.select_one('.poly-price__current .andes-money-amount__currency-symbol')
                
                precio = precio_tag.text.strip() if precio_tag else "Consultar"
                moneda = moneda_tag.text.strip() if moneda_tag else ""
                
                # Ubicacion
                ubicacion_tag = item.select_one('.poly-component__location')
                ubicacion = ubicacion_tag.text.strip() if ubicacion_tag else "CABA"
                
                # Scoring de urgencia básico para el demo
                score = 50
                tags = []
                if "oportunidad" in titulo.lower() or "urge" in titulo.lower():
                    score += 30
                    tags.append("oportunidad")
                if "dueño" in titulo.lower() or "directo" in titulo.lower():
                    score += 20
                    tags.append("dueño directo")
                
                resultados.append({
                    "titulo": titulo,
                    "precio": f"{moneda} {precio}",
                    "link": link,
                    "score_urgencia": score,
                    "señales": ", ".join(tags) if tags else "normal",
                    "zona": ubicacion,
                    "etiqueta": "🔥 URGENTE" if score >= 70 else "⚖️ INTERESANTE"
                })
            except Exception as e:
                print("Error en item:", e)
                continue
                
        return resultados
        
    except Exception as e:
        print(f"❌ Error fatal en scraper: {str(e)}")
        return []

if __name__ == "__main__":
    import datetime
    import os
    from pathlib import Path
    
    zona_str = "CABA"
    results = parse_ml()
    
    # --- ARQUITECTURA DATA LAKE ---
    # Ruta relativa al directorio del script (funciona en WSL2 y Oracle Cloud)
    BASE_DIR = Path(__file__).parent.resolve()
    hoy = datetime.datetime.now()
    ruta_base = BASE_DIR / "base_datos" / hoy.strftime('%Y/%m/%d') / zona_str
    os.makedirs(ruta_base, exist_ok=True)
    
    archivo_salida = ruta_base / "mercadolibre.json"
    
    with open(archivo_salida, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Se guardaron {len(results)} propiedades en {archivo_salida}")
