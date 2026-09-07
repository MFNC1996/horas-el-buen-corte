#!/usr/bin/env python3
"""
Deriva nube/index.html (version Firebase + GitHub Pages) desde app.html
(version artifact). Toda la logica, el diseno y las vistas se comparten;
aqui solo se cambia de donde salen los datos y como se baja el CSV.

Uso:  python3 build-web.py
"""
import re, sys, pathlib

RAIZ = pathlib.Path(__file__).parent
src = (RAIZ / "app.html").read_text(encoding="utf-8")

def cambiar(texto, viejo, nuevo, que):
    if viejo not in texto:
        sys.exit("build-web.py: no encontre el bloque '%s' en app.html.\n"
                 "Probablemente app.html cambio; ajusta el script." % que)
    return texto.replace(viejo, nuevo, 1)

# ---------------------------------------------------------------- 1. config
VIEJO_CAB = '''(function(){
"use strict";
'''
NUEVO_CAB = '''(function(){
"use strict";

/* =======================================================================
   CONFIGURACION DE FIREBASE
   Pega aqui el objeto que te da la consola de Firebase en
   Configuracion del proyecto > Tus apps > App web > Configuracion del SDK.
   Estas claves son publicas por diseno: van en el HTML y no son un secreto.
   Lo que protege los datos son las reglas de Firestore, no estas claves.
   ======================================================================= */
var FIREBASE = {
  apiKey:            "PEGA_AQUI_apiKey",
  authDomain:        "PEGA_AQUI_authDomain",
  projectId:         "PEGA_AQUI_projectId",
  storageBucket:     "PEGA_AQUI_storageBucket",
  messagingSenderId: "PEGA_AQUI_messagingSenderId",
  appId:             "PEGA_AQUI_appId"
};
var VERSION_SDK = "10.12.0";

function faltaConfigurar(){
  return String(FIREBASE.projectId || "").indexOf("PEGA_AQUI") === 0;
}
var MSG_SIN_DB = 'No hay conexion con la base de datos: puedes mirar, pero nada se guarda. Recarga la pagina para reintentar.';

/* Descarga del CSV: pagina web normal, sin la capability de artifacts. */
function descargar(nombre, texto){
  try{
    var url = URL.createObjectURL(new Blob([texto], {type:'text/csv;charset=utf-8'}));
    var a = document.createElement('a');
    a.href = url; a.download = nombre;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function(){ URL.revokeObjectURL(url); }, 4000);
  }catch(e){
    alert('No se pudo generar el archivo.');
  }
}
'''
out = cambiar(src, VIEJO_CAB, NUEVO_CAB, "cabecera del script")

# ------------------------------------------------- 2. mensaje de desconexion
out = cambiar(out,
  """  if(!DB){ el.innerHTML='<p class="msg bad" style="margin:16px 0 0">No hay conexion con el almacenamiento: puedes mirar, pero nada se guarda. Recarga la pagina para reintentar.</p>'; return; }""",
  """  if(!DB){ el.innerHTML='<p class="msg bad" style="margin:16px 0 0">'+esc(MSG_SIN_DB)+'</p>'; return; }""",
  "mensaje de desconexion")

# ------------------------------------------- 3. codigos de error de Firestore
out = cambiar(out,
  """    var t = e && e.code==='quota_exceeded' ? 'La base de datos esta llena. Exporta el CSV y borra registros antiguos.'
          : e && e.code==='resource_exhausted' ? 'Demasiadas operaciones seguidas. Espera unos segundos y reintenta.'
          : 'No se pudo guardar. Reintenta en unos segundos.';""",
  """    var c = e && e.code;
    var t = c==='permission-denied' ? 'Las reglas de Firestore no permiten escribir. Revisalas en la consola de Firebase.'
          : c==='resource-exhausted' ? 'Se agoto la cuota diaria de la base de datos. Reintenta manana.'
          : c==='unavailable' ? 'Sin conexion a internet. Reintenta cuando vuelva la senal.'
          : 'No se pudo guardar. Reintenta en unos segundos.';""",
  "codigos de error")

# ------------------------------------------------------- 4. descarga del CSV
out = cambiar(out, "  if(!DL) return;\n  var lista=filtrados(), S=';';",
                   "  var lista=filtrados(), S=';';", "guarda del boton CSV")
