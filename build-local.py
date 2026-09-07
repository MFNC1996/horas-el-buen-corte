#!/usr/bin/env python3
"""
Deriva local/index.html (version para el servidor del local) desde app.html.

La logica de calculo, el diseno y las vistas se comparten con app.html.
Aqui solo cambia de donde salen los datos: en vez de la base del artifact,
se habla con servidor.py por HTTP.

Uso:  python3 build-local.py
"""
import sys, pathlib

RAIZ = pathlib.Path(__file__).parent
src = (RAIZ / "app.html").read_text(encoding="utf-8")

def cambiar(texto, viejo, nuevo, que):
    if viejo not in texto:
        sys.exit("build-local.py: no encontre el bloque '%s' en app.html.\n"
                 "app.html cambio; hay que ajustar este script." % que)
    return texto.replace(viejo, nuevo, 1)

# ------------------------------------------------------------- 1. encabezado
out = cambiar(src, '(function(){\n"use strict";\n', '''(function(){
"use strict";

var sinRed = false;

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
''', "encabezado")

# ------------------------------------------------- 2. aviso de estado de red
out = cambiar(out, """function banner(){
  var el=$('#conn');
  if(!dbListo){ el.innerHTML='<p class="msg bad" style="margin:16px 0 0">Conectando con el almacenamiento&hellip;</p>'; return; }
  if(!DB){ el.innerHTML='<p class="msg bad" style="margin:16px 0 0">No hay conexion con el almacenamiento: puedes mirar, pero nada se guarda. Recarga la pagina para reintentar.</p>'; return; }
  el.innerHTML='';
}""", """function banner(){
  var el=$('#conn');
  if(!dbListo){ el.innerHTML='<p class="msg bad" style="margin:16px 0 0">Conectando con el servidor&hellip;</p>'; return; }
  if(sinRed){ el.innerHTML='<p class="msg bad" style="margin:16px 0 0">Se perdio la conexion con el computador del local. Revisa que estes en el WiFi de la carniceria y que el servidor este encendido. Lo que cargues ahora no se va a guardar.</p>'; return; }
  el.innerHTML='';
}""", "banner")

# ---------------------------------------------------- 3. mensajes de error
out = cambiar(out, """    var t = e && e.code==='quota_exceeded' ? 'La base de datos esta llena. Exporta el CSV y borra registros antiguos.'
          : e && e.code==='resource_exhausted' ? 'Demasiadas operaciones seguidas. Espera unos segundos y reintenta.'
          : 'No se pudo guardar. Reintenta en unos segundos.';""",
"""    var t = (e && e.code==='servidor')
          ? 'El servidor rechazo el dato. Avisa a quien mantiene la app.'
          : 'No se pudo guardar: sin conexion con el computador del local. Revisa el WiFi y reintenta.';""",
"mensajes de error")

# ------------------------------------------------------ 4. descarga del CSV
out = cambiar(out, "  if(!DL) return;\n  var lista=filtrados(), S=';';",
                   "  var lista=filtrados(), S=';';", "guarda del boton CSV")
out = cambiar(out, "  $('#l-csv').disabled = !lista.length || !DL;",
                   "  $('#l-csv').disabled = !lista.length;", "estado del boton CSV")
out = cambiar(out, """  try{ await DL.save({filename:nombre, data:txt}); }
  catch(e){ if(e && e.code!=='declined') alert('No se pudo generar el archivo. Reintenta en unos segundos.'); }""",
                   "  descargar(nombre, txt);", "llamada de descarga")
out = cambiar(out, "$('#l-csv').addEventListener('click', async function(){",
                   "$('#l-csv').addEventListener('click', function(){", "handler del CSV")

# ------------------------------- 5. sin el tope de documentos del artifact
out = cambiar(out, """  $('#a-cap').innerHTML='Hay <strong>'+n+'</strong> jornadas guardadas.'
    + (n>900 ? ' Se acerca al limite de almacenamiento: exporta el CSV desde Registros y borra las mas antiguas.' : '');""",
"""  $('#a-cap').innerHTML='Hay <strong>'+n+'</strong> jornadas guardadas en el computador del local. '
    + 'El servidor deja una copia de respaldo cada dia en la carpeta respaldos/.';""",
"aviso de capacidad")
out = cambiar(out, ".limit(1000)", ".limit(5000)", "tope de registros")

