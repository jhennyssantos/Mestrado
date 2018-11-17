#!/usr/bin/gnuplot
# A Script to create graphs with errorbars
#
# Mateus Sousa (n00b), May 2017
#
# License GPLv3
#
# Version 1.0

#set terminal pdf
set terminal postscript eps color "Times" 20
set encoding utf8
set termoption enhanced
set output 'bitrate.eps'

set grid ytics lt 0 lw 1 lc rgb "#cccccc"
set grid xtics lt 0 lw 1 lc rgb "#cccccc"
#set style line 1 lt 1 pt 12 ps 2 lw 2 lc rgb "black"
#set style line 2 lt 2 pt 9 ps 2 lw 2 lc rgb "black"
#set style line 3 lt 3 pt 4 ps 2 lw 2 lc rgb "black"
#set style line 4 lt 4 pt 3 ps 2 lw 2 lc rgb "black"
#set style line 5 lt 5  pt 7 ps 2 lw 2 lc rgb "black"

set style line 1 lw 2 lc rgb "blue"
set style line 2 lt 2 pt 9 ps 2 lw 2 lc rgb "black"
set style line 3 lt 3 pt 4 ps 2 lw 2 lc rgb "blue"
set style line 4 lt 4 pt 3 ps 2 lw 2 lc rgb "red"
set style line 5 lt 5 pt 7 ps 2 lw 2 lc rgb "cyan"

set notitle
set xlabel "Tempo (s)"
set ylabel "Taxa de Bits (kbps)"
set xtics 200
set ytics 200

#set key t r

set xrange [0:600]
set yrange [0:700]
#urban_pdr.dat
#urban_pdr.dat
#plot "plotbufferlevel.dat" using 1:2:4:5  title "Ocupação do Buffer" with linespoints ls 1,\
#"plotbufferlevel.dat" using 1:2:4:5 notitle w yerrorbars ls 1,\
#1 / 0 notitle  smooth csplines with lines ls 1

plot "plotbitrate.dat" using 1:3:4  notitle with lines ls 1,\
#"plotbufferlevel.dat" using 1:2 notitle ls 1,\
#1 / 0 notitle  smooth csplines with lines ls 1
