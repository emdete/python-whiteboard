# -*- coding: utf-8 -*-

from builtins import str
from builtins import range
from builtins import object
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import PyQt5.Qt as qt


CONFIG_VERSION = 12


class Configuration(object):

	class __impl(object):
		""" Implementation of the singleton interface """
		
		def __init__(self):
			self.settings = QtCore.QSettings("pywhiteboard","pywhiteboard")
			
			self.defaults = {
				"fullscreen": "Yes",
				"selectedmac": '*',
				"zone1": "1",
				"zone2": "2",
				"zone3": "3",
				"zone4": "0",
				"autoconnect": "Yes",
				"autocalibration": "Yes",
				"sensitivity": "6",
				"smoothing": "10",
				"moveonly": "No",
				"automatrix": "No",
				"nowaitdevices": "Yes",
			}
			
			version = self.getValueStr("version")
			if version == '' or int(version) < CONFIG_VERSION:
				self.settings.clear()
				self.saveValue("version",str(CONFIG_VERSION))
			
			self.activeGroup = None
			self.setGroup("default")
			
		
		def wipe(self):
			self.settings.clear()
		
		
		def saveValue(self,name,value):
			self.settings.setValue(name,QtCore.QVariant(value))

		
		def getValueStr(self,name):
			v = self.settings.value(name)
			if v is None:
				v = ''
			v = str(v)
			if v != '': return v
			if v == '' and name in list(self.defaults.keys()):
				return self.defaults[name]
			else: return ''
		
		
		def writeArray(self,name,lst):
			self.settings.beginWriteArray(name)
			for i,dct in enumerate(lst):
				self.settings.setArrayIndex(i)
				for k in list(dct.keys()):
					self.settings.setValue(k,dct[k])
			self.settings.endArray()
		
		
		def readArray(self,name):
			n = self.settings.beginReadArray(name)
			result = []
			for i in range(0,n):
				self.settings.setArrayIndex(i)
				kys = self.settings.childKeys()
				d = dict()
				for k in kys:
					d[str(k)] = str(self.settings.value(k))
				result.append(d)
			self.settings.endArray()
			return result
		
		
		def setGroup(self,name):
			if self.activeGroup:
				self.settings.endGroup()
			pastGroup = self.activeGroup
			self.activeGroup = name
			self.settings.beginGroup(name)
			return pastGroup
		
		
		########### Get and set profile list ########################
		def getProfileList(self):
			activeGroup = self.setGroup("default")
			result = []
			n = self.settings.beginReadArray("profiles")
			for i in range(0,n):
				self.settings.setArrayIndex(i)
				result.append(str(self.settings.value('item').toString()))
			self.settings.endArray()
			self.setGroup(activeGroup)
			return result
		
		
		def setProfileList(self, profileList):
			activeGroup = self.setGroup("default")
			self.settings.beginWriteArray("profiles")
			for i, profileName in enumerate(profileList):
				self.settings.setArrayIndex(i)
				self.settings.setValue('item', profileName)
			self.settings.endArray()
			self.setGroup(activeGroup)
		##############################################################
		

	# storage for the instance reference
	__instance = None

	def __init__(self):
		""" Create singleton instance """
		# Check whether we already have an instance
		if Configuration.__instance is None:
			# Create and remember i10nstance
			Configuration.__instance = Configuration.__impl()

		# Store instance reference as the only member in the handle
		self.__dict__['_Configuration__instance'] = Configuration.__instance

	def __getattr__(self, attr):
		""" Delegate access to implementation """
		return getattr(self.__instance, attr)

	def __setattr__(self, attr, value):
		""" Delegate access to implementation """
		return setattr(self.__instance, attr, value)



