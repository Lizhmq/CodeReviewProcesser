import os
import pickle
import numpy as np
from classify import infer


def merge(path, outname):
    files = os.listdir(path)
    files = [os.path.join(path, file) for file in files if file.startswith("outtraintmp-lang")]
    out = []
    for file in files:
        with open(file, encoding="utf-8") as f:
            for line in f:
                out.append(line.strip() + "\n")
    with open(outname, "w", encoding="utf-8") as f:
        for line in out:
            f.write(line)
    return


if __name__ == "__main__":
    n_processes = 6
    loaded_svc_model = pickle.load(open("finalized_model.sav", 'rb'))
    classes = np.append(loaded_svc_model.classes_, "UNKNOWN")
    # inname = "data/outtesttmp.jsonl"
    # outname = "data/outtest-am.jsonl"
    # infer(inname, outname, loaded_svc_model, 0.5, n_processes, classes)
    # print("Test done")
    merge("newdata", "newdata/outtrain-lang.jsonl")
    inname = "newdata/outtrain-lang.jsonl"
    outname = "newdata/outtrain-lang-am.jsonl"
    infer(inname, outname, loaded_svc_model, 0.5, n_processes, classes)
    print("Train done")