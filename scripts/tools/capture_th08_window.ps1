param(
    [Parameter(Mandatory = $true)]
    [string]$Output
)

# Bootstrap/menu audit capture only; gameplay sensing remains native memory.
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class Th08WindowCaptureNative {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")]
    public static extern bool SetProcessDPIAware();
}
"@

[Th08WindowCaptureNative]::SetProcessDPIAware() | Out-Null
$process = Get-Process th08 -ErrorAction Stop | Select-Object -First 1
if ($process.MainWindowHandle -eq [IntPtr]::Zero) {
    throw "th08.exe has no main window"
}
$rect = New-Object Th08WindowCaptureNative+RECT
if (-not [Th08WindowCaptureNative]::GetWindowRect($process.MainWindowHandle, [ref]$rect)) {
    throw "GetWindowRect failed"
}
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
if ($width -le 0 -or $height -le 0) {
    throw "TH08 window has invalid dimensions ${width}x${height}"
}

$directory = Split-Path -Parent $Output
if ($directory) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
}
$bitmap = New-Object System.Drawing.Bitmap $width, $height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
try {
    $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
    $bitmap.Save($Output, [System.Drawing.Imaging.ImageFormat]::Png)
} finally {
    $graphics.Dispose()
    $bitmap.Dispose()
}
