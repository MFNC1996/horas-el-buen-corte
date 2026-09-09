# -*- coding: utf-8 -*-
"""
Genera icono.ico con las chairas cruzadas del logo del local.
Sin dependencias: rasteriza a mano y arma el PNG con zlib.

    python hacer_icono.py
"""
import math, os, struct, zlib

PAPEL = (255, 255, 255)
VERDE = (22, 121, 59)
ROJO = (180, 20, 31)
ACERO = (108, 103, 98)
BORDE = (27, 21, 20)
TAMANOS = [256, 128, 64, 48, 32, 16]
SUPER = 4  # muestreo para que los bordes no queden dentados


def en_rect(x, y, cx, cy, ang, mitad_ancho, y0, y1):
    """El punto cae dentro de un rectangulo girado ang grados?"""
    c, s = math.cos(-ang), math.sin(-ang)
    dx, dy = x - cx, y - cy
    lx, ly = dx * c - dy * s, dx * s + dy * c
    return -mitad_ancho <= lx <= mitad_ancho and y0 <= ly <= y1


def color_en(x, y, n):
    """Color del punto (x,y) en un lienzo de n x n, o None si es transparente."""
    r = n / 2.0
    dx, dy = x - r, y - r
    dist = math.hypot(dx, dy)
    if dist > r:
        return None

    for signo in (1, -1):
        ang = math.radians(36 * signo)
        # hoja
        if en_rect(x, y, r, r, ang, 0.135 * n, -0.43 * n, -0.08 * n):
            return ACERO
        # mango
        if en_rect(x, y, r, r, ang, 0.05 * n, -0.08 * n, 0.40 * n):
            return ROJO
    if dist > r * 0.86:
        return VERDE
    return PAPEL


def rasterizar(n):
    g = n * SUPER
    filas = []
    for y in range(n):
        fila = bytearray()
        for x in range(n):
            sr = sg = sb = sa = 0
            for oy in range(SUPER):
                for ox in range(SUPER):
                    c = color_en((x * SUPER + ox + 0.5) / SUPER,
                                 (y * SUPER + oy + 0.5) / SUPER, n)
                    if c is None:
                        continue
                    sr += c[0]; sg += c[1]; sb += c[2]; sa += 255
            t = SUPER * SUPER
            if sa == 0:
                fila += b"\x00\x00\x00\x00"
            else:
                op = sa // t
                fila += bytes((sr * 255 // sa, sg * 255 // sa, sb * 255 // sa, op))
        filas.append(bytes(fila))
    return filas


def png(n, filas):
    cruda = b"".join(b"\x00" + f for f in filas)
    def trozo(tipo, datos):
        return (struct.pack(">I", len(datos)) + tipo + datos +
                struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF))
    return (b"\x89PNG\r\n\x1a\n"
            + trozo(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0))
            + trozo(b"IDAT", zlib.compress(cruda, 9))
            + trozo(b"IEND", b""))


def escribir_modulo(png_grande, png_chico):
    """
    Deja la marca como texto base64 dentro de un modulo, para que la ventana
    la pueda mostrar sin depender de un archivo suelto al lado del .exe.
    """
    import base64
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "imagen_marca.py")
    with open(os.path.normpath(destino), "w") as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write('"""Las chairas cruzadas del logo. Generado por '
                'empaquetado/hacer_icono.py; no editar a mano."""\n\n')
        f.write("CABECERA = \"\"\"%s\"\"\"\n\n"
                % base64.b64encode(png_chico).decode())
        f.write("GRANDE = \"\"\"%s\"\"\"\n"
                % base64.b64encode(png_grande).decode())
    print("imagen_marca.py generado")


def main():
    imagenes = []
    for n in TAMANOS:
        imagenes.append((n, png(n, rasterizar(n))))
        print("  %dx%d listo" % (n, n))

    cab = struct.pack("<HHH", 0, 1, len(imagenes))
    desplazamiento = 6 + 16 * len(imagenes)
    entradas, cuerpos = b"", b""
    for n, datos in imagenes:
        entradas += struct.pack("<BBBBHHII", n if n < 256 else 0, n if n < 256 else 0,
                                0, 0, 1, 32, len(datos), desplazamiento)
        cuerpos += datos
        desplazamiento += len(datos)

    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono.ico")
    with open(destino, "wb") as f:
        f.write(cab + entradas + cuerpos)
    print("icono.ico: %d bytes" % os.path.getsize(destino))
    # PNG grande aparte, para la documentacion
    with open(os.path.join(os.path.dirname(destino), "icono.png"), "wb") as f:
        f.write(imagenes[0][1])
    # y la marca para la cabecera de la ventana
    chico = png(64, rasterizar(64))
    escribir_modulo(imagenes[0][1], chico)


if __name__ == "__main__":
    main()
