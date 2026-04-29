#!/bin/sh
set -e

PREFIX=/usr/share/tailscale-systray
BINDIR=/usr/local/bin
AUTOSTART_DIR=/etc/xdg/autostart
DESKTOP_DIR=/usr/share/applications

echo "Installing system dependencies..."
apt update
apt install -y gir1.2-ayatanaappindicator3-0.1

echo "Setting tailscale operator to $SUDO_USER..."
tailscale set --operator="$SUDO_USER"

echo "Installing tailscale-systray..."
install -d "$PREFIX"
install -m 644 src/tailscale_systray.py "$PREFIX/"
install -m 644 assets/*.png "$PREFIX/"

install -d "$BINDIR"
printf '#!/bin/sh\nexec python3 %s/tailscale_systray.py "$@"\n' "$PREFIX" > "$BINDIR/tailscale-systray"
chmod 755 "$BINDIR/tailscale-systray"

install -d "$AUTOSTART_DIR"
install -m 644 tailscale-systray.desktop "$AUTOSTART_DIR/"

install -d "$DESKTOP_DIR"
install -m 644 tailscale-systray.desktop "$DESKTOP_DIR/"

echo "Done. Tailscale Systray will start on next login, or run 'tailscale-systray' now."
