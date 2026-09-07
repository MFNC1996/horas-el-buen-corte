/**
 * HoraRio - Control de horas trabajadas
 * -------------------------------------
 * Ejecuta UNA sola vez la funcion  crearSistema()  desde el editor de
 * Apps Script (script.google.com > Nuevo proyecto > pegar este archivo).
 *
 * Crea en tu Google Drive:
 *   1. Un Formulario de Google para registrar entrada/salida.
 *   2. Una Planilla de calculo enlazada al formulario, con:
 *        - Hoja "Registros"  : respuestas + horas trabajadas + horas extra (auto)
 *        - Hoja "Resumen"    : totales por semana y trabajador
 *        - Hoja "Panel"      : totales del mes por trabajador
 *        - Hoja "Config"     : umbrales y lista de trabajadores (editable)
 *
 * Al terminar imprime en el registro (Ver > Registros) los links del
 * formulario y de la planilla.
 */

// ---------------------------------------------------------------------------
// AJUSTA ESTO ANTES DE EJECUTAR (igual se puede cambiar despues en la hoja Config)
// ---------------------------------------------------------------------------
var CONFIG_INICIAL = {
  nombreProyecto: 'Control de Horas',
  trabajadores: ['Trabajador 1', 'Trabajador 2', 'Trabajador 3'],
  umbralDiario: 8,          // horas por dia antes de contar extra
  umbralSemanal: 45,        // horas por semana antes de contar extra
  regla: 'Diaria',          // 'Diaria' | 'Semanal' | 'Mayor de ambas'
  opcionesColacion: ['0', '30', '45', '60'],  // minutos descontados
  zonaHoraria: 'America/Santiago',
  locale: 'es_CL'
};

// ---------------------------------------------------------------------------

function crearSistema() {
  var cfg = CONFIG_INICIAL;

  // 1. Planilla -------------------------------------------------------------
  var ss = SpreadsheetApp.create(cfg.nombreProyecto);
  ss.setSpreadsheetTimeZone(cfg.zonaHoraria);
  ss.setSpreadsheetLocale(cfg.locale);

  crearHojaConfig(ss, cfg);

  // 2. Formulario -----------------------------------------------------------
  var form = FormApp.create(cfg.nombreProyecto + ' - Registro de jornada');
  form.setDescription('Registra una fila por trabajador y por dia trabajado.')
      .setCollectEmail(false)
      .setAllowResponseEdits(true)
      .setProgressBar(false)
      .setConfirmationMessage('Registro guardado. Puedes cargar otro.')
      .setShowLinkToRespondAgain(true);

  form.addListItem()
      .setTitle('Trabajador')
      .setChoiceValues(cfg.trabajadores)
      .setRequired(true);

  form.addDateItem()
      .setTitle('Fecha')
      .setIncludesYear(true)
      .setRequired(true);

  form.addTimeItem().setTitle('Hora de entrada').setRequired(true);
  form.addTimeItem().setTitle('Hora de salida').setRequired(true);

  form.addListItem()
      .setTitle('Minutos de colacion')
      .setHelpText('Tiempo NO pagado que se descuenta de la jornada.')
      .setChoiceValues(cfg.opcionesColacion)
      .setRequired(true);

  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  // 3. Hoja de respuestas ---------------------------------------------------
  SpreadsheetApp.flush();
  var registros = esperarHojaRespuestas(ss);
  registros.setName('Registros');
  prepararRegistros(registros);

  // 4. Resto de hojas -------------------------------------------------------
  crearHojaResumen(ss);
  crearHojaPanel(ss, cfg);

  // Borra la hoja vacia que Google crea por defecto
  borrarHojaPorDefecto(ss);

  ss.setActiveSheet(ss.getSheetByName('Panel'));

  Logger.log('LISTO.');
  Logger.log('Formulario (para los trabajadores): ' + form.getPublishedUrl());
  Logger.log('Editar formulario:                  ' + form.getEditUrl());
  Logger.log('Planilla (para el dueno):           ' + ss.getUrl());
}

// ---------------------------------------------------------------------------

function borrarHojaPorDefecto(ss) {
  var propias = ['Registros', 'Resumen', 'Panel', 'Config'];
  var hojas = ss.getSheets();
  for (var i = 0; i < hojas.length; i++) {
    var h = hojas[i];
    if (propias.indexOf(h.getName()) !== -1) continue;
    if (h.getFormUrl()) continue;
    if (h.getLastRow() > 0 || h.getLastColumn() > 0) continue;
    if (ss.getSheets().length > 1) ss.deleteSheet(h);
  }
}

