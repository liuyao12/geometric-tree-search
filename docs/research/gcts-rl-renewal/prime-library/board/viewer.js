(() => {
  'use strict';
  const get = id => document.getElementById(id);
  const canvas = get('board'), scroll = get('scroll'), extent = get('extent');
  const ctx = canvas.getContext('2d');
  const controls = ['attempt','zoom-out','zoom-in','fit','follow','play','position'].map(get);
  const [picker, minus, plus, fitButton, followButton, playButton, slider] = controls;
  const numberFormat = new Intl.NumberFormat();
  const fmt = n => numberFormat.format(n);
  const names = {'prime-divisor':'Prime divisor', 'unbounded-primes':'Prime infinitude',
                 'bounded-positive-le-divides':'Common multiple'};
  const styles = getComputedStyle(document.documentElement);
  const palette = Object.fromEntries(['white','line','vacant','occupied','read','write','reject'].map(
    key => [key,styles.getPropertyValue('--'+key).trim()]));
  const margin = 20, maxScale = 26;
  let attempts, parents, total, state, texture;
  let syntaxMasks, syntaxPalette;
  let scale = 1, fitted = true, follow = false;
  let playTime = 0, playStarted = null, playbackFrame = 0, queued = false, drag;

  function lastAt(items, value, key) {
    let low = 0, high = items.length;
    while (low < high) {
      const mid = (low+high)>>1;
      if (items[mid][key]<=value) low=mid+1;
      else high=mid;
    }
    return low-1;
  }

  function stateAt(time) {
    const index = Math.max(0,lastAt(attempts,time,'start'));
    const attempt = attempts[index];
    const part = Math.min(1,Math.max(0,(time-attempt.start)/attempt.motion));
    const offers = Math.min(attempt.offers,Math.floor(attempt.offers*part));
    const cursor = lastAt(attempt.samples,offers,'offers');
    const sample = attempt.samples[cursor];
    const next = attempt.samples[cursor+1];
    const progress = sample && next ? (offers-sample.offers)/(next.offers-sample.offers) : 0;
    return {index, attempt, offers, rows:part===1 ? attempt.rows : sample?.rows || 0,
            rejected:sample && sample.outcome.endsWith('clash') && progress<.7 && part<1,
            ended:part===1};
  }

  function worldHeight() {
    return Math.max(1,state.attempt.rows+1);
  }

  function fitScale() {
    return Math.min((scroll.clientWidth-2*margin)/state.attempt.width,
                    (scroll.clientHeight-2*margin)/worldHeight());
  }

  function resizePlane() {
    extent.style.width = Math.max(scroll.clientWidth,Math.ceil(scale*state.attempt.width+2*margin))+'px';
    extent.style.height = Math.max(scroll.clientHeight,Math.ceil(scale*worldHeight()+2*margin))+'px';
  }

  function fitBoard() {
    follow=false; fitted=true; scale=fitScale();
    resizePlane();
    scroll.scrollTo(0,0);
    scheduleDraw();
  }

  function centerOnRow() {
    const output = state.attempt.inputs+Math.max(0,state.rows-1);
    scroll.scrollLeft = margin+(output+.5)*scale-scroll.clientWidth*.69;
    scroll.scrollTop = margin+state.rows*scale-scroll.clientHeight*.72;
  }

  function zoom(factor, screenX=scroll.clientWidth/2, screenY=scroll.clientHeight/2) {
    const floor=fitScale();
    const next=Math.max(floor,Math.min(maxScale,scale*factor));
    if (next<=floor*(1+1e-7)) {
      fitBoard();
      return;
    }
    const x=(scroll.scrollLeft+screenX-margin)/scale;
    const y=(scroll.scrollTop+screenY-margin)/scale;
    follow=false; fitted=false; scale=next;
    resizePlane();
    scroll.scrollLeft=margin+x*scale-screenX;
    scroll.scrollTop=margin+y*scale-screenY;
    scheduleDraw();
  }

  function followRow() {
    follow=!follow;
    if (follow) {
      fitted=false;
      scale=Math.max(fitScale(),(scroll.clientHeight-2*margin)/240);
      resizePlane();
      centerOnRow();
    }
    scheduleDraw();
  }

  function setTime(time) {
    playTime=Math.max(0,Math.min(total,time));
    const previous=state?.index;
    state=stateAt(playTime);
    if (state.index!==previous) {
      texture=null;
      picker.value=state.index;
      if (fitted) scale=fitScale();
      else scale=Math.max(fitScale(),scale);
      resizePlane();
      if (!follow) scroll.scrollTo(0,0);
    }
    if (follow) centerOnRow();
    slider.value=Math.round(playTime/total*1000);
    scheduleDraw();
  }

  function coarseReadMarks(attempt) {
    if (texture) return texture;
    const raster=document.createElement('canvas');
    raster.width=1100;
    raster.height=Math.max(1,Math.ceil(attempt.rows*raster.width/attempt.width));
    const paint=raster.getContext('2d');
    const ratio=raster.width/attempt.width;
    for (let row=0;row<attempt.rows;row++) {
      const offset=2*(attempt.first+row);
      const y=Math.floor(row*ratio);
      for (let index=offset;index<offset+2;index++) {
        const slot=parents[index];
        paint.fillStyle=markColor(attempt,slot,row,palette.read);
        paint.fillRect(Math.floor(slot*ratio),y,1,1);
      }
      if (syntaxMasks) {
        const slot=attempt.inputs+row;
        paint.fillStyle=markColor(attempt,slot,row,palette.write);
        paint.fillRect(Math.floor(slot*ratio),y,1,1);
      }
    }
    texture=raster;
    return texture;
  }

  function markColors(attempt,slot) {
    return syntaxMasks && syntaxPalette[syntaxMasks[attempt.syntaxFirst+slot]];
  }

  function markColor(attempt,slot,row,fallback) {
    const colors=markColors(attempt,slot);
    return colors?.length ? colors[(slot+row)%colors.length] : fallback;
  }

  function drawMark(attempt,slot,row,x,y,size,border) {
    const colors=markColors(attempt,slot);
    if (!colors?.length || size<8) {
      ctx.fillStyle=markColor(attempt,slot,row,border);
      ctx.fillRect(x,y,size,size);
      return;
    }
    ctx.fillStyle=border;
    ctx.fillRect(x,y,size,size);
    const band=(size-3)/colors.length;
    colors.forEach((color,i)=>{
      ctx.fillStyle=color;
      ctx.fillRect(x+1.5+i*band,y+1.5,band+.2,size-3);
    });
  }

  function grid(x,y,w,h,left,top,right,bottom) {
    if (scale<8) return;
    ctx.beginPath();
    for (let col=left;col<=right;col++) {
      const at=x+col*scale;
      ctx.moveTo(at,y);ctx.lineTo(at,y+h);
    }
    for (let row=top;row<=bottom;row++) {
      const at=y+row*scale;
      ctx.moveTo(x,at);ctx.lineTo(x+w,at);
    }
    ctx.strokeStyle=palette.line;
    ctx.lineWidth=.55;
    ctx.stroke();
  }

  function scheduleDraw() {
    if (!queued) {
      queued=true;
      requestAnimationFrame(draw);
    }
  }

  function draw() {
    queued=false;
    if (!state) return;
    const width=scroll.clientWidth, height=scroll.clientHeight;
    const ratio=Math.min(2,window.devicePixelRatio || 1);
    if (canvas.width!==Math.round(width*ratio) || canvas.height!==Math.round(height*ratio)) {
      canvas.width=Math.round(width*ratio);
      canvas.height=Math.round(height*ratio);
      canvas.style.width=width+'px';
      canvas.style.height=height+'px';
    }
    ctx.setTransform(ratio,0,0,ratio,0,0);
    ctx.clearRect(0,0,width,height);
    const {attempt,rows,rejected}=state;
    const x=margin-scroll.scrollLeft, y=margin-scroll.scrollTop;
    const w=attempt.width*scale, h=worldHeight()*scale;
    const left=Math.max(0,Math.floor(-x/scale)), top=Math.max(0,Math.floor(-y/scale));
    const right=Math.min(attempt.width,Math.ceil((width-x)/scale));
    const bottom=Math.min(worldHeight(),Math.ceil((height-y)/scale));
    const edge=y+rows*scale;
    ctx.fillStyle=palette.white;
    ctx.fillRect(x,y,w,h);
    ctx.strokeStyle=palette.line;
    ctx.strokeRect(x,y,w,h);
    if (rows) {
      ctx.fillStyle=palette.vacant;
      ctx.fillRect(x,y,w,rows*scale);
      if (scale>=.14) {
        const tile=Math.max(1,scale);
        for (let row=top;row<Math.min(rows,bottom);row++) {
          const offset=(attempt.first+row)*2, out=attempt.inputs+row, v=y+row*scale;
          ctx.fillStyle=palette.occupied;
          ctx.fillRect(x,v,out*scale,scale);
          for (let index=offset;index<offset+2;index++) {
            const slot=parents[index];
            if (slot>=left && slot<right) drawMark(attempt,slot,row,x+slot*scale,v,tile,palette.read);
          }
          if (out>=left && out<right) {
            drawMark(attempt,out,row,x+out*scale,v,tile,palette.write);
          }
        }
      } else {
        ctx.fillStyle=palette.occupied;
        ctx.beginPath();
        ctx.moveTo(x,y);ctx.lineTo(x+attempt.inputs*scale,y);
        ctx.lineTo(x+(attempt.inputs+rows)*scale,edge);ctx.lineTo(x,edge);
        ctx.closePath();ctx.fill();
        const raster=coarseReadMarks(attempt);
        ctx.save();
        ctx.beginPath();ctx.rect(x,y,w,rows*scale);ctx.clip();
        ctx.imageSmoothingEnabled=false;
        ctx.drawImage(raster,x,y,w,raster.height*w/raster.width);
        ctx.restore();
        if (!syntaxMasks) {
          ctx.strokeStyle=palette.write;
          ctx.beginPath();ctx.moveTo(x+attempt.inputs*scale,y);
          ctx.lineTo(x+(attempt.inputs+rows)*scale,edge);ctx.stroke();
        }
      }
    }
    grid(x,y,w,h,left,top,right,bottom);
    if (rejected) {
      ctx.fillStyle=palette.reject;
      ctx.fillRect(x,edge,w,Math.max(2,scale));
    }
    if (syntaxMasks && scale>=.14) {
      for (let slot=0;slot<attempt.inputs;slot++) {
        ctx.fillStyle=markColor(attempt,slot,0,palette.read);
        ctx.fillRect(x+slot*scale,y-2,Math.max(1,scale),2);
      }
    } else {
      ctx.fillStyle=palette.read;
      ctx.fillRect(x,y-2,Math.max(1,attempt.inputs*scale),2);
    }
    minus.disabled=scale<=fitScale()*1.001;
    plus.disabled=scale>=maxScale;
    followButton.setAttribute('aria-pressed',String(follow));
    get('scale').textContent=fitted ? 'Fit' :
      scale<1 ? Math.max(1,Math.round(1/scale))+' tiles/px' : scale.toFixed(1)+' px/tile';
    get('view').textContent='Columns '+fmt(left+1)+'–'+fmt(right)+' of '+fmt(attempt.width)+
      ' · rows '+fmt(top+1)+'–'+fmt(bottom);
    get('offers').textContent=fmt(rows)+' rows · '+fmt(state.offers)+' offers';
    let status='Reading the arithmetic boundary';
    if (rejected) status='Marks clash. The proposed row lifts away.';
    else if (state.ended) status=attempt.status==='proved' ? 'Refutation closed' :
      attempt.limit==='offers' ? 'Offer limit reached' : 'Attempt ended';
    else if (rows) status='Search grows by placing rows';
    const statusNode=get('status');
    if (statusNode.textContent!==status) statusNode.textContent=status;
    const imports=attempt.chapter.imports;
    get('library').textContent=imports.length ?
      'Library: '+imports.map(x=>names[x] || x).join(', ') : 'Theorem library empty';
  }

  function stop() {
    playStarted=null;
    cancelAnimationFrame(playbackFrame);
    playButton.textContent='Play replay';
  }

  function tick(now) {
    if (playStarted===null) return;
    setTime((now-playStarted)/1000);
    if (playTime>=total) stop();
    else playbackFrame=requestAnimationFrame(tick);
  }

  function configure(data,buffer,syntaxBuffer) {
    const words=data.bits===16 ? 2 : 4;
    const view=new DataView(buffer);
    parents=data.bits===16 ? new Uint16Array(buffer.byteLength/2) : new Uint32Array(buffer.byteLength/4);
    for (let i=0;i<parents.length;i++) {
      parents[i]=words===2 ? view.getUint16(i*words,true) : view.getUint32(i*words,true);
    }
    attempts=[];
    const work=data.chapters.flatMap(c=>c.attempts).reduce((n,a)=>n+a.offers,0);
    let start=0;
    data.chapters.forEach((chapter,chapterIndex)=>{
      const group=document.createElement('optgroup');
      group.label=(chapterIndex+1)+'. '+(names[chapter.goal] || chapter.goal);
      chapter.attempts.forEach((attempt,index)=>{
        const result=attempt.status==='proved' ? 'closed' : 'limit reached';
        group.append(new Option('Board '+(index+1)+' · '+result+' · '+fmt(attempt.rows)+' rows',attempts.length));
        const motion=.21+46*attempt.offers/work;
        const end=start+motion+(attempt.offers>100_000 ? .72 : .10);
        attempts.push({...attempt,chapter,start,end,motion});
        start=end;
      });
      picker.append(group);
    });
    total=start;
    if (attempts.at(-1).first+attempts.at(-1).rows!==parents.length/2) {
      throw Error('Tile records are incomplete');
    }
    if (syntaxBuffer) {
      const last=attempts.at(-1);
      if (syntaxBuffer.byteLength!==last.syntaxFirst+last.inputs+last.rows) {
        throw Error('Syntax marks are incomplete');
      }
      syntaxMasks=new Uint8Array(syntaxBuffer);
      syntaxPalette=Array.from({length:256},(_,mask)=>data.syntax.flatMap((item,i)=>
        mask & (1<<i) ? [item.color] : []));
      for (const item of data.syntax) {
        const entry=document.createElement('span'), swatch=document.createElement('i');
        swatch.style.backgroundColor=item.color;
        entry.append(swatch,item.label);
        get('syntax-legend').append(entry);
      }
      get('syntax-hint').hidden=false;
    }
    controls.forEach(button=>{button.disabled=false;});
    setTime(total);
    fitBoard();
  }

  fitButton.addEventListener('click',fitBoard);
  followButton.addEventListener('click',followRow);
  minus.addEventListener('click',()=>zoom(1/1.8));
  plus.addEventListener('click',()=>zoom(1.8));
  scroll.addEventListener('scroll',scheduleDraw,{passive:true});
  scroll.addEventListener('wheel',event=>{
    if (!state) return;
    if (event.ctrlKey || event.metaKey) {
      event.preventDefault();
      const rect=scroll.getBoundingClientRect();
      zoom(Math.exp(-event.deltaY*.004),event.clientX-rect.left,event.clientY-rect.top);
    } else {
      follow=false;
      scheduleDraw();
    }
  },{passive:false});
  scroll.addEventListener('keydown',event=>{
    if (!state) return;
    if (event.key==='+' || event.key==='=' || event.key==='-') {
      event.preventDefault();
      zoom(event.key==='-' ? 1/1.8 : 1.8);
    } else if (event.key.startsWith('Arrow')) {
      follow=false;
      scheduleDraw();
    }
  });
  scroll.addEventListener('pointerdown',event=>{
    if (!state) return;
    follow=false;
    scheduleDraw();
    if (event.pointerType!=='mouse' || event.button!==0 || event.target===scroll) return;
    drag={x:event.clientX,y:event.clientY,left:scroll.scrollLeft,top:scroll.scrollTop};
    scroll.setPointerCapture(event.pointerId);
    scroll.classList.add('dragging');
  });
  scroll.addEventListener('pointermove',event=>{
    if (!drag) return;
    scroll.scrollLeft=drag.left+drag.x-event.clientX;
    scroll.scrollTop=drag.top+drag.y-event.clientY;
  });
  function endDrag() {
    drag=null;
    scroll.classList.remove('dragging');
  }
  scroll.addEventListener('pointerup',endDrag);
  scroll.addEventListener('lostpointercapture',endDrag);
  playButton.addEventListener('click',()=>{
    if (playStarted!==null) {stop();return;}
    if (playTime>=total) setTime(0);
    playStarted=performance.now()-1000*playTime;
    playButton.textContent='Pause';
    playbackFrame=requestAnimationFrame(tick);
  });
  slider.addEventListener('input',()=>{stop();setTime(total*slider.value/1000);});
  picker.addEventListener('change',()=>{
    stop();
    setTime(attempts[picker.value].end-.0001);
  });
  new ResizeObserver(()=>{
    if (!state) return;
    if (fitted) fitBoard();
    else {resizePlane();if (follow) centerOnRow();scheduleDraw();}
  }).observe(scroll);

  const fetchFile=url=>fetch(url).then(response=>{
    if (!response.ok) throw Error('Could not load '+url);
    return response;
  });
  Promise.all([fetchFile('trace.json?v=clause-symbols-1').then(r=>r.json()),fetchFile('parents.bin').then(r=>r.arrayBuffer())])
    .then(async ([data,buffer])=>{
      const syntax=data.syntax?.length ? await fetchFile('syntax.bin').then(r=>r.arrayBuffer()) : null;
      configure(data,buffer,syntax);
    })
    .catch(error=>{get('status').textContent='Search failed to load. '+error.message;});
})();
