import os

print("\n" + "="*50)
print("  ASISTENTE DE CONFIGURACION MERCADOPAGO")
print("="*50 + "\n")

token = input("> Pega tu Access Token aca (clic derecho) y dale Enter:\n> ").strip()

if token.startswith("APP_USR-") or token.startswith("TEST-"):
    with open(".env", "a") as f:
        f.write(f"\nMP_ACCESS_TOKEN={token}\n")
    print("\nEXITO! Token guardado y encriptado en el sistema.")
    print("El Radar Pro ya está listo para facturar.")
else:
    print("\nError: Ese no parece un Access Token valido.")
    print("Asegurate de copiar el que dice 'Access Token' (suele empezar con APP_USR-)")
