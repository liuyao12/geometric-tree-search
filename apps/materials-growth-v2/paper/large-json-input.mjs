// Preserve JSON values without constructing one string for a large container.
// This is bounded-string parsing, not bounded-memory streaming: the input Buffer
// and parsed object still occupy memory. Individual huge scalar strings remain
// subject to the runtime string limit. No precision changes or record truncation.
import {readFileSync} from 'node:fs';
export function parseLargeJSON(buffer,{chunkBytes=8*1024*1024}={}){
 if(!Buffer.isBuffer(buffer)||!Number.isSafeInteger(chunkBytes)||chunkBytes<1)throw Error('Invalid parser input');
 const white=b=>b===32||b===9||b===10||b===13;
 const skip=(p,end)=>{while(p<end&&white(buffer[p]))p++;return p;};
 function valueEnd(start,end){
  let depth=0,string=false,escape=false;
  for(let p=start;p<end;p++){
   const b=buffer[p];
   if(string){if(escape)escape=false;else if(b===92)escape=true;else if(b===34){string=false;if(depth===0)return p+1;}continue;}
   if(b===34){string=true;continue;}
   if(b===123||b===91){depth++;continue;}
   if(b===125||b===93){if(depth===0)return p;if(--depth===0)return p+1;continue;}
   if(depth===0&&(b===44||white(b)))return p;
  }
  return end;
 }
 function parse(start,end){
  start=skip(start,end);while(end>start&&white(buffer[end-1]))end--;
  if(end-start<=chunkBytes)return JSON.parse(buffer.toString('utf8',start,end));
  const object=buffer[start]===123,array=buffer[start]===91;
  if(!object&&!array)return JSON.parse(buffer.toString('utf8',start,end));
  const close=object?125:93,result=object?{}:[];let p=skip(start+1,end);
  if(buffer[p]===close){if(p!==end-1)throw SyntaxError('Trailing JSON content');return result;}
  while(p<end){
   let key;
   if(object){if(buffer[p]!==34)throw SyntaxError('Expected JSON key');const q=valueEnd(p,end);key=JSON.parse(buffer.toString('utf8',p,q));p=skip(q,end);if(buffer[p++]!==58)throw SyntaxError('Expected colon');p=skip(p,end);}
   const q=valueEnd(p,end);if(q<=p)throw SyntaxError('Missing JSON value');const value=parse(p,q);
   if(object)Object.defineProperty(result,key,{value,writable:true,configurable:true,enumerable:true});else result.push(value);
   p=skip(q,end);if(buffer[p]===close){if(p!==end-1)throw SyntaxError('Trailing JSON content');return result;}
   if(buffer[p++]!==44)throw SyntaxError('Expected comma');p=skip(p,end);if(buffer[p]===close)throw SyntaxError('Trailing comma');
  }
  throw SyntaxError('Unclosed JSON container');
 }
 return parse(0,buffer.length);
}
export const readLargeJSON=path=>parseLargeJSON(readFileSync(path));
