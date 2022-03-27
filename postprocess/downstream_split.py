import json
import random

def read_jsonl(path):
    ret = []
    with open(path, 'r') as f:
        for line in f:
            ret.append(json.loads(line))
    return ret

def write_jsonl(path, data):
    with open(path, 'w') as f:
        for d in data:
            f.write(json.dumps(d) + '\n')


random.seed(2233)
trainf = 'newdata/outtrain-lang-am.jsonl'
traindata = read_jsonl(trainf)
random.shuffle(traindata)
msgdata = [data for data in traindata if data["msg"] != "" and data["y"] == 1 and data["cmt_label"] != "UNKNOWN"]
clsdata = [data for data in traindata if data["msg"] == "" and data["y"] == 0]
clsdata = random.choices(clsdata, k=len(msgdata)) + msgdata
print(len(clsdata))
random.shuffle(clsdata)
train_java = [data for data in clsdata if data["lang"] == "java"]
print(len(train_java))
print(sum([dic['y'] for dic in train_java]) / len(train_java))
write_jsonl('newdata/cls-train-java.jsonl', train_java)
del train_java
# train_cs = [data for data in clsdata if data["lang"] == ".cs"]
# print(len(train_cs))
# print(sum([dic['y'] for dic in train_cs]) / len(train_cs))
# write_jsonl('newdata/cls-train-cs.jsonl', train_cs)
# del train_cs
# train_rb = [data for data in clsdata if data["lang"] == "rb"]
# print(len(train_rb))
# print(sum([dic['y'] for dic in train_rb]) / len(train_rb))
# write_jsonl('newdata/cls-train-rb.jsonl', train_rb)
# del train_rb
# write_jsonl('newdata/msg-train.jsonl', msgdata)
# print(f"Cls train: {len(clsdata)}.")
# print(f"Msg train: {len(msgdata)}.")

# testf = 'data/outtest-am.jsonl'
# testdata = read_jsonl(testf)
# random.shuffle(testdata)
# msgdata = [data for data in testdata if data["msg"] != "" and data["y"] == 1 and data["cmt_label"] != "UNKNOWN"]
# clsdata = [data for data in testdata if data["msg"] == "" and data["y"] == 0]
# clsdata = random.choices(clsdata, k=len(msgdata))
# splitl = len(msgdata) // 2
# validcls = clsdata[:splitl] + msgdata[:splitl]
# testcls = clsdata[splitl:] + msgdata[splitl:]
# random.shuffle(validcls)
# random.shuffle(testcls)
# write_jsonl('data/cls-valid.jsonl', validcls)
# write_jsonl('data/cls-test.jsonl', testcls)
# write_jsonl('data/msg-valid.jsonl', msgdata[splitl:])
# write_jsonl('data/msg-test.jsonl', msgdata[:splitl])
# print(f"Cls valid: {len(validcls)}.")
# print(f"Cls test: {len(testcls)}.")
# print(f"Msg valid: {len(msgdata[splitl:])}.")
# print(f"Msg test: {len(msgdata[:splitl])}.")