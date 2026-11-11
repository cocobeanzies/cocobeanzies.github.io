import os
os.environ["PYTHONUTF8"] = "1"
import base64
import json
from math import *
import shutil
import subprocess
import sys
import numpy as np
from PIL import Image
from misc.util import EvalPipe

PORT = 7776
interface = EvalPipe.connect(
	[sys.executable, "-m", "misc.x_compute", str(PORT), "0", "image", "0", "0", "[0]"],
	PORT,
	glob=globals(),
	independent=False,
	timeout=30,
)

def max_size(w, h, maxsize, force=False):
	s = w * h
	m = maxsize * maxsize
	if s > m or force:
		r = (m / s) ** 0.5
		w = round(w * r)
		h = round(h * r)
	return w, h

lossless = False
fmts = ("avif", "webp")

inputs = """
"./coco.gif"
"."
384
False
False

"pictures/galaxy.png"
"pictures"
384
False
False

"pictures/Snowdrop_Cacao.png"
"pictures"
384
True
False

"pictures/Gold_Bean_Sausage.png"
"pictures"
384
True
False

"pictures/Together.png"
"pictures"
3840
False
False

"pictures/Wainbow_Pee_Enn_Gee.png"
"pictures"
2560
False
False

"pictures/Roseland.png"
"pictures"
3840
False
False

"pictures/Roseland_Sun.png"
"pictures"
2560
False
False

"pictures/Roseland_Gradient.png"
"pictures"
3840
False
False

"pictures/Roseland_Clouds.png"
"pictures"
3840
False
False

"pictures/Roseland_Clouds2.png"
"pictures"
3840
False
False

"pictures/Roseland_Leaves.png"
"pictures"
3840
False
False

"pictures/Roseland_1.png"
"pictures"
3840
False
False

"pictures/Roseland_2.png"
"pictures"
3840
False
False

"pictures/Roseland_3.png"
"pictures"
3840
False
False

"pictures/Roseland_Bottom.png"
"pictures"
3840
True
False

"styles-source/animated"
"styles-full/animated"
16384
False
False

"styles-source"
"styles-full"
16384
True
False

"styles-source"
"styles"
384
False
False

"clouds-source"
"clouds"
256
False
False

"jwst-source"
"jwst"
128
False
"trans rights!"

"stamps-source"
"stamps"
128
False
"bad_apple.avif,rickroll.avif,peepys_theme.avif"
"""

def convert_image(fold, fn, dfold, fmt, lossless, stamp):
	sfn = fold + "/" + fn
	fn2 = fn.rsplit(".", 1)[0] + "." + fmt
	dfn = dfold + "/" + fn2
	if os.path.exists(dfn) and os.path.getsize(dfn) and os.path.getmtime(dfn) > os.path.getmtime(sfn):
		return
	optim = "'-o'," if not lossless else ""
	if stamp and fn not in stamp:
		data = interface.run(f"evaluate_image([{repr(sfn)},'stamp_map',[[],None,None,{optim}'-f',{repr(fmt)}]])", timeout=3600)
	elif fn != fn2:
		data = interface.run(f"evaluate_image([{repr(sfn)},'resize_map',[[],None,None,'max',{size},None,{optim}'-f',{repr(fmt)}]])", timeout=3600)
	else:
		with open(sfn, "rb") as f:
			data = f.read()
	with open(dfn, "wb") as f:
		f.write(data)

for info in inputs.split("\n\n"):
	source, dest, size, lossless, stamp = map(eval, info.strip().splitlines())
	if stamp:
		stamp = set(stamp.split(","))
	fmtm = [fmts[-1]] if lossless else fmts
	if not os.path.exists(dest):
		d2 = dest.rsplit("/", 1)[0]
		if d2 != dest and not os.path.exists(d2):
			os.mkdir(d2)
		os.mkdir(dest)
	for fmt in fmtm:
		if os.path.isdir(source):
			sources = sorted(os.listdir(source))
			print(f"{source}: {len(sources)}")
			for style in sources:
				fold = source + "/" + style
				if os.path.isdir(fold):
					dfold = dest + "/" + style
					if not os.path.exists(dfold):
						os.mkdir(dfold)
					for fn in sorted(os.listdir(fold)):
						convert_image(fold, fn, dfold, fmt, lossless, stamp)
				else:
					fold = source + "/"
					convert_image(fold, style, dest, fmt, lossless, stamp)
		else:
			fold, fn = source.replace("\\", "/").rsplit("/", 1)
			convert_image(fold, fn, dest, fmt, lossless, stamp)

with open("index.html", "r+", encoding="utf-8") as f:
	text = f.read()
	first, content = text.split("<!-- BEGIN DYNAMIC IMAGES -->", 1)
	images, content = content.split("<!-- END DYNAMIC IMAGES -->", 1)
	middle, content = content.split("//// BEGIN DYNAMIC CONTENT", 1)
	content, last = content.split("//// END DYNAMIC CONTENT", 1)

	def try_listdir(path):
		try:
			return os.listdir(path)
		except FileNotFoundError:
			return []

	image_map = {
		"lineless": sorted(filter((lambda fn: fn.endswith(".webp")), try_listdir("styles/lineless"))),
		"lined": sorted(filter((lambda fn: fn.endswith(".webp")), try_listdir("styles/lined"))),
		"animated": sorted(filter((lambda fn: fn.endswith(".avif")), try_listdir("styles/animated"))),
	}
	imagelist = "\n".join(f'<img id="{(k + "/" + v).replace("\"", "$")}" loading="lazy" src="/styles/{k}/{v}" alt="{v.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace("_", " ")} by Cocobeanzies">' for k in image_map for v in image_map[k])
	images = f"""<!-- BEGIN DYNAMIC IMAGES -->

{imagelist}

<!-- END DYNAMIC IMAGES -->

"""

	content = f"""//// BEGIN DYNAMIC CONTENT

const STAMPS = {json.dumps(sorted(fn for fn in os.listdir("stamps") if fn.endswith('.avif')))};

const JWST = {json.dumps(sorted(fn for fn in os.listdir("jwst") if fn.endswith('.avif')))};

""" + """/// Style Gallery
const STYLES = [
	{
		name: "Lineless, Cell Shade or Rendering",
		path: "lineless",
		images: """ + json.dumps(image_map["lineless"]) + """,
		shuffle: true
	}, {
		name: "Lined, Typically Cell Shade",
		path: "lined",
		images: """ + json.dumps(image_map["lined"]) + """,
		shuffle: true
	}, {
		name: "Animated, Pixel or Frame-by-Frame",
		path: "animated",
		images: """ + json.dumps(image_map["animated"]) + """,
		shuffle: true,
		animated: true
	}
]

//// END DYNAMIC CONTENT

"""

	text = first + images + middle.lstrip() + content + last.strip()
	# with open("test.html", "w", encoding="utf-8") as f:
		# f.write(text)
	# raise
	f.seek(0)
	f.truncate(len(text))
	f.write(text)

images = "\n".join(f"""<image:image>
<image:loc>https://cocobeanzies.github.io/styles/{k}/{v}</image:loc>
<image:caption>{v.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace("_", " ")} by Cocobeanzies</image:caption>
<image:title>{v.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace("_", " ")}</image:title>
</image:image>""" for k in image_map for v in image_map[k])
with open("sitemap.xml", "w", encoding="utf-8") as f:
	f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset 
  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
	<loc>https://cocobeanzies.github.io</loc>
{images}
  </url>
</urlset>""")