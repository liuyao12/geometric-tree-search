"""Encode the deterministic 30-second turn with one shared GIF palette."""
from pathlib import Path
import sys
from PIL import Image
frames_dir=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/chair-rotation-frames')
out=Path(sys.argv[2] if len(sys.argv)>2 else '3d-reptiles/chair/chair44-rotating-relief.gif')
paths=sorted(frames_dir.glob('*.png'))
assert len(paths)==450
samples=Image.new('RGB',(6*180,3*180))
for j,i in enumerate(range(0,450,25)):
 with Image.open(paths[i]) as frame:samples.paste(frame.convert('RGB').resize((180,180)),((j%6)*180,(j//6)*180))
palette=samples.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
frames=[]
for path in paths:
 with Image.open(path) as frame:frames.append(frame.convert('RGB').quantize(palette=palette,dither=Image.Dither.NONE))
out.parent.mkdir(parents=True,exist_ok=True)
frames[0].save(out,save_all=True,append_images=frames[1:],duration=[70,60,70]*150,loop=0,disposal=1,optimize=True)
with Image.open(out) as animation:
 assert animation.size==(720,720) and animation.n_frames==450 and animation.info['loop']==0
 total=0
 for i in range(animation.n_frames):animation.seek(i);total+=animation.info['duration']
 assert total==30000
print(f'Verified {out}: 450 frames, 30 seconds, 720 x 720, infinite loop, {out.stat().st_size:,} bytes.')
