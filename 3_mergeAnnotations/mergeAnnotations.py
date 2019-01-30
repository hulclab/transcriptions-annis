import sys
import pprint
import os
import re
import json
import platform
import subprocess
import argparse
import xlrd


def first_full_row(sheet, cols):
    for rownum in range(sheet.nrows):
        row = sheet.row(rownum)
        if len(row) < cols:
            continue
        full = True
        for cell in row:
            if not cell.value:
                full = False
                break
        if full:
            return row
    return None


PATH_SEP = "\\" if "Windows" == platform.system() else "/"

parser = argparse.ArgumentParser()
parser.add_argument('source', help='source excel file name')
parser.add_argument('target', help='target experiment file name')
args = parser.parse_args()

# READ TARGET EXPERIMENT FILE
print("Reading target JSON file: " + args.target, flush=True)
try:
    f = open(args.target)
    target = json.loads(f.read())
    f.close()
except FileNotFoundError as err:
    exit(err)

# READ INPUT EXCEL FILE
print("Processing source excel file: " + args.source, flush=True)
try:
    wb = xlrd.open_workbook(args.source, ragged_rows=False)
except FileNotFoundError as err:
    exit(err)

for sheet in wb.sheets():
    stimulus = sheet.name
    r = sheet.nrows
    c = sheet.ncols
    if r >= 2 and c >= 3:
        utterance_index = 0
        last_subject = ''
        firstRow = True
        for rownum in range(r):
            row = sheet.row(rownum)
            if firstRow:
                header = list(map(lambda x: re.sub(r'\W', '_', x.value), row))
                firstRow = False
            else:
                firstCol = True
                for cellnum in range(c):
                    cell = row[cellnum]
                    if firstCol:
                        subject = cell.value
                        firstCol = False
                        if last_subject == subject:
                            utterance_index += 1
                        else:
                            utterance_index = 0
                        last_subject = subject
                    else:
                        if subject not in target["verbalizations"]:
                            print("Warning: no data found to annotate for subject %s (sheet %s, row %s)" % (subject, stimulus, rownum + 1))
                            break
                        if stimulus not in target["verbalizations"][subject]:
                            print("Warning: no data found to annotate for subject %s, stimulus %s (sheet %s, row %s)" % (subject, stimulus, stimulus, rownum + 1))
                            break
                        try:
                            if "meta" not in target["verbalizations"][subject][stimulus][utterance_index]:
                                target["verbalizations"][subject][stimulus][utterance_index]["meta"] = {}
                            target["verbalizations"][subject][stimulus][utterance_index]["meta"][header[cellnum]] = cell.value
                        except IndexError as e:
                            print("Warning: no data found to annotate for subject %s, stimulus %s, utterance %s (sheet %s, row %s)" % (subject, stimulus, utterance_index + 1, stimulus, rownum + 1))
                            break;
print("done.", flush=True)

print("Checking results...", flush=True)
# check result for data sets without annotation
for subject in target["verbalizations"].keys():
    for stimulus in target["verbalizations"][subject].keys():
        for utterance_index in range(len(target["verbalizations"][subject][stimulus])):
            if "meta" not in target["verbalizations"][subject][stimulus][utterance_index]:
                print("Warning: dataset without annotations found: subject %s, stimulus %s, utterance %s" % (subject, stimulus, utterance_index + 1))
print("done.", flush=True)

with open('anno_'+args.target, 'w') as f:
    json.dump(target, f, ensure_ascii=False, indent=2)
