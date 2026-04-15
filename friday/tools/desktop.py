"""
Windows PC control tools — browser, apps, files, volume, clipboard, system, notifications.
These run locally on the user's machine via the MCP server.
"""

import subprocess
import webbrowser
import os
import platform
from urllib.parse import quote_plus


def _ps(command: str, timeout: int = 15) -> str:
    """Run a PowerShell command, return stdout or stderr."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=timeout
        )
        return (result.stdout.strip() or result.stderr.strip() or "OK")
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except FileNotFoundError:
        return "PowerShell not found."


_AUDIO_TYPE = r"""
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"),InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
    void _VtblGap1_6();
    void SetMasterVolumeLevelScalar([MarshalAs(UnmanagedType.R4)] float fLevel, Guid pguidEventContext);
    void _VtblGap2_1();
    [return:MarshalAs(UnmanagedType.R4)] float GetMasterVolumeLevelScalar();
    void _VtblGap3_3();
    void SetMute([MarshalAs(UnmanagedType.Bool)] bool bMute, Guid pguidEventContext);
    [return:MarshalAs(UnmanagedType.Bool)] bool GetMute();
}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"),InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
    [return:MarshalAs(UnmanagedType.Interface)] object Activate([MarshalAs(UnmanagedType.LPStruct)] Guid iid, uint dwClsCtx, IntPtr pActivationParams);
}
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"),InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
    void _VtblGap1_1();
    [return:MarshalAs(UnmanagedType.Interface)] IMMDevice GetDefaultAudioEndpoint(uint dataFlow, uint role);
}
[ComImport,Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumerator {}
'@ -ErrorAction SilentlyContinue
$enum = [MMDeviceEnumerator]::new()
$dev  = $enum.GetDefaultAudioEndpoint(0, 0)
$ep   = $dev.Activate([IAudioEndpointVolume].GUID, 1, [IntPtr]::Zero) -as [IAudioEndpointVolume]
"""


def register(mcp):

    # ------------------------------------------------------------------
    # BROWSER
    # ------------------------------------------------------------------

    @mcp.tool()
    def open_url(url: str) -> str:
        """Open any URL in the user's default web browser."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opened {url} in the browser."

    @mcp.tool()
    def search_google(query: str) -> str:
        """Google-search a topic and open the results in the browser."""
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
        return f"Opened Google search for: {query}"

    @mcp.tool()
    def search_youtube(query: str) -> str:
        """Search YouTube for a video and open the results in the browser."""
        webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
        return f"Opened YouTube search for: {query}"

    # ------------------------------------------------------------------
    # APPLICATIONS
    # ------------------------------------------------------------------

    @mcp.tool()
    def open_application(name: str) -> str:
        """
        Launch a Windows application.
        Examples: 'notepad', 'calc', 'mspaint', 'explorer', 'chrome', 'spotify',
                  'discord', 'vscode', 'taskmgr', 'cmd', 'steam'.
        """
        try:
            subprocess.Popen(f'start "" "{name}"', shell=True)
            return f"Launched {name}."
        except Exception as e:
            return f"Could not launch {name}: {e}"

    @mcp.tool()
    def open_file_or_folder(path: str) -> str:
        """
        Open a file or folder with its default Windows application.
        E.g. open a PDF, image, Word doc, or browse a folder in Explorer.
        """
        try:
            os.startfile(path)
            return f"Opened: {path}"
        except Exception as e:
            return f"Could not open {path}: {e}"

    @mcp.tool()
    def list_running_processes() -> str:
        """Return a list of currently running process names on the PC."""
        out = _ps("Get-Process | Select-Object -ExpandProperty Name | Sort-Object -Unique | Out-String")
        return out or "Could not retrieve process list."

    @mcp.tool()
    def kill_process(name: str) -> str:
        """
        Terminate a running process by name (without the .exe extension).
        Example: 'notepad', 'chrome', 'spotify'.
        """
        out = _ps(f'Stop-Process -Name "{name}" -Force -ErrorAction SilentlyContinue; "Done"')
        return f"Killed {name}. {out}"

    @mcp.tool()
    def run_shell_command(command: str) -> str:
        """
        Run any Windows shell command and return its output.
        Use for tasks not covered by other tools. Be careful with destructive commands.
        """
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=20
            )
            return (result.stdout.strip() or result.stderr.strip() or "Command completed with no output.")
        except subprocess.TimeoutExpired:
            return "Command timed out after 20 seconds."
        except Exception as e:
            return f"Error: {e}"

    # ------------------------------------------------------------------
    # VOLUME & AUDIO
    # ------------------------------------------------------------------

    @mcp.tool()
    def get_volume() -> str:
        """Return the current system master volume level (0-100)."""
        out = _ps(_AUDIO_TYPE + r"[int]($ep.GetMasterVolumeLevelScalar() * 100)")
        return f"Current volume: {out}%"

    @mcp.tool()
    def set_volume(level: int) -> str:
        """Set the system master volume to a specific level (0-100)."""
        level = max(0, min(100, level))
        scalar = round(level / 100, 4)
        out = _ps(_AUDIO_TYPE + f'$ep.SetMasterVolumeLevelScalar({scalar}, [Guid]::Empty); "Volume set to {level}%"')
        return out

    @mcp.tool()
    def mute_audio() -> str:
        """Mute the system audio."""
        out = _ps(_AUDIO_TYPE + '$ep.SetMute($true, [Guid]::Empty); "Muted."')
        return out

    @mcp.tool()
    def unmute_audio() -> str:
        """Unmute the system audio."""
        out = _ps(_AUDIO_TYPE + '$ep.SetMute($false, [Guid]::Empty); "Unmuted."')
        return out

    # ------------------------------------------------------------------
    # CLIPBOARD
    # ------------------------------------------------------------------

    @mcp.tool()
    def get_clipboard() -> str:
        """Return the current text content of the Windows clipboard."""
        return _ps("Get-Clipboard")

    @mcp.tool()
    def set_clipboard(text: str) -> str:
        """Copy text to the Windows clipboard."""
        escaped = text.replace("'", "''")
        _ps(f"Set-Clipboard -Value '{escaped}'")
        return "Text copied to clipboard."

    # ------------------------------------------------------------------
    # SCREEN & SCREENSHOTS
    # ------------------------------------------------------------------

    @mcp.tool()
    def take_screenshot(save_path: str = "") -> str:
        """
        Take a screenshot of the entire screen.
        Optionally specify a save path (e.g. C:\\Users\\user\\Desktop\\shot.png).
        Defaults to the Desktop.
        """
        if not save_path:
            save_path = os.path.join(os.path.expanduser("~"), "Desktop", "friday_screenshot.png")
        out = _ps(f"""
Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$bmp.Save('{save_path}')
$g.Dispose(); $bmp.Dispose()
"Screenshot saved to {save_path}"
""")
        return out

    # ------------------------------------------------------------------
    # NOTIFICATIONS
    # ------------------------------------------------------------------

    @mcp.tool()
    def show_notification(title: str, message: str) -> str:
        """Show a Windows toast notification in the bottom-right corner of the screen."""
        t = title.replace("'", "''")
        m = message.replace("'", "''")
        out = _ps(f"""
Add-Type -AssemblyName System.Windows.Forms
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Information
$n.BalloonTipTitle = '{t}'
$n.BalloonTipText = '{m}'
$n.Visible = $true
$n.ShowBalloonTip(5000)
Start-Sleep -Seconds 1
$n.Dispose()
"Notification shown."
""")
        return out

    # ------------------------------------------------------------------
    # SYSTEM POWER
    # ------------------------------------------------------------------

    @mcp.tool()
    def lock_screen() -> str:
        """Lock the Windows PC screen immediately."""
        subprocess.Popen("rundll32.exe user32.dll,LockWorkStation", shell=True)
        return "Screen locked."

    @mcp.tool()
    def sleep_pc() -> str:
        """Put the PC into sleep mode."""
        _ps("Add-Type -Assembly System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)")
        return "Sleeping..."

    @mcp.tool()
    def shutdown_pc(delay_seconds: int = 30) -> str:
        """
        Shut down the PC after a delay (default 30 seconds).
        Gives the user time to cancel with: shutdown /a
        """
        subprocess.Popen(f"shutdown /s /t {delay_seconds}", shell=True)
        return f"Shutdown scheduled in {delay_seconds} seconds. Say 'cancel shutdown' to abort."

    @mcp.tool()
    def restart_pc(delay_seconds: int = 30) -> str:
        """Restart the PC after a delay (default 30 seconds)."""
        subprocess.Popen(f"shutdown /r /t {delay_seconds}", shell=True)
        return f"Restart scheduled in {delay_seconds} seconds."

    @mcp.tool()
    def cancel_shutdown() -> str:
        """Cancel a pending shutdown or restart."""
        subprocess.Popen("shutdown /a", shell=True)
        return "Shutdown/restart cancelled."

    # ------------------------------------------------------------------
    # FILES & SEARCH
    # ------------------------------------------------------------------

    @mcp.tool()
    def search_files(query: str, folder: str = "") -> str:
        """
        Search for files by name on the PC.
        Optionally restrict the search to a specific folder path.
        """
        if not folder:
            folder = os.path.expanduser("~")
        out = _ps(f"Get-ChildItem -Path '{folder}' -Recurse -Filter '*{query}*' -ErrorAction SilentlyContinue | Select-Object -First 20 FullName | Format-List", timeout=30)
        return out or f"No files matching '{query}' found."

    @mcp.tool()
    def open_downloads_folder() -> str:
        """Open the user's Downloads folder in Windows Explorer."""
        path = os.path.join(os.path.expanduser("~"), "Downloads")
        os.startfile(path)
        return f"Opened Downloads: {path}"

    @mcp.tool()
    def open_desktop() -> str:
        """Open the Desktop folder in Windows Explorer."""
        path = os.path.join(os.path.expanduser("~"), "Desktop")
        os.startfile(path)
        return f"Opened Desktop: {path}"

    # ------------------------------------------------------------------
    # TYPING / INPUT
    # ------------------------------------------------------------------

    @mcp.tool()
    def type_text(text: str) -> str:
        """
        Type text into whatever window is currently focused on the PC.
        Useful for filling in forms, writing notes, etc.
        """
        escaped = text.replace("'", "''")
        _ps(f"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait('{escaped}')
"Typed."
""")
        return f"Typed: {text}"
