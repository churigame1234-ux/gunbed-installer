"""Diagnose Windows file locks without closing games or changing ACLs."""
import contextlib, os, stat, uuid
from pathlib import Path


class InstallAccessError(RuntimeError):
    pass


def file_users(paths):
    if os.name != 'nt':
        return []
    import ctypes as c
    from ctypes import wintypes as w

    class UniqueProcess(c.Structure):
        _fields_ = [('pid', w.DWORD), ('started', w.FILETIME)]

    class ProcessInfo(c.Structure):
        _fields_ = [('process', UniqueProcess), ('name', w.WCHAR * 256),
                    ('service', w.WCHAR * 64), ('kind', c.c_int), ('status', w.ULONG),
                    ('session', w.DWORD), ('restartable', w.BOOL)]

    rm = c.WinDLL('rstrtmgr')
    rm.RmStartSession.argtypes = [c.POINTER(w.DWORD), w.DWORD, w.LPWSTR]
    rm.RmRegisterResources.argtypes = [w.DWORD, w.UINT, c.POINTER(w.LPCWSTR), w.UINT,
                                       c.POINTER(UniqueProcess), w.UINT, c.POINTER(w.LPCWSTR)]
    rm.RmGetList.argtypes = [w.DWORD, c.POINTER(w.UINT), c.POINTER(w.UINT),
                             c.POINTER(ProcessInfo), c.POINTER(w.DWORD)]
    rm.RmEndSession.argtypes = [w.DWORD]
    session = w.DWORD()
    if rm.RmStartSession(c.byref(session), 0, c.create_unicode_buffer(33)):
        return []
    try:
        names = [str(Path(p).resolve()) for p in paths if Path(p).is_file()]
        if not names or rm.RmRegisterResources(session, len(names), (w.LPCWSTR * len(names))(*names), 0, None, 0, None):
            return []
        needed, count, reasons = w.UINT(), w.UINT(), w.DWORD()
        for _ in range(3):
            entries = (ProcessInfo * count.value)() if count.value else None
            result = rm.RmGetList(session, c.byref(needed), c.byref(count), entries, c.byref(reasons))
            if result == 0:
                return [{'pid': entries[i].process.pid, 'name': entries[i].name} for i in range(count.value)]
            if result != 234:
                return []
            count.value = needed.value
        return []
    finally:
        rm.RmEndSession(session)


def access_error(path, error):
    path = Path(path)
    code = getattr(error, 'winerror', None)
    try:
        users = file_users([path])
    except OSError:
        users = []
    if users or code in (32, 33):
        owners = '\n'.join(p['name'] + ' (PID ' + str(p['pid']) + ')' for p in users)
        return InstallAccessError(
            '모드 파일을 다른 프로그램이 사용 중이라 교체할 수 없습니다.\n' + str(path) +
            ('\n\n사용 중인 프로그램:\n' + owners if owners else '') +
            '\n\n런처뿐 아니라 해당 마인크래프트 게임 창도 종료한 뒤 다시 설치하세요. '
            '작업 관리자에서는 위 PID를 확인하세요. 관리자 실행만으로 파일 잠금은 풀리지 않습니다.')
    return InstallAccessError(
        '설치 경로에 파일을 변경할 권한이 없습니다.\n' + str(path) +
        '\n\n게임을 종료한 상태에서 설치기를 우클릭 → 관리자 권한으로 실행해 다시 시도하세요. '
        '계속 거부되면 Windows 보안의 보호 기록에서 설치기 차단 여부를 확인하세요.\n' + str(error))


def preflight_files(paths):
    """Request delete/rename access but do not rename, truncate or delete any file."""
    if os.name != 'nt':
        return
    import ctypes as c
    from ctypes import wintypes as w
    kernel = c.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, c.c_void_p,
                                   w.DWORD, w.DWORD, w.HANDLE]
    kernel.CreateFileW.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    for path in dict.fromkeys(paths):
        if not path.exists():
            continue
        handle = kernel.CreateFileW(str(path), 0x10000, 7, None, 3, 0, None)
        if handle == c.c_void_p(-1).value:
            error = c.WinError(c.get_last_error())
            if error.winerror == 5 and path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
                # Only a verified required mod reaches this point. Its read-only flag
                # is cleared after its backup is durable, inside the transaction.
                if not file_users([path]):
                    continue
            raise access_error(path, error) from error
        kernel.CloseHandle(handle)


def probe_directory(directory):
    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / ('.gunbed-access-' + uuid.uuid4().hex + '.tmp')
    renamed = temporary.with_suffix('.checked')
    try:
        temporary.write_bytes(b'Gunbed installer access check')
        os.replace(temporary, renamed)
        renamed.unlink()
    except PermissionError as error:
        raise access_error(directory, error) from error
    finally:
        with contextlib.suppress(OSError):temporary.unlink(missing_ok=True)
        with contextlib.suppress(OSError):renamed.unlink(missing_ok=True)


def clear_readonly(path):
    if os.name == 'nt' and path.exists() and path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
        path.chmod(stat.S_IWRITE)
