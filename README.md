# Horas El Buen Corte

Control de horas trabajadas para **Carnicería El Buen Corte, Loncoche**.

Sin servidor propio y sin hosting que se duerma. Hay dos versiones de la misma app:

| Versión | Dónde vive | Para quién |
|---|---|---|
| **Artifact** — `app.html` | [Link fijo en Claude](https://claude.ai/code/artifact/b0f37a93-1360-495e-b641-5429ecd67e97) | Solo tú y tu organización de Claude. Para desarrollar y mostrarle la app al cliente. |
| **Web** — `docs/index.html` | [mfnc1996.github.io/horas-el-buen-corte](https://mfnc1996.github.io/horas-el-buen-corte/) | El local. Cualquiera con el link, sin cuenta de nada. **Falta conectarle Firebase.** |

La versión web se genera desde `app.html` con `python3 build-web.py`: la lógica,
el diseño y las vistas son las mismas, solo cambia de dónde salen los datos.

**Para ponerla en línea, sigue [DESPLIEGUE.md](DESPLIEGUE.md).**

---

## Cómo se usa

| Pestaña | Para qué |
|---|---|
| **Registrar** | Cargar una jornada: trabajador, fecha, entrada, salida y colación. |
| **Resumen** | Lo que mira el dueño: totales por trabajador, por semana o por mes. |
| **Registros** | Historial completo, con filtros, edición, borrado y exportación a CSV. |
| **Ajustes** | Umbrales de horas extra y lista de trabajadores. |

### Cargar la hora rápido
Cada campo de hora tiene cuatro formas de llenarse, de la más rápida a la más precisa:

1. **Un chip** con la hora habitual. Los chips **se aprenden solos**: muestran las
   cuatro horas más usadas en los registros ya cargados. Hasta que haya historial,
   muestran horas típicas de local (08:00 / 08:30 / 09:00 / 10:00 y 14:00 / 18:00 / 19:00 / 20:00).
2. **Ahora** — pone la hora actual, redondeada a 5 minutos.
3. **−15 / +15** — ajusta de a cuarto de hora.
4. El campo de hora normal, para cualquier valor exacto.

Debajo, un indicador en vivo muestra las horas trabajadas y, en rojo, las horas
extra que se generarían — antes de guardar.

### Primeros pasos
1. Entra a **Ajustes** y reemplaza «Trabajador 1/2/3» por los nombres reales.
2. Confirma los umbrales (vienen en 8 h al día y 45 h a la semana).
3. Manda el link a los trabajadores por WhatsApp. Que lo guarden en la pantalla
   de inicio del celular: cargar una jornada toma unos 10 segundos.

---

## Horas extra

Las **tres reglas se calculan siempre en paralelo**; el selector de Ajustes solo
elige cuál se muestra como «horas extra a pagar»:

- **Diaria** — lo que excede el umbral de cada día.
- **Semanal** — lo que excede el umbral en el total de la semana.
- **La mayor de las dos.**

Cuando el cliente confirme cuál corresponde, es cambiar un selector: nada que rehacer.

### Fórmulas

**Horas trabajadas** = salida − entrada − colación.
Si la salida es menor que la entrada, se asume que el turno cruza la medianoche
(22:00 a 06:00 son 8 horas, no −16).

**Extra diaria** = `máx(0, horas − umbral diario)`, día por día.
**Extra semanal** = `máx(0, total de la semana − umbral semanal)`, de lunes a domingo.

En la vista de mes, cada semana se cuenta en el mes en que empieza.

### Casos verificados

| Caso | Entrada | Salida | Colación | Horas | Extra (umbral 8) |
|---|---|---|---|---|---|
| Jornada normal | 09:00 | 18:00 | 60 | 8,00 | 0,00 |
| Con extra | 08:00 | 19:30 | 45 | 10,75 | 2,75 |
| Turno nocturno | 22:00 | 06:00 | 0 | 8,00 | 0,00 |
| Nocturno con colación | 23:30 | 07:15 | 30 | 7,25 | 0,00 |
| Media jornada | 09:00 | 13:00 | 0 | 4,00 | 0,00 |
| Sin colación | 09:00 | 18:00 | 0 | 9,00 | 1,00 |
| Salida = entrada | 09:00 | 09:00 | 30 | 0,00 | 0,00 |

---

## Diseño

Toma la identidad del logo del local: rojo carmesí, verde y negro sobre blanco.
Las **chairas cruzadas** son la marca de la cabecera, las **cintas con muesca y
estrella** encabezan cada sección, y el **contorno ondulado** de la insignia
separa la cabecera del contenido. El sombrero de huaso no se usa.

Tipografías: Yellowtail (el nombre del local), Archivo (interfaz) e IBM Plex Mono
(horas y cifras, alineadas en columna). Funciona en tema claro y oscuro, y está
pensada primero para el celular.

---

## Límites y mantención

- La base de datos guarda hasta **5.000 jornadas** (unos 5 años con 3 trabajadores).
  Ajustes avisa al pasar las 900. Para liberar: exportar el CSV y borrar lo antiguo.
- **Cualquiera con el link puede ver y editar todo**, incluidos los registros de
  otros. Para un local de 3 personas es lo razonable; si hace falta separar
  permisos entre dueño y trabajadores, se puede agregar.
- **Quitar un trabajador** de la lista no borra sus jornadas ya registradas: el
  nombre queda guardado en cada registro.
- El CSV sale con `;` y coma decimal, listo para abrir en Excel en Chile.

---

## Pendientes a confirmar con el cliente

1. **Umbral de horas extra**: ¿diario (8 h), semanal (45 h) o el mayor de ambos?
2. **Colación**: hoy se descuenta de la jornada. Si se paga, se usa «Sin colación».
3. **Recargo de horas extra** (ej. 50 %): hoy se informan horas, no pesos. Si hace
   falta el monto, se agrega valor hora y factor de recargo.
4. **Semana laboral**: hoy va de lunes a domingo.

---

## Alternativa: Google Sheets + Formulario

`Codigo.gs` es un script de Google Apps Script que arma el mismo sistema sobre un
Formulario y una planilla de Google, por si el cliente prefiere sus datos dentro
de su propio Drive. Se pega en script.google.com y se ejecuta `crearSistema()`
una vez; deja el formulario, la hoja de registros con las fórmulas, un resumen
semanal, un panel mensual y una hoja de configuración.

No es necesario si se usa la app: son dos caminos para lo mismo.

---

## Archivos

| Archivo | Qué es |
|---|---|
| `app.html` | La app. Fuente única de verdad; se publica como artifact. |
| `build-web.py` | Genera `docs/index.html` desde `app.html`. Falla ruidosamente si algo no calza. |
| `docs/index.html` | Versión para Firebase + GitHub Pages. **Generado — no editar a mano**, salvo para pegar las claves de Firebase. |
| `DESPLIEGUE.md` | Cómo dejarla en línea, paso a paso. |
| `Codigo.gs` | El camino alternativo con Google Sheets. |
| `.prueba/`, `.claude/launch.json` | Andamiaje local de pruebas (un doble de la base de datos para abrir la app en el navegador sin tocar los datos reales). |
