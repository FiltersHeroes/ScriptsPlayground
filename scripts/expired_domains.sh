#!/bin/bash

# v1.5

for i in "$@"; do
pageComma=$(pcregrep -o1 '^([^\/\*\|\@\"\!]*?)#\@?#\K.*' $i)

pagePipe=$(pcregrep -o3 '(domain)(=)([^,]+)' $i)

pageDoublePipe=$(pcregrep -o1 '^.*?\|\|(.*)' $i)

hosts=$(pcregrep -o1 '^.*?0.0.0.0 (.*)' $i)

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium (zakładamy, że skrypt znajduje się w katalogu o 1 niżej od głównego katalogu repozytorium)
MAIN_PATH=$(dirname "$0")/..

FILTERLIST=$(basename $i .txt)
TEMPORARY=$MAIN_PATH/${FILTERLIST}.temp

echo $pageComma >> $TEMPORARY
echo $pagePipe >> $TEMPORARY
echo $pageDoublePipe >> $TEMPORARY
echo $hosts >> $TEMPORARY
sed -i "s/[|]/\n/g" $TEMPORARY
sed -i "s/\,/\n/g" $TEMPORARY
sed -i "s/\ /\n/g" $TEMPORARY
sed -i "s/[/].*//" $TEMPORARY
sed -i "s/[\^].*//" $TEMPORARY
sed -i "s|\~||" $TEMPORARY
sed -i "s|domain=||" $TEMPORARY
sed -i "s|redirect=noopmp3-0.1s||" $TEMPORARY
sed -i '/[/\*]/d' $TEMPORARY
sed -ni '/\./p' $TEMPORARY
sed -i "s|\#||" $TEMPORARY
sed -i "s|\?||" $TEMPORARY
sed -i "s/[$].*//" $TEMPORARY
sort -u -o $TEMPORARY $TEMPORARY


for ips in `cat $TEMPORARY`
do
    hostname=$(host ${ips})
    if [[ "${hostname}" =~ "NXDOMAIN" ]]
    then
            echo "$ips" >> $TEMPORARY.2
    else
            echo "Test"
    fi
done

sed -i "s/^www[0-9]\.//" $TEMPORARY.2
sed -i "s/^www\.//" $TEMPORARY.2
sort -u -o $TEMPORARY.2 $TEMPORARY.2

# Zamieniamy subdomeny na domeny (alpha)
# https://ubuntuforums.org/showthread.php?t=873034&s=99fb8190182be62fbf8f81352b2fa4fa&p=5477397#post5477397
awk -F. '{if ($(NF-1) == "co"|| $(NF-1) == "com" || $(NF-1) == "net" || $(NF-1) == "edu" || $(NF-1) == "org" ) printf $(NF-2)"."; printf $(NF-1)"."$(NF)"\n";}' $TEMPORARY.2 >> $TEMPORARY.3


$MAIN_PATH/scripts/domain-check-2.sh -f $TEMPORARY.3 | tee $TEMPORARY.4
sed '/Expired/!d' $TEMPORARY.4 | cut -d' ' -f1 > $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt

sed '/Unknown/!d' $TEMPORARY.4 | cut -d' ' -f1 >> $TEMPORARY.5

for ips in `cat $TEMPORARY.5`
do
    status_code=$(curl -o /dev/null --silent --head --write-out '%{http_code}\n' $ips)
    if [ $status_code -ne "200" ]
    then
        echo  "$ips $status_code" >> $TEMPORARY.6
    else
        echo "Test"
    fi
done

touch $MAIN_PATH/expired-domains/$FILTERLIST-unknown.txt
mv $TEMPORARY.6 $MAIN_PATH/expired-domains/$FILTERLIST-unknown.txt

sort -u -o $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt
sort -u -o $MAIN_PATH/expired-domains/$FILTERLIST-unknown.txt $MAIN_PATH/expired-domains/$FILTERLIST-unknown.txt
rm -rf $TEMPORARY
rm -rf $TEMPORARY.2
rm -rf $TEMPORARY.3
rm -rf $TEMPORARY.4
rm -rf $TEMPORARY.5
rm -rf $TEMPORARY.6

done
