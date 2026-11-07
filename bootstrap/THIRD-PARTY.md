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


## TRG-21 reference model and sounds

TRG-21 Infinity D geometry, UVs and four skeletal clips: Tettra / Jeongtae Kim; textures: CryTek. Original game: Sudden Attack. Public source: https://blog.jeongtae.com/css-서든어택-trg21인피니티d-스킨-완성-배포/ . Original attribution is retained; these artworks are not relicensed under the client code GPL. Classic DTX texture was supplied by the server owner; its pixels remain unchanged after format decoding. Minecraft player skin is rendered separately and follows the imported arm bones. Source engine binary layouts were consulted from ValveSoftware/source-sdk-2013; no Source engine runtime code is included.


## Classic TRG reference update (0.3.4)
The supplied MiniSudden standalone pack contains TRG-shaped DirectX meshes named mk23.x/mk23sd.x and their mk23.bmp texture. The Gunbed converter retains the mesh topology and UVs, rigs its magazine and bolt, and uses the player's Minecraft skin for native Minecraft block-arm rendering. The JTK donor rig is retimed using observed landmarks in the user-provided review https://www.youtube.com/watch?v=UzyyS6ncmMU . Original Sudden Attack animation data was not supplied; these are adapted poses. No silenced shot audio from the review is included. The existing normal TRG shot is retained.

## Gunbed renewal assets (0.3.6)
QA grenade/incendiary/flashbang models and sheet textures are converted from the server owner’s local zombie-server resource pack. Churi team equipment and selected team block textures are copied from the owner’s local Churi pack. Turret silhouettes are adapted from the four owner-supplied model archives; these artworks retain their original ownership and are not relicensed as client code. ThrowablePose is newly authored Gunbed code.


## Combat update (0.3.8)
LesRaisins Tactical Equipements (xjqsh, LeComte): dagger, karambit and baseball-bat art and reference pin/throw motion. Source https://github.com/LesRaisins-Studios/LesRaisins-Tactical-Equipements . Code GPL-3.0; art remains All Rights Reserved by its authors and is not relicensed by this project. Original four owner-supplied turret meshes retain topology, UVs and normals; Gunbed adds material and team colours. M79 geometry/icon and radio TTS/filtering are newly authored here. Orbital Laser by astroneer83 is a visual reference only; none of its mod/runtime/art assets are bundled. No Counter-Strike voice samples are used.


Radio callouts in 0.3.8: newly synthesized with Piper Joe medium (CC0 dataset), https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/joe/medium . Local generation uses Piper GPL-3.0, https://github.com/OHF-Voice/piper1-gpl . No Counter-Strike voice recording is included.
