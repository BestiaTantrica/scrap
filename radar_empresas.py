"""
=============================================================
  RADAR DE EMPRESAS v1.0 — MIGRACION_SCRAPING_CASH
  Mapeo y Perfilamiento de Inmobiliarias para B2B
=============================================================
"""

from curl_cffi import requests
from bs4 import BeautifulSoup
import json
import time
import random
import os

def scrapear_inmobiliarias(zona='palermo'):
    url = f"https://www.zonaprop.com.ar/inmobiliarias-{zona}.html"
    print(f"[*] Mapeando inmobiliarias en {zona}...")
    
    try:
        response = requests.get(url, impersonate="chrome120", timeout=30)
        if response.status_code != 200:
            print(f"[!] Error {response.status_code} al acceder a la zona.")
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        inmobiliarias = []
        
        # Selectores precisos para Zonaprop 2024
        cards = soup.select('div[data-qa="inmobiliaria-card"], div[class*="InmobiliariaCard"]')
        
        if not cards:
            # Fallback agresivo si los selectores fallan
            cards = soup.select('div[class*="CardContainer"], div[class*="ItemContainer"]')

        for card in cards:
            try:
                # Nombre de la inmobiliaria
                nombre_tag = card.select_one('h2, h3, b, div[class*="Name"]')
                if not nombre_tag: continue
                nombre = nombre_tag.get_text(strip=True)
                
                # Capturar todo el texto de la card para analizar perfil
                texto_card = card.get_text(" ", strip=True).lower()
                cantidad_avisos = 0
                if "avisos" in texto_card:
                    # Extraer el número aproximado
                    import re
                    match = re.search(r'(\d+)\s+avisos', texto_card)
                    if match:
                        cantidad_avisos = int(match.group(1))

                # Clasificación preliminar
                perfil = "ELITE" if cantidad_avisos > 100 else "BARRIAL"
                if "remax" in nombre.lower() or "century" in nombre.lower():
                    perfil = "FRANQUICIA"

                inmobiliarias.append({
                    "nombre": nombre,
                    "zona": zona.title(),
                    "cantidad_avisos": cantidad_avisos,
                    "perfil": perfil,
                    "fecha_mapeo": time.strftime("%Y-%m-%d")
                })
            except: continue
            
        return inmobiliarias

    except Exception as e:
        print(f"[!] Error: {e}")
        return []

def run():
    zonas = ["palermo", "belgrano", "caballito", "lujan"]
    todas = []
    
    for zona in zonas:
        res = scrapear_inmobiliarias(zona)
        todas.extend(res)
        time.sleep(random.uniform(5, 10))
        
    if todas:
        output_file = 'directorio_inmobiliarias.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(todas, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Mapeo finalizado. {len(todas)} empresas perfiladas.")
    else:
        print("\n[!] No se pudieron mapear empresas.")

if __name__ == "__main__":
    run()
