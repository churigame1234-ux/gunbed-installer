"""Best-effort cleanup of verified same-user/session Launcher images; file checks decide install access."""
import csv,io,os,subprocess,time
from pathlib import Path
from functools import lru_cache

LAUNCHERS={'minecraftlauncher.exe','minecraftlauncherbeta.exe'}

@lru_cache(maxsize=1)
def _windows_api():
    import ctypes as c
    from ctypes import wintypes as w
    kernel=c.WinDLL('kernel32',use_last_error=True);advapi=c.WinDLL('advapi32',use_last_error=True)
    kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];kernel.OpenProcess.restype=w.HANDLE
    kernel.CloseHandle.argtypes=[w.HANDLE]
    kernel.ProcessIdToSessionId.argtypes=[w.DWORD,c.POINTER(w.DWORD)]
    kernel.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)]
    kernel.TerminateProcess.argtypes=[w.HANDLE,w.UINT]
    kernel.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD]
    kernel.LocalFree.argtypes=[c.c_void_p];kernel.LocalFree.restype=c.c_void_p
    advapi.OpenProcessToken.argtypes=[w.HANDLE,w.DWORD,c.POINTER(w.HANDLE)]
    advapi.GetTokenInformation.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.POINTER(w.DWORD)]
    advapi.ConvertSidToStringSidW.argtypes=[c.c_void_p,c.POINTER(w.LPWSTR)]
    return c,w,kernel,advapi

def _handle_identity(handle,pid):
    c,w,kernel,advapi=_windows_api();session=w.DWORD();size=w.DWORD(32768);image=c.create_unicode_buffer(size.value)
    if not kernel.ProcessIdToSessionId(pid,c.byref(session)) or not kernel.QueryFullProcessImageNameW(handle,0,image,c.byref(size)):raise c.WinError(c.get_last_error())
    token=w.HANDLE()
    if not advapi.OpenProcessToken(handle,8,c.byref(token)):raise c.WinError(c.get_last_error())
    try:
        needed=w.DWORD();advapi.GetTokenInformation(token,1,None,0,c.byref(needed))
        if not needed.value:raise c.WinError(c.get_last_error())
        user=c.create_string_buffer(needed.value)
        if not advapi.GetTokenInformation(token,1,user,needed,c.byref(needed)):raise c.WinError(c.get_last_error())
        sid=c.cast(user,c.POINTER(c.c_void_p))[0];text=w.LPWSTR()
        if not advapi.ConvertSidToStringSidW(sid,c.byref(text)):raise c.WinError(c.get_last_error())
        try:return session.value,text.value,Path(image.value).name.lower()
        finally:kernel.LocalFree(c.cast(text,c.c_void_p))
    finally:kernel.CloseHandle(token)

def _identity(pid):
    if os.name!='nt':return None
    c,w,kernel,advapi=_windows_api();handle=kernel.OpenProcess(0x1000,False,pid)
    if not handle:return None
    try:return _handle_identity(handle,pid)
    except OSError:return None
    finally:kernel.CloseHandle(handle)

def launcher_processes():
    if os.name!='nt':return []
    process=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW,timeout=15)
    if process.returncode:raise RuntimeError('실행 중인 런처 목록 조회 실패')
    return [(int(row[1]),row[0]) for row in csv.reader(io.StringIO(process.stdout)) if len(row)>1 and row[0].lower() in LAUNCHERS and row[1].isdigit()]

def _terminate(pid,current):
    c,w,kernel,advapi=_windows_api();handle=kernel.OpenProcess(0x101001,False,pid)
    if not handle:raise c.WinError(c.get_last_error())
    try:
        identity=_handle_identity(handle,pid)
        # Recheck the actual open handle: PID reuse must never target another executable/account.
        if identity[:2]!=current[:2] or identity[2] not in LAUNCHERS:return False
        if not kernel.TerminateProcess(handle,0):raise c.WinError(c.get_last_error())
        return kernel.WaitForSingleObject(handle,1500)==0
    finally:kernel.CloseHandle(handle)

def stop_launchers(log=lambda message:None):
    if os.name!='nt':return []
    current=_identity(os.getpid())
    if current is None:
        log('런처 사용자 정보를 확인할 수 없어 설치 파일의 접근 권한을 직접 확인합니다.');return []
    stopped=[];skipped=set()
    for attempt in range(2):
        try:processes=launcher_processes()
        except (OSError,RuntimeError,subprocess.SubprocessError):
            log('런처 목록을 확인하지 못해 설치 파일의 접근 권한을 직접 확인합니다.');return stopped
        progress=False
        for pid,name in processes:
            if pid in skipped or pid in stopped:continue
            identity=_identity(pid)
            if identity is None:
                skipped.add(pid);log('런처 PID '+str(pid)+'의 사용자 정보를 확인하지 못해 파일 접근 검사로 계속합니다.');continue
            if identity[:2]!=current[:2] or identity[2] not in LAUNCHERS:
                skipped.add(pid);continue
            log('현재 사용자 Minecraft Launcher 정리 중 (PID '+str(pid)+')…')
            try:
                if _terminate(pid,current):stopped.append(pid);progress=True;continue
            except (OSError,subprocess.SubprocessError):pass
            skipped.add(pid);log('런처 PID '+str(pid)+'를 종료하지 못해 파일 접근 검사로 계속합니다. 설치 후 런처를 다시 열어주세요.')
        if not progress:break
        time.sleep(.2)
    return stopped
