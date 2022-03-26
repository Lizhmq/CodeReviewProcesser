# CodeReviewProcesser

This repo is created to process the pull request database (refer to [ETCR](https://github.com/Lizhmq/etcr-infrastructure)) and generate the code review dataset.

Run:
```bash
cd process
bash process.sh
```

## Task Description

We create datasets for three downstream tasks:
* **Diff quality estimation**: predict whether a code change is well-written or need to be commented and improved.
* **Review generation**: generate code reviews for a code change automatically.
* **Code refinement**: revise the code based on a given code review.

Refer to our paper: [CodeReviewer](https://arxiv.org/abs/2203.09095) for more details.

![](ex.png)

## Source code

* process/pull_file.py: query GitHub api for source code related to the comments in database.
* process/create_xx_dataset.py: create a specific dataset.