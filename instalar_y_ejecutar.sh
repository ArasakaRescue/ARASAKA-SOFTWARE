#!/bin/bash
# ─────────────────────────────────────────────────────────────────
#  ARASAKA RESCUE SOFTWARE — Instalación y lanzamiento
#  Kali Linux / Debian / Ubuntu
# ─────────────────────────────────────────────────────────────────

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
AMBER='\033[0;33m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${RED}"
cat << 'EOF'
  ╔═══════════════════════════════════════════╗
  ║        ARASAKA RESCUE SOFTWARE            ║
  ║         Instalación de dependencias       ║
  ╚═══════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Detectar gestor de paquetes
if command -v apt-get &>/dev/null; then
    PKG="apt-get"
elif command -v apt &>/dev/null; then
    PKG="apt"
else
    echo -e "${AMBER}Sistema no basado en Debian detectado. Instala manualmente:${NC}"
    echo "  smartmontools, testdisk, ddrescue, python3-pyqt6"
    exit 1
fi

echo -e "${AMBER}[1/4]${NC} Actualizando repositorios..."
sudo $PKG update -qq

echo -e "${AMBER}[2/4]${NC} Instalando dependencias del sistema..."
sudo $PKG install -y \
    smartmontools \
    testdisk \
    gddrescue \
    python3-pip \
    python3-psutil \
    usbutils \
    hdparm \
    2>/dev/null || true

# ddrescue puede llamarse diferente
sudo $PKG install -y ddrescue 2>/dev/null || true

echo -e "${AMBER}[3/4]${NC} Instalando dependencias Python..."
pip3 install PyQt6 pySMART --break-system-packages 2>/dev/null || \
pip3 install PyQt6 pySMART 2>/dev/null || true

echo -e "${AMBER}[4/4]${NC} Verificando instalación..."

MISSING=()
command -v smartctl &>/dev/null || MISSING+=("smartmontools")
command -v testdisk &>/dev/null || MISSING+=("testdisk")
python3 -c "import PyQt6" 2>/dev/null || MISSING+=("PyQt6")

if [ ${#MISSING[@]} -gt 0 ]; then
    echo -e "${RED}Faltan dependencias: ${MISSING[*]}${NC}"
    echo "Instálalas manualmente e intenta de nuevo."
    exit 1
fi

echo -e "${GREEN}✓ Todas las dependencias instaladas correctamente${NC}"
echo ""
echo -e "${RED}${BOLD}LANZANDO ARASAKA RESCUE SOFTWARE...${NC}"
echo -e "${AMBER}Nota: Para acceso completo a SMART y dispositivos, ejecuta con sudo${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$EUID" -ne 0 ]; then
    echo -e "${AMBER}Ejecutando sin root (SMART limitado). Para acceso completo:${NC}"
    echo -e "  sudo bash $0"
    echo ""
fi

python3 "$SCRIPT_DIR/arasaka.py"
