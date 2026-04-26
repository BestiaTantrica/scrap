from curl_cffi import requests

url = "https://inmuebles.mercadolibre.com.ar/departamentos/venta/capital-federal/caba"
response = requests.get(url, impersonate="chrome110")
print(f"Status for {url}: {response.status_code}")

url2 = "https://listado.mercadolibre.com.ar/inmuebles/departamentos/venta/capital-federal/caba"
response2 = requests.get(url2, impersonate="chrome110")
print(f"Status for {url2}: {response2.status_code}")

url3 = "https://listado.mercadolibre.com.ar/inmuebles/departamentos/venta/capital-federal/"
response3 = requests.get(url3, impersonate="chrome110")
print(f"Status for {url3}: {response3.status_code}")
