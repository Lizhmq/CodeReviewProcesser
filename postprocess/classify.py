import os
import json
import numpy as np
import joblib
import argparse
import itertools
from sentence_transformers import SentenceTransformer
import pickle

def getembeddings(sentences):
    """Generate embeddings for the passed sentences
    """
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    return model.encode(sentences, show_progress_bar=True)


def getLabels(preds, thresh, classes):
    """Retrieve labels based on threshold value passed
    """
    prob = np.exp(preds) / np.sum(np.exp(preds), axis=1, keepdims=True)

    above_threshold = prob > thresh
    values_above = np.argmax(above_threshold, axis=1)
    values_above = values_above - (~np.any(prob > thresh, axis=1)).astype(int)
    return classes[values_above]


def getpredictions(data, loaded_svc_model, thre, classes):
    """Get predictions and use the threshold to find final classes.
    """
    preds = loaded_svc_model.decision_function(np.array(data.tolist()))
    return getLabels(preds, thre, classes)

def getpredictions_parallel(processes, embeddings, model, thre, classes):
    """This functions generate the predictions in parallel for faster processing.
    """

    n_chunks = processes
    n_samples = len(embeddings)

    slices = [(int(n_samples * i / n_chunks), int(n_samples * (i + 1) / n_chunks)) for i in range(n_chunks)]

    data_chunks = [embeddings[i[0]:i[1]] for i in slices]

    jobs = (joblib.delayed(getpredictions)(array, model, thre, classes) for array in data_chunks)
    parallel = joblib.Parallel(n_jobs=n_chunks)

    # Run jobs: works
    results = parallel(jobs)

    return list(itertools.chain.from_iterable(results))


def infer(read_name, save_name, loaded_svc_model, thre, n_processes, classes):
    """
    read from a jsonl file and add `cmt_label` property
    """
    datas = [json.loads(line) for line in open(read_name, "r").readlines()]
    cmts = []
    idxs = []
    for i,data in enumerate(datas):
        if 'msg' in data and len(data['msg']) > 0:
            cmts.append(data['msg'].strip())
            idxs.append(i)
    rbembeddings = getembeddings(cmts)
    # preds = getpredictions(rbembeddings)
    unkcnt = 0
    preds = getpredictions_parallel(n_processes, rbembeddings, loaded_svc_model, thre, classes)
    for i, pred in enumerate(preds):
        datas[idxs[i]]['cmt_label'] = pred
        if pred == "UNKNOWN":
            unkcnt += 1
    print(f"UNKNOWN: {unkcnt}")
    with open(save_name, "w") as f:
        for data in datas:
            f.write(json.dumps(data) + "\n")

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--read_name", "-i", type=str, required=True, help="Name of the jsonl file to read")
    parser.add_argument("--save_name", "-o", type=str, required=True, help="Name of the jsonl file to save")
    parser.add_argument("--thresh", "-t", type=float, default=0.5, help="Threshold value to use")
    # default threthold is 0.5
    args = parser.parse_args()

    n_processes = 10
    loaded_svc_model = pickle.load(open("finalized_model.sav", 'rb'))

    classes = np.append(loaded_svc_model.classes_, "UNKNOWN")
    
    infer(args.read_name, args.save_name, loaded_svc_model, args.thresh, n_processes, classes)
