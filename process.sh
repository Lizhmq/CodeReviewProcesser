lang=csharp
ends=.cs
token=[gh_token]


repos=(
GitTools/GitVersion
)


for repo in "${repos[@]}"
do
    python -u pull_file.py --db $repo --repo $repo --lang $lang \
            --tmppath tmpfspl --token $token --ends $ends >> logs/$lang-pf.txt
    python -u create_cls_dataset.py --db $repo --repo $repo --lang $lang \
            --tmppath tmpfscr --outpath reviews --token $token >> logs/$lang-cls.txt
    python -u create_gen_dataset.py --db $repo --repo $repo --lang $lang \
            --tmppath tmpfscr2 --outpath reviews --token $token >> logs/$lang-gen.txt
    python -u create_refine.py --db $repo --repo $repo --lang $lang \
            --tmppath tmpfsref --outpath reviews --token $token --ends $ends >> logs/$lang-ref.txt
done
