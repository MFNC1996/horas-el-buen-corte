# Camino a la autorización de la Dirección del Trabajo

Qué exige la ley chilena para que el Control de Horas pueda ser el registro
**oficial** de asistencia de un local, qué le falta hoy, y qué hay que construir.

Fuente: **Resolución Exenta N° 38, de 26 de abril de 2024**, de la Dirección del
Trabajo, publicada en el Diario Oficial el 9 de mayo de 2024
([texto oficial](https://www.diariooficial.interior.gob.cl/publicaciones/2024/05/09/43846/01/2489163.pdf)
· [Ley Chile](https://www.bcn.cl/leychile/navegar?idNorma=1203415)). Dicta las
condiciones del nuevo inciso 2° del artículo 33 del Código del Trabajo, vigente
desde el 26 de abril de 2024 por la Ley 21.561 (40 horas). Son 73 artículos.

---

## Lo primero, porque cambia todo

**Un sistema electrónico de asistencia no se puede usar sin autorización previa
de la Dirección del Trabajo** (art. 1 y 33 inc. 2 del Código del Trabajo). Usar
uno sin autorizar no es un vacío legal: es tener por no cumplida la obligación
de llevar registro de asistencia, y eso se cursa como infracción al empleador.

Tres cosas que conviene tener claras antes de invertir una hora más:

1. **La autorización es del SISTEMA, no del local** (arts. 3 a, 63 y 72). Una
   vez autorizado, *cualquier* empleador puede usarlo sin pedir permiso propio.
   Para vender el software esto es la mejor noticia del documento: se tramita
   una vez y habilita a todos los clientes que vengan después.
2. **Caduca a los dos años** (art. 69) y la certificación se repite cada 24
   meses (art. 65 d). No es un trámite de una vez.
3. **Hacerlo uno mismo no exime de nada.** El art. 30 dice expresamente que el
   empleador que desarrolla su propio sistema, o se lo encarga a un tercero,
   queda sujeto a todas las reglas igual.

### Mientras tanto, qué puede hacer el local legalmente

El artículo 33 inciso 1° sigue permitiendo el **libro de asistencia en papel**,
que no necesita autorización de nadie. Lo correcto hoy es: el libro de papel
como registro oficial, y el Control de Horas como herramienta interna de
cálculo y pago. No al revés.

---

## Qué exige la resolución, y cómo estamos

Leyenda: ✅ ya está · 🟡 falta parte · ❌ no existe · 🧱 requiere otra arquitectura

### Identificación del trabajador

| Art. | Exigencia | Estado |
|---|---|---|
| 7 a–c | Enrolamiento e identificación por un medio que distinga a una persona de otra | ❌ hoy solo se toca un nombre en pantalla: eso no identifica a nadie |
| 7 g | **Dos medios distintos** de identificación, uno principal y otro de respaldo; al menos uno sin biometría ni datos personales (clave, patrón, tarjeta) | ❌ |
| 7 f | Si se usan claves, el trabajador debe poder cambiarla cuando quiera, y recibir un correo automático con el resultado | ❌ |
| 13.1 d | RUT del trabajador con puntos, guión y dígito verificador | ❌ no se pide el RUT |

### La marcación

| Art. | Exigencia | Estado |
|---|---|---|
| 35, 36 a | Acto voluntario y consciente; el trabajador sabe de antemano qué acción genera una marca | ✅ |
| 36 c | Marcas repetidas seguidas: se conserva la primera y se eliminan las siguientes | ❌ |
| 37 | Marcas automáticas encadenadas (al terminar colación, empieza jornada) | ✅ equivalente |
| 38 | Prohibido bloquear el equipo o la aplicación para impedir marcar | ✅ |
| 11 | Sello de tiempo electrónico | 🟡 se guarda fecha y hora, falta formalizarlo |
| 44 | Cálculo con **precisión de hora, minuto y segundo**, sin aproximar | ❌ hoy las marcas se guardan en HH:MM |
| 8 | **Hash o checksum SHA-2 por cada marcación**, con funciones nativas, más una página web que permita verificar un comprobante con ese hash | ❌ |
| 9, 10 | Transmisión automática en línea a una base de datos central; la captura sin conexión solo se acepta como excepción justificada | 🧱 |

### El comprobante al trabajador

| Art. | Exigencia | Estado |
|---|---|---|
| 12 a–d | Comprobante automático de **cada** marcación, por correo, en formato imprimible, desde una cuenta de sistema no nominativa | ✅ esto ya lo hace la versión 1.8.1 |
| 12 e | Que no existan dos trabajadores con el mismo correo | ❌ |
| 13.1 | Contenido: fecha dd/mm/aa, hora hh:mm:ss, nombre completo, RUT, hash | 🟡 falta RUT, segundos y hash |
| 13.2 | Datos del empleador: razón social, RUT, y dirección exacta del lugar de la marcación (calle, número, comuna, ciudad, región) | ❌ |
| 34 | Cada trabajador debe tener correo registrado; no sirve SMS | 🟡 existe el campo, falta hacerlo obligatorio |

### Corrección de marcas

| Art. | Exigencia | Estado |
|---|---|---|
| 39 | El empleador solo puede modificar, agregar o corregir en los casos tasados | 🟡 |
| 40 | Toda corrección dispara un **correo al trabajador** con la hora original y la nueva, y él tiene **48 horas para oponerse**. Si se opone, la marca vuelve a su estado original | ❌ |
| 41 a | Toda alteración queda **visible en pantalla** con un signo o color | ❌ |
| 41 b | Ninguna corrección puede perjudicar al trabajador | ❌ |
| 14 a–b | Base de datos que impida la adulteración posterior al registro; respaldos con hash que delaten cualquier alteración | ❌ |

### Alertas obligatorias

| Art. | Exigencia | Estado |
|---|---|---|
| 45.1 | Correo automático al trabajador, con copia al empleador, a los **30 minutos** de no haberse marcado un inicio o un término. Vienen activadas de fábrica y se pueden desactivar | ❌ |
| 45.2 | Aviso en pantalla si la jornada cargada excede los límites legales | ❌ |
| 45.3 | Cada 30 días, correo con horas compensables y días acumulados, si se pactó compensar con descanso | ❌ |

### Portal de fiscalización y accesos — lo que no cabe en un programa de escritorio

| Art. | Exigencia | Estado |
|---|---|---|
| 17 | Sitio web público `https://www.nombre.cl`, con enlace visible en la portada, TLS 1.2 o superior, certificado SSL vigente de entidad acreditada, **24/7** | 🧱 |
| 23 | Ingreso del fiscalizador escribiendo su correo **@dt.gob.cl**: el sistema reconoce el dominio y le manda una clave que dura 5 días | 🧱 |
| 24 | Buscador de empleadores, y correo automático al empleador avisando que empezó una fiscalización | 🧱 |
| 25, 27 | Seis reportes con nombres y columnas **exactos**, con filtros por trabajador, grupo, período, rango de 5 años, jornada, turnos y sucursal | 🧱 |
| 22.1 | Perfil del trabajador con acceso permanente a sus registros, desde cualquier lugar y hora, **5 años** hacia atrás | 🧱 |
| 20 d–e | Base de datos y aplicación **en más de un servidor o datacenter**, replicadas y respaldadas afuera | 🧱 |
| 16 | Disponibilidad permanente, con redundancia y monitoreo | 🧱 |

---

## La conclusión incómoda

**El Control de Horas, tal como está, no puede ser autorizado.** No es cosa de
agregarle campos: la resolución exige un servicio web permanente, con base de
datos central replicada, portal para la Dirección del Trabajo y acceso del
trabajador desde cualquier parte. Un programa que vive en el computador del
local no cumple eso ni cumpliéndolo todo lo demás.

Lo que sí sirve, y mucho, es lo que ya está construido: las reglas de
marcación, el cálculo, los informes, los correos y la disciplina de pruebas.
Eso es el núcleo. Lo que falta es ponerle un servidor arriba.

### La arquitectura que sí se puede autorizar

```
  Local (Windows)                  Servidor en Chile (HTTPS, dominio .cl)
  ┌──────────────────┐             ┌────────────────────────────────────┐
  │ Terminal de      │  marca +    │  API              Base de datos    │
  │ marcación        │─ hash ─────▶│  central          replicada        │
  │ (lo que ya está) │  en línea   │                                    │
  │ guarda y reenvía │             │  Portal trabajador (5 años)        │
  │ si se cae el net │             │  Portal fiscalización @dt.gob.cl   │
  └──────────────────┘             │  Verificador de hash público       │
                                   └────────────────────────────────────┘
```

El programa de escritorio pasa a ser el **terminal**: identifica, marca, firma
con hash y envía. Todo lo que la Dirección del Trabajo quiere mirar vive en el
servidor.

### Lo que cuesta, en plata y en tiempo

| Ítem | Quién | Nota |
|---|---|---|
| Desarrollo del backend, los dos portales y los seis reportes | nosotros | es el grueso |
| Certificación por empresa independiente (arts. 64, 65) | [BizPartners](https://www.bizpartners.cl/certificacion-de-aplicaciones-de-registro-y-control-de-asistencia/), [Veltec](https://www.veltec.cl/landing/), [Neosoltec](https://www.neosoltec.cl/servicios/certificacion-de-sistemas-de-control-de-asistencia/) | hay que cotizar; incluye análisis de vulnerabilidades y **se repite cada 24 meses** |
| Informe de vulnerabilidades y diagrama de arquitectura (art. 66.2) | nosotros + certificadora | |
| Dominio .cl, certificado SSL, hosting redundante 24/7 | nosotros | costo mensual permanente |
| Tramitación ante el Departamento Jurídico de la DT (arts. 66–69) | nosotros | respuesta por Oficio ordinario |

La certificación y el hosting no se pagan una vez: son permanentes. **Para un
local de tres trabajadores, este gasto no se justifica.** Se justifica solo si
el sistema se va a vender a varios empleadores, porque la autorización es del
sistema y sirve para todos (art. 72).

---

## Plan de trabajo

### Etapa 1 — lo que hay que hacer igual, sea cual sea la arquitectura

Son cambios al núcleo que la resolución exige y que no dependen del servidor.
Se pueden hacer ahora y dejan el programa mejor aunque el trámite no siga.

1. **Segundos en las marcas** (art. 44). Cambia el formato de `hora` y todo el
   cálculo.
2. **RUT del trabajador**, con validación de dígito verificador y formato con
   puntos y guión (art. 13.1 d).
3. **Datos del empleador**: razón social, RUT y dirección del lugar de trabajo,
   con comuna, ciudad y región (art. 13.2).
4. **Hash SHA-256 por marcación**, guardado junto a la marca (art. 8).
5. **Comprobante con el contenido exacto del art. 13**, reemplazando el correo
   actual.
6. **Bitácora inalterable**: toda corrección queda registrada con su antes y
   después, y se muestra marcada en pantalla (art. 41 a).
7. **Identificación con clave por trabajador**, con cambio de clave y correo de
   aviso (art. 7 f, g).
8. **Correo obligatorio y único** por trabajador (art. 12 e, 34).
9. **Alertas de marcación faltante a los 30 minutos** (art. 45.1), activadas de
   fábrica y desactivables.

### Etapa 2 — el servidor

10. API de recepción de marcas con reenvío desde el terminal.
11. Portal del trabajador, 5 años de historia.
12. Portal de fiscalización con el ingreso por correo @dt.gob.cl.
13. Los seis reportes del art. 27, con los nombres y columnas exactos.
14. Verificador público de comprobantes por hash (art. 8).
15. Redundancia, respaldos externos y monitoreo (arts. 16, 20).

### Etapa 3 — el trámite

16. Diagrama de arquitectura e informe de vulnerabilidades.
17. Certificación con empresa independiente.
18. Carta conductora y antecedentes al Departamento Jurídico (art. 66).

---

## Advertencia

Esto es un análisis técnico de la resolución, hecho leyendo su texto oficial.
No es asesoría legal. Antes de presentar la solicitud conviene que un abogado
laboralista revise la carta conductora y el informe, y que la empresa
certificadora confirme el alcance: es ella la que firma que el sistema cumple.
