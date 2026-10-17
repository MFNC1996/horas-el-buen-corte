# -*- coding: utf-8 -*-
"""
Pruebas de lo que exige la Resolucion Exenta N°38 de la Direccion del Trabajo.

Cada bloque cita el articulo que esta comprobando, para que sirva de evidencia
cuando la empresa certificadora pida la correspondencia articulo por articulo.

    python probar_cumplimiento.py
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cumplimiento as C

fallas = []


def check(que, ok):
    print(("  ok   " if ok else "FALLA ") + que)
    if not ok:
        fallas.append(que)


print("--- RUT del trabajador y del empleador (art. 13.1 d, 13.2 b) ---")
# Comprobado a mano con el modulo 11: 8*2+7*3+6*4+5*5+4*6+3*7+2*2+1*3 = 138,
# 138 % 11 = 6, 11-6 = 5.
check("calcula el digito verificador", C.digito_verificador("12345678") == "5")
check("y el de un organismo publico conocido",
      C.digito_verificador("60503000") == "9")
check("y cuando toca K", C.digito_verificador("10000013") == "K")
check("y cuando toca 0", C.digito_verificador("10000004") == "0")
check("y cuando toca 1", C.digito_verificador("11111111") == "1")
for bueno in ("12.345.678-5", "123456785", "12345678-5", "12 345 678 5"):
    check("acepta '%s'" % bueno, C.rut_valido(bueno))
for malo in ("12.345.678-9", "123456789", "", "abc", "1", "12345678-K"):
    check("rechaza '%s'" % malo, not C.rut_valido(malo))

check("lo formatea con puntos y guion",
      C.formatear_rut("123456785") == "12.345.678-5")
check("respeta el K en mayuscula",
      C.formatear_rut("10000013k") == "10.000.013-K")
check("un RUT corto tambien",
      C.formatear_rut("512666" + C.digito_verificador("512666")) == "512.666-" + C.digito_verificador("512666"))
check("vacio queda vacio", C.formatear_rut("") == "")
try:
    C.formatear_rut("12.345.678-9")
    check("un RUT malo no se formatea, avisa", False)
except ValueError as e:
    check("un RUT malo no se formatea, avisa", "no es valido" in str(e))

print("\n--- sello de integridad de la marcacion (art. 8) ---")
datos = dict(rut_trabajador="12345678-5", fecha="2026-10-17", tipo="entrada",
             hora="08:30:12", rut_empleador="76543210-3",
             registrado_en="2026-10-17 08:30:12")
sello = C.sello_marcacion(**datos)
check("es un SHA-256: 64 caracteres hexadecimales",
      len(sello) == 64 and all(c in "0123456789abcdef" for c in sello))
check("la misma marcacion da el mismo sello",
      C.sello_marcacion(**datos) == sello)
for campo, otro in (("hora", "08:30:13"), ("fecha", "2026-10-18"),
                    ("tipo", "salida"), ("rut_trabajador", "11111111-1"),
                    ("rut_empleador", "11111111-1")):
    cambiada = dict(datos, **{campo: otro})
    check("cambiar %s cambia el sello" % campo,
          C.sello_marcacion(**cambiada) != sello)
check("el RUT con o sin puntos da el mismo sello",
      C.sello_marcacion(**dict(datos, rut_trabajador="12.345.678-5")) == sello)
check("el sello corto se puede dictar por telefono",
      len(C.sello_corto(sello)) == 16 and C.sello_corto(sello).isupper())
check("la cadena firmada lleva version, para no invalidar los viejos",
      C.cadena_sello(**datos).startswith(C.SELLO + "|"))

print("\n--- comprobante de marcacion (art. 12 y 13) ---")
empleador = {"razon_social": "Comercial El Buen Corte SpA",
             "rut": "76.543.210-3", "calle": "Avenida Bernardo O'Higgins",
             "numero": "1234", "comuna": "Loncoche", "ciudad": "Loncoche",
             "region": "Region de La Araucania"}
trabajador = {"nombre": "Ana Soto Perez", "rut": "12345678-5",
              "correo": "ana@gmail.com"}
marca = {"fecha": "2026-10-17", "hora": "08:30:12", "tipo": "entrada",
         "sello": sello}
asunto, cuerpo = C.comprobante(marca, trabajador, empleador, "Entrada")

check("el asunto lleva la fecha y la hora", "17/10/26" in asunto and "08:30:12" in asunto)
check("y el nombre del empleador", "El Buen Corte" in asunto)
check("13.1 a) la fecha va en formato dd/mm/aa", "17/10/26" in cuerpo)
check("13.1 b) la hora va con segundos", "08:30:12" in cuerpo)
check("13.1 c) el nombre completo del trabajador", "Ana Soto Perez" in cuerpo)
check("13.1 d) el RUT con puntos, guion y digito", "12.345.678-5" in cuerpo)
check("13.1 g) el codigo hash generado", sello in cuerpo)
check("13.2 a) la razon social del empleador",
      "Comercial El Buen Corte SpA" in cuerpo)
check("13.2 b) el RUT del empleador con puntos y guion", "76.543.210-3" in cuerpo)
check("13.2 c) la direccion del lugar donde se marca",
      all(p in cuerpo for p in ("Avenida Bernardo O'Higgins", "1234",
                                "Loncoche", "Region de La Araucania")))
check("dice que tipo de marca fue", "Entrada" in cuerpo)
check("12 c) es texto plano, imprimible", "<" not in cuerpo and ">" not in cuerpo)

con_excepcional = dict(empleador, resolucion_excepcional="N°1234 de 01/03/2026")
check("13.1 e) si hay jornada excepcional, va la resolucion",
      "N°1234" in C.comprobante(marca, trabajador, con_excepcional, "Entrada")[1])
check("y si no hay, no aparece la linea",
      "excepcional" not in cuerpo.lower())

print("\n--- sin los datos obligatorios no se emite (art. 13) ---")
for falta in ("razon_social", "rut"):
    try:
        C.comprobante(marca, trabajador, dict(empleador, **{falta: ""}), "Entrada")
        check("sin %s del empleador no deja emitir" % falta, False)
    except ValueError as e:
        check("sin %s del empleador no deja emitir" % falta, "falta" in str(e).lower())
try:
    C.comprobante(marca, dict(trabajador, rut=""), empleador, "Entrada")
    check("sin RUT del trabajador no deja emitir", False)
except ValueError as e:
    check("sin RUT del trabajador no deja emitir", "RUT" in str(e))

print("\n--- aviso de lo que falta para cumplir ---")
cfg_vacia = {}
faltas = C.faltan_datos_para_la_dt(
    cfg_vacia, [{"nombre": "Ana", "rut": "", "correo": ""}])
check("avisa que falta la razon social",
      any("razon social" in f for f in faltas))
check("avisa que falta el RUT del empleador",
      any("RUT del empleador" in f for f in faltas))
check("avisa que falta la direccion", any("direccion" in f for f in faltas))
check("nombra a quien le falta el RUT", any("RUT de: Ana" in f for f in faltas))
check("y a quien le falta el correo", any("correo de: Ana" in f for f in faltas))
cfg_ok = {"razon_social": "X SpA", "rut_empleador": "76543210-3",
          "comuna": "Loncoche"}
check("con todo lleno no reclama nada",
      C.faltan_datos_para_la_dt(
          cfg_ok, [{"nombre": "Ana", "rut": "12345678-5",
                    "correo": "a@b.cl"}]) == [])

print("\n--- la direccion en una linea (art. 13.2 c) ---")
check("arma calle, numero, comuna, ciudad y region",
      C.direccion_en_una_linea(empleador)
      == "Avenida Bernardo O'Higgins 1234, Loncoche, Loncoche, Region de La Araucania")
check("si falta todo, lo dice en vez de quedar en blanco",
      "sin direccion" in C.direccion_en_una_linea({}))

print("")
if fallas:
    print("%d FALLAS: %s" % (len(fallas), fallas))
    sys.exit(1)
print("TODO OK")
