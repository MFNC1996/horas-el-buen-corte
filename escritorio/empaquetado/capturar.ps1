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

# La ventana se centra sola y su tamano sale del de la pantalla, asi que la
# posicion del primer boton de nombre es predecible.
Fotografiar "1-marcar"
[Raton]::Clic(139, 268)
Start-Sleep -Seconds 2
Fotografiar "2-marcar-elegido"

foreach ($n in @("3-jornadas", "4-resumen-y-pago", "5-trabajadores",
                 "6-configuracion")) {
    [System.Windows.Forms.SendKeys]::SendWait("^{TAB}")
    Start-Sleep -Seconds 3
    Fotografiar $n
}

Get-Process -Name ControlDeHoras -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
