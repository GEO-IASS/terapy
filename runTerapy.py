#!/usr/bin/env python
import time
import argparse
import sys
import pylab
import glob
import Terapy
import TeraData

#the option parser is initialized
parser = argparse.ArgumentParser(description='Calculate optical constants from THz-TD Data')
#Path arguments
parser.add_argument('--workpath','-w',type=str,default='',help='specify a base folder')
parser.add_argument('--isample','-is',nargs='*',help='list of sample filenames')
parser.add_argument('--ireference','-ir',nargs='*',help='list of reference filenames')
parser.add_argument('--outname','-o',nargs='?',type=str,help='prefix output filenames')

#input arguments
parser.add_argument('--mode','-m',type=str,default='INRIM',choices=['INRIM','Marburg','lucastestformat'],help='format of the datafiles')

#solver arguments
parser.add_argument('--thickness','-t',type=float,help='sample thickness')

#switches
parser.add_argument('--windowing',action='store_false',help='switch Data Windowing Off')
parser.add_argument('--zeroPadding',action='store_true',help='Switch Zero Padding on')
parser.add_argument('--calcLength',action='store_false',help='switch length calculation off')
parser.add_argument('--NoSavePlots','-s',action='store_true',help='turn off saving plots')
parser.add_argument('--silent',action='store_true',help='switch save results off')
parser.add_argument('--noSVMAF',default=5,nargs='?',type=int,help='No of SVMAF iterations')
parser.add_argument('--showPlots',action='store_true',help='Show plots')

args = parser.parse_args()

starttime=time.time()       #save the initial time
ireffiles=args.ireference   #reference files list
isamfiles=args.isample      #sample file list
mode=args.mode              #input file format
thickness=args.thickness    #thickness im m
basefolder=args.workpath    #basepath where everything should be done

reffiles=[]
samfiles=[]

#generate the list of refference and sample files
for i in range(len(ireffiles)):
    tf=glob.glob(basefolder+ireffiles[i])   
    reffiles+=tf

for i in range(len(isamfiles)):
    tf=glob.glob(basefolder+isamfiles[i])
    samfiles+=tf

#escape if there was no file found 
if len(reffiles)==0:
    print "no Reference File specified"
    sys.exit()
    
if len(samfiles)==0:
    print "no Sample File specified"
    sys.exit()
        
#use the appropriate importer
if mode=='lucastestformat':
    reftd=TeraData.THzTdData(reffiles)
    samtd=TeraData.THzTdData(samfiles)
    
if mode=='Marburg':
    reftd=TeraData.ImportMarburgData(reffiles)
    samtd=TeraData.ImportMarburgData(samfiles)

if mode=='INRIM':
    reftd=TeraData.ImportInrimData(reffiles)
    samtd=TeraData.ImportInrimData(samfiles)

#windowing of the data, Standard: yes
if args.windowing:
    
    reftd.setTDData(reftd.getWindowedData(1e-12))
    samtd.setTDData(samtd.getWindowedData(1e-12))
    
#initialize the fd_data objects        
ref_fd=TeraData.FdData(reftd)
sam_fd=TeraData.FdData(samtd)    

#Zero padding of the data, Standard: no
if args.zeroPadding:
    ref_fd.zeroPadd(5e9)
    sam_fd.zeroPadd(5e9)

#calculate the transfer function
mdata=Terapy.HMeas(ref_fd,sam_fd)
#crop it
mdata.manipulateFDData(-11e9,[200e9,3.2e12])
#initialize the solver
myana=Terapy.teralyz(mdata,thickness)
#do the calculation
myana.doCalculation(args.calcLength,args.noSVMAF,args.silent)

#do some plots
if args.outname==None:
    args.outname=myana.getFilenameSuggestion()

args.outname+='_'

if args.NoSavePlots == False:
    pylab.ioff()
    reftd.doPlotWithunc()
    samtd.doPlotWithunc()
    pylab.legend(('Reference','Sample'))
    pylab.savefig(args.workpath+args.outname + 'Time-Domain.png')
    pylab.close()
    
    ref_fd.doPlot()
    sam_fd.doPlot()
    pylab.figure('FD-ABS-Plot')
    pylab.legend(('Reference','Sample'))
    pylab.savefig(args.workpath+args.outname + 'ABS-Frequency-Domain.png')
    pylab.close()
    pylab.figure('FD-PHASE-Plot')
    pylab.legend(('Reference','Sample'))
    pylab.savefig(args.workpath+args.outname + 'PHASE-Frequency-Domain.png')
    pylab.close()
    
    mdata.doPlot()
    pylab.savefig(args.workpath+args.outname + 'TransferFunction.png')
    pylab.close()

if args.NoSavePlots == False:
    savefig = 1
else:
    savefig = 0

myana.plotRefractiveIndex(1,savefig,args.workpath+args.outname)
    
myana.saveResults(args.workpath+args.outname)

endtime=time.time()
print "Consumed Time: " + str(endtime-starttime)

if args.showPlots:
    pylab.show()
