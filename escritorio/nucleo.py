# -*- coding: utf-8 -*-
"""
Nucleo del control de horas: datos y calculos.

No depende de la interfaz, asi que se puede probar solo. La ventana
(app.py) solo llama a estas funciones.
"""

import os
import sqlite3
import sys
from datetime import date, datetime, timedelta

NEGOCIO_DEF = "Carniceria El Buen Corte"
CIUDAD_DEF = "Loncoche"
# La casilla desde la que salen los avisos. Se deja escrita para no tener que
# acordarse en cada instalacion. La CONTRASENA no se guarda aqui ni en ninguna
# parte del codigo: se escribe una sola vez en Configuracion, en el PC del
# local, y queda en horas.sqlite3, que es un archivo del computador y no viaja
# con el programa. Este repositorio es publico.
CORREO_DEF = "marcacion.elbuencorte@gmail.com"

CONFIG_DEF = {
    # Jornada del contrato. Lo que se pasa de aqui EN EL DIA es hora extra.
    "horas_contrato": "7",
    "umbral_semanal": "45",     # solo como aviso: la ley semanal
    "umbral_diario": "7",       # se mantiene por compatibilidad con bases viejas
    "regla": "diaria",          # el pago sale del excedente DIARIO sobre el contrato
    "modo_extra": "recargo",    # recargo (% sobre la hora normal) | fijo (monto en pesos)
    "recargo_extra": "50",      # % sobre el valor hora, si modo_extra=recargo
    "valor_extra_global": "0",  # $ por hora extra, si modo_extra=fijo
    "negocio": NEGOCIO_DEF,
    "ciudad": CIUDAD_DEF,
    # Aviso por correo al trabajador cada vez que marca. Apagado mientras no
    # se llene la cuenta que envia. La clave se guarda aqui, en el PC: por eso
    # en pantalla se pide una CONTRASENA DE APLICACION y no la de la cuenta.
    "correo_activo": "0",
    "correo_servidor": "smtp.gmail.com",
    "correo_puerto": "587",
    "correo_usuario": CORREO_DEF,   # la casilla desde la que sale el aviso
    "correo_clave": "",         # contrasena de aplicacion de esa casilla
}

# Cuantas veces se reintenta un correo antes de darlo por perdido. Con un
# reintento por minuto, ocho son mas de un rato sin internet.
INTENTOS_CORREO = 8

# Las cuatro marcas del dia, SIEMPRE en este orden.
TIPOS = ["entrada", "colacion_inicio", "colacion_fin", "salida"]
ETIQUETAS = {
    "entrada":         "Entrada",
    "colacion_inicio": "Inicio de colacion",
    "colacion_fin":    "Fin de colacion",
    "salida":          "Salida",
}
# Si alguien marco entrada y se fue sin marcar salida, a las tantas horas
# dejamos de considerar esa jornada abierta y la siguiente marca empieza una nueva.
HORAS_JORNADA_ABIERTA = 20

# Un dia se paga en dos partes, que se pueden pagar por separado.
CONCEPTOS = ("normal", "extra")
NOMBRE_CONCEPTO = {"normal": "horas normales", "extra": "horas extra"}

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


# ----------------------------------------------------------------- ubicacion
def carpeta_datos():
    """Los datos viven fuera del .exe, para que actualizarlo no los borre."""
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    ruta = os.path.join(base, "ControlDeHoras")
    os.makedirs(ruta, exist_ok=True)
    return ruta


# ------------------------------------------------------------------ calculos
def a_minutos(hhmm):
    """'08:30' -> 510. Devuelve None si no se entiende."""
    try:
        h, m = str(hhmm).strip().split(":")
        h, m = int(h), int(m)
    except (ValueError, AttributeError):
        return None
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return None
    return h * 60 + m


