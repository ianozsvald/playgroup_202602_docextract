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
export ROWS='4p;5p;6p;7p;11p' # first identify the rows we need to process
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

## items reviewed

```
dev-0
pdf, pages, score on first 5 items, status, choose?
1ada336f29e8247f9f55a8d7e1b1c0da.pdf, 7, 2, clean, N - TRICK?
87ff1046fb88668ed4e0476d66abd733.pdf, 42
365a65c22610022110ca8610ecfe4034.pdf, 68
d07c46323bb61186b6175bad9a274225.pdf, 14, 5, scanned, Y
a84c1c7a3e570a716f6c61de557b5ff1.pdf, 18, 5, clean, Y
34646877386855695219579059c07302.pdf, 9, 5, scan, Y
bc1881761cdd5edf2d7e5c12958a82f2.pdf, 5, 5, scan, Y
48ec2c34cf13f32eb56baea66dbb665d.pdf, 46
00151bc74f2d59cecbed12e0d607a8e4.pdf, 20
cc9880ece943bf688b49359a8c219b04.pdf
7d56c6cc848666198c050855dbb16092.pdf, 12, 5, scanned, Y
bfd08fe466e142006e4a04e9630d4579.pdf
c1e453df06418b5289b40d04729a09c5.pdf
44ba842bbbd4f18587ad8ae3fe4ecdd7.pdf
6f9b8f27fd43be13d822c0b4654be167.pdf
556ee39a83d9a15738918e8e60dc45a7.pdf
cfe956d594cd45a0267d966dadebf72e.pdf
cc19e4fd0c4a605a7f537050df52483e.pdf
0d45add2d94d80a0eb85e41e22aa43a0.pdf
762f74d04c9fd0a99b2776603704267b.pdf

```

# Things we could test

* calling llm_openrouter with an unknown model name, only_providers should raise
