'use strict';
const controls=[...document.querySelectorAll('input[name="version"]')];
const byId=id=>document.getElementById(id);
let selected='1.21.8',busy=false;
async function loadMetadata(file){
 for(const url of [file+'?v=20261125-zombie','https://raw.githubusercontent.com/churigame1234-ux/gunbed-installer/main/docs/'+file]){
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),10000);
  try{const response=await fetch(url,{cache:'no-store',signal:controller.signal});if(!response.ok)throw Error('metadata');return await response.json();}
  catch{}finally{clearTimeout(timer);}
 }
 throw Error('다운로드 정보에 연결하지 못했습니다. 잠시 후 다시 시도하세요.');
}
let metadata=loadMetadata('downloads.json'),manualMetadata=loadMetadata('manual-downloads.json');
metadata.catch(()=>{});manualMetadata.catch(()=>{});
function updateManual(data){
 const entry=data.versions[selected];if(!entry)return;
 byId('manual-size').textContent=(entry.downloadBytes/1048576).toFixed(1)+' MB · 모드 6개';
 const list=byId('individual-links');list.replaceChildren();
 for(const file of entry.files){
  const li=document.createElement('li'),link=document.createElement('a');
  link.href=file.urls[0];link.textContent=file.file;link.target='_blank';link.rel='noopener';
  const hash=document.createElement('code');hash.textContent='SHA-256: '+file.sha256;
  li.append(link,hash);list.appendChild(li);
 }
}
function choose(version){
 if(busy||!controls.some(input=>input.value===version))return;
 selected=version;byId('chosen').textContent=version;byId('manual-version').textContent=version;
 byId('profile-name').textContent='Gunbed '+version;
 byId('download-label').textContent='자동 설치 EXE · '+version;
 byId('manual-label').textContent='수동 설치 ZIP · '+version;
 byId('download').download='GunbedInstaller-'+version+'.exe';
 byId('download-status').textContent='연결 실패 시 대체 경로로 자동 전환 · SHA-256 검증';
 metadata.then(updateInstaller).catch(()=>{});
 manualMetadata.then(updateManual).catch(()=>{});
}
controls.forEach(input=>input.addEventListener('change',()=>choose(input.value)));
const requested=new URLSearchParams(location.search).get('version');
if(requested&&controls.some(input=>input.value===requested)){controls.find(input=>input.value===requested).checked=true;choose(requested);}
byId('server').addEventListener('click',async()=>{
 try{await navigator.clipboard.writeText('mzs123.mcv.kr');document.querySelector('.copy-label').textContent='복사 완료 ✓';byId('copy-status').textContent='서버 주소를 복사했습니다.';setTimeout(()=>document.querySelector('.copy-label').textContent='주소 복사 ⧉',2500);}
 catch{document.querySelector('.copy-label').textContent='mzs123.mcv.kr';byId('copy-status').textContent='서버 주소: mzs123.mcv.kr';}
});
function updateInstaller(data){
 document.querySelectorAll('[data-installer-version]').forEach(label=>label.textContent=data.version);
 byId('download-size').textContent=(data.online_bytes/1048576).toFixed(1)+' MB · Windows EXE';
 byId('mirror-zip').href=data.archive.url;
 byId('installer-hash').textContent=data.versions.find(v=>v.version===selected).sha256;
}
metadata.then(updateInstaller).catch(()=>{byId('installer-hash').textContent='정보를 받지 못했습니다. 공식 GitHub 배포본의 SHA256SUMS.txt를 확인하세요.';});
manualMetadata.then(updateManual).catch(()=>{byId('manual-size').textContent='연결 후 용량 확인 · 모드 6개';});
function lock(value){
 busy=value;controls.forEach(input=>input.disabled=value);
 for(const id of ['download','manual-download']){
  if(value)byId(id).setAttribute('aria-disabled','true');else byId(id).removeAttribute('aria-disabled');
 }
 byId('manual-download').disabled=value;
}
function save(blob,filename){
 const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=filename;
 document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
}
byId('download').addEventListener('click',async event=>{
 event.preventDefault();if(busy)return;lock(true);
 const version=selected,status=byId('download-status');
 try{
  status.textContent='다운로드 경로를 확인하고 있습니다…';
  const data=await metadata,entry=data.versions.find(v=>v.version===version);
  if(!entry)throw Error('지원하지 않는 버전입니다.');
  const sources=[{url:data.direct_url,size:entry.size,sha256:entry.sha256},
   {url:data.raw_url,size:entry.size,sha256:entry.sha256},
   {url:data.release_base+entry.file,size:entry.size,sha256:entry.sha256}];
  const result=await verifiedDownload(sources,{notify:(kind,source,received)=>{
   if(kind==='connect')status.textContent='EXE 파일을 받는 중…';
   if(kind==='progress')status.textContent='EXE 다운로드 '+Math.floor(received/source.size*100)+'%';
   if(kind==='fallback')status.textContent='연결이 지연되어 대체 경로로 전환합니다…';
  }});
  save(new Blob([result.data],{type:'application/octet-stream'}),entry.file);
  status.textContent='무결성 검증 완료. '+entry.file+'를 저장합니다. 경고가 뜨면 아래 안내를 확인하세요.';
 }catch(error){status.textContent=error.message+' 아래 다른 다운로드도 사용할 수 있습니다.';metadata=loadMetadata('downloads.json');metadata.catch(()=>{});}
 finally{lock(false);}
});
byId('manual-download').addEventListener('click',async()=>{
 if(busy)return;lock(true);const version=selected,status=byId('download-status');
 try{
  status.textContent='수동 설치 모드 정보를 확인하고 있습니다…';
  const original=byId('tissou-original').files[0];if(!original)throw Error('수동 ZIP용 Tissou 2.7 원본을 먼저 선택하세요. 자동 설치기는 이 과정이 필요하지 않습니다.');
  const data=await manualMetadata,entry=data.versions[version];
  const blob=await GunbedManualPack.prepare(entry,data,verifiedDownload,(kind,n,file,received)=>{
   if(kind==='file'||kind==='connect')status.textContent='모드 '+(n+1)+'/5 다운로드 · '+file.file;
   if(kind==='progress')status.textContent='모드 '+(n+1)+'/5 · '+Math.floor(received/file.size*100)+'% · '+file.file;
   if(kind==='fallback')status.textContent='모드 '+(n+1)+'/5 연결 지연 · 대체 경로로 전환합니다…';
   if(kind==='zip')status.textContent='모드 6개 검증 완료 · ZIP으로 묶고 있습니다…';
  },new Uint8Array(await original.arrayBuffer()));
  save(blob,entry.filename);status.textContent='수동 설치 ZIP을 저장합니다. 압축을 풀고 아래 ZIP 넣는 방법을 따라주세요.';
 }catch(error){status.textContent=error.message+' 아래 ‘모드 개별 다운로드’도 사용할 수 있습니다.';manualMetadata=loadMetadata('manual-downloads.json');manualMetadata.catch(()=>{});}
 finally{lock(false);}
});
