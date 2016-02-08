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
		QApplication.instance().focusChanged.connect(focusChange)
		analysisUI.measureButton.clicked.connect(measure.gui)
		analysisUI.closeEvent = closeEvent
		g.m.dialogs.append(analysisUI)
	analysisUI.show()

def closeEvent(ev):
	if g.m.currentTrace != None:
		g.m.currentTrace.p1.removeItem(traceRectROI)
	#traceRectROI.parentItem().removeItem(traceRectROI)
	ev.accept()

def toggleVisible(v):
	traceRectROI.setVisible(v)
	if g.m.currentTrace != None:
		g.m.currentTrace.p1.addItem(traceRectROI)
	buildComboBox()

def buildComboBox():
	analysisUI.traceComboBox.clear()
	if not g.m.currentTrace or len(g.m.currentTrace.rois) == 0:
		analysisUI.traceComboBox.addItem("No Trace Selected")
		return
	model = analysisUI.traceComboBox.model()
	traceRectROI.traces = [None]
	for i, roiLine in enumerate(g.m.currentTrace.rois):
		traceRectROI.traces.append(roiLine['p1trace'])
		item = QStandardItem("ROI #%d" % (i + 1))
		item.setBackground(roiLine['roi'].color)
		model.appendRow(item)
		if roiLine['p1trace'] == traceRectROI.traces[i]:
			traceComboBox.setSelectedItem(i)
	analysisUI.traceComboBox.currentIndexChanged.connect(lambda v: traceRectROI.setTrace(traceRectROI.traces[v]))

def focusChange(old, new):
	if new != None and isinstance(new.window(), TraceFig) and new != g.m.currentTrace:
		if old != None and isinstance(old, TraceFig):
			old.window().p1.removeItem(traceRectROI)
		if traceRectROI not in new.window().p1.getPlotItem().listDataItems():
			new.window().p1.addItem(traceRectROI)

def fillDataTable():
	''' when the region moves, recalculate the polyfit
	data and plot/show it in the table and graph accordingly'''
	t = traceRectROI.getFrameTrace()
	if not t:
		return
	x, y = t
	ftrace = get_polyfit(x, y)
	data = traceRectROI.analyze_trace()
	analysisUI.tableWidget.setData(data)
	analysisUI.tableWidget.setHorizontalHeaderLabels(['Frames', 'Y', 'Ftrace Frames', 'Ftrace Y'])
	