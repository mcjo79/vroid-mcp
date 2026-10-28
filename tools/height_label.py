import numpy as np
from PIL import Image
def label_crop(png, out):
    a=np.asarray(Image.open(png).convert("RGB")).astype(int)
    m=(a[...,2]>200)&(a[...,0]<80)&(a[...,1]>100)&(a[...,1]<180)
    m[:, :1300]=False; m[:, 2150:]=False
    ys,xs=np.where(m)
    Image.open(png).convert("RGB").crop((xs.min()-5,ys.min()-5,xs.max()+5,ys.max()+5)).resize(((xs.max()-xs.min()+10)*3,(ys.max()-ys.min()+10)*3)).save(out)
