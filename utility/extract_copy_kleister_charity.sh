# script to extract cherry-picked items and compile for playgroup
# Ian 2026-02

#cd /media/ian/data/playgroup_datasets/kleister-charity
#git clone https://github.com/applicaai/kleister-charity.git
#$ ./annex-get-all-from-s3.sh

#dev-0$ xz -d in.tsv.xz # uncompress input data
# e.g. $ cut -f1 in.tsv | head -n 20 # list first 20 items

# extract the identified dev-0 good-looking examples
export ROWS='4p;5p;6p;7p;11p;15p;18p' # first identify the rows we need to process
export DATA_FOLDER='/home/ian/workspace/personal/playgroup/playgroup_202602_docextract/data'
export BENCHMARK_FOLDER='/media/ian/data/playgroup_datasets/kleister-charity/dev-0'

cd $BENCHMARK_FOLDER

# extract only the relevant items of input and gold standard data
sed -n $ROWS in.tsv > playgroup_dev_in.tsv
sed -n $ROWS expected.tsv > playgroup_dev_expected.tsv
# extract a list of pdf names we need
cut -f1 in.tsv | sed -n $ROWS > pdf_names.txt
# copy the pdf files and our tsv files to the project data folder
while IFS= read -r filename; do     cp "../documents/$filename" "$DATA_FOLDER/$filename"; done < pdf_names.txt
cp pdf_names.txt $DATA_FOLDER
mv playgroup_dev_*.tsv $DATA_FOLDER
