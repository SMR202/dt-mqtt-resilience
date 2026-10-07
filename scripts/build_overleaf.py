"""Create a complete self-contained LaTeX source and image upload package."""
import json
import re
import shutil
import unicodedata
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper'/'overleaf'
def esc(s):
    s=s.replace('×',' x ').replace('→',' -> ').replace('•','; ').replace('–','-').replace('—','-').replace('\u00a0',' ').replace('µ','mu').replace('σ','sigma').replace('≤','<=')
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode()
    return ''.join({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in s)
def inline(s):
    chunks=[]; pos=0
    pattern=r'\[([^\]]+)\]\(([^)]+)\)|`([^`]+)`|\*\*([^*]+)\*\*'
    for m in re.finditer(pattern,s):
        chunks.append(esc(s[pos:m.start()]))
        if m[1]: chunks.append(r'\href{'+esc(m[2])+r'}{'+esc(m[1])+'}')
        elif m[3]: chunks.append(r'\texttt{'+esc(m[3])+'}')
        else: chunks.append(r'\textbf{'+esc(m[4])+'}')
        pos=m.end()
    chunks.append(esc(s[pos:]))
    return ''.join(chunks).replace('*','')
def build(source_path=None,output_path=None,title_text=None,zip_path=None):
    global OUT
    OUT=Path(output_path) if output_path else ROOT/'paper/overleaf'
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'figures').mkdir(exist_ok=True)
    text=Path(source_path or ROOT/'paper/FINAL_RESEARCH_REPORT.md').read_text(encoding='utf-8')
    text=text.replace('remote cloud validation and instructor approval remain open','remote cloud validation remains open; mentor approval was reported by the project team on 7 October 2026')
    text=text.replace('Instructor/mentor confirmation, official Overleaf integration/access','Mentor approval is reported by the team. Official Overleaf integration/access')
    body=[]; lines=text.splitlines(); i=0
    while i<len(lines):
        line=lines[i]; i+=1
        if line.startswith('# '): continue
        if line.startswith('## References'): break
        if line.startswith('## '):
            heading=re.sub(r'^\d+\.\s*','',line[3:])
            body.append(r'\section{'+esc(heading)+'}')
        elif line.startswith('|'):
            rows=[line]
            while i<len(lines) and lines[i].startswith('|'): rows.append(lines[i]); i+=1
            cells=[r.strip('|').split('|') for r in rows if not re.match(r'^\|[\s:|-]+$',r)]
            n=len(cells[0]); width=.88/n
            body.append(r'\begingroup\small\setlength{\tabcolsep}{3pt}\begin{longtable}{'+('p{'+str(width)+r'\linewidth}')*n+'}\toprule')
            for j,row in enumerate(cells):
                body.append(' & '.join(inline(c.strip()) for c in row)+r' \\')
                if j==0: body.append(r'\midrule\endhead')
            body.append(r'\bottomrule\end{longtable}\endgroup')
        elif line.startswith('!['):
            m=re.match(r'!\[([^]]*)\]\(([^)]+)\)',line)
            name=Path(m[2]).name
            body.append(r'\begin{figure}[htbp]\centering\IfFileExists{figures/'+name+r'}{\includegraphics[width=.95\linewidth]{figures/'+name+r'}}{\fbox{\parbox{.85\linewidth}{Upload figures/'+esc(name)+r' to display this figure.}}}\caption{'+esc(m[1])+r'}\end{figure}')
        elif line.startswith('- '): body.append(r'\noindent\textbullet\ '+inline(line[2:])+r'\par')
        elif line:
            paragraph=inline(line)
            if line.startswith('The selected reference is Rodrigues'):paragraph+=r'\cite{ref1}'
            if line.startswith('The 16-paper literature matrix'):paragraph+=r'\cite{ref2,ref3,ref4,ref6,ref7,ref8,ref9,ref11,ref14,ref15,ref16}'
            body.append(paragraph+'\n')
        else: body.append('')
    meta=json.loads((ROOT/'docs/literature_metadata.json').read_text(encoding='utf-8'))
    if title_text:meta=meta[:1]
    bibliography=[r'\begin{thebibliography}{99}']
    for j,m in enumerate(meta,1):
        authors=', '.join(a.get('family','') for a in m['authors'])
        bibliography.append(r'\bibitem{ref'+str(j)+'} '+esc(authors+'. '+m['title']+'. '+'; '.join(m['venue'])+' ('+str(m['published']['date-parts'][0][0])+'). ')+r'\url{https://doi.org/'+m['doi']+'}.')
    bibliography.append(r'\end{thebibliography}')
    source=r'''\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[margin=22mm]{geometry}
\usepackage{graphicx,longtable,booktabs,amsmath,array}
\usepackage[colorlinks=true,urlcolor=blue,linkcolor=teal,citecolor=teal]{hyperref}
\usepackage{microtype}
\setlength{\emergencystretch}{3em}
\title{Freshness-aware Edge Replay for MQTT Digital-twin Synchronization}
\author{Muhammad Sameer \and Humayun Bilal\\\small Cloud Computing Research Project}
\date{7 October 2026}
\begin{document}
\maketitle
\noindent\textbf{Manuscript note:} Author names follow the predecessor proposal. Confirm affiliations, student IDs and contributions before submission. Mentor approval is reported by the team; this source does not assert final manuscript acceptance. The official course/journal template was not supplied.
'''
    equations=r'''
\section*{Metric definitions and algorithm}
For device $d$, let $u_d(t)$ be the generation time of the newest accepted update. Age of Information is $A_d(t)=t-u_d(t)$. Device-time mean age over evaluation interval $[T_0,T_1]$ is
\[
\overline A=\frac{1}{D(T_1-T_0)}\sum_{d=1}^{D}\int_{T_0}^{T_1} A_d(t)\,dt.
\]
For ground truth $x_d(t)$ and held twin state $\hat x_d(t)$, mean absolute error averages $|x_d(t)-\hat x_d(t)|$. Delivery ratio is the number of unique received updates divided by generated updates; intentionally coalesced updates stay in the denominator. The paper-rule rate threshold is $\mu+3\sigma$, with population standard deviation; official source uses the calibration maximum instead.
\begin{enumerate}
\item Persist each generated update in the local audit table and write or replace its device's live outbox row.
\item Select eligible devices by rotating round-robin service. Submit the retained update with configured MQTT QoS.
\item Delete only its unique outbox ID after publication completion. An older completion cannot delete a replacement.
\item Apply an incoming value only when its device sequence exceeds the last accepted sequence.
\end{enumerate}
The local audit does not imply remote archival completeness, and MQTT completion is not an application commit acknowledgement.
'''
    source+='\n'.join(body)+(equations if not title_text else '')+'\n'.join(bibliography)+'\n'+r'\end{document}'+'\n'
    if title_text:
        source=source.replace('Freshness-aware Edge Replay for MQTT Digital-twin Synchronization',esc(title_text))
    (OUT/'main.tex').write_text(source,encoding='utf-8')
    for name in [Path(p).name for p in re.findall(r'!\[[^]]*\]\(([^)]+)\)',text)]:
        shutil.copy2(ROOT/'figures'/name,OUT/'figures'/name)
    shutil.copy2(ROOT/'paper/phase2_references.bib',OUT/'references.bib')
    with zipfile.ZipFile(zip_path or ROOT/'paper/overleaf_upload.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(OUT))
    print('Created complete main.tex and Overleaf ZIP with referenced figures and BibTeX.')
if __name__=='__main__': build()
