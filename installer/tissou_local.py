"""Create private namespaced runtime assets on the user's PC from their verified official download."""
from pathlib import Path
import hashlib,json,re,zipfile
EXPECTED='aed1af48318a160f049fe8ac52d8445848de89eebc530c45dd5c0c5dc7af95bb'
def build(source:Path,destination:Path):
    if hashlib.sha256(source.read_bytes()).hexdigest()!=EXPECTED:raise ValueError('Tissou original ZIP checksum mismatch')
    textures=sounds=0;destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(source) as original,zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as output:
        def write(name,data):
            entry=zipfile.ZipInfo(name,(2026,11,24,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            output.writestr(entry,data)
        for name in sorted(original.namelist()):
            match=re.fullmatch(r'assets/minecraft/optifine/random/entity/zombie/(zombie\d+\.png)',name)
            if match:write('assets/mzs_tissou/textures/zombie/'+match[1],original.read(name));textures+=1
        ambient=json.loads(original.read('assets/minecraft/sounds.json'))['entity.zombie.ambient']['sounds'];entries=[]
        for index,entry in enumerate(ambient):
            definition={'name':entry} if isinstance(entry,str) else dict(entry)
            name=definition['name'].split(':')[-1];path='assets/minecraft/sounds/'+name+'.ogg'
            if path not in original.namelist():continue
            target=f'ambient/say_{index:03d}';write('assets/mzs_tissou/sounds/'+target+'.ogg',original.read(path));definition['name']='mzs_tissou:'+target;entries.append(definition);sounds+=1
        write('assets/mzs_tissou/sounds.json',json.dumps({'zombie.ambient':{'sounds':entries}},separators=(',',':')))
        write('fabric.mod.json',json.dumps({'schemaVersion':1,'id':'mzs_tissou_local','version':'2.7.0-local','name':'Tissou private zombie assets','environment':'client','license':'All-Rights-Reserved','depends':{'fabricloader':'>=0.19.3','minecraft':'*'}}))
        write('CREDITS.txt','Tissou Zombie Pack by Tissou. All rights reserved.\nGenerated locally from the official download; this derived JAR must not be redistributed.\nhttps://www.curseforge.com/minecraft/texture-packs/tissous-zombie-pack-optifine-1-7x-1-20\nOnly custom namespaced zombie assets are exposed. No vanilla or Gunbed assets are overridden.\n')
    if not textures or not sounds:raise ValueError('Tissou assets are incomplete')
    return {'textures':textures,'ambient_sounds':sounds,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'redistributable':False}
if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    report=build(root/'third-party/TZP_1.20.1_2.7.zip',root/'validation/private-assets/Tissou-local.jar')
    (root/'validation/tissou-local.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
