#!/usr/bin/env python3
"""render_set_c2_one.py (night-render-labels-1107, agent-F, copy of render_set_v_one.py for arm C2 = main 7e6b82164 + border derivatives + toUint8 fast path + PR 2449 vertex normals; DRAFT, never run for rendering).
usage: render_set_c2_one.py --check-all           read only preflight over the 87 images, exit 1 on any unit missing
       render_set_c2_one.py SEGMENT               shift probe, tiled C2 bicubic render of the O box, uint16 (v x 256) store, one row in out/render-set-c2.csv
Inputs: out/m5m6-render-inventory.csv (87 rows from the O record.json files), manifest-tri.csv (shape), out/binary-hashes.txt (C2 sha).
The C2 binary is scratch/build-C2/bin/vc_render_tifxyz (see out/REPORT-F.md)."""
import csv, hashlib, json, os, re, shutil, subprocess, sys, time, urllib.request
R='/data/scrollagent/runs/rev1'; N=R+'/night-render-labels-1107'; S=N+'/scratch'
MAN=R+'/arms-m3ft/cache-control/set/manifest-tri.csv'
OUTROOT=os.environ.get('RSV_OUT', R+'/render-set-c2')
# 2026-11-08 coordinator: floor 70e9 replaced by 30e9 (the 70e9 gate was dropped by the owner on 16/10 to 10e9; 30e9 keeps the 98 percent brake about 9 GB away)
FLOOR=30e9; TILE=4096
BUCKET='https://vesuvius-challenge-open-data.s3.amazonaws.com'
def rd(p): return list(csv.DictReader(l for l in open(p) if not l.startswith('#') and not l.startswith('"#')))
inv=rd(N+'/out/m5m6-render-inventory.csv')
man={r['segment']:r for r in rd(MAN) if r['role']=='image'}
MESHMAN=R+'/two-pipelines/fetch/meshes/manifest.csv'
VBIN=S+'/build-C2/bin/vc_render_tifxyz'; OBIN=S+'/build-O/bin/vc_render_tifxyz'
vsha=[l.split()[1] for l in open(N+'/out/binary-hashes.txt') if l.startswith('C2 ')][0]
def mesh_rows():
    out={}
    for r in rd(MESHMAN): out.setdefault(r['segment'],[]).append(r)
    return out
MROWS=mesh_rows()
def mesh_src(seg,d,mesh_local):
    # 2026-11-08 (agent-D): the local mesh folders keep only meta.json (x.tif y.tif z.tif were pruned), so isdir() was not a test. A mesh is usable when
    # all four files are on disk, or when every file has a url and a sha256 (the O record for rv2prep, fetch/meshes/manifest.csv for the others).
    need=('meta.json','x.tif','y.tif','z.tif')
    if os.path.isdir(mesh_local) and all(os.path.exists(os.path.join(mesh_local,f)) for f in need): return ('local',mesh_local,None)
    if d.get('mesh') and d.get('mesh_sha256'):
        return ('fetch',os.path.basename(d['mesh'].rstrip('/')),{f:(d['mesh']+f,h) for f,h in d['mesh_sha256'].items()})
    rows=[r for r in MROWS.get(seg,[]) if r['file'] in need]
    if {r['file'] for r in rows}==set(need):
        return ('fetch',rows[0]['tifxyz'],{r['file']:(r['source_url'],r['sha256']) for r in rows})
    return None
def get_mesh(seg,pl):
    k=pl['mesh']
    if k[0]=='local': return k[1]
    mdir=os.path.join(S,'data/meshes',seg,k[1]); os.makedirs(mdir,exist_ok=True)
    for f,(url,want) in k[2].items():
        p=os.path.join(mdir,f)
        if not os.path.exists(p) or hashlib.sha256(open(p,'rb').read()).hexdigest()!=want: urllib.request.urlretrieve(url,p)
        if hashlib.sha256(open(p,'rb').read()).hexdigest()!=want: sys.exit('REFUSED %s mesh sha %s'%(seg,f))
    return mdir
def rec_of(seg):
    p=man[seg]['path'].split('volume:two-pipelines/render-tri/')[1][:-5]+'.record.json'
    for b in (R+'/two-pipelines/render-tri/',R+'/rv2prep/stage/render-tri/'):
        if os.path.exists(b+p): return json.load(open(b+p))
    return None
def opt(cmd,f):
    m=re.search(re.escape(f)+r' (\S+)',cmd); return m.group(1) if m else ''
