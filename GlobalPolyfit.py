
from __future__ import (absolute_import, division,print_function, unicode_literals)
import dependency_check
from future.builtins import (bytes, dict, int, list, object, range, str, ascii, chr, hex, input, next, oct, open, pow, round, super, filter, map, zip)
import time
tic=time.time()
import os, sys
import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtCore import pyqtSignal as Signal
from pyqtgraph import plot, show
import pyqtgraph as pg
import global_vars as g
from collections import OrderedDict

class RectSelector(pg.ROI):
	def __init__(self, origin, size):
		pg.ROI.__init__(self, origin, size)
		self.setPen(QPen(QColor(255, 0, 0)))
		## handles scaling horizontally around center
		self.leftHandle = self.addScaleHandle([1, 0.5], [0, 0.5])
		self.rightHandle = self.addScaleHandle([0, 0.5], [1, 0.5])
		
		## handles scaling vertically from opposite edge
		self.bottomHandle = self.addScaleHandle([0.5, 0], [0.5, 1])
		self.topHandle = self.addScaleHandle([0.5, 1], [0.5, 0])

		self.addPolyfill()

		## handles scaling both vertically and horizontally
		#self.addScaleHandle([1, 1], [0, 0])
		#self.addScaleHandle([0, 0], [1, 1])
		self.sigRegionChanged.connect(self.onTranslate)
		self.buildHandlePaths()

		self.traceLine = None

	def setVisible(self, v):
		pg.ROI.setVisible(self, v)
		if g.m.currentTrace:
			self.traceLine = g.m.currentTrace.rois[0]['p1trace']
			x, y = self.traceLine.getData()
			self.setPos([100, min(y)])
			self.setSize([max(x) - 100, max(y)])

	def onTranslate(self):
		t = self.getFrameTrace()
		if not t:
			return
		baseline = self.pos()[1]
		x, y = t
		ftrace = get_polyfit(x, y - baseline)
		data = self.analyze_trace()
		self.polyDataItem.setData(x=x, y=ftrace, pen=self.polyPen)

		pos = [data[k] for k in data.keys() if k.startswith('Rise, Fall')]
		if len(pos) > 0:
			self.fall_rise_points.setData(pos=pos, pen=self.polyPen, symbolSize=4)
		else:
			self.fall_rise_points.clear()

		path = QPainterPath()
		path.moveTo(0, 0)
		i = 0
		for i in range(len(ftrace)):
			path.lineTo(i, ftrace[i])
		path.lineTo(i, 0)
		path.lineTo(0, 0)
		self.polyPathItem.setPath(path)
		self.buildHandlePaths()

	def addPolyfill(self):
		self.polyPen = QPen(QColor(255, 0, 0))
		self.polyPen.setStyle(Qt.DashLine)
		self.polyPen.setDashOffset(5)

		self.polyPathItem = QGraphicsPathItem()
		self.polyPathItem.setBrush(QColor(0, 100, 155, 100))
		self.polyDataItem = pg.PlotDataItem(pen=self.polyPen)
		self.fall_rise_points = pg.ScatterPlotItem()

		self.polyPathItem.setParentItem(self)
		self.polyDataItem.setParentItem(self)
		self.fall_rise_points.setParentItem(self)

	def buildHandlePaths(self):
		w, h = self.size()
		self.leftHandle.path = QPainterPath()
		self.leftHandle.path.moveTo(0, -h/4)
		self.leftHandle.path.lineTo(10, 0)
		self.leftHandle.path.lineTo(0, h/4)
		self.leftHandle.path.lineTo(0, -h/4)
		self.leftHandle._shape = self.leftHandle.path

		self.rightHandle.path = QPainterPath()
		self.rightHandle.path.moveTo(0, -h/4)
		self.rightHandle.path.lineTo(-10, 0)
		self.rightHandle.path.lineTo(0, h/4)
		self.rightHandle.path.lineTo(0, -h/4)
		self.rightHandle._shape = self.rightHandle.path

		self.bottomHandle.path = QPainterPath()
		self.bottomHandle.path.moveTo(-w/4, 0)
		self.bottomHandle.path.lineTo(0, -h / 15)
		self.bottomHandle.path.lineTo(w/4, 0)
		self.bottomHandle.path.lineTo(-w/4, 0)
		self.bottomHandle._shape = self.bottomHandle.path

		self.topHandle.path = QPainterPath()
		self.topHandle.path.moveTo(-w/4, 0)
		self.topHandle.path.lineTo(0, h / 15)
		self.topHandle.path.lineTo(w/4, 0)
		self.topHandle.path.lineTo(-w/4, 0)
		self.topHandle._shape = self.topHandle.path

	def getFrameRect(self):
		origin = self.pos()
		size = self.size()
		return (origin[0], origin[1], origin[0] + size[0], origin[1] + size[1])

	def getFrameTrace(self):
		if not self.traceLine:
			return None
		t = self.traceLine.getData()[1]
		x1, y1, x2, y2 = self.getFrameRect()
		x1 = int(x1)
		x1 = max(0, x1)
		x2 = int(x2)
		x2 = min(x2, len(t))
		t = t[x1:x2 + 1]
		t[t < y1] = y1
		return (np.arange(0, x2+1 - x1), t[:])

	def setTrace(self, t):
		self.traceLine = t

	def getIntegral(self):
		x1, y1, x2, y2 = self.getFrameRect()
		y = self.getTrace()[x1:x2+1]
		return np.trapz(y)

	def analyze_trace(self):
		pos = self.pos()
		size = self.size()
		x, y = self.getFrameTrace()
		ftrace = get_polyfit(x, y)
		x_peak = np.argmax(y)
		f_peak = np.argmax(ftrace)
		data = OrderedDict([('Baseline', (pos[0], pos[1], pos[0], pos[1])), \
							('Peak', (x_peak + pos[0], y[x_peak], f_peak + pos[0], ftrace[f_peak])),\
							('Delta Peak', (x_peak, y[x_peak]-pos[1], f_peak, ftrace[f_peak] - pos[1]))])
		yRiseFall = getRiseFall(x, y)
		ftraceRiseFall = getRiseFall(x, ftrace)
		data.update(OrderedDict([(k, yRiseFall[k] + ftraceRiseFall[k]) for k in yRiseFall.keys()]))
		data['area'] = (0, np.trapz(y), 0, np.trapz(ftrace))
		return data