# --------------------------------------------------------- 6. capa de datos
out = cambiar(out, """(async function(){
  try{
    if(window.claude && typeof window.claude.use==='function'){
      DB = await window.claude.use('db');
      try{ DL = await window.claude.use('downloads'); }catch(e2){ DL=null; }
    }
  }catch(e){ DB=null; }
  dbListo=true;
  pintarTodo();
  if(!DB) return;
""", """/* Adaptador local: expone la misma forma de API que usa el resto del archivo
   (doc / collection / set / update / delete / orderBy / limit / onSnapshot),
   pero hablando con servidor.py. Se mantiene al dia sondeando cada 3 segundos;
   el servidor responde "sinCambios" cuando no hay nada nuevo, asi que el
   trafico real solo ocurre cuando alguien carga o edita una jornada. */
function adaptarLocal(){
  var cache={}, version=-1, docOyentes=[], colOyentes=[], fallas=0;

  function emitirDoc(o){
    var d=cache[o.ruta];
    o.cb({id:o.ruta.split('/').pop(), exists:d!==undefined, data:function(){return d;}});
  }
  function emitirCol(o){
    var docs=Object.keys(cache).filter(function(k){
      var p=k.split('/'); return p.slice(0,-1).join('/')===o.ruta;
    }).map(function(k){
      return {id:k.split('/').pop(), exists:true, data:function(){return cache[k];}};
    });
    if(o.orden){
      var f=o.orden.campo, dir=o.orden.dir==='desc'?-1:1;
      docs.sort(function(a,b){
        var x=a.data()[f], y=b.data()[f];
        return (x<y?-1:x>y?1:0)*dir;
      });
    }else{
      docs.sort(function(a,b){return a.id<b.id?-1:a.id>b.id?1:0;});
    }
    if(o.lim) docs=docs.slice(0,o.lim);
    o.cb({docs:docs, size:docs.length, empty:!docs.length});
  }
  function emitirTodo(){ docOyentes.forEach(emitirDoc); colOyentes.forEach(emitirCol); }

  function sondear(){
    return fetch('/api/docs?version='+version, {cache:'no-store'})
      .then(function(r){ if(!r.ok) throw new Error('http '+r.status); return r.json(); })
      .then(function(d){
        if(sinRed){ sinRed=false; banner(); }
        fallas=0;
        if(d.sinCambios) return;
        version=d.version; cache=d.docs||{}; emitirTodo();
      })
      .catch(function(err){
        fallas++;
        if(fallas>=2 && !sinRed){ sinRed=true; banner(); }
        throw err;
      });
  }
  function escribir(url, cuerpo){
    return fetch(url, {method:'POST', headers:{'Content-Type':'application/json'},
                       body:JSON.stringify(cuerpo)})
      .then(function(r){
        if(!r.ok){ var e=new Error('http '+r.status); e.code='servidor'; throw e; }
        return sondear();
      });
  }
  function envolverDoc(ruta){
    return {
      path: ruta,
      set:    function(d){ return escribir('/api/set', {ruta:ruta, datos:d}); },
      update: function(d){
        var actual=cache[ruta]||{}, nuevo={};
        Object.keys(actual).forEach(function(k){ nuevo[k]=actual[k]; });
        Object.keys(d).forEach(function(k){ nuevo[k]=d[k]; });
        return escribir('/api/set', {ruta:ruta, datos:nuevo});
      },
      delete: function(){ return escribir('/api/borrar', {ruta:ruta}); },
      onSnapshot: function(next){
        var o={ruta:ruta, cb:next};
        docOyentes.push(o);
        if(version>=0) emitirDoc(o);
        return function(){ docOyentes=docOyentes.filter(function(x){return x!==o;}); };
      }
    };
  }
  function envolverCol(ruta, orden, lim){
    return {
      path: ruta,
      doc:     function(id){ return envolverDoc(ruta+'/'+id); },
      orderBy: function(campo, dir){ return envolverCol(ruta, {campo:campo, dir:dir||'asc'}, lim); },
      limit:   function(n){ return envolverCol(ruta, orden, n); },
      onSnapshot: function(next){
        var o={ruta:ruta, orden:orden, lim:lim, cb:next};
        colOyentes.push(o);
        if(version>=0) emitirCol(o);
        return function(){ colOyentes=colOyentes.filter(function(x){return x!==o;}); };
      }
    };
  }
  setInterval(function(){ sondear().catch(function(){}); }, 3000);
  return {doc:envolverDoc, collection:envolverCol, primerSondeo:sondear};
}

(async function(){
  DB = adaptarLocal();
  try{ await DB.primerSondeo(); }catch(e){}
  dbListo=true;
  pintarTodo();
""", "capa de datos")

# ------------------------------------------------- 7. documento HTML completo
out = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
       '<meta name="theme-color" content="#B4141F">\n'
       '<link rel="icon" href="data:image/svg+xml,'
       '%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22%3E'
       '%3Ctext y=%22.9em%22 font-size=%2290%22%3E%F0%9F%94%AA%3C/text%3E%3C/svg%3E">\n'
       + out + '\n</body>\n</html>\n')
out = out.replace('</style>', '</style>\n</head>\n<body>', 1)

destino = RAIZ / "local"
destino.mkdir(exist_ok=True)
(destino / "index.html").write_text(out, encoding="utf-8")
print("local/index.html generado: %d bytes" % len(out.encode("utf-8")))
