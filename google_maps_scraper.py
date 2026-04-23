"""
=============================================================
  GENERADOR DE LEADS B2B — Google Maps Scraper
  Busca inmobiliarias en una zona para armar la base de ventas.
  Filosofía: Efímero, Cero Multimedia (Low RAM).
=============================================================
"""
import asyncio
import csv
import os
from datetime import datetime
from playwright.async_api import async_playwright

os.makedirs("clientes_b2b", exist_ok=True)

async def _block_aggressively(route):
    """Bloquea todo lo que no sea necesario para ahorrar RAM y red."""
    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
        await route.abort()
    else:
        await route.continue_()

async def buscar_inmobiliarias(zona: str, max_resultados: int = 15):
    print(f"\n[B2B Scraper] Buscando inmobiliarias en: {zona}")
    resultados = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await page.route("**/*", _block_aggressively)
        
        try:
            query = f"inmobiliaria en {zona}, argentina"
            await page.goto(f"https://www.google.com/maps/search/{query.replace(' ', '+')}", timeout=60000)
            
            # Esperar a que cargue la lista lateral
            await page.wait_for_selector('a[href*="/maps/place/"]', timeout=15000)
            
            # Scrolleo para cargar mas resultados
            # En Maps la lista lateral tiene el rol de "feed"
            print("[B2B Scraper] Scrolleando resultados...")
            for _ in range(3):
                await page.mouse.wheel(0, 5000)
                await page.wait_for_timeout(1000)
                
            # Extraer links de cada lugar
            places = await page.locator('a[href*="/maps/place/"]').all()
            print(f"[B2B Scraper] Encontrados {len(places)} perfiles. Procesando top {max_resultados}...")
            
            for i, place in enumerate(places[:max_resultados]):
                try:
                    # Scroll al elemento y click
                    await place.scroll_into_view_if_needed()
                    await place.click()
                    await page.wait_for_timeout(2000) # Esperar que abra el panel
                    
                    # Extraer datos del panel principal
                    nombre_tag = page.locator('h1.DUwDvf.fontHeadlineLarge')
                    nombre = await nombre_tag.inner_text() if await nombre_tag.count() > 0 else f"Inmobiliaria {i}"
                    
                    # El telefono suele tener una imagen de icono o el protocolo tel:
                    tel_tag = page.locator('button[data-tooltip="Copiar el número de teléfono"] div.Io6YTe')
                    telefono = await tel_tag.inner_text() if await tel_tag.count() > 0 else ""
                    
                    # Sitio Web
                    web_tag = page.locator('a[data-tooltip="Abrir el sitio web"] div.Io6YTe')
                    web = await web_tag.inner_text() if await web_tag.count() > 0 else ""
                    
                    print(f"  + {nombre} | {telefono} | {web}")
                    
                    resultados.append({
                        "zona": zona,
                        "nombre": nombre,
                        "telefono": telefono,
                        "web": web,
                        "fecha_scraping": datetime.now().strftime("%Y-%m-%d")
                    })
                except Exception as e:
                    print(f"  - Error en perfil {i}: {e}")
                    
        except Exception as e:
            print(f"[B2B Scraper] Error general: {e}")
        finally:
            print("[B2B Scraper] Cerrando navegador para liberar RAM...")
            await context.close()
            await browser.close()
            
    # Guardar en CSV acumulativo
    if resultados:
        fname = "clientes_b2b/base_inmobiliarias.csv"
        file_exists = os.path.isfile(fname)
        with open(fname, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["zona", "nombre", "telefono", "web", "fecha_scraping"])
            if not file_exists:
                writer.writeheader()
            writer.writerows(resultados)
        print(f"\n[B2B Scraper] ✅ {len(resultados)} leads guardados en {fname}")
        
    return resultados

if __name__ == "__main__":
    import sys
    zona_test = sys.argv[1] if len(sys.argv) > 1 else "palermo"
    asyncio.run(buscar_inmobiliarias(zona_test, max_resultados=5))
