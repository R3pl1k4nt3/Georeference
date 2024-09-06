import socket
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut,GeocoderQueryError,GeocoderServiceError
import time
import json


""" # Función personalizada que fuerza el uso de IPv4
class IPv4Nominatim(Nominatim):
    def _call_geocoder(self, url, callback=None, timeout=None, headers=None):
        original_socket = socket.socket
        try:
            # Forzar el uso de IPv4
            socket.socket = lambda *args, **kwargs: original_socket(socket.AF_INET, socket.SOCK_STREAM)
            return super(IPv4Nominatim, self)._call_geocoder(url, callback, timeout, headers)
        finally:
            socket.socket = original_socket
 """


# Función para obtener coordenadas usando Nominatim con manejo de errores de tiempo de espera
def obtener_coordenadas_nominatim(direccion, retries=3, timeout=10):
    #geolocator = IPv4Nominatim(user_agent="geoapiExercises")
    geolocator = Nominatim(user_agent="geoapiExercises")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2)

    """ try:
        for intento in range(retries):
            try:
                location = geocode(direccion, timeout=timeout)
                
                if location:
                    return location.latitude, location.longitude
                else:
                    print(f"Resultado de geocodificación: {location.raw}")  # Imprime el resultado crudo
                    return location.latitude, location.longitude
                    #print(f"No se encontró ubicación para la dirección: {direccion}")
                    #return None, None
            except GeocoderTimedOut:
                print(f"Timeout en el intento {intento + 1} para la dirección: {direccion}")
                time.sleep(2)  # Pausa antes de reintentar
        return None, None  # Si no se encuentra después de varios intentos
    except Exception as e:
        print(f"Error en la geocodificación de {direccion}: {e}")
        return None, None """
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


# Leer archivo Excel
archivo = '/home/alex/Documentos/empresas_listado.xlsx'  # Especifica la ruta del archivo
df = pd.read_excel(archivo)

# Verificar que las columnas "Dirección", "Municipio" y "Provincia" existen
for col in ['Dirección', 'Municipio', 'Provincia']:
    if col not in df.columns:
        raise ValueError(f"La columna {col} no está presente en el archivo")

# Asegurar que las columnas son de tipo str antes de concatenar
df['Dirección'] = df['Dirección'].astype(str)
df['Municipio'] = df['Municipio'].astype(str)
df['Provincia'] = df['Provincia'].astype(str)
df['id'] = df.index

# Limpiar espacios extra y concatenar las columnas para formar la dirección completa
df['DireccionCompleta'] = (df['Dirección'].str.strip() + ', ' +
                            df['Municipio'].str.strip() + ', ' +
                            df['Provincia'].str.strip()).str.replace('\s+', ' ', regex=True)


# Inicializar lista para almacenar coordenadas
coordenadas = []

# Procesar cada dirección
for i, direccion in enumerate(df['DireccionCompleta']):
    # Solo proceder si la dirección no está vacía
    if not direccion.strip():
        print(f"Dirección vacía en el registro {i + 1}")
        coordenadas.append([None, None])
        continue

    lat, lng = obtener_coordenadas_nominatim(direccion)
    coordenadas.append([lat, lng])
    
    # Imprimir progreso cada 100 registros
    if (i + 1) % 100 == 0:
        print(f"Registros procesados: {i + 1}/{len(df)}")
    
    # Guardar progreso temporal cada 100 registros (ajustado para 1000 registros)
    if (i + 1) % 1000 == 0:
        df_temp = df.iloc[:i + 1].copy()  # Solo copia las filas procesadas hasta el momento
        df_temp[['Latitud', 'Longitud']] = pd.DataFrame(coordenadas, index=df_temp.index)
        df_temp.to_excel(f'/home/alex/Documentos/archivo_con_coordenadas_parcial_{i + 1}.xlsx', index=False)
        df_temp_json = df_temp[['id','Nombre', 'Documento', 'Delegacion', 'DireccionCompleta', 'Latitud', 'Longitud']].to_dict(orient='records')
        with open(f'/home/alex/Documentos/archivo_con_coordenadas_parcial_{i + 1}.json', 'w', encoding='utf-8') as f:
            json.dump(df_temp_json, f, indent=4)  
        
    

# Verificar que el número de coordenadas coincide con el número de filas
if len(coordenadas) != len(df):
    raise ValueError("El número de coordenadas no coincide con el número de direcciones")

# Agregar las coordenadas al DataFrame original
df[['Latitud', 'Longitud']] = pd.DataFrame(coordenadas, index=df.index)

# Guardar el resultado final en un archivo Excel
df.to_excel('/home/alex/Documentos/archivo_con_coordenadas_nominatim.xlsx', index=False)

df.to_json = df[['Nombre', 'Documento', 'Delegación', 'DireccionCompleta', 'Latitud', 'Longitud']].to_dict(orient='records')
with open(f'/home/alex/Documentos/archivo_con_coordenadas.json', 'w', encoding='utf-8') as f:
            json.dump(df_temp_json, f, indent=4)

print("Proceso completado. El archivo con coordenadas ha sido guardado.")