def plan(seg):
    d=rec_of(seg); why=[]
    if d is None: return None,['no record.json']
    cmd=d.get('command_box','') if 'command_box' in d else ''
    if not cmd: why.append('no command_box')
    vol=opt(cmd,'--volume'); mesh_local=opt(cmd,'--segmentation')
    if str(d.get('volume','')).startswith('http'): vurl=d['volume']
    elif vol: vurl='%s/%s/volumes/%s/'%(BUCKET,os.path.basename(os.path.dirname(vol)),os.path.basename(vol))
    else: vurl=''; why.append('no volume')
    mk=mesh_src(seg,d,mesh_local)
    if mk is None: why.append('mesh not complete on disk and no url with sha256')
    box=d.get('box')
    if not box: why.append('no box')
    else:
        z,h,w=[int(x) for x in man[seg]['shape'].split('x')]
        if (box[1]-box[0],box[3]-box[2])!=(h,w): why.append('box %s differs from manifest shape %s'%(box,man[seg]['shape']))
    if not d.get('px0_um') and '--voxel-size' not in cmd: why.append('no voxel size')
    return dict(rec=d,cmd=cmd,vol=vurl,mesh_local=mesh_local,mesh=mk,box=box,group=opt(cmd,'--group-idx'),vs=opt(cmd,'--voxel-size'),
                shape=man[seg]['shape']),why
def free(): st=os.statvfs(os.path.dirname(OUTROOT) if not os.path.exists(OUTROOT) else OUTROOT); return st.f_bavail*st.f_frsize
def check_all():
    bad=0
    if hashlib.sha256(open(VBIN,'rb').read()).hexdigest()!=vsha: print('REFUSED V binary sha differs from binary-hashes.txt'); bad+=1
    if not os.path.exists(OBIN): print('REFUSED O binary absent (shift probe)'); bad+=1
    if len(inv)!=87: print('REFUSED inventory has %d rows, expected 87'%len(inv)); bad+=1
    est=0
    for r in inv:
        p,why=plan(r['segment'])
        if why: print('MISSING',r['segment'],'; '.join(why)); bad+=1
        z,h,w=[int(x) for x in r['shape_zyx'].split('x')]; est+=z*h*w
    print('images %d, estimated raw output %.1f GB, free now %.1f GB, floor %.0f GB, problems %d'%(len(inv),est/1e9,free()/1e9,FLOOR/1e9,bad))
    sys.exit(1 if bad else 0)
# 2026-11-08 (agent-D): the V probe uses LINEAR surface interpolation, like O. Evidence (probe_debug.py, 20250511200236, group 0, plane 11): V_lin vs O rms 0.289 (rounding floor),
# V_bic vs O rms 4.462, so bicubic moves the centre plane and cannot be compared to O for the shift. The final tiles still use bicubic (arm V_bic). The 1.0 threshold is unchanged.
def shift_probe(pl,seg,mdir,tmp):
    """render a 1024 x 1024 centre patch of the box with O (record flags) and V_bic at zero shift, return integer (dy,dx) with V(y,x) = O(y+dy,x+dx) and the rms at that shift"""
    import zarr, numpy as np
    from numpy.fft import rfft2, irfft2
    y0,y1,x0,x1=pl['box']; H,W=y1-y0,x1-x0; P=min(1024,H,W); cy,cx=y0+(H-P)//2,x0+(W-P)//2
    outs={}
    for arm,binp,extra in (('O',OBIN,['--surface-interpolation','linear','--p1bf-float32','--p1bf-global-origin','--p1bcpp-bilinear-normals','--interp','trilinear']),('V',VBIN,['--surface-interpolation','linear'])):
        o=os.path.join(tmp,'probe-%s.zarr'%arm)
        c=[binp,'--volume',pl['vol'],'--segmentation',mdir,'--zarr-output',o,'--scale','1','--group-idx',pl['group'] or '0','--num-slices','23','--slice-step','1','--cache-gb','8','--flip-normals',
           '--crop-x',str(cx),'--crop-y',str(cy),'--crop-width',str(P),'--crop-height',str(P),'--pyramid','0','--voxel-size',pl['vs'] or str(pl['rec'].get('px0_um','9.362')),'--voxel-unit','micrometer']+extra
        subprocess.run(['nice','-n','10']+c,check=True,capture_output=True,env=dict(os.environ,HOME=S+'/home-c2',TMPDIR='/data/tmp'))
        a=np.asarray(zarr.open(o,mode='r')['0'][11]).astype(np.float32)
        outs[arm]=a/256 if (arm=='O' and a.max()>255.5) else a
    o_,v_=outs['O'],outs['V']
    # the V canvas can be offset against O: render V on a wider crop is not done here; the shift is searched inside +-64 px by FFT on the common size
    Pm=min(o_.shape[0],v_.shape[0]),min(o_.shape[1],v_.shape[1]); o_=o_[:Pm[0],:Pm[1]]; v_=v_[:Pm[0],:Pm[1]]
    a=v_-v_[v_>0].mean() if (v_>0).any() else v_; b=o_-o_[o_>0].mean() if (o_>0).any() else o_
    cc=irfft2(rfft2(a)*np.conj(rfft2(b)),a.shape); iy,ix=np.unravel_index(np.argmax(cc),cc.shape)
    dy=iy if iy<a.shape[0]//2 else iy-a.shape[0]; dx=ix if ix<a.shape[1]//2 else ix-a.shape[1]
    best=None
    for ddy in range(dy-1,dy+2):
        for ddx in range(dx-1,dx+2):
            vs=np.roll(np.roll(v_,-ddy,0),-ddx,1); m=(vs>0)&(o_>0)
            if m.sum()>1000:
                r=float(np.sqrt(((vs-o_)[m]**2).mean()))
                if best is None or r<best[0]: best=(r,ddy,ddx)
    return best
