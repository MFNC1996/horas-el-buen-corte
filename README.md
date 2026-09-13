# Control de Horas — Carnicería El Buen Corte

Aplicación de escritorio para Windows: lleva las horas trabajadas de los
trabajadores del local y genera el informe mensual para imprimir.

### Descargar

**https://mfnc1996.github.io/horas-el-buen-corte/**

O directo: [ControlDeHoras-Setup.exe](https://github.com/MFNC1996/horas-el-buen-corte/releases/latest/download/ControlDeHoras-Setup.exe) (~18 MB)

Doble clic y sigue el asistente. No necesita internet, ni servidor, ni instalar
Python. Windows va a mostrar el aviso «Windows protegió tu PC» porque el
instalador no está firmado con un certificado de pago: **Más información →
Ejecutar de todas formas**.

---

## Qué hace

| Pestaña | Para qué |
|---|---|
| **Jornadas** | Cargar entrada, salida y colación de cada día. |
| **Resumen del mes** | El cuadro con horas, horas extra y lo que se paga. Exporta a Excel y PDF. |
| **Trabajadores** | Nombres y valor de la hora. |
| **Configuración** | Umbrales de horas extra y cuánto vale la hora extra. |

### Cargar la hora rápido
El botón **Ahora** pone la hora actual redondeada a 5 minutos, **−15/+15** ajustan
de a cuarto de hora, y los botones con horas ponen las más usadas. Abajo se ve al
instante cuántas horas son y si hay extra, antes de guardar.

### El informe mensual
Excel y PDF, listos para imprimir. Traen, por trabajador: turnos trabajados,
horas, colación descontada, horas ordinarias, horas extra, valor de cada hora,
y lo pagado. Más el detalle día por día.

---

## Cálculos

**Horas trabajadas** = salida − entrada − colación.
Los turnos que cruzan la medianoche se calculan completos (22:00 a 06:00 son 8 h).

**Cuándo una hora es extra** — tres reglas, se elige en Configuración:
- **Diaria**: lo que pasa del umbral de cada día (por defecto 8 h).
- **Semanal**: lo que pasa del umbral de la semana, de lunes a domingo (45 h).
- **La mayor de las dos.**

**Cuánto vale la hora extra** — dos modos:
- **Recargo** sobre la hora normal. 50 % es lo que fija la ley en Chile.
- **Monto fijo** en pesos. Cada trabajador puede tener el suyo propio.

Las horas extra de las reglas semanales se reparten entre los meses que toca cada
semana, en proporción a las horas de cada mes. Así horas ordinarias + horas extra
siempre suman las horas del mes, que es lo que tiene que cuadrar en una liquidación.

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
| `escritorio/informes.py` | Informe mensual en Excel y PDF. |
| `escritorio/probar_nucleo.py` | 37 pruebas de los cálculos y la plata. |
| `escritorio/probar_ventana.py` | Arma la ventana entera y revisa sus controles, sin mostrarla. |
| `escritorio/empaquetado/` | Receta de PyInstaller, script de Inno Setup e ícono. |

### Cómo se construye el instalador
`.github/workflows/instalador-windows.yml` lo arma en una máquina Windows de
GitHub Actions: corre las pruebas, empaqueta el `.exe` con PyInstaller, **abre la
aplicación y le saca capturas a las cuatro pestañas** (para poder revisar la
interfaz sin tener un Windows a mano), construye el instalador con Inno Setup y
publica la descarga.

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
