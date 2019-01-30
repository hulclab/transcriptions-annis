import pprint
import os
import json
import platform
import subprocess
from openpyxl import load_workbook

FFMPEG_WIN = 'C:\\ffmpeg-4.1-win64-static\\bin\\ffmpeg'
PATH_SEP = "\\" if "Windows" == platform.system() else "/"

print("Processing source excel file... ", end='', flush=True)
wb = load_workbook(filename = 'Video.xlsx')
first = True
headers = []
jsonout = {}
for row in wb.worksheets[0].rows:
    if first:
        for cell in row:
            headers.append(cell.value)
        first = False
    else:
        for cell in row:
            if cell.col_idx == 1:
                current_exp = cell.value
                if current_exp not in jsonout:
                    jsonout[current_exp] = {}
            elif cell.col_idx == 2:
                current_stimulus = cell.value
                if current_stimulus not in jsonout[current_exp]:
                    jsonout[current_exp][current_stimulus] = {}
            else:
                jsonout[current_exp][current_stimulus][headers[cell.col_idx - 1]] = cell.value.strip()
print("done.", flush=True)

processed_sources = []
for experiment, data in jsonout.items():
    for stimulus, params in data.items():
        src = params['filename']
        if src not in processed_sources:
            outfile = src+'.webm'
            print("Converting file %s... " % outfile, end='', flush=True)
            target_dir = os.path.dirname(src)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            cmd = FFMPEG_WIN+' -y -i video_src'+PATH_SEP+src+' -c:v libvpx-vp9 -b:v 2M video'+PATH_SEP+outfile
            subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            jsonout[experiment][stimulus]['filename'] = outfile
            processed_sources.append(params['filename'])
            print("done.", flush=True)

print("Writing output file... ", end='', flush=True)
with open('video.json', 'w') as f:
    json.dump(jsonout, f, ensure_ascii=False, indent=2)
print("done.", flush=True)
