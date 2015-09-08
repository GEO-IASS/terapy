import sys
#for dynamic loading of the GUI

from PyQt4 import QtGui, uic, QtCore
import numpy as np
import matplotlib.pyplot as plt
import TeraData
from uncertainties import unumpy
from os import path


from thzTreeWidgetItem import THzTreeWidgetItem
from formatdialog import FormatDialog
from selectplotstochange import PlotsToChange
from ui_mainwindow import Ui_TeraView
#for matplotlib widget


class MyWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()        
        
        self.ui=Ui_TeraView()
        self.ui.setupUi(self)
        self.initializeSpectrumCanvas()
        
        self.ui.actionClose.triggered.connect(QtGui.qApp.quit)
        self.ui.actionLoad.triggered.connect(self.loadFile)

        self.ui.actionPlot_Dynamic_Range.triggered.connect(self.plotDR)
        self.ui.actionPlot_SNR.triggered.connect(self.plotSNR)
        self.ui.actionPlot_uncertainty_intervals.triggered.connect(self.plotuncertainty)
        
        self.ui.fileTree.itemChanged.connect(self.updateSpectrumAnalysisPlot)
        self.ui.fileTree.itemDoubleClicked.connect(self.onTreeWidgetItemDoubleClicked)
        self.ui.pb_tdoperations.clicked.connect(self.applytdchanges)
        
        self.show()
    
    def initializeSpectrumCanvas(self):
        
        self.ui.spectrumCanvas.axes.append(self.ui.spectrumCanvas.figure.add_subplot(2,1,1))
        self.ui.spectrumCanvas.axes.append(self.ui.spectrumCanvas.figure.add_subplot(2,1,2))
        ax=self.ui.spectrumCanvas.axes
        
        ax[0].set_xlabel('time in ps')
        ax[0].set_ylabel('Amplitude')        
        
        ax[1].set_xlabel('frequency in THz')
        ax[1].set_ylabel('Amplitude, dB Scale')        
        ax[1].set_xlim([0,10])
        ax[1].set_ylim([-90,0])


        
    def plotSNR(self):
        self.plotspecial('SNR')        

    def plotDR(self):
        self.plotspecial('Dynamic Range')
    
    def plotuncertainty(self):
        self.plotspecial('uncertainty')

    def plotspecial(self,what):
        curvelist=[]
        for i in range(2,self.ui.cb_whichplots.count()):
            curvelist.append(self.ui.cb_whichplots.itemText(i))

        myplotdialog=PlotsToChange(curvelist,"Select Data for which you want the " + what + " plotted: ")
        if myplotdialog.exec_()==QtGui.QDialog.Rejected:
            return

        where=myplotdialog.getPlotsToChange()
        
        #first try to add just to the first entry a new child        
        if where>1:
            for i in range(self.ui.fileTree.topLevelItem(where-2).childCount()):
                
                if self.ui.fileTree.topLevelItem(where-2).child(i).text(1).split(" ")[-1]==what:
                    return 0
            self.addSubplot(self.ui.fileTree.topLevelItem(where-2),what)
        else:
            for row in range(self.ui.fileTree.topLevelItemCount()):
                if where==1 or self.ui.fileTree.topLevelItem(row).checkState(0):
                    found=False
                    for i in range(self.ui.fileTree.topLevelItem(row).childCount()):
                        if self.ui.fileTree.topLevelItem(row).child(i).text(1).split(" ")[-1]==what:
                            found=True
                            break
                    if not found:
                        self.addSubplot(self.ui.fileTree.topLevelItem(row),what)

    def addSubplot(self,tlw,what):
        x=THzTreeWidgetItem()
        
        x.setCheckState(0,QtCore.Qt.Checked)
        leg_label=tlw.tdline[0].get_label()+" " + what
        x.setText(1,leg_label)
            
        if what=='SNR':
            x.tdline=self.ui.spectrumCanvas.figure.axes[0].plot(tlw.tdData.getTimesPs(),tlw.tdData.getSNR(),label=leg_label)
            x.fdline=self.ui.spectrumCanvas.figure.axes[1].plot(tlw.fdData.getfreqsGHz()/1e3,20*np.log10(tlw.fdData.getSNR()),label=leg_label)
            x.setCheckState(0,QtCore.Qt.Checked)
     
            x.setText(2,'test')
            x.setText(3,'test')
        if what=='uncertainty':
            
            #plot absolute and phase along with uncertainties
            f=1
            uabs=unumpy.uarray(tlw.fdData.getFAbs(),tlw.fdData.getFAbsUnc())
            #scale the uncertainty for the 20*log10 plot
            uabs=20*unumpy.log10(uabs)
            uabs-=np.amax(uabs)
            u_a=unumpy.nominal_values(uabs)
            u_s=unumpy.std_devs(uabs)
            
            x.tdline=self.ui.spectrumCanvas.figure.axes[0].plot(tlw.tdData.getTimesPs(),tlw.tdData.getEX()+tlw.tdData.getUncEX(),'k--',
                    tlw.tdData.getTimesPs(),tlw.tdData.getEX()-tlw.tdData.getUncEX(),'k--',label=leg_label)
            x.fdline=self.ui.spectrumCanvas.figure.axes[1].plot(tlw.fdData.getfreqsGHz()[1:]/1e3,u_a[1:]+u_s[1:],'k--',
                    tlw.fdData.getfreqsGHz()[1:]/1e3,u_a[1:]-u_s[1:],'k--',label=leg_label)
     

            x.setText(2,'test')
            x.setText(3,'test')
        if what=='Dynamic Range':             
            
            x.tdline=self.ui.spectrumCanvas.figure.axes[0].plot(tlw.tdData.getTimesPs(),tlw.tdData.getDR(),label=leg_label)
            x.fdline=self.ui.spectrumCanvas.figure.axes[1].plot(tlw.fdData.getfreqsGHz()/1e3,tlw.fdData.getDR(),label=leg_label)
            x.setText(2,'test')
            x.setText(3,'test')
        
        tlw.addChild(x)
        self.ui.spectrumCanvas.axes[0].legend()
        self.ui.spectrumCanvas.axes[1].legend()
        self.ui.spectrumCanvas.draw()
    
    def applytdchanges(self):
        no_datasets=self.ui.fileTree.topLevelItemCount()
        #it=QtGui.QTreeWidgetItemIterator(self.ui.fileTree,QtGui.QTreeWidgetItemIterator.All)
       
        if self.ui.cb_whichplots.currentIndex()==0:
            for row in range(no_datasets):
                if self.ui.fileTree.topLevelItem(row).checkState(0):
                    self.zeroPadding(self.ui.fileTree.topLevelItem(row))
        elif self.ui.cb_whichplots.currentIndex()==1:
             for row in range(no_datasets):
                 self.zeroPadding(self.ui.fileTree.topLevelItem(row))
        else: 
            self.zeroPadding(self.ui.fileTree.topLevelItem(self.ui.cb_whichplots.currentIndex()-2))                 
        
    def windowing(self,data):
        if self.ui.cb_windowing.currentIndex()>0:
            start_window=self.ui.dsb_zeropaddfrom.value()
            end_window=self.ui.dsb_zeropaddfrom.value()
            
            
    def zeroPadding(self,dataset): 
              
        if self.ui.cb_zeropadding.isChecked():
            no_zeros=self.ui.sb_nozeros.value()
            dataset.tdData.zeroPaddData(no_zeros)
