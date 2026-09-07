# Poner la app en línea

Objetivo: que los trabajadores abran un link normal desde el celular, sin cuenta
de nada, y que la app esté siempre disponible.

- **Firebase Firestore** guarda los datos. Es un servicio administrado: no hay
  servidor que se duerma ni cold start.
- **GitHub Pages** sirve el archivo. Es una CDN de archivos estáticos: tampoco
  se duerme.

Toma unos 20 minutos la primera vez. Los planes gratuitos cambian, así que
revisa las cuotas vigentes antes de comprometerte con el cliente.

---

## Parte 1 — Firebase (unos 10 minutos)

### 1. Crear el proyecto

1. Entra a **https://console.firebase.google.com** con la cuenta de Google
   del cliente (o la tuya, y después la transfieres).
2. **Crear un proyecto** → nombre: `el-buen-corte` → puedes desactivar Google
   Analytics, no se usa.

### 2. Crear la base de datos

1. En el menú lateral: **Compilación → Firestore Database → Crear base de datos**.
2. Elige **modo de producción** (las reglas las pones tú en el paso 4; el modo
   de prueba caduca a los 30 días y te deja la app muerta sin aviso).
3. Ubicación: `southamerica-east1` (São Paulo) es la más cercana a Chile.

### 3. Registrar la app web y copiar las claves

1. En **Configuración del proyecto** (el engranaje, arriba a la izquierda) baja
   hasta **Tus apps** y elige el ícono web **`</>`**.
2. Apodo: `horas` . **No** marques Firebase Hosting.
3. Te muestra un bloque `firebaseConfig`. Copia esos seis valores.
4. Abre `docs/index.html`, busca arriba el bloque `var FIREBASE = {` y reemplaza
   cada `PEGA_AQUI_...` por el valor correspondiente.

> Estas claves **son públicas por diseño**: viajan en el HTML de cualquier app
> web de Firebase y no son un secreto. Lo que protege los datos son las reglas
> del paso siguiente.

### 4. Reglas de Firestore

**Compilación → Firestore Database → pestaña Reglas.** Reemplaza todo por:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{documento=**} {
      allow read, write: if true;
    }
  }
}
```

**Publicar.**

Esto deja la base abierta a cualquiera que tenga el link — el mismo modelo que
ya tenías, pero expuesto a internet en vez de a tu organización. Para un local
de 3 personas con un link que no se publica en ninguna parte es un riesgo bajo,
pero es un riesgo real: quien consiga la dirección puede leer, escribir y borrar.
Ver «Si quieres cerrarlo más», al final.

---

## Parte 2 — GitHub Pages (unos 10 minutos)

1. Crea una cuenta en **https://github.com** si no tienes.
2. **New repository** → nombre `horas-el-buen-corte` → **Public** → Create.
   (Pages gratis necesita repositorio público. Como las claves de Firebase son
   públicas de todos modos, no cambia nada; lo que importa son las reglas.)
3. **Add file → Upload files** y sube `docs/index.html`. Que quede en la raíz,
   con ese nombre exacto: `index.html`.
4. **Settings → Pages** → en *Source* elige **Deploy from a branch**,
   rama `main`, carpeta `/ (root)` → **Save**.
5. Espera 1–2 minutos. Arriba aparece el link:
   `https://TU-USUARIO.github.io/horas-el-buen-corte/`

Ese es el link que le mandas a los trabajadores.

---

## Parte 3 — Dejarla andando

1. Abre el link. Debería cargar sin el aviso rojo de «Falta configurar Firebase».
2. Ve a **Ajustes** y agrega los tres trabajadores con sus nombres reales.
   La primera vez la lista viene vacía: la app crea todo al primer uso.
3. Confirma los umbrales (vienen en 8 h al día y 45 h a la semana).
4. Carga una jornada de prueba y revisa que aparezca en **Resumen**.
5. Manda el link por WhatsApp. Que cada uno lo guarde en la pantalla de inicio
   del celular: en Chrome es **⋮ → Agregar a pantalla principal**.

---

## Actualizar la app más adelante

`docs/index.html` no se edita a mano: se genera desde `app.html`, que es la
versión que corre como artifact. Después de cambiar `app.html`:

```bash
python3 build-web.py
```

Eso regenera `docs/index.html` con la lógica nueva. Vuelve a pegarle tus claves
de Firebase y súbelo a GitHub reemplazando el anterior.

El script avisa y se detiene si `app.html` cambió tanto que ya no encuentra los
bloques que tiene que reemplazar, en vez de generar un archivo roto en silencio.

---

## Si quieres cerrarlo más

Con las reglas abiertas, cualquiera con la dirección entra. Opciones, de menos
a más trabajo:

1. **No hacer nada.** La dirección no está indexada ni publicada. Para 3 personas
   en Loncoche, probablemente suficiente.
2. **Un código de acceso en la página.** Rápido de agregar, pero honestamente:
   detiene al curioso, no a alguien que sepa mirar el código fuente. No lo
   presentes como seguridad.
3. **Firebase Authentication.** La forma correcta. Cada trabajador entra con su
   correo o con un enlace mágico, y las reglas exigen sesión iniciada. Es la
   única que de verdad cierra la puerta. Es más trabajo y agrega un paso de
   login para los trabajadores.

Si quieres cualquiera de las dos últimas, dime y la implemento.

---

## Si algo falla

| Síntoma | Causa probable |
|---|---|
| Aviso rojo «Falta configurar Firebase» | Quedó algún `PEGA_AQUI_` sin reemplazar. |
| «No se pudo conectar con Firebase» | Claves mal copiadas, o sin internet. |
| «Las reglas de Firestore no permiten escribir» | Faltó publicar las reglas del paso 4, o caducaron las de modo prueba. |
| La página carga pero no guarda nada | Mira la consola del navegador (F12 → Console). |
| GitHub Pages da 404 | El archivo no está en la raíz o no se llama `index.html`. Pages tarda 1–2 min la primera vez. |
