#!/usr/bin/env python3
"""Insert verified numerical summaries and create a LaTeX report from the HTML article."""
from pathlib import Path
from html.parser import HTMLParser
import html
import json
import re

ROOT = Path(__file__).resolve().parent
PAGE = ROOT.parents[1]/'docs/projects/spectral-tiling-study.html'


class Node:
    def __init__(self,tag='',attrs=()): self.tag,self.attrs,self.children=tag,dict(attrs),[]


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root=Node();self.stack=[self.root]
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs);self.stack[-1].children.append(n)
        if tag not in ('meta','img','br','link','input'): self.stack.append(n)
    def handle_endtag(self,tag):
        if self.stack[-1].tag==tag: self.stack.pop()
    def handle_data(self,data): self.stack[-1].children.append(data)


def escape(s):
    s=s.replace('–','--').replace('—','---').replace('“','``').replace('”',"''").replace('’',"'")
    return ''.join({'&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_',
                    '{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}',
                    '\\':r'\textbackslash{}'}.get(c,c) for c in s)


def text(s):
    parts=re.split(r'(\\\(.*?\\\)|\\\[.*?\\\])',s,flags=re.S)
    return ''.join(p if p.startswith((r'\(',r'\[')) else escape(p) for p in parts)


def find(n,predicate):
    if not isinstance(n,Node): return None
    if predicate(n): return n
    for c in n.children:
        v=find(c,predicate)
        if v:return v


def render(n):
    if isinstance(n,str): return text(n)
    if n.attrs.get('class')=='toc':return ''
    tag=n.tag
    inside=lambda:''.join(render(c) for c in n.children)
    if tag=='h2':return '\n\\section*{'+inside()+'}\n'
    if tag=='h3':return '\n\\subsection*{'+inside()+'}\n'
    if tag=='p':return '\n'+inside()+'\n\n'
    if tag=='strong':return r'\textbf{'+inside()+'}'
    if tag=='a':
        target=n.attrs.get('href','')
        if target.startswith('#'):return r'\hyperlink{'+target[1:]+'}{'+inside()+'}'
        return r'\href{'+target+'}{'+inside()+'}'
    if tag in ('ol','ul'):
        kind='enumerate' if tag=='ol' else 'itemize'
        return '\n\\begin{'+kind+'}\n'+inside()+'\n\\end{'+kind+'}\n'
    if tag=='li':return '\n\\item '+(r'\hypertarget{'+n.attrs['id']+'}{}' if 'id' in n.attrs else '')+inside()
    if tag=='span':return r'\textit{'+inside()+'}'
    if tag=='img':
        filename=Path(n.attrs['src']).name.replace('.png','.pdf')
        return r'\includegraphics[width=\linewidth]{'+filename+'}\n'
    if tag=='figure':return '\n\\begin{figure}[htbp]\n\\centering\n'+inside()+'\n\\end{figure}\n'
    if tag=='figcaption':return '\n\\caption{'+inside()+'}\n'
    if tag=='table':
        rows=[]
        def collect(node):
            if isinstance(node,Node):
                if node.tag=='tr':rows.append(node)
                else:
                    for child in node.children:collect(child)
        collect(n)
        count=len([c for c in rows[0].children if isinstance(c,Node)])
        widths=[.20,.34,.38] if count==3 else [.92/count]*count
        spec=''.join('>{\\raggedright\\arraybackslash}p{'+str(w)+r'\linewidth}' for w in widths)
        lines=[]
        for row in rows:
            cells=[c for c in row.children if isinstance(c,Node) and c.tag in ('td','th')]
            lines.append(' & '.join(render(c) for c in cells)+r' \\'+'\n'+(r'\midrule' if cells[0].tag=='th' else '')+'\n')
        return '\n\\begin{center}\\small\n\\setlength{\\tabcolsep}{4pt}\n\\begin{tabular}{'+spec+'}\n\\toprule\n'+''.join(lines)+'\\bottomrule\n\\end{tabular}\n\\end{center}\n'
    if tag=='th':return r'\textbf{'+inside()+'}'
    return inside()


def main():
    data=json.loads((ROOT/'results.json').read_text())
    verification=json.loads((ROOT/'verification.json').read_text())
    fine=str(max(data['levels']));previous=str(sorted(data['levels'])[-2])
    source=PAGE.read_text()
    # Normalize delimiters in article prose only; JS string escapes must stay intact.
    a=source.index('<article id="report">');b=source.index('</article>',a)
    prose=source[a:b]
    for x in '()[]':prose=prose.replace('\\\\'+x,'\\'+x)
    source=source[:a]+prose+source[b:]
    rows=[]
    for c in data['cases']:
        change=c['relative_difference_from_equilateral'][fine]*100
        rows.append('<tr><td>\\('+format(c['r'],'.6g')+'\\)</td><td>'+c['known_label']+'</td><td>\\('+format(change,'.4g')+r'\%\)</td></tr>')
    table=''.join(rows)
    source=re.sub(r'(<tbody id="numerical-table">).*?(</tbody>)',lambda m:m[1]+table+m[2],source,flags=re.S)
    near=[c for c in data['cases'] if abs(c['r']-1)<=.05+1e-10]
    near_change=max(max(abs(x/y-1) for x,y in zip(c['meshes'][previous]['eigenvalues'],c['meshes'][fine]['eigenvalues'])) for c in near)*100
    info=('Each finest family mesh has \\('+str(data['cases'][0]['meshes'][fine]['nodes'])+'\\) nodes and \\('+str(data['cases'][0]['meshes'][fine]['triangles'])+'\\) triangles. '
          'The largest last-refinement change among the twelve modes is \\('+format(verification['max_fine_vs_previous_relative_change']*100,'.3f')+r'\%\) over all cases, and \('+format(near_change,'.3f')+r'\%\) for \(0.95\le r\le1.05\). '
          'The finest square control differs from its exact first twelve modes by at most \\('+format(verification['square_max_fine_relative_error']*100,'.3f')+r'\%\). '
          'The largest reported relative eigensolver residual is \\('+format(verification['max_eigensolver_relative_residual'],'.2e').replace('e',r'\times10^{')+'}\\).')
    source=re.sub(r'(<p id="numerical-validation">).*?(</p>)',lambda m:m[1]+info+m[2],source,flags=re.S)
    PAGE.write_text(source)
    parser=Parser();parser.feed(source)
    report=find(parser.root,lambda n:n.tag=='article' and n.attrs.get('id')=='report')
    preamble=r'''\documentclass[11pt]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern,amsmath,amssymb,graphicx,booktabs,array,microtype,xcolor}
\usepackage[margin=0.83in]{geometry}
\usepackage[colorlinks=true,linkcolor=teal,urlcolor=teal]{hyperref}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\setlength{\emergencystretch}{3em}
\title{\Huge Can one hear an aperiodic tile?\\[10pt]\large Spectral geometry, planar tiling and forced aperiodicity}
\author{A systematic research study prepared with Codex}
\date{7 October 2026}
\begin{document}
\maketitle
'''
    (ROOT/'report.tex').write_text(preamble+render(report)+'\n\\end{document}\n')
    print('Updated article numerical summaries and generated report.tex')


if __name__=='__main__':main()
