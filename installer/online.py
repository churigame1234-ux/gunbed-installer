"""Fetch the selected version from pinned mirrors, verifying every file."""
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
        # Mirrors are bundled into the signed-by-hash release metadata, never
        # fetched from an editable remote manifest. Old bootstrap files still work.
        mirrors=self.release.get('mirrors',{}).get(expected,[])
        urls=list(dict.fromkeys(mirrors+[url]))
        from urllib.parse import urlparse
        allowed={'churigame1234-ux.github.io','raw.githubusercontent.com','github.com'}
        if any(urlparse(u).scheme!='https' or urlparse(u).hostname not in allowed or urlparse(u).username for u in urls):
            raise ValueError('잘못된 대체 다운로드 주소입니다.')
        errors=[]
        for attempt in range(2):
          for source in urls:
            temporary=target.with_suffix('.part-'+str(os.getpid()))
            try:
                log(filename+' · '+urlparse(source).hostname+' 연결 중…')
                request=urllib.request.Request(source,headers={'User-Agent':'GunbedInstaller/0.3.14'})
                started=time.monotonic()
                with urllib.request.urlopen(request,timeout=20) as response,temporary.open('wb') as output:
                    total=int(response.headers.get('Content-Length',0));received=0;last=0;sha=hashlib.sha256()
                    while block:=response.read(1024*1024):
                        if time.monotonic()-started>180:raise TimeoutError('파일 다운로드 제한 시간 초과')
                        output.write(block);sha.update(block);received+=len(block)
                        if received-last>=8*1024*1024:
                            log(filename+' · '+str(received//1048576)+' / '+(str(total//1048576)+' MB' if total else '? MB'));last=received
                if total and received!=total:raise ValueError('다운로드가 중간에 끊겼습니다: '+filename)
                if sha.hexdigest()!=expected:raise ValueError('다운로드 무결성 검증 실패: '+filename)
                os.replace(temporary,target);return target
            except (OSError,ValueError) as error:
                temporary.unlink(missing_ok=True)
                errors.append(urlparse(source).hostname+': '+str(error))
                log('이 경로에서 받지 못했습니다. 다른 다운로드 경로로 전환합니다.')
          if attempt==0:time.sleep(1)
        raise OSError('모든 다운로드 경로에 연결하지 못했습니다. 잠시 후 재시도하거나 사이트의 오프라인 설치기를 이용하세요.\n'+filename+'\n'+'\n'.join(errors[-len(urls):]))
    def prepare(self,version,log):
        chosen=self.manifest['versions'][version]
        folder=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.cache'))/'GunbedInstaller/cache'/self.release['tag']/version
        folder.mkdir(parents=True,exist_ok=True)
        self.payload=folder
        for v,data in self.manifest['versions'].items():atomic(folder/data['profile'],(self.metadata/data['profile']).read_bytes())
        atomic(folder/'manifest.json',(self.metadata/'manifest.json').read_bytes())
        log(version+'의 필수 파일만 다운로드합니다. 연결 실패 시 대체 경로로 자동 전환합니다.')
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
