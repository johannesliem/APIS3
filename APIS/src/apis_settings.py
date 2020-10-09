# -*- coding: utf-8 -*-
"""
/***************************************************************************
 APISDialog
                                 A QGIS plugin
 APIS - Archaeological Prospection Information System - A QGIS Plugin
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-04-10
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Johannes Liem (digitalcartography.org) and Aerial Archive of the University of Vienna
        email                : johannes.liem@digitalcartography.org
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import sys
from functools import partial

from PyQt5.uic import loadUiType
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QMessageBox

from APIS.src.apis_system_table_editor import APISSystemTableEditor
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ui'))
FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'ui', 'apis_settings.ui'), resource_suffix='')


class APISSettings(QDialog, FORM_CLASS):
    def __init__(self, iface, imageRegistry, parent=None):
        """Constructor."""
        super(APISSettings, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.iface = iface
        self.imageRegistry = imageRegistry
        self.dbm = None
        self.settings = None
        self.setupUi(self)

        s = QSettings()

        # Signals/Slot Connections
        self.rejected.connect(self.onReject)
        self.buttonBox.rejected.connect(self.onReject)
        self.buttonBox.accepted.connect(self.onAccept)

        self.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.onReset)

        self.uiUpdateImageRegistryBtn.clicked.connect(self.updateImageRegistry)

        # Selectors for getFileOpenDialogs
        # paths chosen by user
        self.fileSelectors = {
            "uiConfigIniFile": {
                "button": self.uiConfigIniFileTBtn,
                "infotext": self.tr(u"Wählen Sie eine APIS INI Datei aus ..."),
                "input": self.uiConfigIniFileEdit,
                "path": s.value("APIS/config_ini", ""),
                "filter": self.tr("Config INI (*.ini)")
            }
        }
        for key, item in self.fileSelectors.items():
            input = item['input']
            input.setText(str(item['path']))
            control = item['button']
            slot = partial(self.callOpenFileDialog, key)
            control.clicked.connect(slot)

        self.systemTableEditorDlg = None
        self.sysTables = None
        self.updateSysTablesCombo()
        self.uiEditSystemTableBtn.clicked.connect(lambda: self.openSystemTableEditorDialog(self.uiSystemTableCombo.currentText()))

    def setImageRegistry(self, imageRegistry):
        self.imageRegistry = imageRegistry

    def setDbm(self, dbm):
        self.dbm = dbm

    def setSettings(self, settings):
        self.settings = settings

    def updateImageRegistry(self):
        self.imageRegistry.updateRegistries()

    def updateSysTablesCombo(self):
        if self.settings:
            self.sysTables = self.settings.value("APIS/sys_tables", ['copyright', 'datierung_quelle', 'film_fabrikat', 'fundgewinnung',
                                                                     'fundgewinnung_quelle', 'hersteller', 'kamera', 'projekt'])
            self.uiSystemTableCombo.clear()
            self.uiSystemTableCombo.addItems(self.sysTables)

    def callOpenFileDialog(self, key):
        """
        Ask the user to select a file
        and write down the path to appropriate field
        """
        inPath = QFileDialog.getOpenFileName(
            None,
            caption=self.fileSelectors[key]['infotext'],
            directory=str(self.fileSelectors[key]['input'].text()),  # .encode('utf-8')).strip(' \t'),
            filter=self.fileSelectors[key]['filter']
        )

        if os.path.exists(str(inPath[0])):
            self.fileSelectors[key]['input'].setText(str(inPath[0]))  # str(inPath))

    def openSystemTableEditorDialog(self, table):
        if self.dbm:
            if self.systemTableEditorDlg is None:
                self.systemTableEditorDlg = APISSystemTableEditor(self.dbm, parent=self)

            tableExists = self.systemTableEditorDlg.loadTable(table)
            if tableExists:
                if self.systemTableEditorDlg.exec_():
                    # See if OK was pressed
                    # rec = self.systemTableEditorDlg.getRecord()
                    pass
            else:
                QMessageBox.warning(self, "Tabelle nicht vorhanden", "Die Tabelle {0} ist in der APIS Datenbank nicht vorhanden".format(table))

        else:
            QMessageBox.warning(self, "Warning Database", "Die APIS Datenbank konnte nicht gefunden werden.")

    def onAccept(self):
        '''
        Check DB
        Save options when pressing OK button
        Update Plugin Status
        '''

        # Save Settings
        s = QSettings()
        if len(self.uiConfigIniFileEdit.text()) > 0:
            s.setValue("APIS/config_ini", self.uiConfigIniFileEdit.text())

        self.accept()

    def onReject(self):
        '''
        Run some actions when
        the user closes the dialog
        '''
        self.close()

    def onReset(self):
        '''
        Delte Settings
        '''
        s = QSettings()
        s.remove("APIS/config_ini")
        self.uiConfigIniFileEdit.clear()
