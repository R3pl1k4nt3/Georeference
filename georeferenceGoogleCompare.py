import pandas as pd
from geopy.geocoders import GoogleV3
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderQueryError, GeocoderServiceError
import time
import json
import argparse
import sys


# Aquí ponemos API Key de Google
api_key = ''

# Función para obtener coordenadas usando Google API con manejo de errores de tiempo de espera
def obtener_coordenadas_google(direccion, api_key, retries=3, timeout=10):
    geolocator = GoogleV3(api_key=api_key)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2)

    for intento in range(retries):
        try:
            print(f"Consultando dirección: {direccion}")
            location = geocode(direccion, timeout=timeout)
            if location:
                print(f"Resultado de geocodificación: {location.raw}")  # Imprime el resultado crudo
                return location.latitude, location.longitude
            else:
                print(f"No se encontró ubicación para la dirección: {direccion}")
                return None, None
        except GeocoderTimedOut:
            print(f"Timeout en el intento {intento + 1} para la dirección: {direccion}")
            time.sleep(2)
        except GeocoderServiceError as e:
            print(f"Error de servicio de geocodificación para la dirección {direccion}: {e}")
            time.sleep(2)
        except GeocoderQueryError as e:
            print(f"Error en la consulta de geocodificación para la dirección {direccion}: {e}")
            time.sleep(2)
        except Exception as e:
            print(f"Error en la geocodificación de {direccion}: {e}")
            return None, None
    return None, None


def comparar_archivos(archivo_viejo, archivo_nuevo, api_key, formato='excel'):
    # Leer archivos en formato Excel
    df_viejo = pd.read_excel(archivo_viejo)
    df_nuevo = pd.read_excel(archivo_nuevo)

    # Asegurarse de que el nuevo archivo tenga todas las columnas necesarias
    columnas_necesarias = ['Nombre', 'Documento', 'Delegación', 'Dirección', 'Municipio', 'Provincia', 'id', 'DireccionCompleta', 'Latitud', 'Longitud']
    
    # Añadir las columnas que faltan en df_nuevo
    for columna in columnas_necesarias:
        if columna not in df_nuevo.columns:
            df_nuevo[columna] = None  # Agregar la columna faltante con valores vacíos

    # Verificar si las columnas 'Latitud' y 'Longitud' están en el DataFrame viejo, si no, inicializarlas con None
    if 'Latitud' not in df_viejo.columns:
        df_viejo['Latitud'] = None
    if 'Longitud' not in df_viejo.columns:
        df_viejo['Longitud'] = None

    # Convertir DireccionCompleta a string si no lo es
    df_viejo['DireccionCompleta'] = df_viejo['DireccionCompleta'].astype(str)
    df_nuevo['DireccionCompleta'] = df_nuevo['DireccionCompleta'].astype(str)

    # Unir ambos DataFrames por el campo 'id' para comparar
    df_comparacion = df_nuevo.merge(df_viejo[['id', 'DireccionCompleta', 'Latitud', 'Longitud']], on='id', how='left', suffixes=('_nuevo', '_viejo'))

    # Inicializar lista para coordenadas de nuevos registros o direcciones cambiadas
    coordenadas_actualizadas = []

    # Verificar direcciones nuevas, modificadas o con coordenadas faltantes
    for i, fila in df_comparacion.iterrows():
        direccion_nueva = fila['DireccionCompleta_nuevo']
        direccion_vieja = fila['DireccionCompleta_viejo']
        lat_nueva = fila.get('Latitud_nuevo', None)
        lng_nueva = fila.get('Longitud_nuevo', None)

        # Si la dirección ha cambiado o es un registro nuevo (sin coordenadas) o las coordenadas están vacías (NaN)
        if pd.isna(direccion_vieja) or direccion_nueva != direccion_vieja or pd.isna(lat_nueva) or pd.isna(lng_nueva):
            print(f"Dirección nueva, modificada o sin coordenadas para id {fila['id']}: {direccion_nueva}")
            lat, lng = obtener_coordenadas_google(direccion_nueva, api_key)
            coordenadas_actualizadas.append([lat, lng])
        else:
            # Si ya tiene coordenadas válidas, no recalcular
            coordenadas_actualizadas.append([lat_nueva, lng_nueva])

    # Asignar las nuevas coordenadas al DataFrame
    df_comparacion[['Latitud', 'Longitud']] = pd.DataFrame(coordenadas_actualizadas, index=df_comparacion.index)

    # Rellenar los NaN en 'DireccionCompleta_viejo' con los valores de 'DireccionCompleta_nuevo'
    df_comparacion['DireccionCompleta'] = df_comparacion['DireccionCompleta_nuevo'].fillna(df_comparacion['DireccionCompleta_viejo'])

    # Filtrar los registros que están en el archivo nuevo (comparación de 'id') y eliminar los que ya no existen
    ids_nuevo = set(df_nuevo['id'])  # IDs del nuevo archivo
    df_final = df_viejo[df_viejo['id'].isin(ids_nuevo)]  # Filtrar solo los que existen en el nuevo archivo

    # Combinar los datos actualizados del archivo nuevo
    df_final = df_comparacion[['id', 'Nombre', 'Documento', 'Delegación', 'DireccionCompleta', 'Latitud', 'Longitud']]

    # Guardar el archivo final en el formato especificado
    if formato == 'excel':
        df_final.to_excel('archivo_actualizado.xlsx', index=False)
    elif formato == 'json':
        df_final_json = df_final.to_dict(orient='records')
        with open('archivo_actualizado.json', 'w', encoding='utf-8') as f:
            json.dump(df_final_json, f, ensure_ascii=False, indent=4)

    print("Archivo actualizado guardado.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 script.py archivo_viejo archivo_nuevo [formato]")
        sys.exit(1)

    archivo_viejo = sys.argv[1]
    archivo_nuevo = sys.argv[2]
    formato = sys.argv[3] if len(sys.argv) > 3 else 'excel'

    if formato not in ['excel', 'json']:
        print("Formato no soportado. Usa 'excel' o 'json'.")
        sys.exit(1)

 
    comparar_archivos(archivo_viejo, archivo_nuevo, api_key, formato)