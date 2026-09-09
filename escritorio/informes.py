# -*- coding: utf-8 -*-
"""
Informes mensuales para imprimir: Excel (.xlsx) y PDF.

Los dos muestran lo mismo: turnos trabajados, horas, colacion descontada,
horas extra y cuanto se paga.
"""

from nucleo import pesos, horas_txt, hhmm_txt, _limpio

ROJO = "B4141F"
VERDE = "16793B"
TINTA = "15100F"
GRIS = "EDE9E4"


def _pie(r):
    return [
        "Cada dia se arma con cuatro marcas: entrada, inicio y fin de colacion, "
        "y salida. Horas trabajadas = salida - entrada - colacion. Los turnos "
        "que cruzan la medianoche se calculan completos.",
        "Horas extra: todo lo que se pasa de la jornada del contrato (%s h) EN EL "
        "DIA. El valor del dia = horas normales x valor hora + horas extra x valor "
        "hora extra." % r.get("contrato", r.get("umbral_diario", "7")),
        "El total del periodo es la suma de los valores de cada dia, asi que "
        "siempre cuadra con el detalle.",
        "Valor de la hora extra: %s." % r["regla_extra"],
        "Documento de control interno. Confirme los montos con su contador "
        "antes de usarlos para liquidaciones.",
        "Generado con Control de Horas, desarrollado por Macoem.",
    ]


COLUMNAS = [
    ("Trabajador", 26), ("Turnos", 9), ("Horas trabajadas", 17),
    ("Colacion (h)", 13), ("Horas ordinarias", 17), ("Horas extra", 13),
    ("Valor hora", 13), ("Valor hora extra", 17),
    ("Pago ordinario", 16), ("Pago extra", 14), ("TOTAL", 16),
]


