#!/bin/bash

# v1.7.3

for i in "$@"; do

pageComma=$(pcregrep -o1 '^([^\/\*\|\@\"\!]*?)#\@?#\K.*' $i)

pagePipe=$(pcregrep -o3 '(domain)(=)([^,]+)' $i)

pageDoublePipe=$(pcregrep -o1 '^.*?\|\|(.*)' $i)

hosts=$(pcregrep -o1 '^.*?0.0.0.0 (.*)' $i)

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium (zakładamy, że skrypt znajduje się w katalogu o 1 niżej od głównego katalogu repozytorium)
MAIN_PATH=$(dirname "$0")/..

FILTERLIST=$(basename $i .txt)
TEMPORARY=$MAIN_PATH/${FILTERLIST}.temp

rm -rf $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt
rm -rf $MAIN_PATH/expired-domains/$FILTERLIST-unknown.txt

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

$MAIN_PATH/scripts/domain-check-2.sh -f $TEMPORARY.2 | tee $TEMPORARY.3


sed '/Expired/!d' $TEMPORARY.3 | cut -d' ' -f1 >> $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt
sed '/B_blocked/!d' $TEMPORARY.3 | cut -d' ' -f1 >> $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt
sed '/Unknown/!d' $TEMPORARY.3 | cut -d' ' -f1 >> $TEMPORARY.4

for ips in `cat $TEMPORARY.4`
do
    status_code=$(curl -o /dev/null --silent --head --write-out '%{http_code}\n' $ips)
    if [ $status_code -eq "000" ]
    then
        echo  "$ips" >> $TEMPORARY.5
    elif [ $status_code -ne "200" ] && [ $status_code -ne "000" ]
    then
        echo  "$ips $status_code" >> $MAIN_PATH/expired-domains/$FILTERLIST-unknown.txt
    else
        echo "Test"
    fi
done

# Zamieniamy subdomeny na domeny (alpha)
# https://ubuntuforums.org/showthread.php?t=873034&s=99fb8190182be62fbf8f81352b2fa4fa&p=5477397#post5477397
awk -F. '{if ($(NF-1) == "co"|| $(NF-1) == "com" || $(NF-1) == "net" || $(NF-1) == "edu" || $(NF-1) == "org" ) printf $(NF-2)"."; printf $(NF-1)"."$(NF)"\n";}' $TEMPORARY.5 >> $TEMPORARY.6
sort -u -o $TEMPORARY.6 $TEMPORARY.6

$MAIN_PATH/scripts/domain-check-2.sh -f $TEMPORARY.6 | tee $TEMPORARY.7
sed '/Expired/!d' $TEMPORARY.7 | cut -d' ' -f1 >> $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt
sed '/B_blocked/!d' $TEMPORARY.7 | cut -d' ' -f1 >> $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt
sed '/Unknown/!d' $TEMPORARY.7 | cut -d' ' -f1 >> $TEMPORARY.8

for ips in `cat $TEMPORARY.8`
do
    status_code=$(curl -o /dev/null --silent --head --write-out '%{http_code}\n' $ips)
    if [ $status_code -ne "200" ]
    then
        echo  "$ips $status_code" >> $MAIN_PATH/expired-domains/$FILTERLIST-unknown.txt
    else
        echo "Test"
    fi
done


sort -u -o $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt
sort -u -o $MAIN_PATH/expired-domains/$FILTERLIST-unknown.txt $MAIN_PATH/expired-domains/$FILTERLIST-unknown.txt
rm -rf $TEMPORARY.*
rm -rf $TEMPORARY

if [ ! -s $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt ] ; then
  rm $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt
fi

if [ ! -s $MAIN_PATH/expired-domains/$FILTERLIST-expired.txt ] ; then
  rm $MAIN_PATH/expired-domains/$FILTERLIST-unknown.txt
fi

done
