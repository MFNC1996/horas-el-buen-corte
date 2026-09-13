# Control de Horas — Carnicería El Buen Corte

Aplicación de escritorio para Windows: los trabajadores marcan entrada, colación
y salida; la aplicación calcula las horas extra y cuánto hay que pagarle a cada
uno, y saca el informe mensual para imprimir.

### Descargar

**https://mfnc1996.github.io/horas-el-buen-corte/**

O directo: [ControlDeHoras-Setup.exe](https://github.com/MFNC1996/horas-el-buen-corte/releases/latest/download/ControlDeHoras-Setup.exe) (~24 MB)

Doble clic y sigue el asistente. No necesita servidor ni instalar Python, y
funciona sin internet: lo único que lo usa es el aviso por correo, que es
opcional, y aun así las marcaciones se guardan igual sin conexión. Windows va a mostrar el aviso «Windows protegió tu PC» porque el
instalador no está firmado con un certificado de pago: **Más información →
Ejecutar de todas formas**.

---

## Qué hace

| Pestaña | Para qué |
|---|---|
| **Marcar** | La pantalla del día a día: el trabajador toca su nombre y presiona MARCAR. |
| **Días trabajados** | Un día por fila, con lo que hay que pagar y el check de pagado. |
| **Pagos por persona** | Cuánto se le ha pagado a cada uno y cuánto se le debe. Exporta a Excel y PDF. |
| **Trabajadores** | Nombre, valor de la hora, horas de contrato y correo. |
| **Configuración** | Jornada del contrato, valor de la hora extra, datos del negocio y el aviso por correo. |

### Las cuatro marcas del día
Siempre en este orden:

```
entrada  →  inicio colación  →  fin colación  →  salida
```

Cuál toca no se elige: sale del historial **de ese trabajador**, así que desde el
botón es imposible marcar fuera de orden, y dos personas alternándose no se mezclan
nunca. La hora la pone el reloj del computador. Apenas alguien marca se suelta la
selección, para que el siguiente no marque a nombre del anterior.

Las marcas se guardan una por fila, con su origen (`app`, `manual`). Es el mismo
formato que podría alimentar un reloj biométrico más adelante: bastaría con
insertar ahí.

El administrador puede corregir una marca con doble clic sobre el día, y escribirla
corta: `1930` queda `19:30`.

### Días trabajados y pagos
Cada fila dice a quién, cuántas horas, cuántas normales, cuántas extra, cuánto es
de cada parte y el total del día. Las horas se leen como un reloj: `10:42` son diez
horas con cuarenta y dos minutos.

El cuadrado de la izquierda marca el día como pagado, con su monto y su fecha. El
monto queda congelado: si después cambia el valor de la hora, lo ya pagado no se
mueve. **Un día con un pago no se puede corregir ni eliminar** hasta quitarle el
check. Los días a los que les falta una marca salen en ámbar y no se pueden pagar.

Por persona se ve cuánto se le pagó y cuánto se le debe, separado en horas normales
y horas extra, con el detalle día por día para el que cobra a fin de mes.

### El informe mensual
Excel y PDF, listos para imprimir. Traen, por trabajador: días trabajados, horas,
colación descontada, horas ordinarias, horas extra, lo pagado en cada parte y lo
que se le debe. Más el detalle día por día.

### Detalles
- **Una sola ventana**: si ya está abierto y le dan doble clic de nuevo, no se abre
  otro; aparece adelante el que ya estaba.
- **Pantalla de carga** con el logo mientras abre.
- **Respaldo automático** una copia por día, más un botón para copiar a un pendrive.

---

## Cálculos

**Horas trabajadas** = salida − entrada − colación.
Los turnos que cruzan la medianoche se calculan completos (22:00 a 06:00 son 8 h).

**Cuándo una hora es extra**: lo que se pasa de las horas del contrato **en el
día**. Por defecto 7 h, y se cambia en Configuración. Cada trabajador puede tener
las suyas propias.

**Cuánto vale la hora extra** — dos modos:
- **Recargo** sobre la hora normal. 50 % es lo que fija la ley en Chile.
- **Monto fijo** en pesos. Cada trabajador puede tener el suyo propio.

**Valor del día** = horas normales × valor hora + horas extra × valor hora extra.

**Valor de la hora**, si solo se sabe el sueldo: `sueldo / 30 × 7 / horas semanales`.
La calculadora de la pestaña Trabajadores («¿No lo sabes?») lo hace sola. Con
$553.553 y 42 h semanales da $3.075 la hora.

> Los montos son los que se configuren en la aplicación. Es una herramienta de
> control interno: conviene confirmar las cifras con un contador antes de usarlas
> para liquidaciones de sueldo.

---

## El aviso por correo

Cada marcación le manda un correo al trabajador con qué marcó, a qué hora y cómo
va su día. Se enciende en **Configuración** y el correo de cada persona se pone en
**Trabajadores**.

**La cuenta que envía es `marcacion.elbuencorte@gmail.com`**, y viene escrita por
defecto en la aplicación (`CORREO_DEF`, en [escritorio/nucleo.py](escritorio/nucleo.py)).

**La contraseña no está acá ni en el ejecutable.** Gmail pide una *contraseña de
aplicación* (no la de la cuenta, y exige tener activada la verificación en 2 pasos).
Se escribe una sola vez en Configuración, en el PC del local, y queda guardada en
`horas.sqlite3`, que no viaja con el programa. Este repositorio es público: una clave
escrita en el código quedaría a la vista de cualquiera, y GitHub y Google las anulan
solas cuando las detectan.

Como la configuración vive en AppData, la contraseña sobrevive a las
actualizaciones: solo hay que volver a escribirla si se instala en un PC nuevo.

Marcar y avisar están separados: la marca se guarda siempre y el correo queda en una
cola que se vacía en otro hilo ([escritorio/correo.py](escritorio/correo.py)). Sin
internet nadie se queda sin marcar; el aviso sale cuando vuelve la conexión, y
después de 8 intentos deja de insistir y queda a la vista en Configuración.

---

## Dónde quedan los datos

```
C:\Users\TU-USUARIO\AppData\Local\ControlDeHoras\horas.sqlite3
```

Fuera del programa, para que actualizar no borre nada. El botón **Abrir carpeta
de datos**, en Configuración, lleva ahí. Conviene copiar ese archivo a un pendrive
cada cierto tiempo.

---

## Para desarrollar

```bash
pip install -r escritorio/requisitos.txt
python escritorio/app.py
```

| Archivo | Qué es |
|---|---|
| `escritorio/nucleo.py` | Datos (SQLite) y cálculos. Sin interfaz, para poder probarlo solo. |
| `escritorio/app.py` | La ventana, en Tkinter. |
| `escritorio/correo.py` | Manda los avisos de la cola. Separado del núcleo a propósito. |
| `escritorio/informes.py` | Informe mensual en Excel y PDF. |
| `escritorio/instancia.py` | Deja abrir el programa una sola vez. |
| `escritorio/imagen_marca.py` | El logo, generado; no se edita a mano. |
| `escritorio/empaquetado/` | Receta de PyInstaller, script de Inno Setup, ícono y capturas. |

Las pruebas no necesitan Windows ni pantalla, salvo la última:

| Pruebas | Qué cubren |
|---|---|
| `probar_nucleo.py` | 39 · cálculos de horas y de plata |
| `probar_marcas.py` | 70 · las cuatro marcas, el orden y el día laboral |
| `probar_pagos.py` | 69 · pagos, montos congelados y días bloqueados |
| `probar_correo.py` | 61 · la cola de avisos, con un servidor SMTP de mentira |
| `probar_ventana.py` | 108 · arma la ventana entera y revisa sus controles, sin mostrarla |

### Cómo se construye el instalador
`.github/workflows/instalador-windows.yml` lo arma en una máquina Windows de
GitHub Actions. Sirve como banco de pruebas: el desarrollo es en un Mac que no
puede correr esta ventana, así que **todo lo que se promete acá está verificado
en un Windows de verdad antes de publicarse**.

1. Corre las cinco tandas de pruebas.
2. Empaqueta el `.exe` con PyInstaller.
3. Lo llena con datos de ejemplo y **abre la aplicación para fotografiar cada
   pestaña**, la pantalla de carga y el aviso por correo.
4. Comprueba que el `.exe` empaquetado exporta a Excel y a PDF (una vez se
   publicó una versión donde el PDF fallaba solo al estar empaquetado).
5. Lo abre dos veces para comprobar que no se abre una segunda ventana.
6. Construye el instalador con Inno Setup, lo **instala de verdad, abre la app
   instalada y la desinstala**.
7. Publica la descarga.

Las capturas quedan como artefacto de cada compilación.

---

## Versiones anteriores

Antes de llegar a la aplicación de escritorio se probaron otros caminos, que
quedan en el repositorio por si sirven:

| Carpeta | Qué era |
|---|---|
| `local/` | La misma app como página web servida por un Python en un PC del local, con los celulares entrando por WiFi. Funciona, pero depende de que ese PC esté encendido. |
| `nube/` | Versión web para Firebase + GitHub Pages. Necesita crear un proyecto de Firebase. |
| `Codigo.gs` | Un Google Form que alimenta una planilla de cálculo con las fórmulas puestas. Cero mantención, pero sin interfaz propia. |
| `app.html` | La app web original, de donde salen `local/` y `nube/`. |

Ninguna hace falta para usar la aplicación de escritorio.
