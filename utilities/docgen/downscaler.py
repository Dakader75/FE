import os
from PIL import Image

for fname in os.listdir():
  if 'png' in fname:
    img = Image.open(fname)
    baseheight = min(300, img.size[1])
    wpercent = baseheight/float(img.size[1])
    wsize = int((float(img.size[0])*float(wpercent)))
    img = img.resize((wsize,baseheight), Image.LANCZOS)
    img.save('contributing/' + (fname[:-4]) + '.jpg', optimize=True, quality=95)