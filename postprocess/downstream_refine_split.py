import json
import random


def read_jsonl(path):
    with open(path, 'r') as f:
        for line in f:
            yield json.loads(line)

def write_jsonl(path, data):
    with open(path, 'w') as f:
        for dic in data:
            f.write(json.dumps(dic) + "\n")


trainpaths = ["data/ref-train-0.jsonl", "data/ref-train-1.jsonl", "data/ref-train-2.jsonl"]
data = []
for path in trainpaths:
    for dic in read_jsonl(path):
        data.append(dic)
random.shuffle(data)
write_jsonl("data/ref-train.jsonl", data)

vtpath = "data/ref-validtest.jsonl"
validtest = list(read_jsonl(vtpath))
random.shuffle(validtest)
split_l = len(validtest) // 2
valid = validtest[:split_l]
test = validtest[split_l:]
write_jsonl("data/ref-valid.jsonl", valid)
write_jsonl("data/ref-test.jsonl", test)