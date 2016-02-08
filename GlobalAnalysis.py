from PyQt4 import uic
import global_vars as g
import pyqtgraph as pg
from plugins.GlobalAnalysis.GlobalPolyfit import *
from window import Window
from roi import ROI
from process.measure import measure
from trace import TraceFig

analysisUI = None

def gui():
	global analysisUI
	if analysisUI == None:
		analysisUI = uic.loadUi(os.path.join(os.getcwd(), 'plugins\\GlobalAnalysis\\main.ui'))
		analysisUI.traceROICheck.toggled.connect(toggleVisible)
		traceRectROI.sigRegionChanged.connect(fillDataTable)
		analysisUI.measureButton.clicked.connect(measure.gui)
		analysisUI.closeEvent = closeEvent
		analysisUI.tableWidget.setFormat("%.3f")
		analysisUI.traceComboBox.mousePressEvent = comboBoxClicked
		g.m.dialogs.append(analysisUI)
		analysisUI.traceComboBox.currentIndexChanged.connect(indexChanged)
	analysisUI.show()



def indexChanged(i):
	if analysisUI.traceComboBox.updating or i == -1 or i >= len(analysisUI.all_rois):
		return
	traceRectROI.setTrace(analysisUI.all_rois[i]['p1trace'])

def closeEvent(ev):
	if g.m.currentTrace != None:
		g.m.currentTrace.p1.removeItem(traceRectROI)
	ev.accept()

def toggleVisible(v):
	traceRectROI.setVisible(v)
	if not v:
		analysisUI.tableWidget.clear()
	else:
		fillDataTable()

def buildComboBox():
	analysisUI.traceComboBox.updating = True
	analysisUI.traceComboBox.clear()
	analysisUI.traceWindows = []
	for traceWindow in g.m.traceWindows:
		analysisUI.all_rois.extend(traceWindow.rois)
	if len(analysisUI.all_rois) == 0:
		analysisUI.traceComboBox.addItem("No Trace Selected")
	else:
		model = analysisUI.traceComboBox.model()
		for i, roiLine in enumerate(analysisUI.all_rois):
			item = QStandardItem("ROI #%d" % (i + 1))
			item.setBackground(roiLine['roi'].color)
			model.appendRow(item)
			if roiLine['p1trace'] == traceRectROI.traceLine:
				analysisUI.traceComboBox.setCurrentIndex(i)
	analysisUI.traceComboBox.updating = False

def comboBoxClicked(ev):
	buildComboBox()
	QComboBox.mousePressEvent(analysisUI.traceComboBox, ev)

def fillDataTable():
	''' when the region moves, recalculate the polyfit
	data and plot/show it in the table and graph accordingly'''
	if not traceRectROI.traceLine:
		return
	analysisUI.tableWidget.setData(traceRectROI.data)
	analysisUI.tableWidget.setHorizontalHeaderLabels(['Frames', 'Y', 'Ftrace Frames', 'Ftrace Y'])
	