#!/bin/bash
for i in "$@"; do
pageComma=$(pcregrep -o1 '^([^\/\*\|\@\"\!]*?)#\@?#\K.*' $i)

pagePipe=$(pcregrep -o3 '(domain)(=)([^,]+)' $i) 

pageDoublePipe=$(pcregrep -o1 '^.*?\|\|(.*)' $i)

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium (zakładamy, że skrypt znajduje się w katalogu o 1 niżej od głównego katalogu repozytorium)
MAIN_PATH=$(dirname "$0")/..

FILTERLIST=$(basename $i .txt)
TEMPORARY=$MAIN_PATH/${FILTERLIST}.temp

echo $pageComma >> $TEMPORARY
echo $pagePipe >> $TEMPORARY
echo $pageDoublePipe >> $TEMPORARY
sed -i "s/[|]/\n/g" $TEMPORARY
sed -i "s/\,/\n/g" $TEMPORARY
sed -i "s/\ /\n/g" $TEMPORARY
sed -i "s/[/].*//" $TEMPORARY
sed -i "s/[\^].*//" $TEMPORARY
sed -i "s|\~||" $TEMPORARY
sed -i "s|domain=||" $TEMPORARY
sed -ni '/\./p' $TEMPORARY
sed -i "s|\#||" $TEMPORARY
sed -i "s|\?||" $TEMPORARY
sort -u -o $TEMPORARY $TEMPORARY

for ips in `cat $TEMPORARY`
do
    hostname=$(host ${ips})
    if [[ "${hostname}" =~ "NXDOMAIN" ]]
        then
            echo "${hostname}" | awk '{ print $2 }' >> $TEMPORARY.2
    fi
done

awk '{gsub("www.", "");print}' $TEMPORARY.2 >> $TEMPORARY.3

$MAIN_PATH/scripts/domain-check-2.sh -f $TEMPORARY.3 | tee $TEMPORARY.4
sed '/Expired/!d' $TEMPORARY.4 | cut -d' ' -f1 > $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt
sed '/Unknown/!d' $TEMPORARY.4 | cut -d' ' -f1 > $MAIN_PATH/expired-domains/$FILTERLIST-unknown.txt
sed '/Valid/!d' $TEMPORARY.4 | cut -d' ' -f1 > $MAIN_PATH/expired-domains/$FILTERLIST-clean.txt
rm -rf $TEMPORARY
rm -rf $TEMPORARY.2
rm -rf $TEMPORARY.3
rm -rf $TEMPORARY.4

done