# --------------------------------------------------------------------- Excel
def a_excel(r, ruta):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    borde = Border(*[Side(style="thin", color="D5CFC9")] * 4)
    titulo = Font(name="Calibri", size=16, bold=True, color=ROJO)
    sub = Font(name="Calibri", size=10, color="6C625C")
    cab = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    relleno = PatternFill("solid", fgColor=TINTA)
    negrita = Font(name="Calibri", size=11, bold=True)

    # ---------------- Resumen ----------------
    h = wb.active
    h.title = "Resumen"
    h["A1"] = r["negocio"]; h["A1"].font = titulo
    h["A2"] = "%s  |  Control de horas trabajadas" % r["ciudad"]; h["A2"].font = sub
    h["A3"] = r["titulo"]
    h["A3"].font = Font(name="Calibri", size=13, bold=True, color=TINTA)
    if r.get("subtitulo"):
        h["A4"] = r["subtitulo"]
        h["A4"].font = Font(name="Calibri", size=11, bold=True, color=ROJO)

    fila = 6
    for i, (nombre, ancho) in enumerate(COLUMNAS, start=1):
        c = h.cell(row=fila, column=i, value=nombre)
        c.font = cab; c.fill = relleno; c.border = borde
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        h.column_dimensions[get_column_letter(i)].width = ancho
    h.row_dimensions[fila].height = 30

    for f in r["filas"]:
        fila += 1
        valores = [f["nombre"], f["turnos"], f["horas"], f["colacion"],
                   f["ordinarias"], f["extra"], f["valor_hora"], f["valor_extra"],
                   f["pago_ordinario"], f["pago_extra"], f["total"]]
        for i, v in enumerate(valores, start=1):
            c = h.cell(row=fila, column=i, value=v)
            c.border = borde
            if i == 1:
                c.alignment = Alignment(horizontal="left")
            elif i == 2:
                c.number_format = "0"
            elif i in (3, 4, 5, 6):
                c.number_format = "0.00"
            else:
                c.number_format = '"$"#,##0'
            if i == 6 and f["extra"] > 0:
                c.font = Font(name="Calibri", bold=True, color=ROJO)
            if i == 11:
                c.font = negrita

    fila += 1
    t = r["totales"]
    valores = ["TOTAL", t["turnos"], t["horas"], t["colacion"], t["ordinarias"],
               t["extra"], None, None, t["pago_ordinario"], t["pago_extra"], t["total"]]
    for i, v in enumerate(valores, start=1):
        c = h.cell(row=fila, column=i, value=v)
        c.font = cab; c.fill = relleno; c.border = borde
        if i == 2:
            c.number_format = "0"
        elif i in (3, 4, 5, 6):
            c.number_format = "0.00"
        elif i >= 9:
            c.number_format = '"$"#,##0'

    fila += 2
    for linea in _pie(r):
        h.cell(row=fila, column=1, value=linea).font = sub
        fila += 1

    h.freeze_panes = "A7"
    h.page_setup.orientation = "landscape"
    h.page_setup.fitToWidth = 1
    h.sheet_properties.pageSetUpPr.fitToPage = True
    h.print_title_rows = "6:6"

    # ---------------- Detalle ----------------
    d = wb.create_sheet("Detalle")
    d["A1"] = "Detalle de turnos  -  %s" % r["titulo"]
    d["A1"].font = Font(name="Calibri", size=13, bold=True, color=TINTA)
    encabezados = [("Fecha", 12), ("Dia", 11), ("Trabajador", 20), ("Entrada", 9),
                   ("Col. inicio", 11), ("Col. fin", 10), ("Salida", 9),
                   ("Horas", 9), ("Normales", 10), ("Extra", 9),
                   ("$ normales", 13), ("$ extra", 12), ("VALOR DEL DIA", 15),
                   ("Estado", 20)]
    fila = 3
    for i, (nombre, ancho) in enumerate(encabezados, start=1):
        c = d.cell(row=fila, column=i, value=nombre)
        c.font = cab; c.fill = relleno; c.border = borde
        c.alignment = Alignment(horizontal="center")
        d.column_dimensions[get_column_letter(i)].width = ancho

    for f in r["filas"]:
        for j in f["detalle"]:
            fila += 1
            valores = [j["fecha"], j["dia"], f["nombre"], j.get("entrada", ""),
                       j.get("colacion_inicio", ""), j.get("colacion_fin", ""),
                       j.get("salida", ""), j["horas"], j.get("normales", 0),
                       j.get("extra", 0), j.get("pago_normal", 0),
                       j.get("pago_extra", 0), j.get("total", 0),
                       "completa" if j.get("completa", True)
                       else "falta " + ", ".join(x.lower() for x in j.get("faltan", []))]
            for i, v in enumerate(valores, start=1):
                c = d.cell(row=fila, column=i, value=v)
                c.border = borde
                if i in (8, 9, 10):
                    c.number_format = "0.00"
                if i in (11, 12, 13):
                    c.number_format = '"$"#,##0'
                if i == 13:
                    c.font = Font(name="Calibri", bold=True)
                if i == 10 and (j.get("extra") or 0) > 0:
                    c.font = Font(name="Calibri", bold=True, color=ROJO)
                if i == 14 and v != "completa":
                    c.font = Font(name="Calibri", bold=True, color="8A5A00")

    d.freeze_panes = "A4"
    d.page_setup.fitToWidth = 1
    d.sheet_properties.pageSetUpPr.fitToPage = True
    d.print_title_rows = "3:3"

    wb.save(ruta)
    return ruta


