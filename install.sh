#!/bin/bash
set -e

KIOSK_USER="kiosk"
KIOSK_HOME="/home/$KIOSK_USER"
APP_DIR="$KIOSK_HOME/app"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[*]${NC} $1"; }
print_error() { echo -e "${RED}[!]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }

echo "=========================================="
echo "  Kiosk MVP - Otomatik Kurulum"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    print_error "Bu script root olarak calistirilmali!"
    echo "Kullanim: sudo bash install.sh"
    exit 1
fi

print_status "[1/8] Sistem guncelleniyor..."
apt-get update
apt-get upgrade -y

print_status "[2/8] Gerekli paketler kuruluyor..."
apt-get install -y \
    xorg \
    openbox \
    nodm \
    unclutter \
    python3 \
    python3-venv \
    python3-pip \
    git \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libgl1 \
    libegl1 \
    libxkbcommon0 \
    libdbus-1-3 \
    fontconfig

print_status "[3/8] Kiosk kullanicisi olusturuluyor..."
if id "$KIOSK_USER" &>/dev/null; then
    print_warning "Kullanici zaten mevcut, atlaniyor..."
else
    useradd -m -s /bin/bash -c "Kiosk User" $KIOSK_USER
fi
usermod -aG tty,video $KIOSK_USER

print_status "[4/8] Dizinler olusturuluyor..."
mkdir -p $APP_DIR
mkdir -p $KIOSK_HOME/data
mkdir -p $KIOSK_HOME/logs
mkdir -p $KIOSK_HOME/.config/openbox

print_status "[5/8] Uygulama dosyalari kopyalaniyor..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "$SCRIPT_DIR/app/main.py" "$APP_DIR/"
cp -r "$SCRIPT_DIR/app/config" "$APP_DIR/"
cp -r "$SCRIPT_DIR/app/core" "$APP_DIR/"
cp -r "$SCRIPT_DIR/app/models" "$APP_DIR/"
cp -r "$SCRIPT_DIR/app/services" "$APP_DIR/"
cp -r "$SCRIPT_DIR/app/utils" "$APP_DIR/"
cp -r "$SCRIPT_DIR/app/ui" "$APP_DIR/"

if [ -f "$SCRIPT_DIR/app/database.py" ]; then
    cp "$SCRIPT_DIR/app/database.py" "$APP_DIR/"
fi

chown -R $KIOSK_USER:$KIOSK_USER $KIOSK_HOME

print_status "[6/8] Python ortami hazirlaniyor..."
sudo -u $KIOSK_USER python3 -m venv "$APP_DIR/venv"
sudo -u $KIOSK_USER "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u $KIOSK_USER "$APP_DIR/venv/bin/pip" install PySide6

print_status "[7/8] Sistem yapilandiriliyor..."

echo "allowed_users=anybody" > /etc/X11/Xwrapper.config

cat > /etc/default/nodm << EOF
NODM_ENABLED=true
NODM_USER=$KIOSK_USER
NODM_FIRST_VT=7
NODM_XSESSION=$KIOSK_HOME/.xsession
NODM_X_OPTIONS='-nolisten tcp'
NODM_MIN_SESSION_TIME=60
EOF

cat > $KIOSK_HOME/.xsession << 'EOF'
#!/bin/bash
xset s off
xset -dpms
xset s noblank
unclutter -idle 1 -root &
cd /home/kiosk/app
export PYTHONPATH="/home/kiosk/app"
exec /home/kiosk/app/venv/bin/python -m app.main
EOF

chmod +x $KIOSK_HOME/.xsession
chown $KIOSK_USER:$KIOSK_USER $KIOSK_HOME/.xsession

systemctl enable nodm

print_status "[8/8] Veritabani baslatiliyor..."
cd "$APP_DIR"
sudo -u $KIOSK_USER "$APP_DIR/venv/bin/python" -c "
import sys
sys.path.insert(0, '$APP_DIR')
from app.main import init_database
init_database()
"

echo ""
echo "=========================================="
echo -e "  ${GREEN}Kurulum Tamamlandi!${NC}"
echo "=========================================="
echo ""
echo "Giris Bilgileri:"
echo "  Badge: ADMIN001"
echo "  PIN:   1234"
echo ""
echo "Sistemi yeniden baslatin:"
echo "  reboot"
echo ""
