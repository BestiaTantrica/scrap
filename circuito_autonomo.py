"""
=============================================================
  CIRCUITO AUTÓNOMO — El Gerente IA
  Orquesta: Scraper -> Lead Gen -> Redactor -> Venta
=============================================================
"""
import requests
import time
import subprocess
import os

def ejecutar_ciclo(zona="Palermo"):
    print(f"\nINICIANDO CICLO DE NEGOCIO EN: {zona.upper()}")
    
    # 1. SCRAPING DE PROPIEDADES (Materia Prima)
    print("1/4 Escaneando mercado de oportunidades...")
    r = requests.post("http://localhost:5000/api/buscar", json={"zona": zona, "max_paginas": 2})
    job_id = r.json().get("job_id")
    
    # Esperar resultados
    for _ in range(20):
        time.sleep(10)
        s = requests.get(f"http://localhost:5000/api/status/{job_id}").json()
        if s.get("status") == "done":
            total = len(s.get("resultados", []))
            print(f"Se encontraron {total} propiedades.")
            break
            
    # 2. CAPTACIÓN DE CLIENTES (Inmobiliarias)
    print(f"2/4 Buscando inmobiliarias en {zona}...")
    subprocess.run(["python", "generador_leads_inmobiliarios.py", zona])
    
    # 3. REDACCIÓN Y VENTA (Cerebro Redactor)
    print("3/4 Redactando propuestas de venta asertivas...")
    # El redactor toma el ultimo Excel y los leads del CSV automaticamente
    subprocess.run(["python", "cerebro_redactor.py"])
    
    # 4. CIERRE (El Bot espera los pagos)
    print("4/4 Ciclo completado. El Bot y el Webhook estan listos para recibir pagos.")
    print(f"--- ESPERANDO CONVERSIONES EN {zona.upper()} ---")

if __name__ == "__main__":
    # Podes poner una lista de zonas y que el sistema trabaje solo
    zonas_calientes = ["Palermo", "Belgrano", "Recoleta", "Lujan"]
    for z in zonas_calientes:
        ejecutar_ciclo(z)
        time.sleep(60) # Pausa entre zonas para evitar bloqueos
