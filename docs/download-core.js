'use strict';
// Both the page and regression tests use this exact download/verification code.
async function verifiedDownload(sources, options={}) {
 const fetcher=options.fetcher||fetch;
 const cryptoAPI=options.cryptoAPI||globalThis.crypto;
 const notify=options.notify||(()=>{});
 const failures=[];
 for(const source of sources) {
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),options.timeout||30000);
  try {
   notify('connect',source);
   const response=await fetcher(source.url,{signal:controller.signal,cache:'no-store',credentials:'omit'});
   if(!response.ok)throw Error('HTTP '+response.status);
   const reader=response.body.getReader(),chunks=[];let received=0;
   for(;;) {
    const {done,value}=await reader.read();if(done)break;
    received+=value.length;
    if(received>source.size){await reader.cancel();throw Error('size');}
    chunks.push(value);notify('progress',source,received);
   }
   if(received!==source.size)throw Error('incomplete');
   const data=new Uint8Array(received);let offset=0;
   for(const chunk of chunks){data.set(chunk,offset);offset+=chunk.length;}
   const hash=[...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',data))].map(b=>b.toString(16).padStart(2,'0')).join('');
   if(hash!==source.sha256)throw Error('checksum');
   return {data,source};
  }catch(error){failures.push({host:new URL(source.url,options.baseURL||globalThis.location?.href||'https://localhost/').hostname,error:String(error)});notify('fallback',source);}
  finally{clearTimeout(timer);}
 }
 const error=Error('모든 다운로드 경로에서 받지 못했습니다. 아래 대체 다운로드를 이용해주세요.');
 error.failures=failures;throw error;
}
if(typeof module!=='undefined')module.exports={verifiedDownload};
