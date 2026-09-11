# -*- coding: utf-8 -*-
"""
Prepara todas las piezas del logo a partir de la imagen original del local.

Recorta el circulo (la foto viene con fondo negro alrededor), le pone
transparencia con el borde suavizado, y genera:

  icono.ico                   icono del programa (escritorio, barra de tareas)
  instalador-grande.bmp       imagen del instalador (costado izquierdo)
  instalador-chico.bmp        imagen del instalador (esquina de cada paso)
  ../imagen_marca.py          logo para la ventana y para el PDF, en base64
  ../../docs/logo.png         logo para la pagina de descarga

Solo hace falta correrlo si cambia el logo. Necesita Pillow:
    pip install pillow
    python preparar_logo.py
"""
import base64
import io
import math
import os

from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGINAL = os.path.join(AQUI, "logo-original.jpeg")
PAPEL = (255, 255, 255)
SUPER = 4


def ubicar_circulo(im):
    """Centro y radio del circulo: se buscan sus bordes desde afuera hacia adentro."""
    w, h = im.size
    px = im.load()
    cx, cy = w / 2.0, h / 2.0
    puntos = []
    for g in range(0, 360, 2):
        a = math.radians(g)
        for r in range(int(max(w, h) * 0.75), 0, -1):
            x, y = int(cx + r * math.cos(a)), int(cy + r * math.sin(a))
            if 0 <= x < w and 0 <= y < h and sum(px[x, y]) > 90:
                if 2 < x < w - 3 and 2 < y < h - 3:
                    puntos.append((x, y))
                break

    def dispersion(c):
        ds = [math.hypot(x - c[0], y - c[1]) for x, y in puntos]
        m = sum(ds) / len(ds)
        return sum((d - m) ** 2 for d in ds) / len(ds), m

    mejor = min(((dispersion((cx + dx, cy + dy)), cx + dx, cy + dy)
                 for dx in range(-12, 13) for dy in range(-12, 13)),
                key=lambda t: t[0][0])
    (_, radio), mx, my = mejor
    return mx, my, radio


def recortar():
    im = Image.open(ORIGINAL).convert("RGB")
    cx, cy, radio = ubicar_circulo(im)
    radio -= 7                                  # un poco adentro: sin borde negro
    lado = int(radio * 2)
    x0, y0 = int(round(cx - radio)), int(round(cy - radio))
    cuadro = Image.new("RGB", (lado, lado), (0, 0, 0))
    cuadro.paste(im.crop((x0, y0, x0 + lado, y0 + lado)), (0, 0))

    mascara = Image.new("L", (lado * SUPER, lado * SUPER), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, lado * SUPER - 1, lado * SUPER - 1), fill=255)
    mascara = mascara.resize((lado, lado), Image.LANCZOS)   # borde suavizado
    logo = cuadro.convert("RGBA")
    logo.putalpha(mascara)
    return logo


def achicar(logo, lado):
    return logo.resize((lado, lado), Image.LANCZOS)


def sobre_blanco(logo, lado, ancho=None, alto=None, arriba=None):
    """El logo sobre fondo blanco (para BMP y JPEG, que no tienen transparencia)."""
    ancho, alto = ancho or lado, alto or lado
    fondo = Image.new("RGB", (ancho, alto), PAPEL)
    chico = achicar(logo, lado)
    x = (ancho - lado) // 2
    y = (alto - lado) // 2 if arriba is None else arriba
    fondo.paste(chico, (x, y), chico)
    return fondo


def png(im):
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()


def jpeg(im):
    b = io.BytesIO(); im.save(b, "JPEG", quality=92, optimize=True); return b.getvalue()


def main():
    logo = recortar()
    print("  logo recortado: %dx%d" % logo.size)

    achicar(logo, 256).save(os.path.join(AQUI, "icono.ico"),
                            sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                                   (64, 64), (128, 128), (256, 256)])
    print("  icono.ico")

    # Instalador: la imagen grande del costado y la chica de la esquina.
    sobre_blanco(logo, 140, 164, 314, arriba=70).save(
        os.path.join(AQUI, "instalador-grande.bmp"))
    sobre_blanco(logo, 52, 55, 58).save(os.path.join(AQUI, "instalador-chico.bmp"))
    print("  imagenes del instalador")

    # La ventana muestra PNG (Tk 8.6); el PDF usa JPEG, que reportlab
    # incrusta sin necesitar Pillow dentro del programa.
    destino = os.path.normpath(os.path.join(AQUI, "..", "imagen_marca.py"))
    with open(destino, "w") as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('"""Logo del local, en base64. Generado por '
                'empaquetado/preparar_logo.py; no editar a mano."""\n\n')
        for nombre, datos in (("CABECERA", png(achicar(logo, 62))),
                              ("ICONO", png(achicar(logo, 64))),
                              ("PDF_JPEG", jpeg(sobre_blanco(logo, 300)))):
            f.write('%s = """%s"""\n\n' % (nombre, base64.b64encode(datos).decode()))
    print("  imagen_marca.py")

    docs = os.path.normpath(os.path.join(AQUI, "..", "..", "docs"))
    if os.path.isdir(docs):
        achicar(logo, 360).save(os.path.join(docs, "logo.png"), optimize=True)
        achicar(logo, 64).save(os.path.join(docs, "favicon.png"), optimize=True)
        print("  docs/logo.png y docs/favicon.png")


if __name__ == "__main__":
    main()
