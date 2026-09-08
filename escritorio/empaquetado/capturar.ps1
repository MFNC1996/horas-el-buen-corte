# Abre la aplicacion en Windows y fotografia las cinco pestanas.
# Se usa en la compilacion, para poder revisar la interfaz sin tener un
# Windows a mano. No forma parte del programa que se instala.
param([string]$Exe = "dist\ControlDeHoras.exe",
      [string]$Destino = "capturas")

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms, System.Drawing

$codigo = @'
using System;
using System.Runtime.InteropServices;
public class Raton {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(
    uint dwFlags, uint dx, uint dy, uint dwData, int dwExtraInfo);
  public static void Clic(int x, int y) {
    SetCursorPos(x, y);
    mouse_event(0x0002, 0, 0, 0, 0);   // boton izquierdo abajo
    mouse_event(0x0004, 0, 0, 0, 0);   // boton izquierdo arriba
  }
}
'@
Add-Type -TypeDefinition $codigo

New-Item -ItemType Directory -Force -Path $Destino | Out-Null

$p = Start-Process -FilePath $Exe -PassThru
Start-Sleep -Seconds 15
if ($p.HasExited) {
    Write-Error "La aplicacion se cerro sola (codigo $($p.ExitCode))."
    exit 1
}
Write-Host "La app siguio abierta 15 segundos: arranca bien."

function Fotografiar($nombre) {
    $a = [System.Windows.Forms.SystemInformation]::VirtualScreen.Width
    $h = [System.Windows.Forms.SystemInformation]::VirtualScreen.Height
    $bmp = New-Object System.Drawing.Bitmap $a, $h
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen(0, 0, 0, 0, $bmp.Size)
    $bmp.Save("$PWD\$Destino\$nombre.png",
              [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
    Write-Host "  capturada: $nombre"
}

# La ventana se centra sola y su tamano sale del de la pantalla, asi que las
# posiciones son predecibles. Se hace clic directo en cada pestana: Ctrl+Tab
# se traga eventos y las capturas salian corridas.
$pestanas = @(
    @{ nombre = "1-marcar";          x = 91  },
    @{ nombre = "3-jornadas";        x = 184 },
    @{ nombre = "4-resumen-y-pago";  x = 321 },
    @{ nombre = "5-trabajadores";    x = 470 },
    @{ nombre = "6-configuracion";   x = 611 }
)
$yPestanas = 167

Fotografiar "1-marcar"
[Raton]::Clic(139, 268)          # elegir al primer trabajador
Start-Sleep -Seconds 2
Fotografiar "2-marcar-elegido"

foreach ($t in $pestanas) {
    if ($t.nombre -eq "1-marcar") { continue }
    [Raton]::Clic($t.x, $yPestanas)
    Start-Sleep -Seconds 3
    Fotografiar $t.nombre
}

Get-Process -Name ControlDeHoras -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