function esperarHojaRespuestas(ss) {
  for (var i = 0; i < 10; i++) {
    var hojas = ss.getSheets();
    for (var j = 0; j < hojas.length; j++) {
      if (hojas[j].getFormUrl()) return hojas[j];
    }
    Utilities.sleep(1000);
    SpreadsheetApp.flush();
  }
  throw new Error('No se encontro la hoja de respuestas del formulario.');
}

function crearHojaConfig(ss, cfg) {
  var sh = ss.insertSheet('Config');
  sh.getRange('A1:B1').setValues([['Parametro', 'Valor']]);
  sh.getRange('A2:B5').setValues([
    ['Umbral diario (horas)', cfg.umbralDiario],
    ['Umbral semanal (horas)', cfg.umbralSemanal],
    ['Regla de horas extra', cfg.regla],
    ['', '']
  ]);
  sh.getRange('A6').setValue('Trabajadores');
  var nombres = cfg.trabajadores.map(function (n) { return [n]; });
  sh.getRange(7, 1, nombres.length, 1).setValues(nombres);

  // Validacion para la regla
  var reglas = SpreadsheetApp.newDataValidation()
      .requireValueInList(['Diaria', 'Semanal', 'Mayor de ambas'], true)
      .setAllowInvalid(false).build();
  sh.getRange('B4').setDataValidation(reglas);

  sh.getRange('D2').setValue(
    'Diaria = se paga lo que excede el umbral diario cada dia.\n' +
    'Semanal = se paga lo que excede el umbral semanal en el total de la semana.\n' +
    'Mayor de ambas = se toma el criterio que de mas horas extra.\n\n' +
    'Si agregas o cambias trabajadores aqui, acuerdate de actualizar\n' +
    'tambien las opciones del Formulario.');
  sh.getRange('D2').setWrap(true);
  sh.setColumnWidth(1, 190);
  sh.setColumnWidth(2, 120);
  sh.setColumnWidth(4, 420);
  sh.getRange('A1:B1').setFontWeight('bold').setBackground('#e8eaed');
  sh.getRange('A6').setFontWeight('bold');
  sh.setFrozenRows(1);
}

function prepararRegistros(sh) {
  // Columnas: A Marca temporal | B Trabajador | C Fecha | D Entrada
  //           E Salida | F Colacion | G Horas | H Extra dia | I Semana
  var ent = 'IF(ISNUMBER($D:$D),MOD($D:$D,1),IFERROR(TIMEVALUE($D:$D),0))';
  var sal = 'IF(ISNUMBER($E:$E),MOD($E:$E,1),IFERROR(TIMEVALUE($E:$E),0))';
  var col = 'IFERROR(VALUE($F:$F),0)/60';
  var neto = 'MOD(' + sal + '-' + ent + ',1)*24-' + col;

  var fHoras = '=ARRAYFORMULA(IF(ROW($A:$A)=1,"Horas trabajadas",' +
      'IF($A:$A="","",ROUND(IF((' + neto + ')<0,0,' + neto + '),2))))';

  var fExtra = '=ARRAYFORMULA(IF(ROW($A:$A)=1,"Horas extra (dia)",' +
      'IF($A:$A="","",IF($G:$G>Config!$B$2,ROUND($G:$G-Config!$B$2,2),0))))';

  var fSemana = '=ARRAYFORMULA(IF(ROW($A:$A)=1,"Semana (lunes)",' +
      'IF($C:$C="","",IFERROR($C:$C-WEEKDAY($C:$C,2)+1,""))))';

  sh.getRange('G1').setFormula(fHoras);
  sh.getRange('H1').setFormula(fExtra);
  sh.getRange('I1').setFormula(fSemana);

  sh.getRange('C2:C').setNumberFormat('dd/mm/yyyy');
  sh.getRange('D2:E').setNumberFormat('hh:mm');
  sh.getRange('G2:H').setNumberFormat('0.00');
  sh.getRange('I2:I').setNumberFormat('dd/mm/yyyy');

  sh.getRange('A1:I1').setFontWeight('bold').setBackground('#e8eaed');
  sh.setFrozenRows(1);
  sh.setColumnWidths(1, 9, 130);

  // Resalta en amarillo las filas con horas extra
  var regla = SpreadsheetApp.newConditionalFormatRule()
      .whenFormulaSatisfied('=AND($H2>0,$A2<>"")')
      .setBackground('#fff2cc')
      .setRanges([sh.getRange(2, 1, sh.getMaxRows() - 1, 9)])
      .build();
  sh.setConditionalFormatRules([regla]);
}

