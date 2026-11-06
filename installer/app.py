"""Windows GUI and explicit CLI for the offline Gunbed installer."""
import argparse,json,os,queue,re,sys,threading,traceback
from pathlib import Path
from engine import Installer
from processes import stop_launchers

def resources():return Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))/'payload'
def main():
    filename=re.search(r'GunbedInstaller-([0-9.]+)(?:\s*\(\d+\))?\.exe$',Path(sys.executable).name,re.I)
    parser=argparse.ArgumentParser();parser.add_argument('--install',action='store_true');parser.add_argument('--version',default=filename[1] if filename else '1.21.8');parser.add_argument('--minecraft-dir');parser.add_argument('--game-dir');parser.add_argument('--result-json');parser.add_argument('--smoke-gui',action='store_true')
    args=parser.parse_args()
    if (resources()/'online.json').exists():
        from online import OnlineInstaller
        engine=OnlineInstaller(resources())
    else:engine=Installer(resources())
    root=Path(args.minecraft_dir or Path(os.environ.get('APPDATA',Path.home()))/'.minecraft')
    if args.install:
        result={}
        try:
            engine.locations(root,args.version,args.game_dir)
            stop_launchers()
            result=engine.install(root,args.version,args.game_dir)
        except Exception as e:result={'success':False,'error':str(e)}
        if args.result_json:Path(args.result_json).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        if sys.stdout:print(json.dumps(result,ensure_ascii=True))
        return 0 if result['success'] else 1
    import tkinter as tk
    from tkinter import ttk,filedialog,messagebox
    window=tk.Tk();window.title('Gunbed 모드 설치기 0.3.1');window.geometry('740x680');window.minsize(680,650);window.configure(bg='#0f172a')
    window.option_add('*Font',('맑은 고딕',10))
    style=ttk.Style(window);style.theme_use('clam')
    style.configure('TFrame',background='#0f172a');style.configure('TLabel',background='#0f172a',foreground='#e2e8f0');style.configure('Sub.TLabel',foreground='#94a3b8');style.configure('Title.TLabel',font=('맑은 고딕',23,'bold'),foreground='#f8fafc');style.configure('Accent.TButton',font=('맑은 고딕',12,'bold'),padding=12,background='#38bdf8',foreground='#082f49');style.configure('TButton',padding=6);style.configure('TProgressbar',background='#38bdf8')
    frame=ttk.Frame(window,padding=28);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Gunbed 모드 설치기',style='Title.TLabel').pack(anchor='w')
    ttk.Label(frame,text='게임 버전을 고르면 Loader와 필수 모드를 함께 설치합니다.',style='Sub.TLabel').pack(anchor='w',pady=(5,22))
    version=tk.StringVar(value=args.version);directory=tk.StringVar(value=str(root));target=tk.StringVar();footer=tk.StringVar();status=tk.StringVar(value='설치를 누르면 남아 있는 Minecraft Launcher를 자동 종료합니다.')
    ttk.Label(frame,text='마인크래프트 버전').pack(anchor='w')
    combo=ttk.Combobox(frame,textvariable=version,values=engine.versions,state='readonly',font=('맑은 고딕',12));combo.pack(fill='x',pady=(5,15))
    ttk.Label(frame,text='설치할 게임 폴더 또는 mods 폴더').pack(anchor='w')
    row=ttk.Frame(frame);row.pack(fill='x',pady=(5,9));entry=ttk.Entry(row,textvariable=directory);entry.pack(side='left',fill='x',expand=True)
    def refresh(*_):
        footer.set('설치 후 기존 런처에서 “Gunbed '+version.get()+'”을 선택하고 플레이하세요.')
        try:
            actual,game=engine.locations(Path(directory.get()),version.get(),args.game_dir)
            target.set('모드: '+str(game/'mods')+'\nLoader: '+str(actual))
        except Exception:target.set('설치 경로를 확인해주세요.')
    def browse():
        selected=filedialog.askdirectory(parent=window,title='게임 폴더 또는 mods 폴더 선택',initialdir=directory.get())
        if selected:directory.set(selected)
    choose=ttk.Button(row,text='폴더 선택',command=browse);choose.pack(side='right',padx=(8,0))
    ttk.Label(frame,textvariable=target,style='Sub.TLabel',wraplength=670).pack(anchor='w')
    ttk.Label(frame,text='다른 모드 · 설정 · 월드는 그대로 유지합니다.',foreground='#86efac').pack(anchor='w',pady=(18,3))
    ttk.Label(frame,text='동일한 모드 ID 4종만 백업 후 교체합니다. Fabric Loader 0.19.5 포함.',style='Sub.TLabel',wraplength=670).pack(anchor='w')
    messages=queue.Queue();busy=False;installed=None
    def worker(root_path,selected_version):
        try:
            engine.locations(root_path,selected_version,args.game_dir)
            stop_launchers(lambda m:messages.put(('log',m)))
            result=engine.install(root_path,selected_version,args.game_dir,lambda m:messages.put(('log',m)))
            messages.put(('success',result))
        except Exception as e:messages.put(('error',str(e)))
    def install():
        nonlocal busy
        root_path=Path(directory.get());selected_version=version.get();busy=True;button.configure(state='disabled');combo.configure(state='disabled');entry.configure(state='disabled');choose.configure(state='disabled');progress.start(12);status.set('설치 중입니다…');threading.Thread(target=worker,args=(root_path,selected_version),daemon=True).start()
    button=ttk.Button(frame,text='선택한 버전 설치',style='Accent.TButton',command=install);button.pack(fill='x',pady=(20,12))
    progress=ttk.Progressbar(frame,mode='indeterminate');progress.pack(fill='x')
    ttk.Label(frame,textvariable=status,wraplength=670).pack(anchor='w',pady=(9,6))
    logs=tk.Text(frame,height=5,bg='#1e293b',fg='#cbd5e1',relief='flat',font=('맑은 고딕',9),padx=10,pady=8,state='disabled');logs.pack(fill='both',expand=True)
    ttk.Label(frame,textvariable=footer,style='Sub.TLabel',wraplength=670).pack(anchor='w',pady=(12,0))
    def pump():
        nonlocal busy,installed
        try:
            while True:
                kind,value=messages.get_nowait()
                if kind=='log':logs.configure(state='normal');logs.insert('end',value+'\n');logs.see('end');logs.configure(state='disabled')
                else:
                    busy=False;progress.stop();button.configure(state='normal');combo.configure(state='readonly');entry.configure(state='normal');choose.configure(state='normal')
                    if kind=='success':
                        installed=value;status.set('완료! 런처에서 “'+value['launcher_profile']+'”을 선택하세요.');messagebox.showinfo('설치 완료',value['launcher_profile']+' 설치 완료\n\nFabric Loader '+value['loader']+'\n다른 모드 '+str(len(value['preserved_other_mods']))+'개 보존\n\n기존 런처에서 이 실행 설정을 선택하고 플레이하세요.',parent=window)
                    else:status.set('설치하지 못했습니다. 아래 내용을 확인해주세요.');messagebox.showerror('설치 확인',value,parent=window)
        except queue.Empty:pass
        window.after(100,pump)
    def close():
        if busy:messagebox.showinfo('설치 중','설치가 끝날 때까지 잠시 기다려주세요.',parent=window)
        else:window.destroy()
    window.protocol('WM_DELETE_WINDOW',close);directory.trace_add('write',refresh);version.trace_add('write',refresh);refresh();window.after(100,pump)
    if args.smoke_gui:
        def smoke():
            window.update_idletasks()
            clipped=[]
            def check(widget):
                if widget.winfo_ismapped() and widget.winfo_rooty()+widget.winfo_height()>window.winfo_rooty()+window.winfo_height()+2:clipped.append(str(widget))
                for child in widget.winfo_children():check(child)
            check(frame)
            result={'success':len(combo['values'])==9 and window.winfo_width()>=680 and not clipped,'versions':list(combo['values']),'selected_version':version.get(),'size':[window.winfo_width(),window.winfo_height()],'clipped_widgets':clipped}
            if args.result_json:Path(args.result_json).write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
            window.destroy()
        window.after(900,smoke)
    window.mainloop();return 0
if __name__=='__main__':
    try:sys.exit(main())
    except Exception:
        # GUI executables have no console; retain a useful diagnostic locally.
        path=Path(os.environ.get('TEMP','.'))/'GunbedInstaller-error.log';path.write_text(traceback.format_exc(),encoding='utf-8')
        import tkinter.messagebox
        tkinter.messagebox.showerror('Gunbed 설치 오류','설치기를 시작하지 못했습니다.\n'+str(path))
        raise
