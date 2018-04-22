#!/usr/bin/python

import numpy as np
from scipy.stats import t
from optparse import OptionParser

def ci(data, confidence=0.95):
    std = np.std(data)
    return t.ppf((1+confidence)/2., len(data) - 1)*std/np.sqrt(len(data))

parser = OptionParser()
parser.add_option("-i", "--interval", dest="interval", type="int", default=0, 
                    help="Interval (step) is the number of lines to group"
                    " the input and calculate data (default not grouping)")
parser.add_option("-f", "--field", dest="field", type="int",
                    default=0, help="Field number (start at 0)")
parser.add_option("-c", "--confidence", dest="confidence", type="int",
                    default=0, help="Confidence Interval 1 -- 100 (default not calc)")
parser.add_option("-s", "--skip_header", dest="skip_header", type="int",
                    default=0, help="The number of lines to skip at the"
                    " beginning of the file")
parser.add_option("-m", "--max_rows", dest="max_rows", type="int",
                    default=None, help="The maximum number of rows to read")
(opt, args) = parser.parse_args()


data=np.genfromtxt(str(args[0]), skip_header=opt.skip_header,
                max_rows=opt.max_rows)
if opt.interval == 0:
    opt.interval = len(data)

if opt.confidence > 1:
    opt.confidence = opt.confidence / 100.0
rows=data.shape[0]
if len(data.shape) > 1:
    cols=data.shape[1]
else:
    cols=1

# create an empty arry
nrfiles=len(args)
all=np.ones((int(nrfiles),int(rows),int(10)))

# load data
n=0
mean_range = [list() for _ in xrange(len(data) / opt.interval)]
std_range = [list() for _ in xrange(len(data) / opt.interval)]
mean_total = []
std_total = []
for file in args:
    data=np.genfromtxt(str(file), skip_header=opt.skip_header,
            max_rows=opt.max_rows)
    if cols == 1:
        data.shape = (data.shape[0], 1) 
    all[n,:,0:cols]=data
    n=n+1
    i, k = 0, 0
    while i < len(data):
        j = i + opt.interval
        mean_range[k].append(np.mean(data[i:j,opt.field]))
        std_range[k].append(np.std(data[i:j,opt.field]))
        i += opt.interval
        k += 1
    mean_total.append(np.mean(data[:,opt.field]))
    std_total.append(np.std(data[:,opt.field]))

#calculate mean for individual measurements
mean_all=np.mean(all,axis=0)
std_all=np.std(all,axis=0)

### calc the mean/std/ci for all data in the range
###i=0
###print "Interval\tAvg\tStd\tMin\tMedian\tMax\tCI=%.2f" % (opt.confidence)
###while i < len(data):
###    j = i + opt.interval
###    print "% 5d -- % 5d\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f" % (i, j,
###            np.mean(all[:,i:j,opt.field]),
###            np.std(all[:,i:j,opt.field]),
###            np.min(all[:,i:j,opt.field]),
###            np.median(all[:,i:j,opt.field]),
###            np.max(all[:,i:j,opt.field]),
###            ci(all[:,i:j,opt.field], confidence=opt.confidence))
###    i += opt.interval

### calc mean/std/ci for the average of each range
i, k = 0, 0
print "Interval\tAvg\tStd\tCI=%.2f\tMin\tMedian\tMax" % (opt.confidence)
while i < len(data):
    j = i + opt.interval
    print "% 5d -- % 5d\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f" % (i, j,
            np.mean(mean_range[k]),
            np.std(mean_range[k]),
            ci(mean_range[k], confidence=opt.confidence),
            np.min(mean_range[k]),
            np.median(mean_range[k]),
            np.max(mean_range[k]))
    i += opt.interval
    k += 1

i, j = 0, len(data)
print "% 5d -- % 5d\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f" % (i, j,
        np.mean(mean_total),
        np.std(mean_total),
        ci(mean_total, confidence=opt.confidence),
        np.min(mean_total),
        np.median(mean_total),
        np.max(mean_total))

#print to stdout
#for i in range(rows):
#      a=''
#      for j in range(cols):
#         a=a+str('%.2f %.2f   ' % (mean_all[i,j], std_all[i,j]))
#      print str(a)

