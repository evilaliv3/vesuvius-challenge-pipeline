"""control_render_lib.py (night-render-labels-1107): inputs of the 6 control units of the 14-unit set, read from their sources.
Boxes, meshes, volumes come from the tri control record.json files of two-pipelines (command_box), 0343 from fmb_fb_render.py (P343). PRIVATE."""
import json, os, re
R='/data/scrollagent/runs/rev1'; N=R+'/night-render-labels-1107'; S=N+'/scratch'
BUCKET='https://vesuvius-challenge-open-data.s3.amazonaws.com'
CTL=R+'/two-pipelines/render-tri/controls'
READS=R+'/m5m6-set/reads.json'
CBIN=S+'/build-C2/bin/vc_render_tifxyz'
ORDER=['0343','ag1','ag2','w00','w058','w060']
# meshes of ag1 and ag2 are pruned locally (meta.json only); source and md5 (bucket ETag) listed in reader-recipe-survey/scratch/plan-meshes.tsv
MESHURL={'ag1':'PHerc0841/segments/20260220214732-auto_grown_20260220144552896/mesh/20260220214732-on-20250821151531-9.366um.tifxyz/',
         'ag2':'PHerc0841/segments/20260221022814-auto_grown_20260220174252405/mesh/20260221022814-on-20250821151531-9.366um.tifxyz/'}
def opt(cmd,f):
    m=re.search(re.escape(f)+r' (\S+)',cmd); return m.group(1) if m else ''
def unit(u):
    if u=='0343':
        return dict(unit=u,scroll='PHerc0343',vol=BUCKET+'/PHerc0343/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr/',vol_local=False,
            mesh='/data/repositories/external/pherc343-first-letters/outputs/concat_w047-w048_R5B2_z9500-11000.tifxyz',box=[0,2560,0,6720],vs='8.64',
            group='0',old_kind='uint8 27 planes stock 0343-lin (planes 2..24 centred), old binary BIN_SM linear')
    rec=None
    for sc in ('PHerc0841','PHerc1447'):
        p='%s/%s/%s.record.json'%(CTL,sc,u)
        if os.path.exists(p): rec=json.load(open(p)); break
    cmd=rec['command_box']
    return dict(unit=u,scroll=sc,vol=opt(cmd,'--volume'),vol_local=True,mesh=opt(cmd,'--segmentation'),box=rec['box'],vs=opt(cmd,'--voxel-size'),
                group=opt(cmd,'--group-idx'),old_kind='float render of the tri control, old binary pas-p1bcpp (record binary_sha256 %s), linear'%rec['binary_sha256'][:12])
def reads_row(u):
    for r in json.load(open(READS))['units']:
        if r['unit']==u: return r
    raise KeyError(u)