#            dataset.tdline[0].remove()
            dataset.fdData=TeraData.FdData(dataset.tdData)
            self.updateDetails(dataset)
            self.doTdFdPlot(dataset)
            print("zeropadding applied")
            
    def loadFile(self):
        filenames=QtGui.QFileDialog.getOpenFileNames()
        if len(filenames)==0:
            return 
            
        myformatdialog=FormatDialog()
        
        myformatdialog.setFilenames(filenames)
        self.ui.mainStatus.showMessage("Load Files")
        if myformatdialog.exec_()==QtGui.QDialog.Rejected:
            return
        fileformat=myformatdialog.getDataFormat()
        if myformatdialog.doAveraging():
            display_filename=path.split(str(filenames[0]))[1]
            for i in range(1,len(filenames)):
                display_filename+=" \n" + path.split(str(filenames[i]))[1]
            x=self.fillTree(display_filename,filenames,fileformat) 
        else:          
            for fn in filenames:
                x=self.fillTree(path.split(str(fn))[1],[fn],fileformat)
        self.ui.mainStatus.clearMessage()
        
        return filenames
        
    def fillTree(self,display_filename,filenames,fileformat):
            
        x=THzTreeWidgetItem()
       
        x.setFlags(x.flags() | QtCore.Qt.ItemIsEditable)
        x.tdData=TeraData.THzTdData(map(str,filenames),fileformat)
        x.fdData=TeraData.FdData(x.tdData)
        
        x.setCheckState(0,QtCore.Qt.Checked)
        x.setText(1,display_filename)
        self.updateDetails(x)        
        self.doTdFdPlot(x)
        self.ui.fileTree.addTopLevelItem(x)
        self.ui.cb_whichplots.addItem(display_filename)
        
        return x
        
    
    def updateSpectrumAnalysisPlot(self,item,column):
        #something else happened so return
        if column>1:
            return
            
        #the name of the plot changed, so change legend entry!
        if column==1:
            
            item.tdline[0].set_label(item.text(1))
            for i in range(item.childCount()):
                oldlabel=item.child(i).text(1)
                item.child(i).tdline[0].set_label(item.text(1) +" " +oldlabel.split(" ")[-1])
                item.child(i).setText(1,item.text(1) +" " +oldlabel.split(" ")[-1])
            
            item.fdline[0].set_label(item.text(1))
            for i in range(item.childCount()):
                oldlabel=item.child(i).text(1)
                item.child(i).fdline[0].set_label(item.text(1) + " " + oldlabel.split(" ")[-1])
                item.child(i).setText(1,item.text(1) +" " +oldlabel.split(" ")[-1])
                
        #the plots status changed
        if column ==0:
            if item.checkState(0):
                for line in item.tdline:
