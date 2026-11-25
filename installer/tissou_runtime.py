"""Fetch the creator's pinned original and derive private assets locally, before modifying Minecraft."""
from pathlib import Path
import hashlib,os,time,urllib.request
from tissou_local import EXPECTED,build

URL='https://mediafilez.forgecdn.net/files/4750/306/TZP_1.20.1_2.7.zip'
def local_assets(log=lambda message:None):
    cache=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.cache'))/'GunbedInstaller/cache/tissou-2.7'
    cache.mkdir(parents=True,exist_ok=True);source=cache/'TZP_1.20.1_2.7.zip'
    if not source.exists() or hashlib.sha256(source.read_bytes()).hexdigest()!=EXPECTED:
        log('좀비 외형 원본을 제작자 배포처에서 다운로드합니다…')
        temporary=source.with_suffix('.part-'+str(os.getpid()))
        try:
            started=time.monotonic();sha=hashlib.sha256();size=0
            request=urllib.request.Request(URL,headers={'User-Agent':'GunbedZombieInstaller/0.3.21'})
            with urllib.request.urlopen(request,timeout=20) as response,temporary.open('wb') as output:
                while block:=response.read(1024*1024):
                    size+=len(block)
                    if size>50*1024*1024 or time.monotonic()-started>180:raise OSError('좀비 외형 다운로드 제한 시간을 초과했습니다.')
                    output.write(block);sha.update(block)
            if sha.hexdigest()!=EXPECTED:raise ValueError('좀비 외형 원본 검증에 실패했습니다. 설치 파일은 변경하지 않았습니다.')
            os.replace(temporary,source)
        finally:temporary.unlink(missing_ok=True)
    log('이 PC에서 사용할 좀비 외형을 준비합니다. OptiFine은 필요하지 않습니다.')
    temporary=cache/('Tissou-local-'+str(os.getpid())+'.jar')
    try:
        build(source,temporary)
        return temporary.read_bytes()
    finally:temporary.unlink(missing_ok=True)
