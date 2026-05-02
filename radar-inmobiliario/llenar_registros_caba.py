"""
=============================================================
  FÁBRICA DE VALOR — Llenado de Registros CABA
  Exprime el free tier de Groq procesando barrios en serie.
=============================================================
"""
import requests
import time
import json
import os

BARRIOS_CABA = [
    "Palermo", "Recoleta", "Belgrano", "Caballito", "Villa Urquiza",
    "Almagro", "Flores", "San Telmo", "Puerto Madero", "Colegiales",
    "Nuñez", "Chacarita", "Villa Crespo", "Balvanera", "Monserrat"
]

def procesar_barrio(barrio):
    print(f"\n[FÁBRICA] >>> Procesando: {barrio.upper()}")
    
    url = "http://localhost:5000/api/buscar"
    payload = {
        "zona": barrio,
        "operacion": "venta",
        "tipo": "departamentos",
        "max_paginas": 1,
        "plataformas": ["zonaprop", "mercadolibre"]
    }
    
    try:
        r = requests.post(url, json=payload)
        job_id = r.json().get("job_id")
        print(f"      Job ID: {job_id}. Esperando finalización...")
        
        # Polling para esperar que termine y la IA haga su magia
        for _ in range(30): # 1 minuto max por barrio
            time.sleep(2)
            status_res = requests.get(f"http://localhost:5000/api/status/{job_id}").json()
            if status_res.get("status") == "done":
                print(f"      ✓ {barrio} completado con {status_res.get('total')} resultados.")
                return True
    except Exception as e:
        print(f"      × Error en {barrio}: {e}")
    
    return False

def ejecutar_fabrica():
    print("=== INICIANDO PRODUCCIÓN DE VALOR DIGITAL (CABA) ===")
    print(f"Target: {len(BARRIOS_CABA)} barrios estratégicos.")
    
    for barrio in BARRIOS_CABA:
        procesar_barrio(barrio)
        print("--- Pausa de enfriamiento (10s) para evitar bloqueos ---")
        time.sleep(10)

if __name__ == "__main__":
    # Asegurarse que el servidor Flask esté corriendo antes de ejecutar
    ejecutar_fabrica()
