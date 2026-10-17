# -*- coding: utf-8 -*-
"""
Lo que exige la Resolucion Exenta N°38 de 2024 de la Direccion del Trabajo.

Aca viven las piezas que la norma pide de forma literal y que se pueden
escribir y probar solas: el RUT, el sello de integridad de cada marcacion y
el comprobante que se le manda al trabajador.

Cada funcion dice a que articulo responde. Eso no es adorno: cuando la
empresa certificadora revise el sistema (art. 64 y 65) va a pedir exactamente
esa correspondencia, articulo por articulo.

El detalle de que falta esta en CUMPLIMIENTO-DT.md, en la raiz del proyecto.
"""

import hashlib
import re
from datetime import datetime

# Version del formato del sello. Si algun dia cambia como se arma la cadena
# que se firma, sube este numero: los comprobantes viejos se siguen
# verificando con su propia version y no se invalidan solos.
SELLO = "CH1"


# ---------------------------------------------------------------- el RUT
def limpiar_rut(texto):
    """Deja solo numeros y el digito verificador, en mayuscula."""
    return re.sub(r"[^0-9kK]", "", texto or "").upper()


def digito_verificador(cuerpo):
    """Modulo 11, el calculo de toda la vida."""
    suma, factor = 0, 2
    for c in reversed(str(cuerpo)):
        suma += int(c) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    return {11: "0", 10: "K"}.get(resto, str(resto))


def rut_valido(texto):
    limpio = limpiar_rut(texto)
    if len(limpio) < 2 or not limpio[:-1].isdigit():
        return False
    return digito_verificador(limpio[:-1]) == limpio[-1]


def formatear_rut(texto):
    """
    Devuelve el RUT con puntos, guion y digito verificador.

    La resolucion lo pide escrito asi, tal cual, en el comprobante
    (art. 13.1 letra d y 13.2 letra b): 12.345.678-5
    """
    limpio = limpiar_rut(texto)
    if not limpio:
        return ""
    if not rut_valido(limpio):
        raise ValueError(
            "El RUT '%s' no es valido: el digito verificador no cuadra. "
            "Revisa que este bien copiado." % texto)
    cuerpo, dv = limpio[:-1], limpio[-1]
    partes = []
    while len(cuerpo) > 3:
        partes.insert(0, cuerpo[-3:])
        cuerpo = cuerpo[:-3]
    partes.insert(0, cuerpo)
    return "%s-%s" % (".".join(partes), dv)


# ------------------------------------------- sello de cada marcacion (art. 8)
def cadena_sello(rut_trabajador, fecha, tipo, hora, rut_empleador, registrado_en):
    """
    La cadena exacta que se firma. Tiene que poder rehacerse igual years
    despues para que el verificador en linea de el mismo resultado.
    """
    return "|".join([SELLO, limpiar_rut(rut_trabajador), fecha, tipo, hora,
                     limpiar_rut(rut_empleador), registrado_en])


def sello_marcacion(rut_trabajador, fecha, tipo, hora, rut_empleador,
                    registrado_en):
    """
    SHA-256 de la marcacion (art. 8).

    La norma pide una funcion hash nativa del lenguaje o del motor de datos,
    del tipo SHA-2, y prohibe expresamente los codigos armados a mano
    concatenando atributos sin aplicar esas funciones. Esto es hashlib, que
    es la de Python.
    """
    cadena = cadena_sello(rut_trabajador, fecha, tipo, hora, rut_empleador,
                          registrado_en)
    return hashlib.sha256(cadena.encode("utf-8")).hexdigest()


def sello_corto(sello):
    """Los primeros 16 caracteres, para leerlos por telefono sin enloquecer."""
    return (sello or "")[:16].upper()


# ------------------------------------------- comprobante de marcacion (art. 13)
def _dd_mm_aa(iso):
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%y")


