This docoument is for Ian, to convert the Kleister Charity dataset raw data into a smaller useful subset for a playgroup session.

# Setup notes for Ian

```
cd /media/ian/data/playgroup_datasets/kleister-charity
git clone https://github.com/applicaai/kleister-charity.git
$ ./annex-get-all-from-s3.sh

dev-0$ xz -d in.tsv.xz # uncompress input data
# e.g. $ cut -f1 in.tsv | head -n 20 # list first 20 items

$ cd dev-0
# extract the identified dev-0 good-looking examples
export ROWS='4p;5p;11p' # first identify the rows we need to process
export DATA_FOLDER='/home/ian/workspace/personal/playgroup/playgroup_202602_docextract/data'

# extract only the relevant items of input and gold standard data
sed -n $ROWS in.tsv > playgroup_dev_in.tsv
sed -n $ROWS expected.tsv > playgroup_dev_expected.tsv
# extract a list of pdf names we need
cut -f1 in.tsv | sed -n $ROWS > pdf_names.txt
# copy the pdf files and our tsv files to the project data folder
while IFS= read -r filename; do     cp "../documents/$filename" "$DATA_FOLDER/$filename"; done < pdf_names.txt
cp pdf_names.txt $DATA_FOLDER
mv playgroup_dev_*.tsv $DATA_FOLDER

```

# Things we could test

* calling llm_openrouter with an unknown model name, only_providers should raise
