"""Generate app icon at all required sizes and produce assets/icon.icns."""
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QApplication

ROOT = Path(__file__).parent.parent
ICONSET = ROOT / "assets" / "icon.iconset"
ICONSET.mkdir(parents=True, exist_ok=True)

# Required sizes for a macOS .icns
SIZES = [16, 32, 64, 128, 256, 512, 1024]


def draw_icon(size: int) -> QPixmap:
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    r = s * 0.22          # corner radius

    # ── gradient background ───────────────────────────────────
    grad = QLinearGradient(0, 0, 0, s)
    grad.setColorAt(0.0, QColor("#1DB954"))   # Spotify-ish green top
    grad.setColorAt(1.0, QColor("#0d7a38"))   # darker green bottom

    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, s, s), r, r)
    p.fillPath(path, grad)

    # ── music note ────────────────────────────────────────────
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 230))

    m = s * 0.18          # margin
    nh = s * 0.22         # note-head height
    nw = s * 0.26         # note-head width
    sw = s * 0.08         # stem width

    # Note head (ellipse, slightly tilted via shear)
    p.save()
    p.translate(s * 0.28, s * 0.68)
    p.rotate(-20)
    p.drawEllipse(QRectF(-nw / 2, -nh / 2, nw, nh))
    p.restore()

    # Stem
    stem_x = s * 0.28 + nw * 0.4
    p.fillRect(
        int(stem_x), int(s * 0.24),
        int(sw), int(s * 0.46),
        QColor(255, 255, 255, 230),
    )

    # Flag / beam (top-right hook)
    flag_path = QPainterPath()
    flag_path.moveTo(stem_x + sw, s * 0.24)
    flag_path.cubicTo(
        stem_x + sw + s * 0.22, s * 0.30,
        stem_x + sw + s * 0.22, s * 0.40,
        stem_x + sw,             s * 0.44,
    )
    flag_path.lineTo(stem_x + sw, s * 0.38)
    flag_path.cubicTo(
        stem_x + sw + s * 0.14, s * 0.34,
        stem_x + sw + s * 0.14, s * 0.28,
        stem_x + sw,             s * 0.24,
    )
    flag_path.closeSubpath()
    p.fillPath(flag_path, QColor(255, 255, 255, 230))

    p.end()
    return px


def main() -> None:
    app = QApplication(sys.argv)

    for size in SIZES:
        px = draw_icon(size)
        # 1x
        path_1x = ICONSET / f"icon_{size}x{size}.png"
        px.save(str(path_1x))
        # 2x (retina) — only relevant for sizes that have a @2x pair
        if size <= 512:
            px2 = draw_icon(size * 2)
            path_2x = ICONSET / f"icon_{size}x{size}@2x.png"
            px2.save(str(path_2x))

    print(f"Saved {len(list(ICONSET.glob('*.png')))} PNG files to {ICONSET}")

    # Convert to .icns using macOS iconutil
    icns_path = ROOT / "assets" / "icon.icns"
    result = subprocess.run(
        ["iconutil", "-c", "icns", str(ICONSET), "-o", str(icns_path)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"Created {icns_path}")
    else:
        print(f"iconutil failed: {result.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    main()
