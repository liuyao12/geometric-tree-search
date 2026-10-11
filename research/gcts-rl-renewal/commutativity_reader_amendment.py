"""Presentation-only reader copies; all frozen experiment artifacts stay intact."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/research/gcts-rl-renewal'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def main():
    source=DOC/'commutativity_feasibility.html';raw=source.read_bytes();text=raw.decode()
    replacements={
      '<summary>Complete induction interface for x</summary>':r'<summary>Complete induction interface for \(x\)</summary>',
      '<summary>Complete induction interface for y</summary>':r'<summary>Complete induction interface for \(y\)</summary>',
      'GCTS automatically selected7high-level rows;30-command generic checked DAG-sharing expansion':'GCTS automatically selected 7 high-level rows; 30-command generic checked DAG-sharing expansion',
      'Ordinary forward chaining automatically selected11rows;67-command generic checked DAG-sharing expansion; original8GCTS searches remain unknown':'Ordinary forward chaining automatically selected 11 rows; 67-command generic checked DAG-sharing expansion; original 8 GCTS searches remain unknown'}
    for before,after in replacements.items():
      assert text.count(before)==1,before;text=text.replace(before,after)
    text=text.replace('</main>', '<p class="small">Presentation amendment: variable labels are typeset and displayed discovery descriptions are spaced. <a href="commutativity_feasibility.html">The frozen original reader</a> and all experiment data remain unchanged. <a href="commutativity_reader_amendment.json">Exact amendment receipt</a>.</p></main>')
    original_data=re.search(r'<script id="family-data" type="application/json">(.*?)</script>',raw.decode(),re.S).group(1)
    assert original_data==re.search(r'<script id="family-data" type="application/json">(.*?)</script>',text,re.S).group(1)
    assert len(json.loads(original_data))==42
    dest=DOC/'commutativity-feasibility.html';dest.write_text(text)
    capacity=DOC/'commutativity_capacity.html';capacity_raw=capacity.read_bytes();capacity_text=capacity_raw.decode().replace('commutativity_feasibility.html#result','commutativity-feasibility.html#result')
    assert capacity_text!=capacity_raw.decode()
    capacity_text=capacity_text.replace('</main>', '<p class="small">This reader links the presentation-amended feasibility view. <a href="commutativity_capacity.html">The frozen original capacity reader</a> and all experiment data remain unchanged.</p></main>')
    capacity_dest=DOC/'commutativity-capacity.html';capacity_dest.write_text(capacity_text)
    assert source.read_bytes()==raw and capacity.read_bytes()==capacity_raw
    receipt=dict(status='passed-presentation-only',replacements=replacements,complete_family_payload_bytes_preserved=True,families=42,source_sha256=digest(Path(__file__).read_bytes()),files=[dict(original=p.name,original_sha256=digest(r),derived=d.name,derived_sha256=digest(d.read_bytes())) for p,r,d in [(source,raw,dest),(capacity,capacity_raw,capacity_dest)]])
    (DOC/'commutativity_reader_amendment.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(status=receipt['status'],families=42,files=[r['derived'] for r in receipt['files']])))
if __name__=='__main__':main()
