# Sources and assets

The geometry helpers in `kr.mzs.gunbedvisual.model` are adapted from
[TACZ-FabricContinued](https://github.com/kalkulator777/TACZ-FabricContinued),
branch `1.21.11`, retaining GPL-3.0 terms. `LICENSE` contains the licence.
The exact upstream commit is `aa1ba11c3ea84d4079833d03872e9a2e7fd5d1e5`.
The mesh coordinate system follows that implementation. Gunbed's networking,
version adapters and animation timing are separate from TaCZ's combat code.

TaCZ's original art assets have separate CC BY-NC-ND-4.0 terms. They are not
relicensed as GPL by this project. Source art is kept byte-for-byte unchanged;
do not redistribute altered art or treat it as freely editable commercial art.
The paid Exception Armorer pack shown in the reference video is not included.

Original project: https://github.com/MCModderAnchor/TACZ
Art licence: https://creativecommons.org/licenses/by-nc-nd/4.0/

The distribution also includes the [Nuit skybox renderer](https://github.com/FlashyReese/nuit)
by FlashyReese, under the MIT licence, and Fabric API under Apache-2.0.
For Minecraft 1.21.9 and 1.21.10, Gunbed provides compatibility builds from
Nuit's `1.21.8/dev` commit `d17a1599aaa021b18a0d98d7ceef95ff51257ac9`.
Those builds adapt key categories, resource reloads, the celestial rendering
type and the sky-pass method signature. Their complete sources and MIT licence
are included in `source/Nuit-Gunbed-ports.zip`. Other Nuit JARs are unmodified upstream releases.
Nuit renders metadata converted from the user's local Dewier pack; the original
image files remain unchanged. That user-supplied pack is delivered separately
as the server resource pack, not inside these client mod JARs.