function crearHojaResumen(ss) {
  var sh = ss.insertSheet('Resumen');
  sh.getRange('A1').setValue('Resumen semanal por trabajador')
    .setFontWeight('bold').setFontSize(12);

  sh.getRange('A2').setFormula(
    '=IFERROR(QUERY(Registros!$A:$I,"select I, B, sum(G) where B is not null ' +
    'group by I, B order by I desc, B ' +
    'label I \'Semana (lunes)\', B \'Trabajador\', sum(G) \'Horas trabajadas\'",1),' +
    '{"Semana (lunes)","Trabajador","Horas trabajadas"})');

  sh.getRange('D2:F2').setValues([[
    'Extra por regla semanal', 'Extra por regla diaria', 'Horas extra a pagar'
  ]]);

  sh.getRange('D3').setFormula(
    '=ARRAYFORMULA(IF($A3:$A="","",' +
    'IF($C3:$C>Config!$B$3,ROUND($C3:$C-Config!$B$3,2),0)))');

  sh.getRange('E3').setFormula(
    '=ARRAYFORMULA(IF($A3:$A="","",' +
    'ROUND(SUMIFS(Registros!$H:$H,Registros!$I:$I,$A3:$A,Registros!$B:$B,$B3:$B),2)))');

  sh.getRange('F3').setFormula(
    '=ARRAYFORMULA(IF($A3:$A="","",' +
    'IF(Config!$B$4="Semanal",$D3:$D,' +
    'IF(Config!$B$4="Diaria",$E3:$E,' +
    'IF($D3:$D>$E3:$E,$D3:$D,$E3:$E)))))');

  sh.getRange('A2:F2').setFontWeight('bold').setBackground('#e8eaed');
  sh.getRange('A3:A').setNumberFormat('dd/mm/yyyy');
  sh.getRange('C3:F').setNumberFormat('0.00');
  sh.setFrozenRows(2);
  sh.setColumnWidths(1, 6, 150);
}

function crearHojaPanel(ss, cfg) {
  var sh = ss.insertSheet('Panel');
  sh.getRange('A1').setValue('Panel de control - Horas del mes')
    .setFontWeight('bold').setFontSize(14);

  sh.getRange('A3').setValue('Mes:').setFontWeight('bold');
  sh.getRange('B3').setFormula('=EOMONTH(TODAY(),-1)+1');
  sh.getRange('B3').setNumberFormat('mmmm yyyy');
  sh.getRange('C3').setValue('<- escribe aqui el 1 de otro mes para cambiar de periodo');
  sh.getRange('C3').setFontColor('#666666');

  sh.getRange('A5:E5').setValues([[
    'Trabajador', 'Dias registrados', 'Horas trabajadas',
    'Horas extra (dia)', 'Promedio horas/dia'
  ]]);

  var desde = '$B$3';
  var hasta = 'EOMONTH($B$3,0)';

  sh.getRange('A6').setFormula('=FILTER(Config!$A$7:$A,Config!$A$7:$A<>"")');
  sh.getRange('B6').setFormula(
    '=ARRAYFORMULA(IF($A6:$A="","",COUNTIFS(Registros!$B:$B,$A6:$A,' +
    'Registros!$C:$C,">="&' + desde + ',Registros!$C:$C,"<="&' + hasta + ')))');
  sh.getRange('C6').setFormula(
    '=ARRAYFORMULA(IF($A6:$A="","",ROUND(SUMIFS(Registros!$G:$G,Registros!$B:$B,$A6:$A,' +
    'Registros!$C:$C,">="&' + desde + ',Registros!$C:$C,"<="&' + hasta + '),2)))');
  sh.getRange('D6').setFormula(
    '=ARRAYFORMULA(IF($A6:$A="","",ROUND(SUMIFS(Registros!$H:$H,Registros!$B:$B,$A6:$A,' +
    'Registros!$C:$C,">="&' + desde + ',Registros!$C:$C,"<="&' + hasta + '),2)))');
  sh.getRange('E6').setFormula(
    '=ARRAYFORMULA(IF($A6:$A="","",IF($B6:$B=0,0,ROUND($C6:$C/$B6:$B,2))))');

  sh.getRange('A5:E5').setFontWeight('bold').setBackground('#e8eaed');
  sh.getRange('C6:E').setNumberFormat('0.00');
  sh.setColumnWidths(1, 5, 150);
  sh.setColumnWidth(3, 160);

  sh.getRange('A12').setValue('Como se usa').setFontWeight('bold');
  sh.getRange('A13').setValue(
    '1. Los trabajadores cargan su jornada en el Formulario (link en el menu Extensiones o guardalo en el celular).\n' +
    '2. Cada respuesta cae en la hoja "Registros" y las horas se calculan solas.\n' +
    '3. "Resumen" muestra el detalle semanal; este Panel muestra el mes.\n' +
    '4. Los umbrales de horas extra se cambian en la hoja "Config".');
  sh.getRange('A13').setWrap(true);
  sh.getRange('A13:E18').merge();
}
