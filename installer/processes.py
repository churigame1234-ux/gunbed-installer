"""Stop only Minecraft Launcher images; never terminate Java/game/server processes."""
import csv,io,os,subprocess,time

LAUNCHERS={'minecraftlauncher.exe','minecraftlauncherbeta.exe'}
def launcher_processes():
    if os.name!='nt':return []
    process=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW,timeout=15)
    if process.returncode:raise RuntimeError('실행 중인 런처를 확인하지 못했습니다.')
    return [(int(row[1]),row[0]) for row in csv.reader(io.StringIO(process.stdout)) if len(row)>1 and row[0].lower() in LAUNCHERS and row[1].isdigit()]
def stop_launchers(log=lambda message:None):
    stopped=[]
    for attempt in range(5):
        processes=launcher_processes()
        if not processes:return stopped
        for pid,name in processes:
            log('남아 있는 Minecraft Launcher 종료 중…')
            subprocess.run(['taskkill','/PID',str(pid),'/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=15)
            stopped.append(pid)
        time.sleep(.35)
    if launcher_processes():raise RuntimeError('런처를 종료할 권한이 없습니다. 설치기를 관리자 권한으로 실행해주세요. 게임·Java·서버 프로세스는 종료하지 않았습니다.')
    return stopped
