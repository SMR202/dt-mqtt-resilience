"""Build the instructor's initial reproduction report from audited sources."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.build_report import pdf
from scripts.build_overleaf import build
ROOT=Path(__file__).resolve().parents[1]

def main():
    fig,ax=plt.subplots(figsize=(10,3.4),layout='constrained')
    ax.set(xlim=(0,10),ylim=(0,3.4));ax.axis('off')
    nodes={'Device':(1.5,2.2),'MQTT broker':(5,2.2),'Digital twin':(8.5,2.2),'Rate monitor':(5,.6),'HTTP / proxy intervention':(8.5,.6)}
    for label,(x,y) in nodes.items():
        ax.text(x,y,label,ha='center',va='center',fontsize=11,bbox=dict(boxstyle='round,pad=.7',facecolor='#edf3f5',edgecolor='#29485d'))
    for a,b in [('Device','MQTT broker'),('MQTT broker','Digital twin'),('MQTT broker','Rate monitor'),('HTTP / proxy intervention','Digital twin')]:
        x,y=nodes[a];u,v=nodes[b]
        ax.annotate('',xy=(u if x==u else u-.9,v if y==v else v-.35),xytext=(x if x==u else x+.9,y if y==v else y+.35),arrowprops=dict(arrowstyle='->',color='#29485d',lw=1.7))
    ax.text(5,3.05,'Official baseline: synthetic devices and containerized services',ha='center',fontsize=12,color='#18354a')
    fig.savefig(ROOT/'figures/baseline_architecture.png',dpi=180);plt.close(fig)
    source=ROOT/'paper/INITIAL_REPRODUCTION_REPORT.md'
    pdf(source,ROOT/'paper/INITIAL_REPRODUCTION_REPORT.pdf')
    build(source,ROOT/'paper/initial_overleaf','Initial Reproduction Report',ROOT/'paper/initial_overleaf_upload.zip')
if __name__=='__main__':main()
