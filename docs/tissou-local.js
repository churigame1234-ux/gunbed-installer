'use strict';
// All processing stays in this browser. No original or generated Tissou art is hosted here.
const TissouLocal=(()=>{
 const expected='aed1af48318a160f049fe8ac52d8445848de89eebc530c45dd5c0c5dc7af95bb';
 async function create(input,zip){
  const bytes=input instanceof Uint8Array?input:new Uint8Array(input);
  if(bytes.length!==14177090)throw Error('Tissou 2.7 원본 ZIP 파일을 선택하세요.');
  const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');
  if(digest!==expected)throw Error('선택한 원본 ZIP의 검증에 실패했습니다. 안내된 Tissou 2.7을 받아주세요.');
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),decode=new TextDecoder(),entries=new Map();
  let end=bytes.length-22;
  while(end>=Math.max(0,bytes.length-65557)&&view.getUint32(end,true)!==0x06054b50)end--;
  if(end<0)throw Error('ZIP 디렉터리를 찾을 수 없습니다.');
  const count=view.getUint16(end+10,true);let offset=view.getUint32(end+16,true);
  for(let n=0;n<count;n++){
   if(view.getUint32(offset,true)!==0x02014b50)throw Error('ZIP 디렉터리가 올바르지 않습니다.');
   const length=view.getUint16(offset+28,true),extra=view.getUint16(offset+30,true),comment=view.getUint16(offset+32,true);
   entries.set(decode.decode(bytes.subarray(offset+46,offset+46+length)),{method:view.getUint16(offset+10,true),compressed:view.getUint32(offset+20,true),size:view.getUint32(offset+24,true),local:view.getUint32(offset+42,true)});offset+=46+length+extra+comment;
  }
  async function read(name){
   const e=entries.get(name);if(!e)throw Error('원본 파일이 누락되었습니다: '+name);
   if(e.size>8*1048576||view.getUint32(e.local,true)!==0x04034b50)throw Error('ZIP 항목이 올바르지 않습니다.');
   const start=e.local+30+view.getUint16(e.local+26,true)+view.getUint16(e.local+28,true),compressed=bytes.slice(start,start+e.compressed);
   const result=e.method===0?compressed:e.method===8?new Uint8Array(await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer()):null;
   if(!result||result.length!==e.size)throw Error('ZIP 항목을 읽지 못했습니다.');return result;
  }
  const files=[];
  for(const name of [...entries.keys()].sort()){
   const match=name.match(/^assets\/minecraft\/optifine\/random\/entity\/zombie\/(zombie\d+\.png)$/);
   if(match)files.push({name:'assets/mzs_tissou/textures/zombie/'+match[1],data:await read(name)});
  }
  const sounds=JSON.parse(decode.decode(await read('assets/minecraft/sounds.json')))['entity.zombie.ambient'].sounds,ambient=[];
  for(let n=0;n<sounds.length;n++){
   const item=typeof sounds[n]==='string'?{name:sounds[n]}:{...sounds[n]},source='assets/minecraft/sounds/'+item.name.split(':').pop()+'.ogg';
   if(!entries.has(source))continue;
   const target='ambient/say_'+String(n).padStart(3,'0');files.push({name:'assets/mzs_tissou/sounds/'+target+'.ogg',data:await read(source)});item.name='mzs_tissou:'+target;ambient.push(item);
  }
  files.push({name:'assets/mzs_tissou/sounds.json',data:JSON.stringify({'zombie.ambient':{sounds:ambient}})},
   {name:'fabric.mod.json',data:JSON.stringify({schemaVersion:1,id:'mzs_tissou_local',version:'2.7.0-local',name:'Tissou private zombie assets',environment:'client',license:'All-Rights-Reserved',depends:{fabricloader:'>=0.19.3',minecraft:'*'}})},
   {name:'CREDITS.txt',data:'Tissou Zombie Pack by Tissou. All rights reserved.\nCreated locally from the verified official original. Do not redistribute this derived JAR.\nhttps://www.curseforge.com/minecraft/texture-packs/tissous-zombie-pack-optifine-1-7x-1-20\n'});
  if(files.length!==1829)throw Error('좀비 외형 구성이 올바르지 않습니다.');
  return {file:'Tissou-local.jar',data:new Uint8Array(await zip(files).arrayBuffer())};
 }
 return {create,expected};
})();
if(typeof module!=='undefined')module.exports=TissouLocal;
