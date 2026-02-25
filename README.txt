# WebScrapping Fuentes

Descargador automático de documentos de fuentes legales colombianas (Corte Constitucional, Consejo de Estado, Corte Suprema de Justicia).

## Instalación

Solo necesitas ejecutar el archivo `.exe`. No requiere Python ni instalación adicional.

**Requisitos de Sistema:**
- Windows 7+
- 500 MB de espacio libre
- Conexión a internet

## Uso

1. Ejecuta `WebScrapping.exe`
2. Ve a la pestaña "Dashboard"
3. En "Configurar Scheduler", ingresa el intervalo en segundos
   - 3600 = 1 hora
   - 1800 = 30 minutos
   - 300 = 5 minutos
4. Haz clic en "Iniciar Scheduler"

El aplicativo descargará documentos automáticamente según el intervalo configurado.

## Archivos Generados

El aplicativo crea estos archivos automáticamente:

- **memory.db** - Base de datos de documentos descargados
- **scraper.log** - Registro de eventos y errores
- **downloads/** - Carpeta con documentos descargados
- **config/settings.json** - Configuración del usuario

Estos archivos se crean la primera vez que ejecutas el programa.

## Fuentes Soportadas

- Corte Constitucional
- Consejo de Estado (CE)
- Corte Suprema de Justicia (CSJ)

## Solución de Problemas

### El programa no inicia
- Descarga los archivos en una carpeta sin caracteres especiales
- Asegúrate de tener permisos de escritura en la carpeta

### Los documentos no se descargan
- Verifica tu conexión a internet
- Revisa el log en `scraper.log` para ver errores específicos
- Algunos sitios pueden tener restricciones de acceso

### El scheduler no ejecuta
- Verifica que hayas ingresado un número positivo en segundos
- Revisa los mensajes en la consola del programa

## Contacto

Para reportar problemas o sugerencias, contacta al equipo de desarrollo.
