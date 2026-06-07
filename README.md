# ⬡ ARASAKA RESCUE SOFTWARE v1.0

Herramienta profesional de diagnóstico, análisis SMART y recuperación
de discos para Kali Linux / Debian / Ubuntu.

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

# Con root (acceso completo a SMART, todos los dispositivos)
sudo python3 arasaka.py
```

---

## Dependencias

| Paquete         | Uso                              | Instalación                    |
|-----------------|----------------------------------|--------------------------------|
| PyQt6           | Interfaz gráfica                 | pip3 install PyQt6             |
| psutil          | Métricas de E/S en tiempo real   | pip3 install psutil            |
| pySMART         | Datos SMART Python               | pip3 install pySMART           |
| smartmontools   | Backend SMART (smartctl)         | apt install smartmontools       |
| testdisk        | Análisis de particiones          | apt install testdisk           |
| gddrescue       | Imágenes de disco                | apt install gddrescue          |

---

## Funciones

- **Detección automática** de HDD, SSD SATA, SSD NVMe, USB, SD
- **Análisis SMART completo** — atributos ATA y NVMe
- **Métricas en tiempo real** — velocidad lectura/escritura, IOPS
- **Información de particiones** — tipo FS, tamaño, punto de montaje
- **Barra de uso** de espacio en disco
- **Integración con testdisk** — análisis y recuperación de particiones
- **Integración con photorec** — recuperación de archivos por firma
- **Imágenes DD** — backup sector a sector con ddrescue o dd
- **Re-escaneo automático** cada 15 segundos
- **Modo solo lectura** — no modifica datos automáticamente

---

## Notas de seguridad

- La app opera en **modo solo lectura** por defecto
- Las operaciones críticas (DD, clonado) piden **confirmación explícita**
- Se requiere confirmación manual antes de cualquier escritura

---

## Recuperación avanzada

Para recuperación sector a sector, usa testdisk/photorec que se abren
en terminal desde la propia aplicación con un clic.

Para ddrescue manual:
```bash
sudo ddrescue -d -r3 /dev/sdX /destino/imagen.img /destino/imagen.log
```

---

## Soporte de dispositivos

- HDD SATA/SAS
- SSD SATA
- SSD NVMe (M.2)
- Pendrives USB
- Tarjetas SD (vía lector)
- Discos externos USB
- Adaptadores SATA-USB (SMART puede ser limitado por firmware)
