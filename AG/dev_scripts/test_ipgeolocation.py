#!/usr/bin/env python
"""
Test script para verificar integración con ipgeolocation.io API.

Ejecutar: python test_ipgeolocation.py
"""

import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_ipgeolocation_api():
    """Prueba la API de ipgeolocation.io con varias IPs de prueba"""

    api_key = os.getenv('IPGEOLOCATION_API_KEY')

    if not api_key or api_key == 'your-api-key-here':
        print("❌ ERROR: IPGEOLOCATION_API_KEY no configurada en .env")
        print("   Edita el archivo .env y añade tu API key")
        return False

    print("=" * 70)
    print("TEST DE ipgeolocation.io API")
    print("=" * 70)
    print(f"\nAPI Key: {api_key[:10]}..." + "*" * 20)
    print()

    # IPs de prueba
    test_ips = [
        ('8.8.8.8', 'Google DNS (USA)'),
        ('1.1.1.1', 'Cloudflare DNS (Australia)'),
        ('200.93.192.1', 'IP de Ecuador'),
    ]

    success_count = 0

    for ip, description in test_ips:
        print(f"\n🌍 Probando IP: {ip} ({description})")
        print("-" * 70)

        try:
            response = requests.get(
                'https://api.ipgeolocation.io/ipgeo',
                params={'apiKey': api_key, 'ip': ip},
                timeout=5
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # Verificar si hay error
                if 'message' in data and 'error' in data.get('message', '').lower():
                    print(f"❌ Error en respuesta: {data.get('message')}")
                    continue

                # Mostrar información relevante
                print(f"✅ Respuesta exitosa:")
                print(f"   Ciudad: {data.get('city', 'N/A')}")
                print(f"   Provincia/Estado: {data.get('state_prov', 'N/A')}")
                print(f"   País: {data.get('country_name', 'N/A')} ({data.get('country_code2', 'N/A')})")
                print(f"   Coordenadas: {data.get('latitude', 'N/A')}, {data.get('longitude', 'N/A')}")
                print(f"   Zona horaria: {data.get('time_zone', {}).get('name', 'N/A')}")
                print(f"   ISP: {data.get('isp', 'N/A')}")

                success_count += 1
            else:
                print(f"❌ Error HTTP {response.status_code}")
                print(f"   Respuesta: {response.text[:200]}")

        except requests.Timeout:
            print("❌ Timeout al conectar con la API")
        except requests.RequestException as e:
            print(f"❌ Error de conexión: {str(e)}")
        except Exception as e:
            print(f"❌ Error inesperado: {str(e)}")

    print("\n" + "=" * 70)
    print(f"RESUMEN: {success_count}/{len(test_ips)} pruebas exitosas")
    print("=" * 70)

    if success_count == len(test_ips):
        print("\n✅ Todas las pruebas pasaron correctamente!")
        print("   La API de ipgeolocation.io está funcionando.")
        return True
    else:
        print(f"\n⚠️  {len(test_ips) - success_count} prueba(s) fallaron.")
        print("   Verifica tu API key y conexión a internet.")
        return False


def test_ecuador_ip():
    """Prueba específica para IP de Ecuador (país objetivo)"""

    api_key = os.getenv('IPGEOLOCATION_API_KEY')

    if not api_key or api_key == 'your-api-key-here':
        return

    print("\n" + "=" * 70)
    print("TEST ESPECÍFICO: IP DE ECUADOR")
    print("=" * 70)

    # IP conocida de Ecuador
    ecuador_ip = '186.4.217.54'  # IP de Guayaquil, Ecuador

    try:
        response = requests.get(
            'https://api.ipgeolocation.io/ipgeo',
            params={'apiKey': api_key, 'ip': ecuador_ip},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()

            print(f"\n📍 Ubicación detectada:")
            print(f"   IP: {ecuador_ip}")
            print(f"   Ciudad: {data.get('city', 'N/A')}")
            print(f"   Provincia: {data.get('state_prov', 'N/A')}")
            print(f"   País: {data.get('country_name', 'N/A')}")

            # Verificar si es Ecuador
            if data.get('country_code2') == 'EC':
                print(f"\n✅ IP correctamente identificada como Ecuador")

                # Verificar si es Guayas (Milagro está en Guayas)
                state = data.get('state_prov', '')
                if 'Guayas' in state or 'guayas' in state.lower():
                    print(f"✅ Provincia Guayas detectada (donde está Milagro)")
                else:
                    print(f"ℹ️  Provincia detectada: {state}")
            else:
                print(f"⚠️  IP no identificada como Ecuador (código: {data.get('country_code2')})")
        else:
            print(f"❌ Error HTTP {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


def check_api_quota():
    """Verifica el uso de cuota de la API (si está disponible)"""

    api_key = os.getenv('IPGEOLOCATION_API_KEY')

    if not api_key or api_key == 'your-api-key-here':
        return

    print("\n" + "=" * 70)
    print("INFORMACIÓN DE CUOTA API")
    print("=" * 70)
    print("\nPlan gratuito: 50,000 requests/mes")
    print("Para ver uso actual: https://app.ipgeolocation.io/")
    print("\nNota: La API no expone endpoints públicos de cuota,")
    print("debes revisar el dashboard web para ver estadísticas.")
    print("=" * 70)


if __name__ == '__main__':
    print("\n🚀 Iniciando pruebas de ipgeolocation.io\n")

    # Test principal
    success = test_ipgeolocation_api()

    # Test específico de Ecuador
    if success:
        test_ecuador_ip()

    # Información de cuota
    check_api_quota()

    print("\n✨ Tests completados\n")