def a_hhmm(minutos):
    minutos = int(minutos) % 1440
    return "%02d:%02d" % (minutos // 60, minutos % 60)


def normalizar_hora(texto):
    """
    Entiende la hora escrita como venga y la deja en HH:MM.

        830   -> 08:30      8      -> 08:00
        1930  -> 19:30      19     -> 19:00
        8:30  -> 08:30      8.30   -> 08:30

    Devuelve None si de verdad no se entiende.
    """
    t = str(texto or "").strip().replace(".", ":").replace(" ", ":")
    if not t:
        return None
    if ":" in t:
        partes = [x for x in t.split(":") if x != ""]
        if len(partes) == 1 and partes[0].isdigit():
            h, m = int(partes[0]), 0
        elif len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
            h, m = int(partes[0]), int(partes[1])
        else:
            return None
    else:
        d = "".join(c for c in t if c.isdigit())
        if not d or len(d) > 4:
            return None
        if len(d) <= 2:
            h, m = int(d), 0
        elif len(d) == 3:
            h, m = int(d[0]), int(d[1:])
        else:
            h, m = int(d[:2]), int(d[2:])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return None
    return "%02d:%02d" % (h, m)


def minutos_turno(entrada, salida):
    """Minutos entre entrada y salida. Si cruza medianoche, suma 24 h."""
    e, s = a_minutos(entrada), a_minutos(salida)
    if e is None or s is None:
        return 0
    d = s - e
    if d < 0:
        d += 1440
    return d


def horas_trabajadas(entrada, salida, colacion_min):
    """Horas efectivas, con la colacion ya descontada. Nunca negativas."""
    d = minutos_turno(entrada, salida) - int(colacion_min or 0)
    return round(max(0, d) / 60.0, 2)


def extra_del_dia(horas, umbral_diario):
    return round(max(0.0, horas - float(umbral_diario)), 2)


def horas_de_marcas(marcas):
    """
    Horas efectivas de un dia a partir de sus marcas.

    Necesita entrada y salida. Si estan las dos de colacion, se descuenta ese
    rato. Cada tramo se mide con el resto de 24 h, asi que un turno que cruza
    la medianoche (22:00 a 06:00) sale bien.
    """
    por_tipo = {}
    for m in marcas:
        por_tipo[m["tipo"]] = m["hora"]
    if "entrada" not in por_tipo or "salida" not in por_tipo:
        return 0.0
    bruto = minutos_turno(por_tipo["entrada"], por_tipo["salida"])
    colacion = 0
    if "colacion_inicio" in por_tipo and "colacion_fin" in por_tipo:
        colacion = minutos_turno(por_tipo["colacion_inicio"], por_tipo["colacion_fin"])
    return round(max(0, bruto - colacion) / 60.0, 2)


def minutos_colacion(marcas):
    """Minutos de colacion de un dia, 0 si no estan las dos marcas."""
    por_tipo = dict((m["tipo"], m["hora"]) for m in marcas)
    if "colacion_inicio" in por_tipo and "colacion_fin" in por_tipo:
        return minutos_turno(por_tipo["colacion_inicio"], por_tipo["colacion_fin"])
    return 0


def lunes_de(iso):
    d = datetime.strptime(iso, "%Y-%m-%d").date()
    return (d - timedelta(days=d.weekday())).isoformat()


def nombre_dia(iso):
    return DIAS[datetime.strptime(iso, "%Y-%m-%d").date().weekday()]


def nombre_mes(mes):
    return MESES[mes - 1]


def ultimo_dia(anio, mes):
    if mes == 12:
        return date(anio, 12, 31).day
    return (date(anio, mes + 1, 1) - timedelta(days=1)).day


def pesos(monto):
    """1234567 -> '$1.234.567'"""
    return "$" + "{:,.0f}".format(round(monto or 0)).replace(",", ".")


def horas_txt(h):
    """10.5 -> '10,50'"""
    return "{:.2f}".format(h or 0).replace(".", ",")


def hhmm_txt(h):
    """10.5 -> '10:30'"""
    total = int(round((h or 0) * 60))
    return "%d:%02d" % (total // 60, total % 60)


# --------------------------------------------------------------------- datos
class Datos(object):
    def __init__(self, ruta=None):
        self.ruta = ruta or os.path.join(carpeta_datos(), "horas.sqlite3")
        self.cx = sqlite3.connect(self.ruta)
        self.cx.row_factory = sqlite3.Row
        self.cx.execute("PRAGMA journal_mode=WAL")
        self.cx.execute("PRAGMA foreign_keys=ON")
        self._preparar()

    def _preparar(self):
        c = self.cx
        c.execute("""CREATE TABLE IF NOT EXISTS trabajadores (
                       id         INTEGER PRIMARY KEY AUTOINCREMENT,
                       nombre     TEXT    NOT NULL,
                       valor_hora REAL    NOT NULL DEFAULT 0,
                       valor_hora_extra REAL NOT NULL DEFAULT 0,
                       horas_contrato REAL NOT NULL DEFAULT 0,
                       activo     INTEGER NOT NULL DEFAULT 1,
                       orden      INTEGER NOT NULL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS jornadas (
                       id            INTEGER PRIMARY KEY AUTOINCREMENT,
                       trabajador_id INTEGER NOT NULL REFERENCES trabajadores(id),
                       fecha         TEXT    NOT NULL,
                       entrada       TEXT    NOT NULL,
                       salida        TEXT    NOT NULL,
                       colacion      INTEGER NOT NULL DEFAULT 0,
                       nota          TEXT    NOT NULL DEFAULT '')""")
        c.execute("CREATE INDEX IF NOT EXISTS ix_jornadas_fecha ON jornadas(fecha)")
        # Una fila por marca. Es el formato que tambien podria alimentar un
        # reloj biometrico mas adelante: basta con insertar aqui.
        c.execute("""CREATE TABLE IF NOT EXISTS marcas (
                       id            INTEGER PRIMARY KEY AUTOINCREMENT,
                       trabajador_id INTEGER NOT NULL REFERENCES trabajadores(id),
                       fecha         TEXT    NOT NULL,   -- dia laboral (el de la entrada)
                       tipo          TEXT    NOT NULL,   -- entrada|colacion_inicio|colacion_fin|salida
                       hora          TEXT    NOT NULL,   -- HH:MM, editable por el administrador
                       origen        TEXT    NOT NULL DEFAULT 'app',
                       registrado_en TEXT    NOT NULL DEFAULT '',
                       nota          TEXT    NOT NULL DEFAULT '')""")
        c.execute("CREATE INDEX IF NOT EXISTS ix_marcas ON marcas(trabajador_id, fecha)")
        # Un dia pagado: cuanto se pago y cuando. El monto queda fijo, para que
        # si despues cambia el valor hora, lo ya pagado no cambie de golpe.
        c.execute("""CREATE TABLE IF NOT EXISTS pagos (
                       trabajador_id INTEGER NOT NULL REFERENCES trabajadores(id),
                       fecha         TEXT    NOT NULL,
                       concepto      TEXT    NOT NULL,   -- normal | extra
                       monto         INTEGER NOT NULL,
                       pagado_en     TEXT    NOT NULL,
                       PRIMARY KEY (trabajador_id, fecha, concepto))""")
        # Migracion para bases creadas antes de que existiera el valor fijo.
        columnas = [f[1] for f in c.execute("PRAGMA table_info(trabajadores)")]
        if "valor_hora_extra" not in columnas:
            c.execute("ALTER TABLE trabajadores ADD COLUMN "
                      "valor_hora_extra REAL NOT NULL DEFAULT 0")
        if "horas_contrato" not in columnas:
            c.execute("ALTER TABLE trabajadores ADD COLUMN "
                      "horas_contrato REAL NOT NULL DEFAULT 0")
        if "correo" not in columnas:
            c.execute("ALTER TABLE trabajadores ADD COLUMN "
                      "correo TEXT NOT NULL DEFAULT ''")
        # Cola de avisos por correo. Se encola al marcar y se envia aparte,
        # asi una caida de internet no deja a nadie sin poder marcar.
        c.execute("""CREATE TABLE IF NOT EXISTS correos (
                       id            INTEGER PRIMARY KEY AUTOINCREMENT,
                       trabajador_id INTEGER NOT NULL REFERENCES trabajadores(id),
                       para          TEXT    NOT NULL,
                       asunto        TEXT    NOT NULL,
                       cuerpo        TEXT    NOT NULL,
                       creado_en     TEXT    NOT NULL,
                       intentos      INTEGER NOT NULL DEFAULT 0,
                       ultimo_error  TEXT    NOT NULL DEFAULT '',
                       enviado_en    TEXT    NOT NULL DEFAULT '')""")
        c.execute("CREATE INDEX IF NOT EXISTS ix_correos ON correos(enviado_en, intentos)")
        c.execute("""CREATE TABLE IF NOT EXISTS config (
                       clave TEXT PRIMARY KEY,
                       valor TEXT NOT NULL)""")
        for k, v in CONFIG_DEF.items():
            c.execute("INSERT OR IGNORE INTO config VALUES (?,?)", (k, v))
        c.execute("UPDATE config SET valor=? WHERE clave='correo_usuario' AND valor=''",
                  (CORREO_DEF,))
        c.commit()
        self.migrar_jornadas_a_marcas()
        self._migrar_pagos_en_dos_partes()

    def cerrar(self):
        self.cx.close()

    # -- configuracion --------------------------------------------------
    def config(self):
        cfg = dict(CONFIG_DEF)
        for f in self.cx.execute("SELECT clave, valor FROM config"):
            cfg[f["clave"]] = f["valor"]
        return cfg

    def guardar_config(self, cambios):
        for k, v in cambios.items():
            self.cx.execute("INSERT INTO config VALUES (?,?) "
                            "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
                            (k, str(v)))
        self.cx.commit()

    def num(self, clave):
        try:
            return float(self.config().get(clave, CONFIG_DEF.get(clave, 0)))
        except (TypeError, ValueError):
            return float(CONFIG_DEF.get(clave, 0))

    # -- trabajadores ---------------------------------------------------
    def trabajadores(self, solo_activos=True):
        sql = "SELECT * FROM trabajadores"
        if solo_activos:
            sql += " WHERE activo=1"
        sql += " ORDER BY orden, id"
        return [dict(f) for f in self.cx.execute(sql)]

    def trabajador(self, tid):
        f = self.cx.execute("SELECT * FROM trabajadores WHERE id=?", (tid,)).fetchone()
        return dict(f) if f else None

    def agregar_trabajador(self, nombre, valor_hora=0, valor_hora_extra=0,
                           horas_contrato=0, correo=""):
        nombre = (nombre or "").strip()
        if not nombre:
            raise ValueError("El nombre no puede estar vacio.")
        correo = limpiar_correo(correo)
        orden = self.cx.execute(
            "SELECT COALESCE(MAX(orden),0)+1 FROM trabajadores").fetchone()[0]
        cur = self.cx.execute(
            "INSERT INTO trabajadores (nombre, valor_hora, valor_hora_extra, "
            "horas_contrato, correo, orden) VALUES (?,?,?,?,?,?)",
            (nombre, float(valor_hora or 0), float(valor_hora_extra or 0),
             float(horas_contrato or 0), correo, orden))
        self.cx.commit()
        return cur.lastrowid

    def editar_trabajador(self, tid, nombre, valor_hora, valor_hora_extra=0,
                          horas_contrato=0, correo=""):
        nombre = (nombre or "").strip()
        if not nombre:
            raise ValueError("El nombre no puede estar vacio.")
        correo = limpiar_correo(correo)
        self.cx.execute("UPDATE trabajadores SET nombre=?, valor_hora=?, "
                        "valor_hora_extra=?, horas_contrato=?, correo=? WHERE id=?",
                        (nombre, float(valor_hora or 0), float(valor_hora_extra or 0),
                         float(horas_contrato or 0), correo, tid))
        self.cx.commit()

    def desactivar_trabajador(self, tid):
        """No se borra: sus jornadas historicas tienen que seguir cuadrando."""
        self.cx.execute("UPDATE trabajadores SET activo=0 WHERE id=?", (tid,))
        self.cx.commit()

    def jornadas_de(self, tid):
        return self.cx.execute(
            "SELECT COUNT(DISTINCT fecha) FROM marcas WHERE trabajador_id=?",
            (tid,)).fetchone()[0]

    # -- jornadas -------------------------------------------------------
    def guardar_jornada(self, jid, tid, fecha, entrada, salida, colacion, nota=""):
        datetime.strptime(fecha, "%Y-%m-%d")          # valida el formato
        if a_minutos(entrada) is None or a_minutos(salida) is None:
            raise ValueError("La hora de entrada o de salida no es valida.")
        if entrada == salida:
            raise ValueError("La entrada y la salida son la misma hora.")
        colacion = max(0, int(colacion or 0))
        if colacion >= minutos_turno(entrada, salida):
            raise ValueError("La colacion no puede durar mas que el turno.")
        if jid:
            self.cx.execute("""UPDATE jornadas SET trabajador_id=?, fecha=?, entrada=?,
                               salida=?, colacion=?, nota=? WHERE id=?""",
                            (tid, fecha, entrada, salida, colacion, nota or "", jid))
        else:
            self.cx.execute("""INSERT INTO jornadas
                               (trabajador_id, fecha, entrada, salida, colacion, nota)
                               VALUES (?,?,?,?,?,?)""",
                            (tid, fecha, entrada, salida, colacion, nota or ""))
        self.cx.commit()

    def borrar_jornada(self, jid):
        self.cx.execute("DELETE FROM jornadas WHERE id=?", (jid,))
        self.cx.commit()

    # ================================================================
    #  MARCAS
    #  Que le toca marcar a alguien se calcula SIEMPRE desde el historial
    #  del trabajador que se pasa por parametro. No hay estado global ni
    #  compartido, asi que dos personas marcando alternadamente no se
    #  pueden mezclar. Esto importa: de aqui sale el pago.
    # ================================================================

    def marcas_de(self, tid, fecha):
        """Las marcas de ese trabajador en ese dia laboral, en orden."""
        return [dict(f) for f in self.cx.execute(
            "SELECT * FROM marcas WHERE trabajador_id=? AND fecha=? "
            "ORDER BY id", (tid, fecha))]

    def _dia_laboral(self, tid, ahora):
        """
        A que dia laboral pertenece la proxima marca de ESTE trabajador.

        Si tiene una jornada empezada y sin cerrar, la marca sigue en ese dia
        aunque el calendario ya haya cambiado: asi un turno de noche (entra
        22:00, sale 06:00) queda entero en un solo dia laboral.
        """
        fila = self.cx.execute(
            "SELECT fecha FROM marcas WHERE trabajador_id=? "
            "ORDER BY fecha DESC, id DESC LIMIT 1", (tid,)).fetchone()
        hoy = ahora.date().isoformat()
        if not fila:
            return hoy
        fecha = fila["fecha"]
        marcas = self.marcas_de(tid, fecha)
        if self.proxima_de(set(m["tipo"] for m in marcas)) is None:
            return hoy                                   # jornada completa
        entrada = [m for m in marcas if m["tipo"] == "entrada"]
        if entrada:
            ini = datetime.strptime(fecha + " " + entrada[0]["hora"], "%Y-%m-%d %H:%M")
            if (ahora - ini).total_seconds() > HORAS_JORNADA_ABIERTA * 3600:
                return hoy                               # se quedo abierta, se abandona
        return fecha

    @staticmethod
    def proxima_de(tipos_presentes):
        """La primera de las cuatro que falta. None si ya estan todas."""
        for t in TIPOS:
            if t not in tipos_presentes:
                return t
        return None

    def estado(self, tid, ahora=None):
        """Que le toca marcar a este trabajador, y como va su dia."""
        ahora = ahora or datetime.now()
        fecha = self._dia_laboral(tid, ahora)
        marcas = self.marcas_de(tid, fecha)
        proxima = self.proxima_de(set(m["tipo"] for m in marcas))
        return {
            "trabajador_id": tid, "fecha": fecha, "marcas": marcas,
            "proxima": proxima, "etiqueta": ETIQUETAS.get(proxima, ""),
            "completa": proxima is None,
            "horas": horas_de_marcas(marcas),
        }

    def marcar(self, tid, ahora=None, origen="app"):
        """
        Registra la marca que corresponda, con la hora del reloj del sistema.

        Cual es no se elige: sale del historial propio del trabajador, asi que
        desde el boton es imposible marcar fuera de orden.

        `origen` queda guardado para cuando las marcas lleguen de un reloj
        biometrico en vez de la pantalla.
        """
        ahora = ahora or datetime.now()
        est = self.estado(tid, ahora)
        if est["completa"]:
            raise ValueError(
                "Ya estan las cuatro marcas del dia %s. Si algo quedo mal, "
                "corrigelo en la pestana Jornadas." % est["fecha"])
        self.cx.execute(
            "INSERT INTO marcas (trabajador_id, fecha, tipo, hora, origen, registrado_en) "
            "VALUES (?,?,?,?,?,?)",
            (tid, est["fecha"], est["proxima"], ahora.strftime("%H:%M"),
             origen, ahora.strftime("%Y-%m-%d %H:%M:%S")))
        self.cx.commit()
        r = {"tipo": est["proxima"], "etiqueta": ETIQUETAS[est["proxima"]],
             "hora": ahora.strftime("%H:%M"), "fecha": est["fecha"]}
        r["correo"] = self.encolar_aviso(tid, r, ahora)
        return r

    # -- aviso por correo -----------------------------------------------
    #  Marcar y avisar son cosas distintas a proposito: la marca se guarda
    #  siempre, y el correo queda en una cola que se vacia cuando hay internet.
    #  Si el correo falla, el trabajador igual quedo marcado.

    def encolar_aviso(self, tid, marca, ahora=None):
        """Deja en la cola el aviso de una marca. Devuelve a quien se le avisa."""
        try:
            if self.config().get("correo_activo", "0") != "1":
                return None
            t = self.trabajador(tid)
            para = limpiar_correo(t.get("correo") if t else "")
            if not para:
                return None
            asunto, cuerpo = self.texto_aviso(t, marca, ahora)
            self.encolar_correo(tid, para, asunto, cuerpo, ahora)
            return para
        except Exception:
            # Nada de lo que pase con el correo puede impedir una marcacion.
            return None

    def texto_aviso(self, trabajador, marca, ahora=None):
        """Lo que le llega al trabajador: que marco, a que hora, y como va su dia."""
        cfg = self.config()
        negocio = cfg.get("negocio", NEGOCIO_DEF)
        est = self.estado(trabajador["id"], ahora)
        asunto = "%s a las %s - %s" % (marca["etiqueta"], marca["hora"], negocio)
        hechas = dict((m["tipo"], m["hora"]) for m in est["marcas"])
        lineas = ["Hola %s:" % trabajador["nombre"], "",
                  "Quedo registrada tu marca de %s a las %s del %s."
                  % (marca["etiqueta"].upper(), marca["hora"],
                     texto_dia(marca["fecha"])), "", "Tus marcas de ese dia:"]
        for tipo in TIPOS:
            lineas.append("   %-20s %s" % (ETIQUETAS[tipo], hechas.get(tipo, "--:--")))
        if est["completa"]:
            lineas += ["", "Jornada completa: %s horas trabajadas."
                           % hhmm_txt(est["horas"])]
        elif est["horas"]:
            lineas += ["", "Llevas %s horas trabajadas." % hhmm_txt(est["horas"])]
        lineas += ["", "--",
                   "Aviso automatico del Control de Horas de %s." % negocio,
                   "No respondas a este correo.  Si algo no cuadra, avisale al jefe."]
        return asunto, "\n".join(lineas)

    def encolar_correo(self, tid, para, asunto, cuerpo, ahora=None):
        ahora = ahora or datetime.now()
        cur = self.cx.execute(
            "INSERT INTO correos (trabajador_id, para, asunto, cuerpo, creado_en) "
            "VALUES (?,?,?,?,?)",
            (tid, para, asunto, cuerpo, ahora.strftime("%Y-%m-%d %H:%M:%S")))
        self.cx.commit()
        return cur.lastrowid

    def correos_por_enviar(self, limite=20):
        return [dict(f) for f in self.cx.execute(
            "SELECT * FROM correos WHERE enviado_en='' AND intentos<? "
            "ORDER BY id LIMIT ?", (INTENTOS_CORREO, limite))]

    def correo_enviado(self, cid, ahora=None):
        ahora = ahora or datetime.now()
        self.cx.execute("UPDATE correos SET enviado_en=?, ultimo_error='' WHERE id=?",
                        (ahora.strftime("%Y-%m-%d %H:%M:%S"), cid))
        self.cx.commit()

    def correo_fallo(self, cid, error):
        self.cx.execute("UPDATE correos SET intentos=intentos+1, ultimo_error=? "
                        "WHERE id=?", (str(error)[:300], cid))
        self.cx.commit()

    def cuenta_correos(self):
        """Como va la cola, para mostrarlo en pantalla."""
        f = self.cx.execute(
            "SELECT SUM(enviado_en<>'') enviados, "
            "       SUM(enviado_en='' AND intentos<?) esperando, "
            "       SUM(enviado_en='' AND intentos>=?) perdidos FROM correos",
            (INTENTOS_CORREO, INTENTOS_CORREO)).fetchone()
        return {"enviados": f["enviados"] or 0, "esperando": f["esperando"] or 0,
                "perdidos": f["perdidos"] or 0}

    def ultimo_error_correo(self):
        f = self.cx.execute("SELECT ultimo_error FROM correos WHERE enviado_en='' "
                            "AND ultimo_error<>'' ORDER BY id DESC LIMIT 1").fetchone()
        return f["ultimo_error"] if f else ""

    def reintentar_correos(self):
        """Pone en cero los intentos de los que se dieron por perdidos."""
        cur = self.cx.execute("UPDATE correos SET intentos=0 WHERE enviado_en=''")
        self.cx.commit()
        return cur.rowcount

    def purgar_correos(self, dias=90, hoy=None):
        """Los avisos ya enviados no se guardan para siempre."""
        limite = ((hoy or date.today()) - timedelta(days=dias)).isoformat()
        cur = self.cx.execute("DELETE FROM correos WHERE enviado_en<>'' "
                              "AND enviado_en<?", (limite,))
        self.cx.commit()
        return cur.rowcount

    # -- correcciones del administrador ---------------------------------
    def _no_pagado(self, tid, fecha):
        """Un dia con algo ya pagado no se corrige: primero hay que desmarcarlo."""
        pagados = [p for p in self.pagos_de(tid, fecha).values() if p]
        if pagados:
            raise ValueError(
                "Ese dia ya tiene un pago registrado (%s el %s). Para corregirlo, "
                "primero quitale los checks de pagado."
                % (pesos(sum(p["monto"] for p in pagados)), pagados[0]["pagado_en"]))

    def editar_marca(self, mid, hora=None, tipo=None):
        m = self.cx.execute("SELECT * FROM marcas WHERE id=?", (mid,)).fetchone()
        if not m:
            raise ValueError("Esa marca ya no existe.")
        m = dict(m)
        self._no_pagado(m["trabajador_id"], m["fecha"])
        if hora is not None:
            limpia = normalizar_hora(hora)
            if limpia is None:
                raise ValueError(
                    "'%s' no se entiende como hora. Puedes escribir 1430 o 14:30." % hora)
            m["hora"] = limpia
        if tipo is not None:
            if tipo not in TIPOS:
                raise ValueError("Tipo de marca desconocido.")
            if tipo != m["tipo"] and any(
                    x["tipo"] == tipo and x["id"] != mid
                    for x in self.marcas_de(m["trabajador_id"], m["fecha"])):
                raise ValueError("Ese dia ya tiene una marca de %s. "
                                 "Corrige o borra la otra primero." % ETIQUETAS[tipo])
            m["tipo"] = tipo
        self.cx.execute("UPDATE marcas SET hora=?, tipo=?, origen='manual' WHERE id=?",
                        (m["hora"], m["tipo"], mid))
        self.cx.commit()

    def agregar_marca(self, tid, fecha, tipo, hora):
        """Para cuando a alguien se le olvido marcar y hay que agregarla."""
        if tipo not in TIPOS:
            raise ValueError("Tipo de marca desconocido.")
        hora = normalizar_hora(hora)
        if hora is None:
            raise ValueError(
                "No se entiende esa hora. Puedes escribir 1430 o 14:30.")
        datetime.strptime(fecha, "%Y-%m-%d")
        self._no_pagado(tid, fecha)
        if any(m["tipo"] == tipo for m in self.marcas_de(tid, fecha)):
            raise ValueError("Ese dia ya tiene una marca de %s." % ETIQUETAS[tipo])
        self.cx.execute(
            "INSERT INTO marcas (trabajador_id, fecha, tipo, hora, origen, registrado_en) "
            "VALUES (?,?,?,?,'manual',?)",
            (tid, fecha, tipo, hora, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.cx.commit()

    def borrar_marca(self, mid):
        m = self.cx.execute("SELECT trabajador_id, fecha FROM marcas WHERE id=?",
                            (mid,)).fetchone()
        if m:
            self._no_pagado(m["trabajador_id"], m["fecha"])
        self.cx.execute("DELETE FROM marcas WHERE id=?", (mid,))
        self.cx.commit()

    def borrar_dia(self, tid, fecha):
        """
        Borra el dia completo de un trabajador (sus cuatro marcas), por
        ejemplo si se registro por error un dia que no vino.

        Un dia pagado no se borra: primero hay que quitarle el check, para
        que no desaparezca por accidente un pago ya registrado.
        """
        self._no_pagado(tid, fecha)
        cur = self.cx.execute("DELETE FROM marcas WHERE trabajador_id=? AND fecha=?",
                              (tid, fecha))
        self.cx.commit()
        return cur.rowcount

    # -- pagos ---------------------------------------------------------
    #  Cada dia se paga en dos partes: las horas normales y las extra. Se
    #  pueden pagar juntas o por separado, para poder pagarle a alguien solo
    #  sus horas extra, por ejemplo.

    def _migrar_pagos_en_dos_partes(self):
        """Pasa los pagos del formato anterior (un solo monto por dia) a dos."""
        columnas = [f[1] for f in self.cx.execute("PRAGMA table_info(pagos)")]
        if "concepto" in columnas or not columnas:
            return
        viejos = [dict(f) for f in self.cx.execute("SELECT * FROM pagos")]
        cfg = self.config()
        trabajadores = dict((t["id"], dict(t))
                            for t in self.trabajadores(solo_activos=False))
        self.cx.execute("ALTER TABLE pagos RENAME TO pagos_de_un_solo_monto")
        self.cx.execute("""CREATE TABLE pagos (
                             trabajador_id INTEGER NOT NULL REFERENCES trabajadores(id),
                             fecha         TEXT    NOT NULL,
                             concepto      TEXT    NOT NULL,
                             monto         INTEGER NOT NULL,
                             pagado_en     TEXT    NOT NULL,
                             PRIMARY KEY (trabajador_id, fecha, concepto))""")
        for v in viejos:
            t = trabajadores.get(v["trabajador_id"], {})
            horas = horas_de_marcas(self.marcas_de(v["trabajador_id"], v["fecha"]))
            val = valor_dia(cfg, t, horas)
            # Lo que se pagó se reparte entre las dos partes tal como valen hoy.
            if val["total"] > 0:
                escala = float(v["monto"]) / val["total"]
                normal = int(round(val["pago_normal"] * escala))
            else:
                normal = int(v["monto"])
            partes = [("normal", normal), ("extra", int(v["monto"]) - normal)]
            for concepto, monto in partes:
                if monto > 0:
                    self.cx.execute("INSERT INTO pagos VALUES (?,?,?,?,?)",
                                    (v["trabajador_id"], v["fecha"], concepto,
                                     monto, v["pagado_en"]))
        self.cx.commit()

    def pagos(self):
        """{(trabajador_id, fecha, concepto): pago} de todo lo pagado."""
        return dict(((f["trabajador_id"], f["fecha"], f["concepto"]), dict(f))
                    for f in self.cx.execute("SELECT * FROM pagos"))

    def pago_de(self, tid, fecha, concepto):
        f = self.cx.execute("SELECT * FROM pagos WHERE trabajador_id=? AND fecha=? "
                            "AND concepto=?", (tid, fecha, concepto)).fetchone()
        return dict(f) if f else None

    def pagos_de(self, tid, fecha):
        return dict((c, self.pago_de(tid, fecha, c)) for c in CONCEPTOS)

    @staticmethod
    def _cuales(concepto):
        return CONCEPTOS if concepto in (None, "todo") else (concepto,)

    def marcar_pagado(self, tid, fecha, concepto="todo", hoy=None):
        """
        Deja pagada una parte del dia (o las dos), con lo que vale ahora.

        Solo se pagan dias completos: a uno al que le falta una marca no se le
        conoce el valor. Y no se paga una parte que vale $0.
        """
        dias = dias_con_valor(self, fecha, fecha, tid)
        if not dias:
            raise ValueError("Ese trabajador no tiene marcas ese dia.")
        dia = dias[0]
        if not dia["completa"]:
            raise ValueError("A ese dia le faltan marcas (%s). Completalo antes de "
                             "pagarlo." % ", ".join(x.lower() for x in dia["faltan"]))
        cuales = self._cuales(concepto)
        montos = {"normal": dia["pago_normal"], "extra": dia["pago_extra"]}
        pagados = self.pagos_de(tid, fecha)
        pagado_ahora = 0
        for c in cuales:
            if pagados[c] or montos[c] <= 0:
                continue
            self.cx.execute("INSERT INTO pagos VALUES (?,?,?,?,?)",
                            (tid, fecha, c, int(montos[c]),
                             (hoy or date.today()).isoformat()))
            pagado_ahora += int(montos[c])
        self.cx.commit()
        if pagado_ahora == 0 and not any(pagados[c] for c in cuales):
            if len(cuales) == 1:
                raise ValueError("Ese dia no tiene %s que pagar."
                                 % NOMBRE_CONCEPTO[cuales[0]])
            raise ValueError("Ese dia vale $0. Revisa el valor hora del trabajador "
                             "en la pestana Trabajadores.")
        return pagado_ahora

    def desmarcar_pagado(self, tid, fecha, concepto="todo"):
        for c in self._cuales(concepto):
            self.cx.execute("DELETE FROM pagos WHERE trabajador_id=? AND fecha=? "
                            "AND concepto=?", (tid, fecha, c))
        self.cx.commit()

    def pagar_pendientes(self, tid, desde=None, hasta=None, concepto="todo", hoy=None):
        """Paga de una vez lo que falte del rango: todo, o solo una de las partes."""
        dias, total = 0, 0
        for d in dias_con_valor(self, desde, hasta, tid):
            if not d["completa"]:
                continue
            falta = sum(d["por_pagar_" + c] for c in self._cuales(concepto))
            if falta <= 0:
                continue
            total += self.marcar_pagado(tid, d["fecha"], concepto, hoy)
            dias += 1
        return dias, total

    def marcas(self, desde=None, hasta=None, tid=None):
        sql = ("SELECT m.*, t.nombre FROM marcas m "
               "JOIN trabajadores t ON t.id = m.trabajador_id WHERE 1=1")
        p = []
        if desde:
            sql += " AND m.fecha >= ?"; p.append(desde)
        if hasta:
            sql += " AND m.fecha <= ?"; p.append(hasta)
        if tid:
            sql += " AND m.trabajador_id = ?"; p.append(tid)
        sql += " ORDER BY m.fecha DESC, t.orden, m.id"
        return [dict(f) for f in self.cx.execute(sql, p)]

    # -- dias armados desde las marcas ----------------------------------
    def jornadas(self, desde=None, hasta=None, tid=None):
        """
        Un dia por trabajador, armado desde sus cuatro marcas.

        Devuelve la misma forma que usaba el formato viejo (entrada, salida,
        minutos de colacion), para que los resumenes y los informes no tengan
        que saber que por debajo ahora hay marcas.
        """
        por_dia = {}
        for m in self.marcas(desde, hasta, tid):
            clave = (m["fecha"], m["trabajador_id"])
            por_dia.setdefault(clave, []).append(m)

        trabajadores = dict((t["id"], t) for t in self.trabajadores(solo_activos=False))
        salida = []
        for (fecha, tid_), marcas in por_dia.items():
            t = trabajadores.get(tid_, {})
            por_tipo = dict((x["tipo"], x["hora"]) for x in marcas)
            salida.append({
                "id": "%s|%s" % (fecha, tid_),
                "trabajador_id": tid_,
                "nombre": t.get("nombre", "?"),
                "valor_hora": t.get("valor_hora", 0),
                "valor_hora_extra": t.get("valor_hora_extra", 0),
                "horas_contrato": t.get("horas_contrato", 0),
                "fecha": fecha,
                "entrada": por_tipo.get("entrada", ""),
                "salida": por_tipo.get("salida", ""),
                "colacion": minutos_colacion(marcas),
                "colacion_inicio": por_tipo.get("colacion_inicio", ""),
                "colacion_fin": por_tipo.get("colacion_fin", ""),
                "horas": horas_de_marcas(marcas),
                "dia": nombre_dia(fecha),
                "extra_dia": 0.0,          # el pago es semanal; se llena para el informe
                "marcas": marcas,
                "completa": self.proxima_de(set(por_tipo)) is None,
                "faltan": [ETIQUETAS[t2] for t2 in TIPOS if t2 not in por_tipo],
                "nota": "",
            })
        salida.sort(key=lambda d: (d["fecha"], d["nombre"]), reverse=True)
        return salida

    def total_jornadas(self):
        return len(set((m["fecha"], m["trabajador_id"])
                       for m in self.cx.execute(
                           "SELECT fecha, trabajador_id FROM marcas")))

    def total_marcas(self):
        return self.cx.execute("SELECT COUNT(*) FROM marcas").fetchone()[0]

    def migrar_jornadas_a_marcas(self):
        """
        Pasa las jornadas del formato viejo (una fila con entrada, salida y
        minutos de colacion) a cuatro marcas. La colacion se ubica al medio del
        turno, porque el formato viejo no guardaba a que hora habia sido.
        """
        hechas = 0
        for j in self.cx.execute("SELECT * FROM jornadas ORDER BY fecha, id").fetchall():
            j = dict(j)
            if self.marcas_de(j["trabajador_id"], j["fecha"]):
                continue                                   # ya migrada
            ent = a_minutos(j["entrada"])
            if ent is None or a_minutos(j["salida"]) is None:
                continue
            bruto = minutos_turno(j["entrada"], j["salida"])
            col = int(j["colacion"] or 0)
            puestas = [("entrada", ent), ("salida", ent + bruto)]
            if 0 < col < bruto:
                medio = ent + (bruto - col) // 2
                puestas += [("colacion_inicio", medio), ("colacion_fin", medio + col)]
            for tipo, minutos in puestas:
                self.cx.execute(
                    "INSERT INTO marcas (trabajador_id, fecha, tipo, hora, origen, "
                    "registrado_en) VALUES (?,?,?,?,'migrado','')",
                    (j["trabajador_id"], j["fecha"], tipo, a_hhmm(minutos)))
            hechas += 1
        self.cx.commit()
        return hechas

    # -- respaldos ------------------------------------------------------
    def carpeta_respaldos(self):
        c = os.path.join(os.path.dirname(self.ruta), "respaldos")
        os.makedirs(c, exist_ok=True)
        return c

    def respaldar(self, destino=None, conservar=30):
        """
        Copia la base de datos. Sin destino hace la copia del dia dentro de
        respaldos/ y borra las mas viejas; con destino la guarda donde se le
        diga (un pendrive, por ejemplo).

        Usa la copia propia de SQLite y no copiar el archivo a mano, porque
        con WAL el archivo suelto puede quedar a medias.
        """
        automatico = destino is None
        if automatico:
            destino = os.path.join(self.carpeta_respaldos(),
                                   "horas-%s.sqlite3" % date.today().isoformat())
            if os.path.exists(destino):
                return None                      # ya hay copia de hoy
        otro = sqlite3.connect(destino)
        try:
            with otro:
                self.cx.backup(otro)
        finally:
            otro.close()
        if automatico:
            self._podar_respaldos(conservar)
        return destino

    def _podar_respaldos(self, conservar):
        c = self.carpeta_respaldos()
        copias = sorted(f for f in os.listdir(c)
                        if f.startswith("horas-") and f.endswith(".sqlite3"))
        for viejo in copias[:-conservar] if conservar > 0 else []:
            try:
                os.remove(os.path.join(c, viejo))
            except OSError:
                pass

    def ultimo_respaldo(self):
        """(fecha, cuantas copias hay). (None, 0) si todavia no hay ninguna."""
        try:
            copias = sorted(f for f in os.listdir(self.carpeta_respaldos())
                            if f.startswith("horas-") and f.endswith(".sqlite3"))
        except OSError:
            return None, 0
        if not copias:
            return None, 0
        return copias[-1][len("horas-"):-len(".sqlite3")], len(copias)

    def sembrar_si_vacia(self):
        if self.cx.execute("SELECT COUNT(*) FROM trabajadores").fetchone()[0]:
            return False
        for i in (1, 2, 3):
            self.agregar_trabajador("Trabajador %d" % i, 0)
        return True


# ------------------------------------------------------- valor de la hora extra
def valor_hora_extra(cfg, trabajador):
    """
    Cuanto vale una hora extra para este trabajador.

    Dos modos, elegidos en Configuracion:
      - 'recargo': la hora normal mas un porcentaje (50 % es lo legal en Chile).
      - 'fijo':    un monto en pesos escrito a mano. Si el trabajador tiene el
                   suyo, manda ese; si no, se usa el valor general.
    """
    normal = float(trabajador.get("valor_hora") or 0)
    if str(cfg.get("modo_extra", "recargo")) == "fijo":
        propio = float(trabajador.get("valor_hora_extra") or 0)
        if propio > 0:
            return propio
        try:
            return float(cfg.get("valor_extra_global") or 0)
        except (TypeError, ValueError):
            return 0.0
    try:
        recargo = float(cfg.get("recargo_extra") or 0)
    except (TypeError, ValueError):
        recargo = 0.0
    return normal * (1.0 + recargo / 100.0)


def texto_regla_extra(cfg):
    if str(cfg.get("modo_extra", "recargo")) == "fijo":
        return "monto fijo por hora extra"
    return "hora normal + %s%% de recargo" % _limpio(cfg.get("recargo_extra", "50"))


def _limpio(n):
    t = str(n)
    return t[:-2] if t.endswith(".0") else t


# ==========================================================================
#  VALOR DEL DIA
#  Lo que se pasa de la jornada del contrato EN EL DIA es hora extra.
#  El valor del dia = horas normales x valor hora + horas extra x valor
#  hora extra. La semana y el mes son la suma de los dias, asi que
#  siempre cuadran y el jefe no tiene que sacar cuentas.
# ==========================================================================

def horas_contrato_de(cfg, trabajador):
    """Jornada diaria del contrato. La del trabajador manda sobre la general."""
    propia = float((trabajador or {}).get("horas_contrato") or 0)
    if propia > 0:
        return propia
    try:
        return float(cfg.get("horas_contrato", 7) or 7)
    except (TypeError, ValueError):
        return 7.0


def valor_dia(cfg, trabajador, horas):
    """
    Reparte las horas de un dia entre normales y extra, y les pone precio.

    Ejemplo del local: contrato de 7 h, entra 08:30, colacion de 13:30 a
    14:30, sale 19:30 -> 10 h trabajadas = 7 normales + 3 extra.
    """
    contrato = horas_contrato_de(cfg, trabajador)
    horas = round(float(horas or 0), 2)
    normales = round(min(horas, contrato), 2)
    extra = round(max(0.0, horas - contrato), 2)
    v_normal = float((trabajador or {}).get("valor_hora") or 0)
    v_extra = valor_hora_extra(cfg, trabajador or {})
    pago_normal = round(normales * v_normal)
    pago_extra = round(extra * v_extra)
    return {
        "contrato": contrato, "horas": horas,
        "normales": normales, "extra": extra,
        "valor_hora": v_normal, "valor_extra": v_extra,
        "pago_normal": pago_normal, "pago_extra": pago_extra,
        "total": pago_normal + pago_extra,
    }


def valor_hora_desde_sueldo(sueldo_mensual, horas_semanales):
    """
    Valor de la hora ordinaria a partir del sueldo del contrato.

        sueldo mensual / 30 = sueldo diario
        sueldo diario x 7   = sueldo semanal
        sueldo semanal / horas semanales pactadas = valor hora

    Con $553.553 y 42 h semanales da $3.075 la hora.
    """
    try:
        sueldo = float(sueldo_mensual or 0)
        horas = float(horas_semanales or 0)
    except (TypeError, ValueError):
        return 0.0
    if sueldo <= 0 or horas <= 0:
        return 0.0
    return round(sueldo / 30.0 * 7.0 / horas)


def limpiar_correo(texto):
    """
    Deja la direccion lista para guardar, o avisa si no parece una.

    No se trata de validar todo el estandar: basta con atajar los errores de
    tipeo que dejarian al trabajador sin aviso y sin que nadie se entere.
    """
    correo = (texto or "").strip()
    if not correo:
        return ""
    if (correo.count("@") != 1 or " " in correo
            or correo.startswith("@") or correo.endswith("@")):
        raise ValueError("'%s' no parece un correo. Tiene que ser algo como "
                         "nombre@gmail.com" % correo)
    dominio = correo.split("@")[1]
    if "." not in dominio or dominio.startswith(".") or dominio.endswith("."):
        raise ValueError("'%s' no parece un correo: le falta el punto del "
                         "dominio, como en gmail.com" % correo)
    return correo


def texto_dia(iso):
    d = datetime.strptime(iso, "%Y-%m-%d").date()
    return "%s %d de %s" % (DIAS[d.weekday()], d.day, nombre_mes(d.month))


# ------------------------------------------------- dias con su valor en pesos
def dias_con_valor(datos, desde, hasta, tid=None):
    """Los dias del rango, cada uno con sus horas repartidas y su valor."""
    cfg = datos.config()
    trabajadores = dict((t["id"], dict(t))
                        for t in datos.trabajadores(solo_activos=False))
    pagos = datos.pagos()
    salida = []
    for j in datos.jornadas(desde, hasta, tid):
        t = trabajadores.get(j["trabajador_id"], {})
        d = dict(j)
        d.update(valor_dia(cfg, t, j["horas"]))
        d["extra_dia"] = d["extra"]        # nombre que usan los informes
        cobrado = 0
        for c in CONCEPTOS:
            p = pagos.get((j["trabajador_id"], j["fecha"], c))
            d["pagado_" + c] = p is not None
            d["monto_pagado_" + c] = p["monto"] if p else 0
            d["pagado_en_" + c] = p["pagado_en"] if p else ""
            d["por_pagar_" + c] = 0 if p else d["pago_" + c]
            cobrado += d["monto_pagado_" + c]
        d["cobrado"] = cobrado
        d["por_pagar"] = d["por_pagar_normal"] + d["por_pagar_extra"]
        d["pagado_algo"] = d["pagado_normal"] or d["pagado_extra"]
        d["pagado"] = (d["completa"] and d["total"] > 0 and d["por_pagar"] == 0)
        d["pagado_en"] = d["pagado_en_normal"] or d["pagado_en_extra"]
        salida.append(d)
    salida.sort(key=lambda x: (x["fecha"], x["nombre"]))
    return salida


def _agrupar(datos, desde, hasta, titulo, subtitulo=""):
    """
    Por trabajador: dias trabajados, cuanto se le pago y cuanto se le debe.

    Lo pagado sale del monto que quedo registrado al pagar, no de recalcular:
    asi lo que ya se entrego no cambia si despues se ajusta un valor.
    """
    cfg = datos.config()
    dias = dias_con_valor(datos, desde, hasta)
    por_trab = {}
    for d in dias:
        por_trab.setdefault(d["trabajador_id"], []).append(d)

    filas = []
    for t in datos.trabajadores(solo_activos=False):
        suyos = por_trab.get(t["id"])
        if not suyos:
            continue
        pagados = [d for d in suyos if d["pagado"]]
        pendientes = [d for d in suyos if d["completa"] and d["por_pagar"] > 0]
        incompletos = [d for d in suyos if not d["completa"]]
        f = {
            "id": t["id"], "nombre": t["nombre"],
            "contrato": horas_contrato_de(cfg, dict(t)),
            "valor_hora": float(t["valor_hora"] or 0),
            "valor_extra": valor_hora_extra(cfg, dict(t)),
            "turnos": len(suyos),
            "horas": round(sum(d["horas"] for d in suyos), 2),
            "ordinarias": round(sum(d["normales"] for d in suyos), 2),
            "extra": round(sum(d["extra"] for d in suyos), 2),
            "total": sum(d["total"] for d in suyos),
            "dias_pagados": len(pagados),
            "pagado_normal": sum(d["monto_pagado_normal"] for d in suyos),
            "pagado_extra": sum(d["monto_pagado_extra"] for d in suyos),
            "pagado": sum(d["cobrado"] for d in suyos),
            "dias_pendientes": len(pendientes),
            "por_pagar_normal": sum(d["por_pagar_normal"] for d in pendientes),
            "por_pagar_extra": sum(d["por_pagar_extra"] for d in pendientes),
            "por_pagar": sum(d["por_pagar"] for d in pendientes),
            "dias": suyos, "detalle": suyos, "incompletos": incompletos,
        }
        filas.append(f)

    filas.sort(key=lambda f: f["nombre"].lower())
    totales = {}
    for k in ("turnos", "horas", "ordinarias", "extra", "total",
              "dias_pagados", "pagado", "pagado_normal", "pagado_extra",
              "dias_pendientes", "por_pagar", "por_pagar_normal", "por_pagar_extra"):
        v = sum(f[k] for f in filas)
        totales[k] = round(v, 2) if isinstance(v, float) else v
    return {
        "desde": desde, "hasta": hasta, "titulo": titulo, "subtitulo": subtitulo,
        "cfg": cfg, "filas": filas, "totales": totales,
        "regla_extra": texto_regla_extra(cfg),
        "contrato": _limpio(cfg.get("horas_contrato", "7")),
        "negocio": cfg.get("negocio", NEGOCIO_DEF),
        "ciudad": cfg.get("ciudad", CIUDAD_DEF),
    }


def resumen_mensual(datos, anio, mes):
    """Un mes completo, por trabajador, con lo pagado y lo pendiente."""
    desde = "%04d-%02d-01" % (anio, mes)
    hasta = "%04d-%02d-%02d" % (anio, mes, ultimo_dia(anio, mes))
    r = _agrupar(datos, desde, hasta,
                 "%s de %d" % (nombre_mes(mes).capitalize(), anio))
    r["anio"], r["mes"] = anio, mes
    return r


def resumen_todo(datos):
    """Todo lo registrado, sin importar el mes."""
    return _agrupar(datos, None, None, "Todo lo registrado")


def pendiente_fuera(datos, desde, hasta):
    """
    Dias completos y sin pagar que quedan FUERA del rango que se esta mirando.
    Sirve para avisar que alguien tiene plata pendiente de otro mes.
    """
    n, total = 0, 0
    for d in dias_con_valor(datos, None, None):
        if not d["completa"] or d["por_pagar"] <= 0:
            continue
        if (desde and d["fecha"] < desde) or (hasta and d["fecha"] > hasta):
            n += 1
            total += d["por_pagar"]
    return n, total