traceRectROI = RectSelector([0, 0], [10, 10])
traceRectROI.setVisible(False)

def get_polyfit(x, y):
	np.warnings.simplefilter('ignore', np.RankWarning)
	poly=np.poly1d(np.polyfit(x, y, 20))
	ftrace=poly(x)
	return ftrace
	
def getRiseFall(x, y):
	x_peak = np.where(y == max(y))[0][0]
	baseline = (x[0], y[0])
	dPeak = (x_peak, y[x_peak]-y[0])
	data = OrderedDict([('Rise 20%', [-1, -1]),
		('Rise 50%', [-1, -1]), ('Rise 80%', [-1, -1]),
		('Rise 100%', [-1, -1]), ('Fall 80%', [-1, -1]),
		('Fall 50%', [-1, -1]), ('Fall 20%', [-1, -1])])
	try:
		thresh20=dPeak[1]*.2 + baseline[1]
		thresh50=dPeak[1]*.5 + baseline[1]
		thresh80=dPeak[1]*.8 + baseline[1]

		data['Rise 20%'] = [np.argwhere(y>thresh20)[0][0], thresh20]
		data['Rise 50%'] = [np.argwhere(y>thresh50)[0][0], thresh50]
		data['Rise 80%'] = [np.argwhere(y>thresh80)[0][0], thresh80]
		data['Rise 100%'] = [np.argmax(y), max(y)]

		tmp=np.squeeze(np.argwhere(y<thresh80))
		data['Fall 80%'] = [tmp[tmp>data['Rise 100%'][0]][0], thresh80]
		tmp=np.squeeze(np.argwhere(y<thresh50))
		data['Fall 50%'] = [tmp[tmp>data['Fall 80%'][0]][0], thresh50]
		tmp=np.squeeze(np.argwhere(y<thresh20))
		data['Fall 20%'] = [tmp[tmp>data['Fall 50%'][0]][0], thresh20]
	except Exception as e:
		pass
		#print("Analysis Failed: %s" % e)
	return data