class ConfigDialog(QtWidgets.QDialog):

	def __init__(self, parent, wii=None):
		super(ConfigDialog, self).__init__(parent)
		self.ui = uic.loadUi("configuration.ui",self)
		
		self.wii = wii
		
		self.ui.check_fullscreen.stateChanged.connect(self.checkStateChanged)
		self.ui.check_autoconnect.stateChanged.connect(self.checkStateChanged)
		self.ui.check_autocalibration.stateChanged.connect(self.checkStateChanged)
		self.ui.check_automatrix.stateChanged.connect(self.checkStateChanged)
		self.ui.check_nowait.stateChanged.connect(self.checkStateChanged)
		
		self.ui.button_addDev.clicked.connect(self.addDevice)
		self.ui.button_remDev.clicked.connect(self.removeDevice)
		
		pixmap = QtGui.QPixmap("screen.png")
		self.areasScene = QtWidgets.QGraphicsScene()
		self.areasScene.addPixmap(pixmap)
		self.screenAreas.setScene(self.areasScene)
		self.screenAreas.show()
		
		self.ui.combo1.currentIndexChanged.connect(self.changeCombo)
		self.ui.combo2.currentIndexChanged.connect(self.changeCombo)
		self.ui.combo3.currentIndexChanged.connect(self.changeCombo)
		self.ui.combo4.currentIndexChanged.connect(self.changeCombo)
		self.updateCombos()
		
		self.ui.slider_ir.setMinimum(1)
		self.ui.slider_ir.setMaximum(6)
		self.ui.slider_ir.valueChanged.connect(self.sliderIrMoved)
		
		self.ui.slider_smoothing.setMinimum(1)
		self.ui.slider_smoothing.setMaximum(10)
		self.ui.slider_smoothing.valueChanged.connect(self.sliderSmMoved)
		
		self.refreshWidgets()
		self.checkButtons()
	
	
	
	def refreshWidgets(self):
		conf = Configuration()
		self.ui.check_fullscreen.setChecked(conf.getValueStr("fullscreen") == "Yes")
		self.ui.check_autoconnect.setChecked(conf.getValueStr("autoconnect") == "Yes")
		self.ui.check_autocalibration.setChecked(conf.getValueStr("autocalibration") == "Yes")
		self.ui.check_automatrix.setChecked(conf.getValueStr("automatrix") == "Yes")
		self.ui.check_nowait.setChecked(conf.getValueStr("nowaitdevices") == "Yes")
		self.updateCombos()
		self.setupMacTable()
		
		sens = int(conf.getValueStr("sensitivity"))
		self.ui.slider_ir.setValue(sens)
		smth = int(conf.getValueStr("smoothing"))
		self.ui.slider_smoothing.setValue(smth)
		
	
	
	def checkButtons(self):
		if self.wii == None:
			self.ui.button_addDev.setEnabled(False)
		else:
			self.ui.button_addDev.setEnabled(True)
	
	
	
	def setupMacTable(self):
		self.ui.tableMac.setColumnCount(2)
		self.ui.tableMac.setHorizontalHeaderLabels([self.tr('Address'), self.tr('Comment')])
		self.ui.tableMac.setSelectionMode(QtWidgets.QTableWidget.SingleSelection)
		self.ui.tableMac.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
		self.refreshMacTable()
		header = self.ui.tableMac.horizontalHeader()
		header.setStretchLastSection(True)
		self.ui.tableMac.cellClicked.connect(self.macTableCellSelected)
	
	
	def macTableCellSelected(self,r,c):
		address = str(self.ui.tableMac.item(r,0).text())
		conf = Configuration()
		conf.saveValue('selectedmac',address)
	
	
	def refreshMacTable(self):
		while self.ui.tableMac.item(0,0):
			self.ui.tableMac.removeRow(0)
		
		self.ui.tableMac.insertRow(0)
		item = QtWidgets.QTableWidgetItem('*')
		self.ui.tableMac.setItem(0,0,item)
		item = QtWidgets.QTableWidgetItem(self.tr('All devices'))
		self.ui.tableMac.setItem(0,1,item)
		self.ui.tableMac.selectRow(0)
		conf = Configuration()
		lst = conf.readArray('maclist')
		for elem in lst:
			rc = self.ui.tableMac.rowCount()
			self.ui.tableMac.insertRow(rc)
			item = QtWidgets.QTableWidgetItem(elem['address'])
			self.ui.tableMac.setItem(rc,0,item)
			item = QtWidgets.QTableWidgetItem(elem['comment'])
			self.ui.tableMac.setItem(rc,1,item)
			selected = conf.getValueStr('selectedmac')
			if selected == elem['address']:
				self.ui.tableMac.selectRow(rc)
	
	
	
	
	def addDevice(self):
		if self.wii == None: return
		conf = Configuration()
		d = conf.readArray('maclist')
		address = self.wii.addr
		for item in d:
			if item['address'] == address: return
		
		comment, ok = QtWidgets.QInputDialog.getText(self,
			self.tr("Comment"), self.tr('Wii device description'))
		
		if ok:
			d.append( {'address': address, 'comment': comment} )
			conf.writeArray('maclist',d)
			self.refreshMacTable()
	
	
	def removeDevice(self):
		conf = Configuration()
		mlist = conf.readArray('maclist')
		for it in self.ui.tableMac.selectedItems():
			if it.column() == 0:
				address = it.text()
				mlist = [ elem for elem in mlist if elem['address'] != address ]
				conf.writeArray('maclist',mlist)
				self.refreshMacTable()
				conf.saveValue('selectedmac','*')
				return
	
	
	def sliderSmMoved(self,val):
		conf = Configuration()
		conf.saveValue("smoothing",str(val))
		self.ui.label_smoothing.setText(self.tr("Smoothing: ") + str(val))
	
	
	def sliderIrMoved(self, val):
		conf = Configuration()
		conf.saveValue("sensitivity",str(val))
		self.ui.label_sensitivity.setText(self.tr("IR Sensitivity: ") + str(val))
	
		
	def finish(self):
		self.close()
	
	
	def updateCombos(self):
		conf = Configuration()
		for combo,zone in [(self.ui.combo1,"zone1"), (self.ui.combo2,"zone2"), (self.ui.combo3,"zone3"), (self.ui.combo4,"zone4")]:
			ind = int(conf.getValueStr(zone))
			combo.setCurrentIndex(ind)

	def changeCombo(self,i):
		sender = self.sender()
		conf = Configuration()
		if sender == self.ui.combo1:
			conf.saveValue("zone1",str(i))
		elif sender == self.ui.combo2:
			conf.saveValue("zone2",str(i))
		elif sender == self.ui.combo3:
			conf.saveValue("zone3",str(i))
		elif sender == self.ui.combo4:
			conf.saveValue("zone4",str(i))
	
	def checkStateChanged(self,i):
		yesno = 'Yes'
		if i == 0: yesno = 'No'
		sender = self.sender()
		conf = Configuration()
		if sender == self.ui.check_fullscreen:
			conf.saveValue('fullscreen',yesno)
		if sender == self.ui.check_autoconnect:
			conf.saveValue('autoconnect',yesno)
		if sender == self.ui.check_autocalibration:
			conf.saveValue('autocalibration',yesno)
		if sender == self.ui.check_automatrix:
			conf.saveValue('automatrix',yesno)
		if sender == self.ui.check_nowait:
			conf.saveValue('nowaitdevices',yesno)
	
	
	def closeEvent(self,e):
		e.accept()



