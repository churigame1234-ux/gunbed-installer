'use strict';
// STORE ZIP: the JARs are already compressed. No executable or remote ZIP library.
const GunbedManualPack=(()=>{
 const table=new Uint32Array(256);
 for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=(c&1)?0xedb88320^(c>>>1):c>>>1;table[n]=c>>>0;}
 const crc32=data=>{let c=0xffffffff;for(let n=0;n<data.length;n++)c=table[(c^data[n])&255]^(c>>>8);return (c^0xffffffff)>>>0;};
 function zip(files){
  const parts=[],central=[];let offset=0,size=0;
  if(files.length>65535)throw Error('ZIP 파일 수를 초과했습니다.');
  for(const file of files){
   if(!file.name||file.name.startsWith('/')||file.name.split('/').some(p=>p==='..'||p===''||p.includes('\\')))throw Error('잘못된 ZIP 경로입니다.');
   const name=new TextEncoder().encode(file.name),data=typeof file.data==='string'?new TextEncoder().encode(file.data):file.data;
   if(!(data instanceof Uint8Array)||name.length>65535||offset+data.length+name.length+30>0xffffffff)throw Error('지원하지 않는 ZIP 크기입니다.');
   const crc=crc32(data),local=new Uint8Array(30+name.length),l=new DataView(local.buffer);
   l.setUint32(0,0x04034b50,true);l.setUint16(4,20,true);l.setUint16(6,0x800,true);l.setUint16(12,0x5d74,true);l.setUint32(14,crc,true);l.setUint32(18,data.length,true);l.setUint32(22,data.length,true);l.setUint16(26,name.length,true);local.set(name,30);
   const entry=new Uint8Array(46+name.length),e=new DataView(entry.buffer);
   e.setUint32(0,0x02014b50,true);e.setUint16(4,20,true);e.setUint16(6,20,true);e.setUint16(8,0x800,true);e.setUint16(14,0x5d74,true);e.setUint32(16,crc,true);e.setUint32(20,data.length,true);e.setUint32(24,data.length,true);e.setUint16(28,name.length,true);e.setUint32(42,offset,true);entry.set(name,46);
   parts.push(local,data);central.push(entry);offset+=local.length+data.length;size+=entry.length;
  }
  const end=new Uint8Array(22),e=new DataView(end.buffer);e.setUint32(0,0x06054b50,true);e.setUint16(8,files.length,true);e.setUint16(10,files.length,true);e.setUint32(12,size,true);e.setUint32(16,offset,true);
  return new Blob([...parts,...central,end],{type:'application/zip'});
 }
 function instructions(version,loader){return `Gunbed ${version} 수동 설치\r\n\r\n이 ZIP에는 EXE 설치기와 Fabric Loader가 없습니다. mods 폴더의 필수 모드 4개를 직접 설치하는 묶음입니다.\r\n\r\n1. Minecraft와 런처를 종료합니다.\r\n2. 런처에서 Minecraft ${version} + Fabric Loader ${loader}를 준비합니다. Fabric 공식 안내: https://fabricmc.net/use/installer/\r\n   Fabric을 지원하는 별도 런처는 해당 런처의 모드 로더 설정을 이용하세요. Forge/NeoForge 프로필은 사용할 수 없습니다.\r\n3. 실행 설정의 '게임 디렉터리'를 확인하고 그 안의 mods 폴더를 엽니다. 없으면 만듭니다.\r\n   기본 경로: %APPDATA%\\.minecraft\\mods\r\n   별도 게임 폴더 예: %APPDATA%\\.minecraft\\1.21.8 mod\\mods\r\n4. 기존 GunbedVisuals, GunbedAssets, Fabric API, Nuit가 있으면 중복되지 않도록 mods 밖의 백업 폴더로 옮깁니다. 다른 모드·설정·월드는 지우지 마세요.\r\n5. 이 ZIP의 mods 폴더 안에 있는 .jar 4개를 실제 게임 폴더의 mods 안에 복사합니다. JAR 파일 자체는 압축을 풀지 않습니다.\r\n6. Minecraft ${version}의 Fabric 프로필로 실행하고 mzs123.mcv.kr에 접속한 뒤 Gunbed를 선택합니다.\r\n\r\nZIP의 게임 버전과 실행 프로필을 맞추세요. SHA256SUMS.txt는 모드 파일의 무결성 확인용입니다.\r\n출처·라이선스는 THIRD-PARTY.md와 SOURCE-LINKS.json을 확인하세요. 다운로드 파일은 보안 검사의 대상이며 ZIP도 안전을 보장하는 형식은 아닙니다.\r\n`;}
 async function prepare(entry,metadata,download,notify=()=>{}){
  if(!entry||entry.files.length!==4)throw Error('수동 설치 파일 정보를 확인할 수 없습니다.');
  const files=[];let sums='';
  for(let n=0;n<entry.files.length;n++){
   const f=entry.files[n];if(!/^[a-zA-Z0-9_.+()-]+\.jar$/.test(f.file))throw Error('잘못된 모드 파일 이름입니다.');
   notify('file',n,f);const result=await download(f.urls.map(url=>({url,size:f.size,sha256:f.sha256})),{timeout:180000,notify:(kind,source,received)=>notify(kind,n,f,received)});
   files.push({name:'mods/'+f.file,data:result.data});sums+=f.sha256+'  mods/'+f.file+'\r\n';
  }
  files.push({name:'설치방법.txt',data:'\ufeff'+instructions(entry.version,metadata.loader)},{name:'SHA256SUMS.txt',data:sums},{name:'THIRD-PARTY.md',data:metadata.thirdParty},{name:'licenses/Nuit-MIT.txt',data:metadata.nuitLicense},{name:'SOURCE-LINKS.json',data:JSON.stringify(metadata.sourceLinks,null,2)});
  notify('zip');return zip(files);
 }
 return {crc32,zip,instructions,prepare};
})();
if(typeof module!=='undefined')module.exports=GunbedManualPack;
