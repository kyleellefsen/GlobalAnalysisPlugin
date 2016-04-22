from PyQt4 import uic
import global_vars as g
import pyqtgraph as pg
from plugins.GlobalAnalysis.GlobalPolyfit import *
from window import Window
from roi import ROI
from process.measure import measure
from process.file_ import save_file_gui
from trace import TraceFig

analysisUI = None
log_data = ''

def gui():
	global analysisUI, log_data
	if analysisUI == None:
		analysisUI = uic.loadUi(os.path.join(os.getcwd(), 'plugins\\GlobalAnalysis\\main.ui'))
		analysisUI.traceROICheck.toggled.connect(toggleVisible)
		traceRectROI.sigRegionChanged.connect(fillDataTable)
		traceRectROI.mouseClickEvent = clickEvent
		analysisUI.measureButton.clicked.connect(measure.gui)
		analysisUI.closeEvent = closeEvent
		analysisUI.tableWidget.setFormat("%.3f")
		analysisUI.traceComboBox.mousePressEvent = comboBoxClicked
		analysisUI.logButton.clicked.connect(logData)
		analysisUI.saveButton.clicked.connect(lambda : save_file_gui(saveLoggedData, prompt="Save Logged Ploynomial Fit Data", filetypes="*.txt"))
		g.m.dialogs.append(analysisUI)
		analysisUI.traceComboBox.updating = False
		analysisUI.all_rois = []
		analysisUI.traceComboBox.currentIndexChanged.connect(indexChanged)
	log_data = ''
	analysisUI.show()

class PseudoClick():
	def __init__(self, pos):
		self._pos = pos
	def pos(self):
		return self._pos

def clickEvent(ev):
	pos = ev.pos()
	pos = traceRectROI.mapToView(pos)
	measure.pointclicked(PseudoClick(pos), overwrite=True)

def saveLoggedData(fname):
	global log_data
	with open(fname, 'w') as outf:
		outf.write("Value\tFtrace Frame\tFtrace Y\n")
		outf.write(log_data)
	log_data = ''

def logData():
	global log_data
	for name, vals in traceRectROI.data.items():
		log_data += "%s\t%s\n" % (name, '\t'.join([str(i) for i in vals]))
	log_data += "\n"

def indexChanged(i=0):
	if analysisUI.traceComboBox.updating or i == -1 or i >= len(analysisUI.all_rois):
		return
	traceRectROI.setTrace(analysisUI.all_rois[i]['p1trace'])
	fillDataTable()

def closeEvent(ev):
	try:
		traceRectROI.scene().removeItem(traceRectROI)
	except:
		pass
	ev.accept()

def toggleVisible(v):
	buildComboBox()
	traceRectROI.setVisible(v)
	indexChanged()
	if not v:
		analysisUI.tableWidget.clear()
	else:
		fillDataTable()

def buildComboBox():
	analysisUI.traceComboBox.updating = True
	analysisUI.traceComboBox.clear()
	analysisUI.all_rois = []
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
	analysisUI.tableWidget.setHorizontalHeaderLabels(['Ftrace Frames', 'Ftrace Y'])
	