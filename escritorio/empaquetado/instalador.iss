; Inno Setup: genera ControlDeHoras-Setup.exe
; Instala la aplicacion, crea accesos directos y deja un desinstalador.

#define Nombre    "Control de Horas"
#define Version   "1.6.1"
#define Empresa   "Macoem"
#define Ejecutable "ControlDeHoras.exe"

[Setup]
AppId={{8B3E7A94-2C51-4F6D-9E12-7A4C5D8B1F30}
AppName={#Nombre}
AppVersion={#Version}
AppVerName={#Nombre} {#Version}
AppPublisher={#Empresa}
AppPublisherURL=https://github.com/MFNC1996/horas-el-buen-corte
DefaultDirName={autopf}\ControlDeHoras
DefaultGroupName={#Nombre}
DisableProgramGroupPage=yes
DisableDirPage=no
OutputDir=..\..\salida
OutputBaseFilename=ControlDeHoras-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; Sin exigir administrador: instala para el usuario actual si no hay permisos.
PrivilegesRequiredOverridesAllowed=dialog
PrivilegesRequired=lowest
UninstallDisplayName={#Nombre}
UninstallDisplayIcon={app}\{#Ejecutable}
SetupIconFile=icono.ico
WizardImageFile=instalador-grande.bmp
WizardSmallImageFile=instalador-chico.bmp

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "Crear un acceso directo en el Escritorio"; \
  GroupDescription: "Accesos directos:"

[Files]
Source: "..\..\dist\{#Ejecutable}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\LEEME.txt";          DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#Nombre}";              Filename: "{app}\{#Ejecutable}"
Name: "{group}\Desinstalar {#Nombre}";  Filename: "{uninstallexe}"
Name: "{autodesktop}\{#Nombre}";        Filename: "{app}\{#Ejecutable}"; Tasks: escritorio

[Run]
Filename: "{app}\{#Ejecutable}"; Description: "Abrir {#Nombre} ahora"; \
  Flags: nowait postinstall skipifsilent

[Messages]
es.WelcomeLabel2=Esto instalara [name/ver] en tu computador.%n%nLos datos se guardan aparte, en tu carpeta de usuario, asi que puedes actualizar la aplicacion sin perder las jornadas registradas.
