#!/usr/bin/python3
import sys
import re
import subprocess
import pprint
import os
import glob
import argparse
import json
import platform

# Constants
PATH_TT = "/home/hulc/Desktop/tt/"
PATH_PEPPER = "/home/hulc/Desktop/pepper/"

PATH_TT_WIN = "D:\\ANNIS\\TreeTagger\\"
PATH_PEPPER_WIN = "D:\\ANNIS\\pepper\\"
PATH_SEP = "\\"

CURRENT_OS = platform.system()

def get_tagged(language, text):
    # tagger = subprocess.Popen(PATH_TT+"cmd/tree-tagger-english", shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # tagger = subprocess.Popen(PATH_TT+"cmd/tagger-chunker-german", shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    tagger = None
    if (CURRENT_OS == "Windows"):
        if (language == 'german'):
            tagger = 'perl %TTcmd\\utf8-tokenize-string.perl -a %TTlib\\german-abbreviations "%s" | %TTbin\\tree-tagger %TTlib\\german.par -token -lemma -sgml -no-unknown  | perl -nae "if ($#F==0){print}else{print \\"$F[0]-$F[1]\\n\\"}" | %TTbin\\tree-tagger %TTlib\\german-chunker.par -token -sgml -eps 0.00000001 -hyphen-heuristics | perl %TTcmd\\filter-chunker-output-german.perl | %TTbin\\tree-tagger %TTlib\\german.par -quiet -token -lemma -sgml -no-unknown'.replace('%TT', PATH_TT_WIN) % text
        if (language == 'english'):
            tagger = 'perl %TT\\cmd\\utf8-tokenize.perl -e -a %TT\\lib\\english-abbreviations "%s" | %TT\\bin\\tree-tagger %TT\\lib\\english.par -quiet -token -lemma -sgml -no-unknown | perl -nae "if ($#F==0){print}else{print \\"$F[0]-$F[1]\\n\\"}" | %TT\\bin\\tree-tagger %TT\\lib\\english-chunker.par -token -sgml -eps 0.00000001 -hyphen-heuristics | perl %TT\\cmd\\filter-chunker-output.perl | %TT\\bin\\tree-tagger %TT\\lib\\english.par -quiet -token -lemma -sgml -no-unknown'.replace('%TT', PATH_TT_WIN) % text
        if tagger:
            return "".join(["%s\n" % l for l in subprocess.check_output(tagger, shell=True, stderr=subprocess.DEVNULL).decode("utf-8").splitlines()])
        else:
            return "".join(["%s\t\t\n" % l for l in text.split()])

# ARGS
parser = argparse.ArgumentParser()
parser.add_argument('target', help='target corpus name')
args = parser.parse_args()

# CREATE TARGET DIR
target_dir = '.'+PATH_SEP+args.target
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

# READ meta file
try:
    meta = json.loads(open("video.json").read())
except FileNotFoundError:
    print("Could not open file: video.json")
    exit(1)

# TRAVERSE SOURCE DIR
video_linker_rows = []
for source_file in glob.glob("*.json"):
    if source_file == "video.json":
        continue
    print("Processing source file " + source_file + "... ", end='', flush=True)
    try:
        source = json.loads(open(source_file).read())
    except FileNotFoundError:
        print("Could not open file: " + source_file)
        continue

    exp = source['id']
    if exp not in meta:
        print('WARNING: no metadata set found for experiment %s' % exp)
        meta[exp] = {}

    for subject, subject_dict in source['verbalizations'].items():
        for stimulus, utterances in subject_dict.items():
            tt_string = "<meta%ATTR%>\n%TTRES%</meta>"
            meta_str = ' subject_id="%s"' % subject
            if stimulus not in meta[exp]:
                print('WARNING: no video data found for experiment %s, stimulus %s' % (exp, stimulus))
                meta[exp][stimulus] = {'filename': '', 'global_name': ''}
            video_id = meta[exp][stimulus]['global_name']
            video_file = os.path.basename(meta[exp][stimulus]['filename'])
            meta_str += ' video_file="%s" video_id="%s"' % (video_file, video_id)
            if subject not in source['subject_meta']:
                print('WARNING: no subject metadata set found for %s, %s' % (exp, subject))
                source['subject_meta'][subject] = {}
            for meta_key, meta_value in source['subject_meta'][subject].items():
                meta_str += ' %s="%s"' % (meta_key, meta_value)
            u_str = ""
            u_index = 1
            for u in utterances:
                u_meta_str = ''
                if 'meta' in u:
                    for meta_key, meta_value in u['meta'].items():
                        u_meta_str += ' %s="%s"' % (meta_key, meta_value)
                u_str += '<U utterance="%s"%s>\n%s</U>\n' % (u_index, u_meta_str, get_tagged(source['language'], u['text']))
                u_index += 1
            out = tt_string.replace("%ATTR%", meta_str).replace("%TTRES%", u_str)
            with open(target_dir+'/%s_%s_%s.tab' % (exp, subject, stimulus), 'w') as f:
                f.write(out)
            if video_file:
                video_linker_rows.append((target_dir+PATH_SEP+'ExtData'+PATH_SEP+'%s_%s_%s' % (exp, subject, stimulus), 'video'+PATH_SEP+video_file))
    print("done.", flush=True)

# CREATE VIDEO SYMLINKS
print("Processing video links... ", end='', flush=True)
for target_path, src in video_linker_rows:
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    if not os.path.exists(target_path+PATH_SEP+'link.webm'):
        subprocess.call(['mklink', '/H', target_path+PATH_SEP+'link.webm', src], shell=True)
print("done.", flush=True)

# RUN PEPPER
print("Converting to ANNIS format... ", end='', flush=True)
pepper_file = '%s.pepper' % exp
with open(pepper_file, 'w') as f:
    f.write('''<?xml version="1.0" encoding="UTF-8"?>
<pepper-job id="klnlv0lf" version="1.0">
	<importer name="TreetaggerImporter" path="%s">
	</importer>
	<exporter name="ANNISExporter" path="%s">
	</exporter>
</pepper-job>''' % (target_dir, target_dir))
cmd = 'java -cp lib/*;plugins/*; -Dfile.encoding=UTF-8 -Dlogback.configurationFile=./conf/logback.xml -XX:+IgnoreUnrecognizedVMOptions --add-modules=java.se.ee org.corpus_tools.pepper.cli.PepperStarter '+os.getcwd()+PATH_SEP+pepper_file
subprocess.call(cmd, cwd=PATH_PEPPER_WIN if CURRENT_OS == "Windows" else PATH_PEPPER)
# subprocess.call(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, cwd=PATH_PEPPER_WIN if CURRENT_OS == "Windows" else PATH_PEPPER)

# CLEANUP
# os.remove(pepper_file)
# for tmp_file in glob.glob(target_dir+"/*.tab"):
#     os.remove(tmp_file)
print("done.", flush=True)