out = cambiar(out, "  $('#l-csv').disabled = !lista.length || !DL;",
                   "  $('#l-csv').disabled = !lista.length;", "estado del boton CSV")
out = cambiar(out,
  """  try{ await DL.save({filename:nombre, data:txt}); }
  catch(e){ if(e && e.code!=='declined') alert('No se pudo generar el archivo. Reintenta en unos segundos.'); }""",
  """  descargar(nombre, txt);""", "llamada de descarga")
out = cambiar(out, "$('#l-csv').addEventListener('click', async function(){",
                   "$('#l-csv').addEventListener('click', function(){", "handler del CSV")

# ------------------------------------------------------- 5. arranque Firebase
VIEJO_ARRANQUE = """(async function(){
  try{
    if(window.claude && typeof window.claude.use==='function'){
      DB = await window.claude.use('db');
      try{ DL = await window.claude.use('downloads'); }catch(e2){ DL=null; }
    }
  }catch(e){ DB=null; }
  dbListo=true;
  pintarTodo();
  if(!DB) return;
"""
NUEVO_ARRANQUE = """/* Adaptador: expone sobre Firestore la misma forma de API que usa el resto
   del archivo (doc / collection / set / delete / orderBy / limit / onSnapshot),
   asi la logica de la app queda identica en las dos versiones. */
function adaptar(fs, F){
  function envolverDoc(ruta){
    var ref = F.doc(fs, ruta);
    return {
      path: ruta,
      set:    function(d){ return F.setDoc(ref, d); },
      update: function(d){ return F.updateDoc(ref, d); },
      delete: function(){ return F.deleteDoc(ref); },
      onSnapshot: function(next, err){
        return F.onSnapshot(ref, function(s){
          next({id:s.id, exists:s.exists(), data:function(){return s.data();}});
        }, err);
      }
    };
  }
  function envolverCol(ruta, filtros){
    filtros = filtros || [];
    return {
      path: ruta,
      doc: function(id){ return envolverDoc(ruta+'/'+id); },
      orderBy: function(campo, dir){ return envolverCol(ruta, filtros.concat([F.orderBy(campo, dir||'asc')])); },
      limit:   function(n){ return envolverCol(ruta, filtros.concat([F.limit(n)])); },
      onSnapshot: function(next, err){
        var q = F.query.apply(null, [F.collection(fs, ruta)].concat(filtros));
        return F.onSnapshot(q, function(qs){
          next({
            docs: qs.docs.map(function(s){
              return {id:s.id, exists:true, data:function(){return s.data();}};
            }),
            size: qs.size, empty: qs.empty
          });
        }, err);
      }
    };
  }
  return {doc:envolverDoc, collection:envolverCol};
}

(async function(){
  if(faltaConfigurar()){
    MSG_SIN_DB = 'Falta configurar Firebase: abre index.html y pega tus claves en el bloque FIREBASE, arriba del script.';
    dbListo=true; pintarTodo(); return;
  }
  try{
    var base = "https://www.gstatic.com/firebasejs/"+VERSION_SDK+"/";
    var appMod = await import(base+"firebase-app.js");
    var F      = await import(base+"firebase-firestore.js");
    DB = adaptar(F.getFirestore(appMod.initializeApp(FIREBASE)), F);
  }catch(e){
    DB=null;
    MSG_SIN_DB = 'No se pudo conectar con Firebase. Revisa tu conexion a internet y las claves del bloque FIREBASE.';
  }
  dbListo=true;
  pintarTodo();
  if(!DB) return;
"""
out = cambiar(out, VIEJO_ARRANQUE, NUEVO_ARRANQUE, "arranque")

# ---------------------------------------- 6. documento HTML completo y titulo
out = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
       '<meta name="theme-color" content="#B4141F">\n'
       '<link rel="icon" href="data:image/svg+xml,'
       '%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22%3E'
       '%3Ctext y=%22.9em%22 font-size=%2290%22%3E%F0%9F%94%AA%3C/text%3E%3C/svg%3E">\n'
       + out.replace('<title>', '<title>', 1)
       + '\n</body>\n</html>\n')
out = out.replace('</style>', '</style>\n</head>\n<body>', 1)

destino = RAIZ / "nube"
destino.mkdir(exist_ok=True)
(destino / "index.html").write_text(out, encoding="utf-8")
print("nube/index.html generado: %d bytes" % len(out.encode("utf-8")))