def run(seg):
    # 2026-11-08 coordinator: the render cache under scratch/home/.VC3D grew to 86 GB in 36 segments (disk 96 percent); it holds only re-fetchable remote chunks, so it is emptied before every segment
    for _e in os.listdir(os.path.join(S,'home-c2/.VC3D')) if os.path.isdir(os.path.join(S,'home-c2/.VC3D')) else []: shutil.rmtree(os.path.join(S,'home-c2/.VC3D',_e),ignore_errors=True)
    import zarr, numcodecs, numpy as np
    pl,why=plan(seg)
    if why: sys.exit('REFUSED %s: %s'%(seg,'; '.join(why)))
    # 2026-11-08 (coordinator decision): group 0 only; group 2 refused until the level offset is settled
    if pl['group']!='0' and not os.environ.get('RSV_ALLOW_GROUP2'): sys.exit('REFUSED %s: group %s not rendered (group 0 only)'%(seg,pl['group']))
    z,h,w=[int(x) for x in pl['shape'].split('x')]
    need=z*h*w
    if free()-need<FLOOR: sys.exit('REFUSED %s: free %.1f GB minus %.1f GB output under the floor %.0f GB'%(seg,free()/1e9,need/1e9,FLOOR/1e9))
    work=os.path.join(OUTROOT,seg); os.makedirs(work,exist_ok=True); tmp=os.path.join(work,'tmp'); os.makedirs(tmp,exist_ok=True)
    mdir=get_mesh(seg,pl)
    t0=time.time(); pr=shift_probe(pl,seg,mdir,tmp)
    if pr is None or pr[0]>1.0: sys.exit('REFUSED %s: shift probe rms %s (rounding floor about 0.29)'%(seg,pr))
    _,dy,dx=pr
    y0,y1,x0,x1=pl['box']; dst=os.path.join(work,'image.zarr')
    g=zarr.open_group(dst,mode='w',zarr_format=2); arr=g.create_array('0',shape=(z,h,w),chunks=(z,512,512),dtype='uint16',compressors=numcodecs.Zstd(level=3),fill_value=0)
    for ty in range(0,h,TILE):
        for tx in range(0,w,TILE):
            th,tw=min(TILE,h-ty),min(TILE,w-tx); t=os.path.join(tmp,'tile.zarr'); shutil.rmtree(t,ignore_errors=True)
            c=[VBIN,'--volume',pl['vol'],'--segmentation',mdir,'--zarr-output',t,'--scale','1','--group-idx',pl['group'] or '0','--num-slices','23','--slice-step','1','--cache-gb','8','--flip-normals',
               '--crop-x',str(x0+tx-dx),'--crop-y',str(y0+ty-dy),'--crop-width',str(tw),'--crop-height',str(th),'--pyramid','0','--voxel-size',pl['vs'] or str(pl['rec'].get('px0_um','9.362')),'--voxel-unit','micrometer','--surface-interpolation','bicubic']
            subprocess.run(['nice','-n','10']+c,check=True,capture_output=True,env=dict(os.environ,HOME=S+'/home-c2',TMPDIR='/data/tmp'))
            a=np.asarray(zarr.open(t,mode='r')['0'])
            if a.shape!=(z,th,tw): sys.exit('REFUSED %s tile shape %s expected %s'%(seg,a.shape,(z,th,tw)))
            arr[:,ty:ty+th,tx:tx+tw]=a.astype(np.uint16)*256     # same scale as the O store: x = v / 65280
    shutil.rmtree(tmp,ignore_errors=True)
    csvp=N+'/out/render-set-c2.csv'; new=not os.path.exists(csvp)
    with open(csvp,'a',newline='') as f:
        w_=csv.writer(f)
        if new: w_.writerow(['time','tool','segment','shape','shift_dy','shift_dx','probe_rms','seconds','out','binary_sha256'])
        w_.writerow([time.strftime('%FT%TZ',time.gmtime()),'render_set_c2_one.py',seg,pl['shape'],dy,dx,'%.4f'%pr[0],'%.1f'%(time.time()-t0),dst,vsha])
if __name__=='__main__':
    if sys.argv[1]=='--check-all': check_all()
    else: run(sys.argv[1])
