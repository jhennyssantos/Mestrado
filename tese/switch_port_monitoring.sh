#!/usr/bin/bash
while true
do
cat stats1.log > stats1.old
cat stats2.log > stats2.old
curl -X GET http://localhost:8080/stats/port/000000000001 >
raw1.log
curl -X GET http://localhost:8080/stats/port/000000000002 >
raw2.log
cat raw1.log | awk '{gsub ("tx_dropped", "\ntx_dropped") } 1' |
column -t | awk '{print $ 11 $12 $7 $8 $17 $ 18 $19 $20 $27 $28 $23
$24}' | column -t -s ',' | column -t -s ':' | sort -k2 -n >
stats1.log
cat raw2.log | awk '{gsub ("tx_dropped", "\ntx_dropped") } 1' |
column -t | awk '{print $ 11 $12 $7 $8 $17 $ 18 $19 $20 $27 $28 $23
$24}' | column -t -s ',' | column -t -s ':' | sort -k2 -n >
stats2.log
rm raw1.log raw2.log
echo " "
echo "SWITCH S1"
echo "========="
cat stats1.log
echo " "
echo "SWITCH S2"
echo "========="
cat stats2.log
echo " "
paste stats1.log stats1.old | awk '{for (i=0;i<=NF/2;i++) printf
"%s ", ($i==$i+0)?$i-$(i+NF/2):$i; print ""}' | awk '{print $1 " "
$2 " " $27 " " $28 " " $29 " " $30 " " $31 " " $32 " " $33 " "$34
" " $35 " " $36}' | column -t > diff.log
echo "================================= "
echo "PORT STATS (DIFFERENCE) SWITCH S1"
echo "================================="
cat diff.log
echo " "
cat diff.log | awk '{print $4}' | tr '\n' ' ' > diff-linear.log
awk '{if ($2 > "100" && $3 > "100") system("bash -c '\''" "bash
config1.sh" "'\''")}' diff-linear.log
awk '{if ($2 < "10" && $3 < "10" && $4 < "10" && $5 < "10" && $6 <
"10" && $7 < "10" && $8 < "10" && $9 < "10" && $11 < "10" && $12 <
"10" && $13 < "10") system("bash -c '\''" "bash remove-config.sh"
"'\''")}' diff-linear.log
echo " "
sleep 10
done
