# ==============================================================================
# Archivo  : packaging/generar_iconos.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Genera logo.png (transparente), icono.ico
#          |            | (Windows, 16-256 px; logo.png sirve para macOS/Linux) a
#          |            | partir de assets/logo.jpeg, recortando la tarjeta
#          |            | redondeada y eliminando el fondo.
# ==============================================================================
"""Genera los iconos de la aplicación desde el logo original.

Uso:  uv run python packaging/generar_iconos.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent.parent / "src" / "generador_croquis" / "assets"
ORIGEN = ASSETS / "logo.jpeg"

# Tarjeta blanca del logo dentro del JPEG de 2048 px (medida sobre el original).
TARJETA = (334, 255, 1713, 1781)
RADIO = 160
TAMANOS_ICO = [16, 20, 24, 32, 40, 48, 64, 128, 256]


def recortar_tarjeta(origen: Path) -> Image.Image:
    """Recorta la tarjeta, vuelve transparente el exterior y la centra en un lienzo cuadrado."""
    img = Image.open(origen).convert("RGBA").crop(TARJETA)
    escala = 4
    mascara = Image.new("L", (img.width * escala, img.height * escala), 0)
    ImageDraw.Draw(mascara).rounded_rectangle(
        (0, 0, mascara.width - 1, mascara.height - 1), RADIO * escala, fill=255
    )
    img.putalpha(mascara.resize(img.size, Image.LANCZOS))

    lado = max(img.size)
    lienzo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    lienzo.paste(img, ((lado - img.width) // 2, (lado - img.height) // 2), img)
    return lienzo


def main() -> None:
    logo = recortar_tarjeta(ORIGEN)
    logo.resize((512, 512), Image.LANCZOS).save(ASSETS / "logo.png", optimize=True)
    logo.save(ASSETS / "icono.ico", sizes=[(s, s) for s in TAMANOS_ICO])
    for nombre in ("logo.png", "icono.ico"):
        ruta = ASSETS / nombre
        print(f"{ruta.relative_to(ASSETS.parent.parent.parent)}  {ruta.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
