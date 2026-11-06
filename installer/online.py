"""Fetch only the selected version from public GitHub Releases, verifying every file."""
import hashlib,json,os,time,urllib.request,zipfile
from pathlib import Path
from engine import Installer,atomic,digest

class OnlineInstaller(Installer):
    def __init__(self,metadata):
        self.metadata=Path(metadata)
        self.release=json.loads((self.metadata/'online.json').read_text(encoding='utf-8'))
        super().__init__(metadata)
    def fetch(self,url,expected,filename,log):
        cache=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.cache'))/'GunbedInstaller/cache'/self.release['tag']/'files'
        cache.mkdir(parents=True,exist_ok=True);target=cache/(expected+'-'+filename)
        if target.exists() and digest(target.read_bytes())==expected:return target
        if not url.startswith(self.release['asset_base']+'/'):raise ValueError('잘못된 다운로드 주소입니다.')
        for attempt in range(3):
            temporary=target.with_suffix('.part-'+str(os.getpid()))
            try:
                request=urllib.request.Request(url,headers={'User-Agent':'GunbedInstaller/0.3.6'})
                with urllib.request.urlopen(request,timeout=35) as response,temporary.open('wb') as output:
                    total=int(response.headers.get('Content-Length',0));received=0;last=0;sha=hashlib.sha256()
                    while block:=response.read(1024*1024):
                        output.write(block);sha.update(block);received+=len(block)
                        if received-last>=8*1024*1024:
                            log(filename+' · '+str(received//1048576)+' / '+(str(total//1048576)+' MB' if total else '? MB'));last=received
                if sha.hexdigest()!=expected:raise ValueError('다운로드 무결성 검증 실패: '+filename)
                os.replace(temporary,target);return target
            except Exception:
                temporary.unlink(missing_ok=True)
                if attempt==2:raise
                log('다운로드 재시도 중…');time.sleep(.5)
    def prepare(self,version,log):
        chosen=self.manifest['versions'][version]
        folder=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.cache'))/'GunbedInstaller/cache'/self.release['tag']/version
        folder.mkdir(parents=True,exist_ok=True)
        self.payload=folder
        for v,data in self.manifest['versions'].items():atomic(folder/data['profile'],(self.metadata/data['profile']).read_bytes())
        atomic(folder/'manifest.json',(self.metadata/'manifest.json').read_bytes())
        log('GitHub에서 '+version+'의 필수 파일만 다운로드합니다.')
        mod_files=[]
        for entry in chosen['mods']:
            log('확인: '+entry['file']);mod_files.append((entry,self.fetch(entry['url'],entry['sha256'],entry['file'],log)))
        for entry in chosen['libraries']:
            source=self.fetch(entry['url'],entry['sha256'],Path(entry['target']).name,log)
            target=folder/entry['path']
            if not target.exists() or digest(target.read_bytes())!=entry['sha256']:atomic(target,source.read_bytes())
        temporary=folder/('clients-'+str(os.getpid())+'.zip')
        with zipfile.ZipFile(temporary,'w',zipfile.ZIP_STORED) as archive:
            for entry,path in mod_files:archive.write(path,entry['path'])
            for name in ('THIRD-PARTY.md','licenses/Nuit-MIT.txt'):archive.write(self.metadata/name,name)
            archive.writestr('source/source-links.json',json.dumps(self.release['sources'],ensure_ascii=False,indent=2))
        os.replace(temporary,folder/'clients.zip')
    def install(self,root,version,game_dir=None,log=lambda message:None):
        self.locations(root,version,game_dir)
        self.prepare(version,log)
        from processes import stop_launchers
        stop_launchers(log)
        return super().install(root,version,game_dir,log)
