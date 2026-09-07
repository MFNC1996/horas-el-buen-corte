# Estado del despliegue

## ✅ Hecho — GitHub Pages

**https://mfnc1996.github.io/horas-el-buen-corte/**

Repositorio: https://github.com/MFNC1996/horas-el-buen-corte
(público, sitio servido desde `main` → `/docs`)

Ya está en línea. Es una CDN de archivos estáticos: no se duerme, no tiene
cold start. Hoy la página carga completa pero avisa que falta la base de datos.

## ⬜ Falta — Firebase

Es lo único pendiente, y es lo único que **no puedo hacer yo**: requiere crear
una cuenta e iniciar sesión con contraseña. Además conviene que el proyecto
quede a nombre del cliente y no mío, porque ahí van a vivir sus datos.

Son unos 10 minutos.

---

## Los 4 pasos

### 1. Crear el proyecto
1. Entra a **https://console.firebase.google.com** con la cuenta de Google
   del cliente (o la tuya, y después la transfieres).
2. **Crear un proyecto** → nombre `el-buen-corte` → puedes desactivar Google
   Analytics, no se usa.

### 2. Crear la base de datos
1. Menú lateral: **Compilación → Firestore Database → Crear base de datos**.
2. Elige **modo de producción**.
   > No elijas modo de prueba: sus reglas caducan a los 30 días y te dejan la
   > app muerta sin aviso, justo cuando el cliente ya confió en ella.
3. Ubicación: **`southamerica-east1`** (São Paulo), la más cercana a Chile.

### 3. Publicar las reglas
**Firestore Database → pestaña Reglas.** Reemplaza todo por esto y dale
**Publicar**:

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

Esto deja la base abierta a cualquiera que tenga el link. Ver «Sobre el
acceso», más abajo.

### 4. Registrar la app web y pasarme las claves
1. **Configuración del proyecto** (el engranaje, arriba a la izquierda) →
   baja hasta **Tus apps** → ícono web **`</>`**.
2. Apodo: `horas`. **No** marques Firebase Hosting.
3. Te muestra un bloque `firebaseConfig` con seis valores.

**Pégamelos en el chat tal cual** y yo los pongo en el archivo y lo publico.

> Estas claves **son públicas por diseño**: viajan en el HTML de cualquier app
> web de Firebase, cualquiera puede verlas con «ver código fuente». No son un
> secreto y no hay problema en pasármelas. Lo que protege los datos son las
> reglas del paso 3, no las claves.

Si prefieres hacerlo tú: en `nube/index.html`, arriba del script, está el
bloque `var FIREBASE = {` con seis `PEGA_AQUI_...` para reemplazar.

---

## Después de eso

1. Abre el link. Ya no debería salir el aviso rojo.
2. **Ajustes** → agrega los tres trabajadores con sus nombres reales.
   La primera vez la lista viene vacía; la app crea todo al primer uso.
3. Confirma los umbrales (vienen en 8 h al día y 45 h a la semana).
4. Carga una jornada de prueba y revisa que salga en **Resumen**.
5. Manda el link por WhatsApp. Que cada uno lo guarde en la pantalla de inicio:
   en Chrome del celular es **⋮ → Agregar a pantalla principal**.

---

## Sobre el acceso

Con esas reglas, **cualquiera que consiga el link puede leer, escribir y borrar**.
Para tres personas en Loncoche con un link que no se publica en ninguna parte,
el riesgo es bajo — pero es real y conviene que sea una decisión tuya, no un
descuido.

Si quieres cerrarlo:

1. **Nada.** La dirección no está indexada. Probablemente suficiente.
2. **Un código en la página.** Rápido, pero detiene al curioso y no a alguien
   que abra el código fuente. No lo presentes como seguridad.
3. **Firebase Authentication.** La forma correcta: cada trabajador entra con su
   correo y las reglas exigen sesión iniciada. Más trabajo, y agrega un login.

Dime si quieres la 2 o la 3 y la implemento.

---

## Actualizar la app más adelante

`nube/index.html` no se edita a mano: se genera desde `app.html`, que es la
fuente única. Después de cambiar `app.html`:

```bash
python3 build-web.py && git add -A && git commit -m "actualiza la app" && git push
```

GitHub Pages republica solo en 1–2 minutos. El script se detiene con un error
si `app.html` cambió tanto que ya no reconoce los bloques que debe reemplazar,
en vez de generar un archivo roto en silencio.

> Ojo: `build-web.py` regenera el archivo **con los `PEGA_AQUI_` de vuelta**.
> Después de correrlo hay que volver a pegar las claves de Firebase.

---

## Si algo falla

| Síntoma | Causa probable |
|---|---|
| «Falta configurar Firebase» | Quedó algún `PEGA_AQUI_` sin reemplazar. |
| «No se pudo conectar con Firebase» | Claves mal copiadas, o sin internet. |
| «Las reglas de Firestore no permiten escribir» | Faltó publicar las reglas del paso 3, o caducaron las de modo prueba. |
| La página carga pero no guarda | Consola del navegador (F12 → Console). |
| El link da 404 | Pages tarda 1–2 min en la primera publicación. |
