# Instalar el control de horas en el computador del local

La app corre en un computador de la carnicería y los celulares entran por el
WiFi. No depende de ningún servicio externo ni de ninguna cuenta.

## Lo que necesitas

- Un computador que quede **encendido** en el local (Mac o Windows).
- **Python 3**. En Mac ya viene instalado. En Windows se baja de
  [python.org](https://www.python.org/downloads/) y al instalarlo hay que
  marcar la casilla **«Add Python to PATH»**.
- Que los celulares estén en la **misma red WiFi**.

## Instalación

1. Descarga el proyecto y descomprímelo en el computador del local.
2. Entra a la carpeta `local`.
3. Doble clic en:
   - **Mac:** `instalar-mac.command`
   - **Windows:** `instalar-windows.bat`

Eso deja el servidor encendido y configurado para arrancar solo.

> En Mac, la primera vez macOS puede bloquearlo por venir de internet.
> Clic derecho sobre el archivo → **Abrir** → **Abrir** de nuevo.

4. Te va a mostrar dos direcciones:

```
En este computador:      http://localhost:8080
Desde los celulares:     http://192.168.1.50:8080
Direccion estable:       http://elbuencorte.local:8080
```

**Manda la «dirección estable» por WhatsApp.** Esa no cambia aunque el router
le cambie la IP al computador. Si en algún celular no funciona, usa la de los
números.

5. Que cada uno la guarde en la pantalla de inicio del celular:
   en Chrome es **⋮ → Agregar a pantalla principal**.

## Dejarlo listo para usar

1. Abre la dirección y ve a **Ajustes**.
2. Cambia «Trabajador 1/2/3» por los nombres reales.
3. Confirma los umbrales (vienen en 8 h al día y 45 h a la semana).
4. Carga una jornada de prueba y revisa que salga en **Resumen**.

---

## Que esté siempre disponible

El instalador ya deja hecho lo que se puede hacer por software:

- **Arranca solo** cada vez que se enciende el computador.
- **Se levanta solo** si el servidor se cae.
- En Mac, **impide que el equipo se suspenda** mientras corre.
- **Respalda la base de datos** todos los días en `local/respaldos/`,
  y conserva los últimos 30 días.

Quedan dos cosas que hay que hacer a mano una sola vez, porque son ajustes del
sistema operativo:

**Que el computador inicie sesión solo al encenderse.** Si no, después de un
corte de luz se queda esperando la contraseña y la app no vuelve.

- Mac: Configuración del sistema → Usuarios y grupos → Inicio de sesión
  automático.
- Windows: escribe `netplwiz` en el buscador y desmarca «Los usuarios deben
  escribir su nombre y contraseña».

**Que no se suspenda.** La pantalla puede apagarse, el equipo no.

- Mac: Configuración del sistema → Bloqueo de pantalla y Energía.
- Windows: Configuración → Sistema → Inicio/apagado → Suspensión: **Nunca**.

### Lo que esto no resuelve

Con todo lo anterior, la app está disponible siempre que el computador tenga
luz y esté en la red. **Si se corta la luz o alguien apaga el equipo, la app se
cae hasta que vuelva a encenderse** — con el arranque automático, sola.

Si el local tiene cortes seguidos, lo que de verdad lo resuelve es un UPS
(una batería de respaldo) para el computador y el router. Sale bastante menos
que un mes de servidor en la nube.

La otra opción es moverla a la nube, y ahí sí queda independiente del local.
Eso pide crear una cuenta de Firebase; está todo escrito y listo en
[`nube/`](nube/) y en [DESPLIEGUE.md](DESPLIEGUE.md) para cuando lo quieras.

---

## Uso diario

No hay que hacer nada. El servidor queda corriendo solo.

**Respaldos.** Cada día se guarda una copia en `local/respaldos/`. De vez en
cuando conviene copiar esa carpeta a un pendrive o al Drive: si se echa a
perder el disco del computador, es lo único que salva los datos.

También puedes exportar el CSV desde la pestaña **Registros** cuando quieras;
sale con `;` y coma decimal, listo para Excel en Chile.

## Sobre el acceso

Cualquiera conectado al WiFi del local que sepa la dirección puede entrar y
editar. Como está en la red interna y no en internet, nadie de afuera llega.
Para una carnicería de tres personas es razonable; si quieres que cada
trabajador tenga clave, se puede agregar.

---

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| «Se perdió la conexión con el computador del local» | Revisa que el celular esté en el WiFi de la carnicería y que el computador esté encendido. |
| La dirección `.local` no funciona en un celular | Usa la de números (`http://192.168.x.x:8080`). |
| Cambió la dirección de números | Usa la `.local`, o pide en el router una reserva de IP para ese computador. |
| No abre en el propio computador | Abre `local/registro/salida.log` y mira el error. |
| «No encontré Python» | Instálalo desde python.org. En Windows marca «Add Python to PATH». |
| Quiero apagarlo | Mac: `desinstalar-mac.command`. Windows: borra `ControlDeHoras.vbs` de la carpeta que se abre escribiendo `shell:startup`. |

## Para quien mantenga el código

`local/index.html` no se edita a mano: se genera desde `app.html`, que es la
fuente única de las tres versiones.

```bash
python3 build-local.py   # -> local/index.html  (servidor del local)
python3 build-web.py     # -> nube/index.html   (Firebase, opcional)
```

Los dos scripts se detienen con un error si `app.html` cambió tanto que ya no
reconocen los bloques que deben reemplazar, en vez de generar un archivo roto
en silencio.