# ----------------------------------------------------------------------- PDF
def a_pdf(r, ruta):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer)

    rojo = colors.HexColor("#" + ROJO)
    tinta = colors.HexColor("#" + TINTA)
    gris = colors.HexColor("#" + GRIS)
    suave = colors.HexColor("#6C625C")

    est = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=est["Title"], fontSize=18, textColor=rojo,
                        alignment=0, spaceAfter=1)
    h2 = ParagraphStyle("h2", parent=est["Normal"], fontSize=9, textColor=suave,
                        spaceAfter=8)
    h3 = ParagraphStyle("h3", parent=est["Normal"], fontSize=13, textColor=tinta,
                        spaceAfter=10, fontName="Helvetica-Bold")
    sec = ParagraphStyle("sec", parent=est["Normal"], fontSize=11, textColor=tinta,
                         spaceBefore=14, spaceAfter=5, fontName="Helvetica-Bold")
    nota = ParagraphStyle("nota", parent=est["Normal"], fontSize=7.2,
                          textColor=suave, leading=10)

    doc = SimpleDocTemplate(ruta, pagesize=landscape(A4),
                            leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=13 * mm, bottomMargin=13 * mm,
                            title="Control de horas - " + r["titulo"])
    hist = [Paragraph(r["negocio"], h1),
            Paragraph("%s &nbsp;|&nbsp; Control de horas trabajadas" % r["ciudad"], h2),
            Paragraph(r["titulo"], h3)]
    if r.get("subtitulo"):
        hist.append(Paragraph(
            r["subtitulo"].upper(),
            ParagraphStyle("pago", parent=est["Normal"], fontSize=10.5,
                           textColor=rojo, fontName="Helvetica-Bold",
                           spaceAfter=10)))

    datos = [["Trabajador", "Turnos", "Horas\ntrabaj.", "Colacion\n(h)",
              "Horas\nordinarias", "Horas\nextra", "Valor\nhora",
              "Valor hora\nextra", "Pago\nordinario", "Pago\nextra", "TOTAL"]]
    for f in r["filas"]:
        datos.append([f["nombre"], str(f["turnos"]), horas_txt(f["horas"]),
                      horas_txt(f["colacion"]), horas_txt(f["ordinarias"]),
                      horas_txt(f["extra"]), pesos(f["valor_hora"]),
                      pesos(f["valor_extra"]), pesos(f["pago_ordinario"]),
                      pesos(f["pago_extra"]), pesos(f["total"])])
    t = r["totales"]
    datos.append(["TOTAL", str(t["turnos"]), horas_txt(t["horas"]),
                  horas_txt(t["colacion"]), horas_txt(t["ordinarias"]),
                  horas_txt(t["extra"]), "", "", pesos(t["pago_ordinario"]),
                  pesos(t["pago_extra"]), pesos(t["total"])])

    anchos = [46, 15, 20, 19, 24, 19, 22, 25, 27, 24, 29]
    tabla = Table(datos, colWidths=[a * mm for a in anchos], repeatRows=1)
    tabla.hAlign = "LEFT"
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), tinta),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.6),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5CFC9")),
        ("BACKGROUND", (0, -1), (-1, -1), tinta),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i, f in enumerate(r["filas"], start=1):
        if i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), gris))
        if f["extra"] > 0:
            estilo.append(("TEXTCOLOR", (5, i), (5, i), rojo))
            estilo.append(("FONTNAME", (5, i), (5, i), "Helvetica-Bold"))
        estilo.append(("FONTNAME", (10, i), (10, i), "Helvetica-Bold"))
    tabla.setStyle(TableStyle(estilo))
    hist.append(tabla)

    for f in r["filas"]:
        hist.append(Paragraph("%s &nbsp;&mdash;&nbsp; %d turnos, %s h, %s"
                              % (f["nombre"], f["turnos"], horas_txt(f["horas"]),
                                 pesos(f["total"])), sec))
        det = [["Fecha", "Dia", "Entrada", "Col. inicio", "Col. fin", "Salida",
                "Horas", "Normal", "Extra", "$ normal", "$ extra", "VALOR DIA"]]
        for j in f["detalle"]:
            det.append([j["fecha"], j["dia"], j.get("entrada", "-"),
                        j.get("colacion_inicio", "-") or "-",
                        j.get("colacion_fin", "-") or "-", j.get("salida", "-"),
                        horas_txt(j["horas"]), horas_txt(j.get("normales", 0)),
                        horas_txt(j.get("extra", 0)) if j.get("extra") else "-",
                        pesos(j.get("pago_normal", 0)),
                        pesos(j.get("pago_extra", 0)) if j.get("pago_extra") else "-",
                        pesos(j.get("total", 0))])
        td = Table(det, colWidths=[24 * mm, 20 * mm, 19 * mm, 21 * mm, 19 * mm,
                                   18 * mm, 16 * mm, 17 * mm, 15 * mm, 23 * mm,
                                   21 * mm, 26 * mm], repeatRows=1)
        td.hAlign = "LEFT"
        td.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), gris),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.4),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D5CFC9")),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("FONTNAME", (11, 1), (11, -1), "Helvetica-Bold"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        hist.append(td)

    hist.append(Spacer(1, 10 * mm))
    for linea in _pie(r):
        hist.append(Paragraph("&bull; " + linea, nota))

    doc.build(hist)
    return ruta
