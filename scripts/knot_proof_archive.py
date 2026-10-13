"""Split concatenated gzip members without changing a single archived byte."""
import hashlib,zlib,shutil
from pathlib import Path

def archive_parts(source,destination,prefix,limit=32*1024*1024):
    source=Path(source);destination=Path(destination)
    if source.stat().st_size<=limit:
        name=prefix+'-proofs.jsonl.gz';shutil.copyfile(source,destination/name)
        return {'file':name}
    parts=[];writer=None;part_size=0;part_hash=None;member=bytearray();decoder=zlib.decompressobj(31)
    def close_part():
        if writer is not None:
            writer.close();parts.append({'file':name,'bytes':part_size,'sha256':part_hash.hexdigest()})
    try:
        with source.open('rb') as stream:
            while True:
                pending=stream.read(65536)
                if not pending:break
                while pending:
                    decoder.decompress(pending);tail=decoder.unused_data
                    member.extend(pending[:len(pending)-len(tail)])
                    if decoder.eof:
                        if writer is None or part_size+len(member)>limit:
                            close_part();name=f'{prefix}-proofs-{len(parts)+1:03d}.jsonl.gz';writer=(destination/name).open('wb');part_size=0;part_hash=hashlib.sha256()
                        writer.write(member);part_size+=len(member);part_hash.update(member);member.clear();decoder=zlib.decompressobj(31)
                    pending=tail
        if member:raise ValueError('Truncated gzip proof member')
        close_part();writer=None
    finally:
        if writer is not None:writer.close()
    if sum(p['bytes'] for p in parts)!=source.stat().st_size:raise ValueError('Archive splitting lost bytes')
    return {'files':parts,'compression':'Original concatenated gzip members; joining parts reproduces the original archive SHA256.'}
