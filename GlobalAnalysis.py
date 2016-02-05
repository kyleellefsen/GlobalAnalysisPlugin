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
	analysisUI = uic.loadUi(os.path.join(os.getcwd(), 'plugins\\GlobalAnalysis\\main.ui'))
	analysisUI.traceROICheck.toggled.connect(toggleVisible)
	traceRectROI.sigRegionChanged.connect(roiTranslated)
	QApplication.instance().focusChanged.connect(focusChange)
	analysisUI.measureButton.clicked.connect(measure.gui)
	analysisUI.closeEvent = closeEvent
	analysisUI.show()
	g.m.dialogs.append(analysisUI)

def closeEvent(ev):
	if g.m.currentTrace != None:
		g.m.currentTrace.p1.removeItem(traceRectROI)
	ev.accept()

def toggleVisible(v):
	traceRectROI.setVisible(v)
	if g.m.currentTrace != None:
		g.m.currentTrace.p1.addItem(traceRectROI)

def buildComboBox():
	if not g.m.currentTrace:
		return
	analysisUI.traceComboBox.clear()
	analysisUI.traceComboBox.addItem("No Trace Selected")
	model = analysisUI.traceComboBox.model()
	traceRectROI.traces = [None]
	for i, roiLine in enumerate(g.m.currentTrace.rois):
		traceRectROI.traces.append(roiLine['p1trace'])
		item = QStandardItem("ROI #%d" % (i + 1))
		item.setBackground(roiLine['roi'].color)
		model.appendRow(item)
		
	analysisUI.traceComboBox.currentIndexChanged.connect(lambda v: traceRectROI.setTrace(traceRectROI.traces[v]))

def focusChange(old, new):
	if new != None and isinstance(new.window(), TraceFig):
		if old != None and isinstance(old, TraceFig):
			old.window().p1.removeItem(traceRectROI)
		if traceRectROI not in new.window().p1.getPlotItem().listDataItems():
			new.window().p1.addItem(traceRectROI)
		if new != g.m.currentTrace:
			buildComboBox()

def roiTranslated():
	''' when the region moves, recalculate the polyfit
	data and plot/show it in the table and graph accordingly'''

	t = traceRectROI.getFrameTrace()
	if not t:
		return
	x, y = t
	ftrace = get_polyfit(x, y)
	data = analyze_trace(x, y, ftrace)
	traceRectROI.polyDataItem.setData(x=x, y=ftrace, pen=traceRectROI.polyPen)

	pos = [data[k] for k in data.keys() if k.startswith('Rise, Fall')]
	if len(pos) > 0:
		traceRectROI.fall_rise_points.setData(pos=pos, pen=traceRectROI.polyPen, symbolSize=4)
	else:
		print("Cannot find points")
		traceRectROI.fall_rise_points.clear()
	traceRectROI.polyPathItem.setPath(makePolyPath(x, ftrace, data['Baseline'][1]))
	analysisUI.tableWidget.setData(data)
	analysisUI.tableWidget.setHorizontalHeaderLabels(['Frames', 'Y', 'Ftrace Frames', 'Ftrace Y'])