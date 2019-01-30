#!/usr/bin/python3
import re
import json
import os
import glob
import argparse
import platform


def meta_match(l, meta_search):
    for meta_key, meta_re in meta_search.items():
        meta_match = meta_re.match(l)
        if meta_match:
            return (meta_key, meta_match.group(1).strip())
    return ('', '')


# ARGS
parser = argparse.ArgumentParser()
parser.add_argument('source', help='source folder name')
parser.add_argument('exp', help='experiment name')
parser.add_argument('--language', '-l', help='language of dataset', default='english')
args = parser.parse_args()

# DEFINE HEADER METADATA TO LOOK FOR
meta_search = {}
meta_search["subject_id"] = re.compile(r"^\s*Subject\s*ID:?\s*<?(.*)>?", re.IGNORECASE)
meta_search["subject_code"] = re.compile(r"^\s*Subject\s*Code:?\s*<?(.*)>?", re.IGNORECASE)
meta_search["country"] = re.compile(r"^\s*Country\s*:?\s*<?(.*)>?", re.IGNORECASE)
meta_search["sex"] = re.compile(r"^\s*Sex\s*:?\s*<?(.*)>?", re.IGNORECASE)
meta_search["age"] = re.compile(r"^\s*Age\s*:?\s*<?(.*?)>?", re.IGNORECASE)
meta_search["second_languages"] = re.compile(r"^\s*Second Languages\s*:?\s*<?(.*)>?", re.IGNORECASE)
text_re = re.compile(r"^\s*\d+(.*)$")
stimulus_re = re.compile(r"^<?(.*)>?:\s*$")

jsonout = {}
jsonout['id'] = args.exp
jsonout['language'] = args.language
jsonout['subject_meta'] = {}
jsonout['verbalizations'] = {}
# TRAVERSE SOURCE DIR
for source_file in glob.glob(args.source+"/*.txt"):
    try:
        lines = [line.strip() for line in open(source_file)]
    except FileNotFoundError:
        print("Could not open file: " + source_file)
        continue
    if len(lines) < 1:
        print("File has no content: " + source_file)
        continue
    print("Processing source file " + source_file, end='', flush=True)

    current_stimulus = ''
    current_text = ''
    meta = {}
    verbalizations = {}
    for l in lines:
        (meta_key, meta_value) = meta_match(l, meta_search)
        if meta_key:
            meta[meta_key] = meta_value
        else:
            sm = stimulus_re.match(l)
            tm = text_re.match(l)
            if sm:
                if current_stimulus and current_utterances:
                    verbalizations[current_stimulus] = current_utterances
                    print(".", end='', flush=True)
                current_stimulus = sm.group(1).strip()
                current_utterances = []
            elif tm:
                current_utterance = {}
                current_utterance['text'] = tm.group(1).strip()
                current_utterances.append(current_utterance)

    subject_identifier = meta.get('subject_id', '') + meta.get('subject_code', '')
    if not subject_identifier:
        subject_identifier = os.path.splitext(os.path.basename(source_file))[0]
    jsonout['subject_meta'][subject_identifier] = meta
    jsonout['verbalizations'][subject_identifier] = verbalizations
    print("done.", flush=True)

with open(args.exp+'.json', 'w') as f:
    json.dump(jsonout, f, ensure_ascii=False, indent=2)