#                    self.ui.spectrumCanvas.axes[0].add_line(line)
                    line.set_label(item.text(1))
                    line.set_visible(True)
                for line in item.fdline:
#                    self.ui.spectrumCanvas.axes[1].add_line(line)
                    line.set_label(item.text(1))
                    line.set_visible(True)
            else:
                for line in item.tdline:
#                    line.remove()
                    line.set_label(None)
                    line.set_visible(False)
                for line in item.fdline:
#                    line.remove()
                    line.set_label(None)
                    line.set_visible(False)
                    
        self.ui.spectrumCanvas.axes[0].legend()
        self.ui.spectrumCanvas.axes[1].legend()
        self.ui.spectrumCanvas.draw()
        
    def updateDetails(self,thztreeitem):
        d=thztreeitem.fdData.getBandwidth()
        thztreeitem.setText(2,'dt='+'{:3.2f}'.format(thztreeitem.tdData.dt*1e15) + 'fs' +'\n'
                                'Pulsewidth=' + '{:3.2f}'.format(thztreeitem.tdData.getPeakWidth()*1e12) + 'ps')
        thztreeitem.setToolTip(2,'Pulse Position: ' + '{:3.3f}'.format(thztreeitem.tdData.getPeakPosition()*1e12) + ' ps\n'+ 
                                'DataLength=' + '{:d}'.format(thztreeitem.tdData.getLength()) + 'Points\n' +
                                'TimeWindowLength=' + '{:3.2f}'.format((thztreeitem.tdData.getTimes()[-1]-thztreeitem.tdData.getTimes()[0])*1e12)+'Ps')
        
        thztreeitem.setText(3,'df=' +'{:3.2f}'.format(thztreeitem.fdData.getfbins()/1e9) + 'GHz' +'\n'
                                'Bandwidth='+'{:3.1f}'.format((d[1]-d[0])/1e12) + 'THz')

    
    def doTdFdPlot(self,thztreeitem):
        #in case no color yet defined
        if thztreeitem.color==None:
            thztreeitem.color=plt.cm.hsv(np.random.rand(1)[0])

        #in case of update, remove existing lines from plot, 
        for line in thztreeitem.tdline:
            line.set_xdata(thztreeitem.tdData.getTimesPs())
            line.set_ydata(thztreeitem.tdData.getEX())
            
        for line in thztreeitem.fdline:
            absdata=20*np.log10(thztreeitem.fdData.getFAbs())
            line.set_xdata(thztreeitem.fdData.getfreqsGHz()/1e3)
            line.set_ydata(absdata-np.amax(absdata))
            
        if len(thztreeitem.tdline)==0:
            thztreeitem.tdline=self.ui.spectrumCanvas.figure.axes[0].plot(thztreeitem.tdData.getTimesPs(),thztreeitem.tdData.getEX(),color=thztreeitem.color,label=thztreeitem.text(1))
            absdata=20*np.log10(thztreeitem.fdData.getFAbs())
            absdata-=np.amax(absdata)
            thztreeitem.fdline=self.ui.spectrumCanvas.figure.axes[1].plot(thztreeitem.fdData.getfreqsGHz()/1e3,absdata,color=thztreeitem.color,label=thztreeitem.text(1))
        
        self.ui.spectrumCanvas.axes[0].legend()
        self.ui.spectrumCanvas.axes[1].legend()
        self.ui.spectrumCanvas.draw()        

    def onTreeWidgetItemDoubleClicked(self,item,column): 
        if column==1:
            self.ui.fileTree.editItem(item,column)
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec_())