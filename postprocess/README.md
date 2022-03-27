## Postprocess

### Files

* classify.py: classify the comment with the model `finalized_model.sav`.
* cleaner.py: clean the code and comments.
* pretrain_data.py: collect data from json files and clean, write to large chunks.
* pretrain_rechunk.py: resplit the pre-train data to a specifical number of chunks (e.g. 64 chunks).
* downstream_xx.py: process downstream (benchmark) datasets.



### Warning
Before you run the code, please make sure you have modified the **absolute path** in the code, and read the comments carefully in
the source code.

### Pre-train data
```bash
python pretrain_data.py
python static.py
python pretrain_rechunk.py
```

### Benchmark dataset
CLS & MSG
```bash
python downstream_train.py  / python downstream_test.py
python downstream_downsample.py     # downsample no msg data to create a balanced data
python downstream_taglabel.py       # classify the message labels
python downstream_split.py          # split to train, test, valid
```

REF
```bash
python downstream_refine.py
python downstream_refine_split.py
```