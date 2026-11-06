"""Offline Fabric/profile installation; replace only four exact mod identities."""
from __future__ import annotations
import datetime,hashlib,json,os,shutil,uuid,zipfile
from pathlib import Path
from file_access import InstallAccessError,access_error,clear_readonly,preflight_files,probe_directory

IDS={'gunbed_visuals','gunbed_assets','fabric-api','nuit'}
PROFILE_FILES=('launcher_profiles.json','launcher_profiles_microsoft_store.json')

def digest(data):return hashlib.sha256(data).hexdigest()
def read_json(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.gunbed-'+uuid.uuid4().hex+'.tmp')
    try:temporary.write_bytes(data);os.replace(temporary,path)
    finally:temporary.unlink(missing_ok=True)
def mod_id(data):
    import io
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as jar:return json.loads(jar.read('fabric.mod.json').decode('utf-8-sig')).get('id')
    except (KeyError,ValueError,zipfile.BadZipFile):return None

class Installer:
    def __init__(self,payload):
        self.payload=Path(payload)
        self.manifest=read_json(self.payload/'manifest.json')
        self.versions=list(self.manifest['versions'])
    def profiles(self,root):
        return {name:read_json(root/name) for name in PROFILE_FILES if (root/name).exists()}
    def locations(self,selected,version,game_dir=None):
        selected=Path(os.path.expandvars(str(selected))).expanduser().resolve()
        root=next((path for path in (selected,*selected.parents) if (path/'versions').is_dir()),None)
        if root is None and selected.is_dir():
            standard=Path(os.environ.get('APPDATA',Path.home()))/'.minecraft'
            if (standard/'versions').is_dir():root=standard.resolve()
        if root is None:raise ValueError('실제 .minecraft의 versions 폴더를 찾지 못했습니다. 마인크래프트 폴더 또는 그 안의 게임/mods 폴더를 선택하세요.')
        if game_dir:game=Path(os.path.expandvars(str(game_dir))).expanduser().resolve()
        elif selected!=root:game=selected.parent if selected.name.lower()=='mods' else selected
        else:game=self._profile_target(root,version)
        if game.name.lower()=='mods':game=game.parent
        return root,game
    def target(self,root,version):
        return self.locations(root,version)[1]
    def _profile_target(self,root,version):
        root=Path(root).expanduser().resolve()
        profiles=self.profiles(root)
        candidates=[]
        for data in profiles.values():
            for key,profile in data.get('profiles',{}).items():
                last=profile.get('lastVersionId','')
                if last=='fabric-loader-'+self.manifest['loader']+'-'+version or last.endswith('-'+version) and 'fabric' in last.lower():
                    directory=Path(profile.get('gameDir') or root).expanduser()
                    if not directory.is_absolute():directory=root/directory
                    candidates.append((0 if key=='gunbed-'+version else 1,directory.resolve()))
        return sorted(candidates,key=lambda v:v[0])[0][1] if candidates else root/'gunbed'/version
    def verified(self,relative,expected):
        path=self.payload/relative
        if not path.resolve().is_relative_to(self.payload.resolve()):raise ValueError('Invalid package path')
        data=path.read_bytes()
        if digest(data)!=expected:raise ValueError('설치 파일 검증 실패: '+relative)
        return data
    def install(self,root,version,game_dir=None,log=lambda message:None):
        if version not in self.versions:raise ValueError('지원하지 않는 버전입니다.')
        root,game=self.locations(root,version,game_dir)
        if not root.is_dir() or not (root/'versions').is_dir():raise ValueError('마인크래프트 설치 폴더가 올바르지 않습니다.')
        mods=game/'mods'
        if mods.exists() and (not mods.is_dir() or mods.resolve().parent!=game.resolve()):raise ValueError('연결된 mods 폴더에는 설치하지 않습니다. 실제 게임 폴더를 선택하세요.')
        chosen=self.manifest['versions'][version]
        log('설치 파일과 Fabric Loader '+self.manifest['loader']+' 검증 중…')
        bundle=self.payload/'clients.zip'
        profile_bytes=self.verified(chosen['profile'],chosen['profile_sha256'])
        profile=json.loads(profile_bytes)
        assert profile['id']=='fabric-loader-'+self.manifest['loader']+'-'+version
        assert profile['inheritsFrom']==version
        incoming={}
        legal_files={}
        with zipfile.ZipFile(bundle) as archive:
            for entry in chosen['mods']:
                data=archive.read(entry['path'])
                if digest(data)!=entry['sha256']:raise ValueError('모드 무결성 검증 실패: '+entry['file'])
                identity=mod_id(data)
                if identity not in IDS or identity in incoming:raise ValueError('필수 모드 ID가 올바르지 않습니다.')
                incoming[identity]=(entry['file'],data)
            for name in ('THIRD-PARTY.md','licenses/Nuit-MIT.txt'):
                legal_files[name]=archive.read(name)
            if 'source/source-links.json' in archive.namelist():legal_files['source/source-links.json']=archive.read('source/source-links.json')
            else:
                for name in ('source/GunbedVisuals-source.zip','source/Nuit-Gunbed-ports.zip'):legal_files[name]=archive.read(name)
        assert set(incoming)==IDS
        libraries=[(entry,self.verified(entry['path'],entry['sha256'])) for entry in chosen['libraries']]
        old_profiles=self.profiles(root)
        originals={};duplicates=[];untouched={};readonly={}
        def existing_mod_bytes(path):
            try:return path.read_bytes()
            except PermissionError as error:raise access_error(path,error) from error
        for path in mods.glob('*.jar'):
            if path.resolve().parent!=mods.resolve():raise ValueError('연결된 모드 파일은 자동으로 교체하지 않습니다: '+path.name)
            data=existing_mod_bytes(path);identity=mod_id(data)
            if identity in IDS:
                if path.name!=incoming[identity][0] or data!=incoming[identity][1]:duplicates.append(path)
            else:untouched[path.name]=digest(data)
        for name,data in incoming.values():
            existing=mods/name
            if existing.exists() and mod_id(existing_mod_bytes(existing)) not in IDS:raise ValueError('다른 모드가 같은 파일명을 사용합니다. 보존을 위해 설치를 중단합니다: '+name)
        log('기존 모드 파일의 사용 중 여부와 폴더 쓰기 권한 확인 중…')
        preflight_files(duplicates+[mods/name for name,data in incoming.values() if (mods/name).exists() and existing_mod_bytes(mods/name)!=data])
        probe_directory(mods)
        stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
        backup=root/'gunbed-backups'/stamp
        changed=[]
        def remember(path):
            if path in originals:return
            data=path.read_bytes() if path.exists() else None
            originals[path]=data
            if data is not None:readonly[path]=not bool(path.stat().st_mode & 0o200)
            if data is not None:
                if path.parent==mods:relative=Path('mods')/path.name
                elif path.is_relative_to(root):relative=Path('minecraft')/path.relative_to(root)
                else:relative=Path('game')/path.relative_to(game)
                dest=backup/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        def write(path,data):
            if path.exists() and path.read_bytes()==data:return
            remember(path)
            if path.parent==mods:clear_readonly(path)
            atomic(path,data);changed.append(str(path))
        try:
            log('Fabric 실행 파일 설치 중…')
            version_dir=root/'versions'/profile['id']
            write(version_dir/(profile['id']+'.json'),profile_bytes)
            for entry,data in libraries:write(root/'libraries'/entry['target'],data)
            for name,data in legal_files.items():write(root/'gunbed'/name,data)
            mods.mkdir(parents=True,exist_ok=True)
            for path in duplicates:
                remember(path)
                log('동일 모드 백업: '+path.name)
                # Backup is already durable; unlink is restricted to verified duplicate IDs.
                if mod_id(path.read_bytes()) not in IDS:raise RuntimeError('설치 중 모드 파일이 변경되었습니다.')
                clear_readonly(path)
                path.unlink()
            for name,data in incoming.values():write(mods/name,data)
            log('기존 실행 설정의 Loader 업데이트 및 Gunbed 실행 설정 등록 중…')
            profile_names=list(old_profiles) or ['launcher_profiles.json']
            now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
            updated=[]
            for name in profile_names:
                destination=root/name
                initial=old_profiles.get(name)
                current=read_json(destination) if destination.exists() else {'profiles':{}}
                if initial is not None and current!=initial:raise RuntimeError('설치 중 런처 설정이 변경되었습니다. 런처를 종료하고 다시 설치하세요.')
                profiles=current.setdefault('profiles',{})
                template={}
                for key,item in profiles.items():
                    last=item.get('lastVersionId','')
                    same_mc=last.endswith('-'+version) and 'fabric' in last.lower()
                    previous_dir=Path(item.get('gameDir') or root).expanduser()
                    if not previous_dir.is_absolute():previous_dir=root/previous_dir
                    if same_mc and previous_dir.resolve()==game:
                        template=dict(item);item['lastVersionId']=profile['id'];updated.append(key)
                entry={k:v for k,v in template.items() if k in ('javaArgs','javaDir','resolution')}
                entry.update({'name':'Gunbed '+version,'type':'custom','icon':'Diamond_Sword','created':profiles.get('gunbed-'+version,{}).get('created',now),'lastUsed':now,'lastVersionId':profile['id'],'gameDir':str(game)})
                profiles['gunbed-'+version]=entry
                write(destination,json.dumps(current,ensure_ascii=False,indent=2).encode('utf-8'))
            for name,expected in untouched.items():
                if digest((mods/name).read_bytes())!=expected:raise RuntimeError('다른 모드 파일이 변경되었습니다: '+name)
            # Only installer-owned metadata, with no launcher/account tokens.
            report={'success':True,'minecraft':version,'loader':self.manifest['loader'],'minecraft_dir':str(root),'game_dir':str(game),'launcher_profile':'Gunbed '+version,'version_id':profile['id'],'installed_mods':list(incoming),'preserved_other_mods':list(untouched),'duplicates_backed_up':[p.name for p in duplicates],'updated_existing_profiles':updated,'backup':str(backup),'changed_files':changed,'base_version_present':(root/'versions'/version/(version+'.json')).exists()}
            write(game/'gunbed-installation.json',json.dumps(report,ensure_ascii=False,indent=2).encode('utf-8'))
            backup.mkdir(parents=True,exist_ok=True)
            atomic(backup/'restore-index.json',json.dumps([{'path':str(p),'existed':data is not None} for p,data in originals.items()],ensure_ascii=False,indent=2).encode('utf-8'))
            log('설치 완료 — 런처에서 Gunbed '+version+'을 선택하세요.')
            return report
        except BaseException as failure:
            recovery_errors=[]
            for path,data in reversed(list(originals.items())):
                try:
                    # A failed unlink/replace leaves its destination unchanged.
                    # Rewriting it would mask the original error with a second
                    # access-denied error while rolling back a locked JAR.
                    if data is None:path.unlink(missing_ok=True)
                    elif not path.exists() or path.read_bytes()!=data:atomic(path,data)
                    if readonly.get(path) and path.exists():path.chmod(0o444)
                except OSError as recovery_error:recovery_errors.append(str(path)+': '+str(recovery_error))
            if recovery_errors:
                log('일부 파일의 자동 복구가 실패했습니다. 백업 위치: '+str(backup))
                raise RuntimeError(str(failure)+'\n\n일부 파일을 복구하지 못했습니다. 백업: '+str(backup)+'\n'+'\n'.join(recovery_errors)) from failure
            log('설치가 중단되어 변경 파일을 원래 상태로 복구했습니다.')
            if isinstance(failure,PermissionError):raise access_error(failure.filename2 or failure.filename or mods,failure) from failure
            raise
