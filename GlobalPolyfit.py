
from __future__ import (absolute_import, division,print_function, unicode_literals)
import dependency_check
from future.builtins import (bytes, dict, int, list, object, range, str, ascii, chr, hex, input, next, oct, open, pow, round, super, filter, map, zip)
import time
tic=time.time()
import os, sys
import numpy as np
from PyQt4.QtCore import * # Qt is Nokias GUI rendering code written in C++.  PyQt4 is a library in python which binds to Qt
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
		self.addScaleHandle([1, 0.5], [0, 0.5])
		self.addScaleHandle([0, 0.5], [1, 0.5])

		## handles scaling vertically from opposite edge
		self.addScaleHandle([0.5, 0], [0.5, 1])
		self.addScaleHandle([0.5, 1], [0.5, 0])

		## handles scaling both vertically and horizontally
		self.addScaleHandle([1, 1], [0, 0])
		self.addScaleHandle([0, 0], [1, 1])

		self.polyPen = QPen(QColor(255, 0, 0))
		self.polyPen.setStyle(Qt.DashLine)
		self.polyPen.setDashOffset(5)
		#g.m.currentTrace.p1.menu.addMenu(self.menu)
		#self.sigRemoved.connect(lambda : g.m.currentTrace.rangeMenu.removeAction(self.menu.menuAction()))

		self.polyPathItem = QGraphicsPathItem()
		self.polyPathItem.setBrush(QColor(0, 100, 155, 100))
		self.polyDataItem = pg.PlotDataItem(pen=self.polyPen)
		self.fall_rise_points = pg.ScatterPlotItem()

		self.polyPathItem.setParentItem(self)
		self.polyDataItem.setParentItem(self)
		self.fall_rise_points.setParentItem(self)
		self.trace = None

	def parentChanged(self):
		if self.trace:
			x, y = self.trace.getData()
			self.setPos(.2 * max(x), max(0, min(y)))
			self.setSize(len(x) // 1.5, max(y))

	def getFrameRect(self):
		origin = self.pos()
		size = self.size()
		return (origin[0], origin[1], origin[0] + size[0], origin[1] + size[1])

	def getFrameTrace(self):
		if not self.trace:
			return None
		t = self.trace.getData()[1]
		x1, y1, x2, y2 = self.getFrameRect()
		x1 = int(x1)
		x1 = max(0, x1)
		x2 = int(x2)
		x2 = min(x2, len(t))
		return (np.arange(0, x2+1 - x1), t[x1:x2 + 1])

	def setTrace(self, t):
		self.trace = t
		print(t)

	def getIntegral(self):
		x1, y1, x2, y2 = self.getFrameRect()
		y = self.getTrace()[x1:x2+1]
		return np.trapz(y)

traceRectROI = RectSelector([0, 0], [10, 10])


def get_polyfit(x, y):
	np.warnings.simplefilter('ignore', np.RankWarning)
	poly=np.poly1d(np.polyfit(x, y, 20))
	ftrace=poly(x)
	return ftrace
	
def analyze_trace(x, y, ftrace):
	x_peak = np.argmax(y)
	f_peak = np.argmax(ftrace)
	data = OrderedDict([('Baseline', (x[0], y[0], x[0], ftrace[0])), ('Peak', (x_peak + x[0], y[x_peak], f_peak + x[0], ftrace[f_peak])),\
		('Delta Peak', (x_peak, y[x_peak]-y[0], f_peak, ftrace[f_peak] - ftrace[0]))])
	yRiseFall = getRiseFall(x, y)
	ftraceRiseFall = getRiseFall(x, ftrace)
	data.update(OrderedDict([(k, yRiseFall[k] + ftraceRiseFall[k]) for k in yRiseFall.keys()]))
	data['area'] = (0, np.trapz(y - x[0]), 0, np.trapz(ftrace - x[0]))
	return data

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
		print("Analysis Failed: %s" % e)
	return data

def makePolyPath(x, ftrace, baseline):
	poly_path = QPainterPath(QPointF(x[0], baseline))
	for pt in zip(x, ftrace):
		poly_path.lineTo(pt[0], pt[1])
	poly_path.lineTo(x[-1], baseline)
	poly_path.closeSubpath()
	return poly_path

def replaceRange(im, region, val):
	x1, x2 = region
	x1 = max(0, x1)
	x2 = min(x2, len(im))
	im[x1:x2 + 1] = val
	return im