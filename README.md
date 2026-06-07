# ⬡ ARASAKA RESCUE SOFTWARE v1.0

```text
 █████╗ ██████╗  █████╗ ███████╗ █████╗ ██╗  ██╗ █████╗
██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗██║ ██╔╝██╔══██╗
███████║██████╔╝███████║███████╗███████║█████╔╝ ███████║
██╔══██║██╔══██╗██╔══██║╚════██║██╔══██║██╔═██╗ ██╔══██║
██║  ██║██║  ██║██║  ██║███████║██║  ██║██║  ██╗██║  ██║

      R E S C U E   S O F T W A R E
```

> **Tus recuerdos valen.**

Herramienta profesional de diagnóstico, monitoreo SMART, análisis forense y recuperación de datos para Kali Linux, Debian y Ubuntu.

ARASAKA RESCUE SOFTWARE está diseñada para detectar automáticamente dispositivos de almacenamiento, evaluar su estado de salud, identificar posibles fallos y facilitar la recuperación de información crítica mediante una interfaz moderna, clara y orientada tanto a técnicos como a usuarios avanzados.

---

## Características Principales

### Diagnóstico y Monitoreo

* Detección automática de HDD, SSD SATA, SSD NVMe, USB y tarjetas SD.
* Análisis SMART avanzado.
* Estado de salud de la unidad.
* Temperatura en tiempo real.
* Horas de funcionamiento.
* Vida útil restante.
* Sectores defectuosos y reasignados.
* Riesgo de fallo estimado.

### Información del Dispositivo

* Fabricante y modelo.
* Número de serie.
* Capacidad total.
* Espacio utilizado y disponible.
* Tipo de sistema de archivos.
* Punto de montaje.
* Información detallada de particiones.

### Recuperación de Datos

* Integración con TestDisk.
* Integración con PhotoRec.
* Recuperación de particiones eliminadas.
* Recuperación de archivos por firma.
* Escaneo profundo de dispositivos.

### Clonado y Rescate

* Creación de imágenes de disco.
* Copias sector a sector.
* Compatibilidad con ddrescue.
* Respaldo de unidades dañadas.
* Procedimientos de recuperación segura.

### Monitorización en Tiempo Real

* Velocidad de lectura.
* Velocidad de escritura.
* Estadísticas de E/S.
* Actualización automática cada 15 segundos.
* Indicadores visuales de actividad.

### Seguridad

* Operación en modo solo lectura por defecto.
* Sin modificaciones automáticas.
* Confirmación obligatoria para operaciones críticas.
* Protección contra sobrescritura accidental.

---

## Instalación rápida

```bash
chmod +x instalar_y_ejecutar.sh
sudo bash instalar_y_ejecutar.sh
```

---

## Ejecución manual

```bash
# Sin root (funcionalidad limitada)
python3 arasaka.py

# Con root (acceso completo a SMART y todos los dispositivos)
sudo python3 arasaka.py
```

---

## Dependencias

| Paquete       | Uso                          | Instalación               |
| ------------- | ---------------------------- | ------------------------- |
| PyQt6         | Interfaz gráfica             | pip3 install PyQt6        |
| psutil        | Métricas en tiempo real      | pip3 install psutil       |
| pySMART       | Datos SMART                  | pip3 install pySMART      |
| smartmontools | Backend SMART                | apt install smartmontools |
| testdisk      | Recuperación de particiones  | apt install testdisk      |
| gddrescue     | Imágenes y rescate de discos | apt install gddrescue     |

---

## Recuperación Avanzada

ARASAKA RESCUE SOFTWARE integra herramientas ampliamente utilizadas en recuperación de datos y análisis de almacenamiento.

### TestDisk

Permite:

* Recuperar particiones eliminadas.
* Reparar tablas de particiones.
* Analizar estructuras dañadas.

### PhotoRec

Permite:

* Recuperar archivos eliminados.
* Recuperar información desde dispositivos dañados.
* Recuperación basada en firmas de archivos.

### ddrescue

Para clonado y rescate avanzado:

```bash
sudo ddrescue -d -r3 /dev/sdX /destino/imagen.img /destino/imagen.log
```

---

## Soporte de Dispositivos

* HDD SATA
* HDD SAS
* SSD SATA
* SSD NVMe (M.2)
* Pendrives USB
* Tarjetas SD
* Discos externos USB
* Adaptadores SATA-USB*

* Algunas funciones SMART pueden estar limitadas por el firmware del adaptador.

---

## Filosofía del Proyecto

Cuando un disco falla, no solo están en riesgo archivos.

Están en riesgo fotografías, documentos, proyectos, investigaciones, recuerdos y años de trabajo.

ARASAKA RESCUE SOFTWARE nace con un objetivo simple:

# Tus recuerdos valen.

---

## Licencia

Distribuido bajo licencia MIT.

---

## Descargo de Responsabilidad

Aunque la aplicación está diseñada para minimizar riesgos y operar en modo seguro, siempre se recomienda realizar copias de seguridad antes de ejecutar procedimientos de recuperación o clonado sobre dispositivos con fallos físicos o lógicos.
