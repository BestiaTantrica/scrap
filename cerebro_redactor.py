"""
=============================================================
  CEREBRO REDACTOR — Agente de Ventas IA
  Toma leads B2B y oportunidades del mercado para crear
  mensajes de venta hiper-personalizados.
=============================================================
"""
import pandas as pd
import os
import glob

def obtener_ultima_oportunidad(zona="Palermo"):
    """Busca el ultimo archivo Excel generado."""
    archivos = glob.glob(f"resultados/*.xlsx")
    if not archivos:
        return None
    # Ordenar por fecha de creacion
    ultimo = max(archivos, key=os.path.getctime)
    df = pd.read_excel(ultimo)
    
    if df.empty: return None
    
    # Buscamos la mejor oportunidad (dueño directo, score alto)
    fuego = df[df['score_urgencia'] > 40].sort_values(by='score_urgencia', ascending=False)
    if fuego.empty:
        return df.iloc[0].to_dict() # Fallback al primero
    return fuego.iloc[0].to_dict()

def redactar_propuesta_ia(inmobiliaria, oportunidad):
    """
    Aqui es donde ocurre la magia. 
    En produccion, esto llamaria a una API de LLM (Gemini/Groq).
    Por ahora, armamos el 'Template Inteligente' que la IA completaria.
    """
    nombre_inmo = inmobiliaria['nombre']
    zona = inmobiliaria['zona']
    precio = oportunidad['precio']
    fuente = oportunidad['fuente']
    desc = oportunidad['descripcion'][:100]
    
    # Tono Anti-IA: Callejero, B2B directo, sin adornos.
    prompt_draft = f"""
ASUNTO: Dueño directo en {zona} ({precio}) - Contacto

Hola equipo.

Mi radar acaba de detectar un particular publicando en {zona} a {precio}.
{desc}...

Por el nivel de urgencia, se va a quemar rápido. Si quieren captarlo ustedes antes que la competencia, pasen por la web y destraben el contacto:
http://localhost:5000 (Buscá la zona {zona})

Abrazo,
Radar.
    """
    return prompt_draft

def procesar_leads():
    if not os.path.exists("clientes_b2b/base_inmobiliarias.csv"):
        print("No hay base de inmobiliarias. Corra el generador primero.")
        return

    inmos = pd.read_csv("clientes_b2b/base_inmobiliarias.csv")
    
    print(f"\n--- CEREBRO REDACTOR: Procesando {len(inmos)} Leads ---\n")
    
    for _, inmo in inmos.tail(3).iterrows(): # Procesamos los ultimos 3 para la prueba
        op = obtener_ultima_oportunidad(inmo['zona'])
        if op:
            mensaje = redactar_propuesta_ia(inmo, op)
            print(f"MENSAJE PARA: {inmo['nombre']}")
            print("-" * 30)
            print(mensaje)
            print("-" * 30 + "\n")

if __name__ == "__main__":
    procesar_leads()
