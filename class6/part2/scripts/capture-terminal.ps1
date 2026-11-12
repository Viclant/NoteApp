param(
    [Parameter(Mandatory = $true)][string]$CmdFile,
    [Parameter(Mandatory = $true)][string]$Title,
    [Parameter(Mandatory = $true)][string]$OutFile,
    [int]$WaitSeconds = 8,
    [int]$Width = 1320,
    [int]$Height = 760
)

# Real console capture on Windows: the command runs in a real Windows Terminal
# window, the window is moved to a known position on top of everything, and the
# pixels are read from the screen. Nothing is drawn or re-typeset.

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class WinCap {
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr l);
    [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr h);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h, uint msg, IntPtr w, IntPtr l);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
    [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, IntPtr extra);

    public static IntPtr Find(string title) {
        IntPtr found = IntPtr.Zero;
        EnumWindows(delegate(IntPtr h, IntPtr l) {
            if (!IsWindowVisible(h)) return true;
            int len = GetWindowTextLength(h);
            if (len == 0) return true;
            StringBuilder sb = new StringBuilder(len + 1);
            GetWindowText(h, sb, sb.Capacity);
            if (sb.ToString().StartsWith(title)) { found = h; return false; }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    public static void Front(IntPtr h) {
        ShowWindow(h, 9);
        keybd_event(0x12, 0, 0, IntPtr.Zero);
        SetForegroundWindow(h);
        keybd_event(0x12, 0, 2, IntPtr.Zero);
    }
}
"@

$wt = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\wt.exe'
if (-not (Test-Path -LiteralPath $wt)) { throw "Windows Terminal (wt.exe) not found at $wt" }

& $wt -w new new-tab --title $Title cmd.exe /k $CmdFile | Out-Null

$handle = [IntPtr]::Zero
$deadline = (Get-Date).AddSeconds(20)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 400
    $handle = [WinCap]::Find($Title)
    if ($handle -ne [IntPtr]::Zero) { break }
}
if ($handle -eq [IntPtr]::Zero) { throw "terminal window '$Title' never appeared" }

[void][WinCap]::Front($handle)
# put the window on top, at a known position, so the capture is not spoiled
[void][WinCap]::SetWindowPos($handle, [IntPtr](-1), 0, 0, $Width, $Height, 0x0040)   # HWND_TOPMOST
Start-Sleep -Seconds $WaitSeconds      # let the commands run and finish

$rect = New-Object WinCap+RECT
[void][WinCap]::GetWindowRect($handle, [ref]$rect)
$left = $rect.Left; $top = $rect.Top
$w = $rect.Right - $rect.Left; $h = $rect.Bottom - $rect.Top

$bmp = New-Object System.Drawing.Bitmap($w, $h)
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$gfx.CopyFromScreen($left, $top, 0, 0, (New-Object System.Drawing.Size($w, $h)))
$gfx.Dispose()
$bmp.Save($OutFile, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()

# give the topmost flag back and close only this window (WM_CLOSE)
[void][WinCap]::SetWindowPos($handle, [IntPtr](-2), 0, 0, 0, 0, 0x0001)   # HWND_NOTOPMOST, SWP_NOMOVE|NOSIZE
[void][WinCap]::SendMessage($handle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)

Write-Output ("saved {0} ({1}x{2} at {3},{4})" -f $OutFile, $w, $h, $left, $top)
