'use strict';
const base='https://github.com/churigame1234-ux/gunbed-installer/releases/download/v0.3.13/';
const controls=[...document.querySelectorAll('input[name="version"]')];
function choose(version){
 if(!controls.some(input=>input.value===version))return;
 document.getElementById('chosen').textContent=version;
 document.getElementById('profile-name').textContent='Gunbed '+version;
 document.getElementById('download-label').textContent=version+' 설치기 다운로드';
 document.getElementById('download').href=base+'GunbedInstaller-'+version+'.exe';
}
controls.forEach(input=>input.addEventListener('change',()=>choose(input.value)));
const requested=new URLSearchParams(location.search).get('version');
if(requested&&controls.some(input=>input.value===requested)){controls.find(input=>input.value===requested).checked=true;choose(requested)}
document.getElementById('server').addEventListener('click',async()=>{
 try{await navigator.clipboard.writeText('mzs123.mcv.kr');document.querySelector('.copy-label').textContent='복사 완료 ✓';document.getElementById('copy-status').textContent='서버 주소를 복사했습니다.';setTimeout(()=>document.querySelector('.copy-label').textContent='주소 복사 ⧉',2500)}
 catch{document.querySelector('.copy-label').textContent='mzs123.mcv.kr';document.getElementById('copy-status').textContent='서버 주소: mzs123.mcv.kr'}
});
fetch('downloads.json?v=0.3.6').then(response=>{if(!response.ok)throw Error('metadata');return response.json()}).then(data=>{document.getElementById('download-size').textContent=(data.online_bytes/1048576).toFixed(1)+' MB · Windows EXE'}).catch(()=>{});
