# Gunbed Installer

Windows 10/11 x64 installer for MZS Gunbed FPS BedWars.

**Download:** https://churigame1234-ux.github.io/gunbed-installer/

Installer 0.3.15 installs the tested 0.3.15 adapters (same executable classes as 0.3.13, updated asset dependency metadata) and shared assets 0.3.15, fixing opaque optical apertures on five mounted scopes. Choose Minecraft 1.21.8–26.3 and install Fabric Loader 0.19.5 plus four required mods. Online executables try static Pages files, commit-pinned raw files, and GitHub Releases in order, verifying SHA-256 and length before using any file. Older offline installers contain the opaque optics and are not offered for this update.

The website downloads and verifies the EXE before saving it, and switches paths automatically on timeout, HTTP errors, truncation or checksum mismatch. A ZIP download is also available. External service outages cannot be eliminated, but release-edge errors no longer block all downloads. Unchanged libraries remain under `docs/files/v0.3.13/`; the updated adapters and model assets are under `docs/files/v0.3.15/`.

## Existing installations

You may select `.minecraft`, a separate game directory such as `1.21.8 mod`, or its `mods` directory. Mods go to that exact game directory; Loader goes to the actual Minecraft root. Other version folders, unrelated mods, settings and worlds remain untouched. Only the four matching Fabric mod IDs are backed up and replaced.

The install button terminates residual **MinecraftLauncher.exe / MinecraftLauncherBeta.exe** processes by PID. It never terminates Java, Minecraft game or server processes. Close a running game yourself before replacing its loaded mods.

## Sources and licenses

Installer code in `installer/` is MIT licensed. The downloadable mods retain their respective licenses; see `bootstrap/THIRD-PARTY.md`. Corresponding Gunbed Visuals source and Nuit port source are available with the binaries in the same GitHub Release. TaCZ art is distributed unchanged under its stated noncommercial terms. Paid Exception Armorer assets are not included.

## Build the online installer

Use Python 3.12 and `pip install pyinstaller==6.16.0` on Windows, then:

```powershell
python -m PyInstaller --onefile --windowed --noupx --name GunbedInstaller --paths installer --add-data "bootstrap;payload" installer/app.py
```

The `bootstrap` directory pins public release URLs and SHA-256 digests. To create a version-selected executable, copy the compiled EXE to e.g. `GunbedInstaller-1.21.8.exe`. The filename selects its initial version; all supported versions remain available in the UI.

No player records, server configuration, account files or authentication credentials are included in this repository.


Client 0.3.13 includes respawn loadout repeat, the updated combat rules and inventory display. This installer-only fix does not change gameplay, server records, ownership or balance.