def comprobante(marca, trabajador, empleador, etiqueta):
    """
    El texto del comprobante, con el contenido minimo del articulo 13.

    `marca` trae fecha (ISO), hora (hh:mm:ss), tipo y sello.
    `trabajador` trae nombre y rut.
    `empleador` trae razon_social, rut y las partes de la direccion del lugar
    donde se presta el servicio, que es lo que pide el art. 13.3: el lugar
    efectivo, no la casa matriz.

    Devuelve (asunto, cuerpo). El cuerpo va en texto plano a proposito: el
    art. 12 letra c exige que el comprobante sea imprimible.
    """
    faltan = [c for c in ("razon_social", "rut") if not (empleador.get(c) or "").strip()]
    if faltan:
        raise ValueError(
            "Para emitir el comprobante faltan datos del empleador: %s. "
            "Se llenan en Configuracion." % ", ".join(faltan))
    if not (trabajador.get("rut") or "").strip():
        raise ValueError(
            "%s no tiene RUT registrado, y el comprobante lo exige. "
            "Se agrega en la pestana Trabajadores." % trabajador.get("nombre", ""))

    asunto = "Comprobante de marcacion %s %s - %s" % (
        _dd_mm_aa(marca["fecha"]), marca["hora"], empleador["razon_social"])
    l = [
        "COMPROBANTE DE MARCACION",
        "Registro y control de asistencia - articulo 33 del Codigo del Trabajo",
        "",
        "TRABAJADOR",
        "   Nombre            : %s" % trabajador["nombre"],
        "   RUT               : %s" % formatear_rut(trabajador["rut"]),
        "",
        "MARCACION",
        "   Tipo              : %s" % etiqueta,
        "   Fecha             : %s" % _dd_mm_aa(marca["fecha"]),
        "   Hora              : %s" % marca["hora"],
        "",
        "EMPLEADOR",
        "   Razon social      : %s" % empleador["razon_social"],
        "   RUT               : %s" % formatear_rut(empleador["rut"]),
        "   Lugar de trabajo  : %s" % direccion_en_una_linea(empleador),
    ]
    if (empleador.get("resolucion_excepcional") or "").strip():
        l.append("   Jornada excepcional: resolucion %s"
                 % empleador["resolucion_excepcional"])
    l += [
        "",
        "SELLO DE INTEGRIDAD (SHA-256)",
        "   %s" % marca["sello"],
        "",
        "Este codigo permite comprobar que la marcacion no fue alterada",
        "despues de registrarse.",
        "",
        "--",
        "Comprobante generado automaticamente. No respondas este correo.",
        "Guardalo: es tu constancia de la marcacion.",
    ]
    return asunto, "\n".join(l)


def direccion_en_una_linea(empleador):
    """Calle, numero, comuna, ciudad y region, como pide el art. 13.2 letra c."""
    partes = [empleador.get(c) or "" for c in
              ("calle", "numero", "comuna", "ciudad", "region")]
    calle = " ".join(p for p in partes[:2] if p.strip())
    resto = [p.strip() for p in partes[2:] if p.strip()]
    todo = [p for p in ([calle] + resto) if p]
    return ", ".join(todo) if todo else "(sin direccion registrada)"


def faltan_datos_para_la_dt(cfg, trabajadores):
    """
    Que falta para que los comprobantes cumplan el articulo 13.

    Devuelve una lista de frases listas para mostrar. Sirve para avisar en
    pantalla antes de que el problema aparezca en una fiscalizacion.
    """
    faltas = []
    if not (cfg.get("razon_social") or "").strip():
        faltas.append("la razon social del empleador")
    if not (cfg.get("rut_empleador") or "").strip():
        faltas.append("el RUT del empleador")
    if not (cfg.get("comuna") or "").strip():
        faltas.append("la direccion del local (calle, numero y comuna)")
    sin_rut = [t["nombre"] for t in trabajadores if not (t.get("rut") or "").strip()]
    if sin_rut:
        faltas.append("el RUT de: " + ", ".join(sin_rut))
    sin_correo = [t["nombre"] for t in trabajadores
                  if not (t.get("correo") or "").strip()]
    if sin_correo:
        faltas.append("el correo de: " + ", ".join(sin_correo))
    return faltas
