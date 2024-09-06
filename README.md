## GEOREFERENCe.PY


### Scripts para obtener las coordenadas a partir de una dirección. Está preparado para leer archivos excel con los campos [Nombre Documento Delegación Dirección Municipio Provincia].

* GeoreferenceNominatim = Emplea nominatim de openstreetmap
* GeoreferenceGoogle = Emplea la api de google. Es necesario tener una apikey
* GeoreferenceGoogleCompare = Compara dos archivos con coordenadas y genera un nuevo archivo con las posibles variaciones.

* Genera un xlxs y un json con los siguientes campos: 
       * "id": 0,
       * "Nombre": "NOMBRE EMPRESA",
       * "Documento": "CIF",
       * "Delegación": 0,
       * "DireccionCompleta": "DIRECCION X, CIUDAD, PROVINCIA",
       * "Latitud": XXXX
       * "Longitud": XXXXXX

        
