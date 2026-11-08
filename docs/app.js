'use strict';
const controls=[...document.querySelectorAll('input[name="version"]')];
let selected='1.21.8',busy=false;
async function loadMetadata(){
 for(const url of ['downloads.json?v=0.3.14','https://raw.githubusercontent.com/churigame1234-ux/gunbed-installer/main/docs/downloads.json']){
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),10000);
  try{const response=await fetch(url,{cache:'no-store',signal:controller.signal});if(!response.ok)throw Error('metadata');return await response.json();}
  catch{}finally{clearTimeout(timer);}
 }
 throw Error('다운로드 정보에 연결하지 못했습니다.');
}
const metadata=loadMetadata();
metadata.catch(()=>{});
function choose(version){
 if(!controls.some(input=>input.value===version))return;
 selected=version;
 document.getElementById('chosen').textContent=version;
 document.getElementById('profile-name').textContent='Gunbed '+version;
 document.getElementById('download-label').textContent=version+' 설치기 다운로드';
 document.getElementById('download').download='GunbedInstaller-'+version+'.exe';
}
controls.forEach(input=>input.addEventListener('change',()=>choose(input.value)));
const requested=new URLSearchParams(location.search).get('version');
if(requested&&controls.some(input=>input.value===requested)){controls.find(input=>input.value===requested).checked=true;choose(requested)}
document.getElementById('server').addEventListener('click',async()=>{
 try{await navigator.clipboard.writeText('mzs123.mcv.kr');document.querySelector('.copy-label').textContent='복사 완료 ✓';document.getElementById('copy-status').textContent='서버 주소를 복사했습니다.';setTimeout(()=>document.querySelector('.copy-label').textContent='주소 복사 ⧉',2500)}
 catch{document.querySelector('.copy-label').textContent='mzs123.mcv.kr';document.getElementById('copy-status').textContent='서버 주소: mzs123.mcv.kr'}
});
metadata.then(data=>{
 document.getElementById('download-size').textContent=(data.online_bytes/1048576).toFixed(1)+' MB · Windows EXE';
 document.getElementById('mirror-zip').href=data.archive.url;
 document.getElementById('offline-download').href=data.offline.url;
}).catch(()=>{});
document.getElementById('download').addEventListener('click',async event=>{
 event.preventDefault();if(busy)return;busy=true;
 const version=selected,button=document.getElementById('download'),status=document.getElementById('download-status');
 button.setAttribute('aria-disabled','true');controls.forEach(input=>input.disabled=true);
 try{
  status.textContent='다운로드 경로를 확인하고 있습니다…';
  const data=await metadata,entry=data.versions.find(v=>v.version===version);
  if(!entry)throw Error('지원하지 않는 버전입니다.');
  const sources=[{url:data.direct_url,size:entry.size,sha256:entry.sha256},
   {url:data.raw_url,size:entry.size,sha256:entry.sha256},
   {url:data.release_base+entry.file,size:entry.size,sha256:entry.sha256}];
  const result=await verifiedDownload(sources,{notify:(kind,source,received)=>{
   if(kind==='connect')status.textContent='파일을 받는 중…';
   if(kind==='progress')status.textContent='다운로드 '+Math.floor(received/source.size*100)+'%';
   if(kind==='fallback')status.textContent='연결이 지연되어 대체 경로로 전환합니다…';
  }});
  const objectURL=URL.createObjectURL(new Blob([result.data],{type:result.source.archive?'application/zip':'application/octet-stream'}));
  const link=document.createElement('a');link.href=objectURL;link.download=result.source.archive?'GunbedInstaller-'+version+'.zip':entry.file;
  document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(objectURL),60000);
  status.textContent=result.source.archive?'검증 완료. ZIP 압축을 풀고 설치기에서 '+version+' 버전을 선택하세요.':'검증 완료. 다운로드한 '+entry.file+'를 실행하세요.';
 }catch(error){status.textContent=error.message+' 아래의 ZIP 대체 다운로드도 사용할 수 있습니다.';}
 finally{busy=false;button.removeAttribute('aria-disabled');controls.forEach(input=>input.disabled=false);}
});
