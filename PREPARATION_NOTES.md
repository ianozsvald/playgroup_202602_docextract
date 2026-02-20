
# Setup notes for Ian

```
cd /media/ian/data/playgroup_datasets/kleister-charity
git clone https://github.com/applicaai/kleister-charity.git
$ ./annex-get-all-from-s3.sh

dev-0$ xz -d in.tsv.xz # uncompress input data
# e.g. $ cut -f1 in.tsv | head -n 20 # list first 20 items

$ cd dev-0
# extract the identified dev-0 good-looking examples
sed -n '4p;5p;11p' in.tsv > playgroup_dev_in.tsv
sed -n '4p;5p;11p' expected.tsv > playgroup_dev_expected.tsv
# extract a list of pdf names we need
$ cut -f1 in.tsv | head -n 20 > pdf_names.txt

# back in playgroup root (where this file is)
$ cd /home/ian/workspace/personal/playgroup/playgroup_202602_docextract
$ mv /media/ian/data/playgroup_datasets/kleister-charity/dev-0/playgroup_dev_* data/

```