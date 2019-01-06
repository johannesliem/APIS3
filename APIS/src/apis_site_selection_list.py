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

from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import QDialog, QMessageBox, QAbstractItemView, QHeaderView, QPushButton, QFileDialog, QMenu, QAction
from PyQt5.QtCore import QSettings, Qt, QDateTime, QFile, QDir
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon

from qgis.core import QgsDataSourceUri, QgsProject, QgsVectorLayer, QgsVectorFileWriter, QgsFeature

from APIS.src.apis_site import APISSite
from APIS.src.apis_utils import SiteHasFindspot, SitesHaveFindspots, GetFindspotNumbers, OpenFileOrFolder, GetFindspotNumbers
from APIS.src.apis_printer import APISPrinterQueue, APISListPrinter, APISTemplatePrinter, OutputMode
from APIS.src.apis_printing_options import APISPrintingOptions

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'ui', 'apis_site_selection_list.ui'), resource_suffix='')


class APISSiteSelectionList(QDialog, FORM_CLASS):
    def __init__(self, iface, dbm, imageRegistry, apisLayer, parent=None):
        """Constructor."""
        super(APISSiteSelectionList, self).__init__(parent)

        self.iface = iface
        self.dbm = dbm
        self.imageRegistry = imageRegistry
        self.apisLayer = apisLayer

        self.settings = QSettings(QSettings().value("APIS/config_ini"), QSettings.IniFormat)

        self.setupUi(self)

        self.query = None

        self.uiSiteListTableV.doubleClicked.connect(self.openSiteDialog)

        self.uiResetSelectionBtn.clicked.connect(self.uiSiteListTableV.clearSelection)

        mLayer = QMenu()
        mLayer.addSection("In QGIS laden")
        aLayerLoadSite = mLayer.addAction(QIcon(os.path.join(QSettings().value("APIS/plugin_dir"), 'ui', 'icons', 'layer.png')), "Fundort(e)")
        aLayerLoadSite.triggered.connect(self.loadSiteInQgis)
        aLayerLoadInterpretation = mLayer.addAction(QIcon(os.path.join(QSettings().value("APIS/plugin_dir"), 'ui', 'icons', 'layer.png')), "Interpretation(en)")
        aLayerLoadInterpretation.triggered.connect(self.loadSiteInterpretationInQgis)
        mLayer.addSection("SHP Export")
        aLayerExportSite = mLayer.addAction(QIcon(os.path.join(QSettings().value("APIS/plugin_dir"), 'ui', 'icons', 'shp_export.png')), "Fundort(e)")
        aLayerExportSite.triggered.connect(self.exportSiteAsShp)
        self.uiLayerTBtn.setMenu(mLayer)
        self.uiLayerTBtn.clicked.connect(self.uiLayerTBtn.showMenu)

        mPdfExport = QMenu()
        aPdfExportSiteList = mPdfExport.addAction(QIcon(os.path.join(QSettings().value("APIS/plugin_dir"), 'ui', 'icons', 'pdf_export.png')), "Fundortliste")
        aPdfExportSiteList.triggered.connect(lambda: self.exportAsPdf(tab_list=True))
        aPdfExportSite = mPdfExport.addAction(QIcon(os.path.join(QSettings().value("APIS/plugin_dir"), 'ui', 'icons', 'pdf_export.png')), "Fundort")
        aPdfExportSite.triggered.connect(lambda: self.exportAsPdf(detail=True))
        aPdfExportSiteFindspotList = mPdfExport.addAction(QIcon(os.path.join(QSettings().value("APIS/plugin_dir"), 'ui', 'icons', 'pdf_export.png')), "Fundort und Funstellenliste")
        aPdfExportSiteFindspotList.triggered.connect(lambda: self.exportAsPdf(detail=True, subList=True))
        aPdfExportSiteFindspotListFindspot = mPdfExport.addAction(QIcon(os.path.join(QSettings().value("APIS/plugin_dir"), 'ui', 'icons', 'pdf_export.png')), "Fundort, Funstellenliste und Fundstellen")
        aPdfExportSiteFindspotListFindspot.triggered.connect(lambda: self.exportAsPdf(detail=True, subList=True, subDetail=True))
        self.uiPdfExportTBtn.setMenu(mPdfExport)
        self.uiPdfExportTBtn.clicked.connect(self.uiPdfExportTBtn.showMenu)

        self.siteDlg = None
        self.printingOptionsDlg = None

    def hideEvent(self,event):
        self.query = None

    def loadSiteListBySpatialQuery(self, query=None, info=None, update=False):
        if self.query is None:
            self.query = query

        self.model = self.dbm.queryToQStandardItemModel(self.query)

        if self.model is None or self.model.rowCount() < 1:
            if not update:
                QMessageBox.warning(None, "Fundort Auswahl", u"Es wurden keine Fundorte gefunden!")
            self.query = None
            self.done(1)
            return False

        self.setupTable()

        self.uiItemCountLbl.setText(str(self.model.rowCount()))
        if info != None:
            self.uiInfoLbl.setText(info)

        return True

    def setupTable(self):
        self.uiSiteListTableV.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.uiSiteListTableV.setModel(self.model)
        self.uiSiteListTableV.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.uiSiteListTableV.resizeColumnsToContents()
        self.uiSiteListTableV.resizeRowsToContents()
        self.uiSiteListTableV.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.uiSiteListTableV.selectionModel().selectionChanged.connect(self.onSelectionChanged)

    def onSelectionChanged(self):
        self.uiSelectionCountLbl.setText("{0}".format(len(self.uiSiteListTableV.selectionModel().selectedRows())))

    def openSiteDialog(self, idx):
        siteNumber = self.model.item(idx.row(), 0).text()
        if self.siteDlg == None:
            self.siteDlg = APISSite(self.iface, self.dbm, self.imageRegistry, self.apisLayer)
            self.siteDlg.siteEditsSaved.connect(self.reloadTable)
            self.siteDlg.siteDeleted.connect(self.reloadTable)
        self.siteDlg.openInViewMode(siteNumber)
        self.siteDlg.show()
        # Run the dialog event loop

        if self.siteDlg.exec_():
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
        self.siteDlg.removeSitesFromSiteMapCanvas()
        #QMessageBox.warning(None, self.tr(u"Load Site"), self.tr(u"For Site: {0}".format(siteNumber)))

    def reloadTable(self, editsSaved):
        self.query.exec_()
        #QMessageBox.information(None, "SqlQuery", self.query.executedQuery())
        self.loadSiteListBySpatialQuery(self.query, None, True)
        #QMessageBox.warning(None, self.tr(u"Load Site"), self.tr(u"Reload Table Now"))

    def loadSiteInQgis(self):
        siteList = self.askForSiteList()
        if siteList:
            #QMessageBox.warning(None, self.tr(u"SiteList"), u"{0}".format(u", ".join(siteList)))
            polygon, point = self.askForGeometryType()
            if polygon or point:
                #QMessageBox.warning(None, self.tr(u"SiteList"), u"{0}, {1}".format(polygon, point))

                # get PolygonLayer
                subsetString = u'"fundortnummer" IN ('
                for siteNumber in siteList:
                    subsetString += u'\'{0}\','.format(siteNumber)
                subsetString = subsetString[:-1]
                subsetString += u')'
                siteLayer = self.getSpatialiteLayer('fundort', subsetString)

                if polygon:
                    # load PolygonLayer
                    self.loadLayer(siteLayer)

                if point:
                    # generate PointLayer
                    centerPointLayer = self.generateCenterPointLayer(siteLayer)
                    # load PointLayer
                    self.loadLayer(centerPointLayer)

                self.close()

    def loadSiteInterpretationInQgis(self):
        siteList = self.askForSiteList([2])
        if siteList:
            interpretationsToLoad = []
            noInterpretations = []
            intBaseDir = self.settings.value("APIS/int_base_dir")
            intDir = self.settings.value("APIS/int_dir")
            for siteNumber, kgName in siteList:
                country, siteNumberN = siteNumber.split(".")
                siteNumberN = siteNumberN.zfill(6)
                if country == u"AUT":
                    kgName = u"{0} ".format(kgName.lower().replace(".", "").replace("-", " ").replace("(", "").replace(")", ""))
                else:
                    kgName = ""
                #QMessageBox.information(None, 'info', u"{0}, {1}, {2}, {3}".format(siteNumber, siteNumberN, country, kgName))

                shpFile = u"luftint_{0}.shp".format(siteNumberN)
                intShpPath = os.path.normpath(os.path.join(intBaseDir, country, u"{0}{1}".format(kgName, siteNumberN), intDir, shpFile))
                if os.path.isfile(intShpPath):
                    interpretationsToLoad.append(intShpPath)
                else:
                    noInterpretations.append(siteNumber)

            if len(interpretationsToLoad) > 0:
                for intShp in interpretationsToLoad:
                    # TODO load Shape Files with ApisLayerHandling
                    self.apisLayer.requestShapeFile(intShp, epsg=None, layerName=None, groupName="Interpretationen",useLayerFromTree=True, addToCanvas=True)

                    #QMessageBox.information(None, u"Interpretation", intShp)
            else:
                QMessageBox.warning(None, u"Fundort Interpretation", u"Für die ausgewählten Fundorte ist keine Interpretation vorhanden.")


            #subsetString += u'\'{0}\','.format(siteNumber)
            #subsetString = subsetString[:-1]
            #subsetString += u')'
            #siteLayer = self.getSpatialiteLayer('fundort_interpretation', subsetString)
            #count = siteLayer.dataProvider().featureCount()
            #QMessageBox.information(None, "Feature Count", "Feature Count: {0}".format(count))
            #count = 0
            #if count > 0:
            #    pass
                #siteListLayer = list(set(siteLayer.getValues('fundortnummer')[0]))
                #siteListLayer = [sub_list[0] for sub_list in list(siteLayer.getValues('fundortnummer'))]
                #QMessageBox.warning(None, u"Fundort Interpretation", u"Layer: {0}".format(u", ".join(siteListLayer)))
                #QMessageBox.warning(None, u"Fundort Interpretation", u"Selection: {0}".format(u",".join(siteList)))

                #noInterpretation = list(set(siteList) - set(siteListLayer))
                #if len(noInterpretation) > 0:
                 #   QMessageBox.warning(None, u"Fundort Interpretation", u"Für einige Fundorte ist keine Interpretation vorhanden. [{0}]".format(u", ".join(noInterpretation)))

                #self.loadLayer(siteLayer)
                #self.close()
           # else:
           #     QMessageBox.warning(None, u"Fundort Interpretation", u"Für die ausgewählten Fundorte ist keine Interpretation vorhanden.")

    def exportSiteAsShp(self):
        siteList = self.askForSiteList()
        if siteList:
            # QMessageBox.warning(None, self.tr(u"SiteList"), u"{0}".format(u", ".join(siteList)))
            polygon, point = self.askForGeometryType()
            if polygon or point:
                # QMessageBox.warning(None, self.tr(u"SiteList"), u"{0}, {1}".format(polygon, point))

                # get PolygonLayer
                subsetString = u'"fundortnummer" IN ('
                for siteNumber in siteList:
                    subsetString += u'\'{0}\','.format(siteNumber)
                subsetString = subsetString[:-1]
                subsetString += u')'
                siteLayer = self.getSpatialiteLayer('fundort', subsetString)

                now = QDateTime.currentDateTime()
                time = now.toString("yyyyMMdd_hhmmss")
                if polygon:
                    # save PolygonLayer
                    self.exportLayer(siteLayer, time)

                if point:
                    # generate PointLayer
                    centerPointLayer = self.generateCenterPointLayer(siteLayer)
                    # save PointLayer
                    self.exportLayer(centerPointLayer, time)

    def exportAsPdf(self, tab_list=False, detail=False, subList=False, subDetail=False):
        if self.printingOptionsDlg is None:
            self.printingOptionsDlg = APISPrintingOptions(self)

        if tab_list and not detail and not subList and not subDetail:
            self.printingOptionsDlg.setWindowTitle("Druck Optionen: Fundortliste")
        elif detail and not tab_list and not subList and not subDetail:
            self.printingOptionsDlg.setWindowTitle("Druck Optionen: Fundort")
        elif detail and subList and not tab_list and not subDetail:
            self.printingOptionsDlg.setWindowTitle("Druck Optionen: Fundort und Funndstellenliste")
        elif detail and subList and subDetail and not tab_list:
            self.printingOptionsDlg.setWindowTitle("Druck Optionen: Fundort, Funndstellenliste und Fundstellen")
        else:
            self.printingOptionsDlg.setWindowTitle("Druck Optionen: Fundort Auswahl")

        if self.uiSiteListTableV.model().rowCount() == 1:
            self.printingOptionsDlg.configure(False, False)
        elif not self.uiSiteListTableV.selectionModel().hasSelection():
            self.printingOptionsDlg.configure(False, detail)
        else:
            if len(self.uiSiteListTableV.selectionModel().selectedRows()) == 1:
                self.printingOptionsDlg.configure(True, detail)
            elif len(self.uiSiteListTableV.selectionModel().selectedRows()) == self.uiSiteListTableV.model().rowCount():
                self.printingOptionsDlg.configure(False, detail)
            else:
                self.printingOptionsDlg.configure(True, detail)

        self.printingOptionsDlg.show()

        if self.printingOptionsDlg.exec_():
            # get settings from dialog
            selectionModeIsAll = self.printingOptionsDlg.selectionModeIsAll()
            outputMode = self.printingOptionsDlg.outputMode()

            siteList = self.getSiteList(selectionModeIsAll)
            if siteList:
                pdfsToPrint = []
                if tab_list:
                    pdfsToPrint.append({'type': APISListPrinter.SITE, 'idList': siteList})
                if detail:
                    for s in siteList:
                        pdfsToPrint.append({'type': APISTemplatePrinter.SITE, 'idList': [s]})
                        if SiteHasFindspot(self.dbm.db, s) and (subList or subDetail):
                            findspotList = GetFindspotNumbers(self.dbm.db, [s])
                            if findspotList:
                                if subList:
                                    pdfsToPrint.append({'type': APISListPrinter.FINDSPOT, 'idList': findspotList})
                                if subDetail:
                                    for f in findspotList:
                                        pdfsToPrint.append({'type': APISTemplatePrinter.FINDSPOT, 'idList': [f]})

                if pdfsToPrint:
                    APISPrinterQueue(pdfsToPrint,
                                     outputMode,
                                     openFile=self.printingOptionsDlg.uiOpenFilesChk.isChecked(),
                                     openFolder=self.printingOptionsDlg.uiOpenFolderChk.isChecked(),
                                     dbm=self.dbm,
                                     parent=self)

    def askForSiteList(self, plusCols=None):
        if self.uiSiteListTableV.selectionModel().hasSelection():
            #Abfrage ob Fundorte der selektierten Bilder Exportieren oder alle
            msgBox = QMessageBox()
            msgBox.setWindowTitle(u'Fundorte')
            msgBox.setText(u'Wollen Sie die ausgewählten Fundorte oder die gesamte Liste verwenden?')
            msgBox.addButton(QPushButton(u'Auswahl'), QMessageBox.YesRole)
            msgBox.addButton(QPushButton(u'Gesamte Liste'), QMessageBox.NoRole)
            msgBox.addButton(QPushButton(u'Abbrechen'), QMessageBox.RejectRole)
            ret = msgBox.exec_()

            if ret == 0:
                siteList = self.getSiteList(False, plusCols)
            elif ret == 1:
                siteList = self.getSiteList(True, plusCols)
            else:
                return None
        else:
            siteList = self.getSiteList(True, plusCols)

        return siteList

    def getSiteList(self, getAll, plusCols=None):
        siteList = []
        site = []
        if self.uiSiteListTableV.selectionModel().hasSelection() and not getAll:
            rows = self.uiSiteListTableV.selectionModel().selectedRows()
            for row in rows:
                if plusCols:
                    site = []
                if not self.uiSiteListTableV.isRowHidden(row.row()):
                    if plusCols:
                        site.append(self.model.item(row.row(), 0).text())
                        for col in plusCols:
                            site.append(self.model.item(row.row(), col).text())
                        siteList.append(site)
                    else:
                        siteList.append(self.model.item(row.row(), 0).text())
        else:
            for row in range(self.model.rowCount()):
                if plusCols:
                    site = []
                if not self.uiSiteListTableV.isRowHidden(row):
                    if plusCols:
                        site.append(self.model.item(row, 0).text())
                        for col in plusCols:
                            site.append(self.model.item(row, col).text())
                        siteList.append(site)
                    else:
                        siteList.append(self.model.item(row, 0).text())

        return siteList

    def askForGeometryType(self):
        # Abfrage ob Fundorte der selektierten Bilder Exportieren oder alle
        msgBox = QMessageBox()
        msgBox.setWindowTitle(u'Fundorte')
        msgBox.setText(u'Wollen Sie für die Fundorte Polygone, Punkte oder beide Layer verwenden?')
        msgBox.addButton(QPushButton(u'Polygone'), QMessageBox.ActionRole)
        msgBox.addButton(QPushButton(u'Punkte'), QMessageBox.ActionRole)
        msgBox.addButton(QPushButton(u'Polygone und Punkte'), QMessageBox.ActionRole)
        msgBox.addButton(QPushButton(u'Abbrechen'), QMessageBox.RejectRole)
        ret = msgBox.exec_()

        if ret == 0:
            polygon = True
            point = False
        elif ret == 1:
            polygon = False
            point = True
        elif ret == 2:
            polygon = True
            point = True
        else:
            return None, None

        return polygon, point

    def getSpatialiteLayer(self, layerName, subsetString=None, displayName=None):
        if not displayName:
            displayName = layerName
        uri = QgsDataSourceUri()
        uri.setDatabase(self.dbm.db.databaseName())
        uri.setDataSource('', layerName, 'geometry')
        layer = QgsVectorLayer(uri.uri(), displayName, 'spatialite')
        if subsetString:
            layer.setSubsetString(subsetString)

        return layer

        #symbol_layer = QgsSimpleLineSymbolLayerV2()
        #symbol_layer.setWidth(0.6)
        #symbol_layer.setColor(QColor(100, 50, 140, 255))
        #self.siteLayer.rendererV2().symbols()[0].changeSymbolLayer(0, symbol_layer)

    def loadLayer(self, layer):
        QgsProject.instance().addMapLayer(layer)

    def exportLayer(self, layer, time):
        geomType = "Punkt" if layer.geometryType() == 0 else "Polygon"
        saveDir = self.settings.value("APIS/working_dir", QDir.home().dirName())
        layerName = QFileDialog.getSaveFileName(self, u'Fundorte {0} Export Speichern'.format(geomType), saveDir + "\\" + 'Fundorte_{0}_{1}'.format(geomType, time), '*.shp')[0]
        if layerName:
            check = QFile(layerName)
            if check.exists():
                if not QgsVectorFileWriter.deleteShapeFile(layerName):
                    QMessageBox.warning(None, "Fundorte Export", u"Es ist nicht möglich die SHP Datei {0} zu überschreiben!".format(layerName))
                    return

            error = QgsVectorFileWriter.writeAsVectorFormat(layer, layerName, "UTF-8", layer.crs(), "ESRI Shapefile")

            if error == QgsVectorFileWriter.NoError:
                #QMessageBox.information(None, "Fundorte Export", u"Die ausgewählten Fundorte wurden in eine SHP Datei exportiert.")
                msgBox = QMessageBox()
                msgBox.setWindowTitle(u'Fundorte Export')
                msgBox.setText(u"Die ausgewählten Fundorte wurden in eine SHP Datei exportiert.")
                msgBox.addButton(QPushButton(u'SHP Datei laden'), QMessageBox.ActionRole)
                msgBox.addButton(QPushButton(u'Ordner öffnen'), QMessageBox.ActionRole)
                msgBox.addButton(QPushButton(u'SHP Datei laden und Ordner öffnen'), QMessageBox.ActionRole)
                msgBox.addButton(QPushButton(u'OK'), QMessageBox.AcceptRole)
                ret = msgBox.exec_()

                if ret == 0 or ret == 2:
                    # Shp Datei in QGIS laden
                    self.iface.addVectorLayer(layerName, "", 'ogr')

                if ret == 1 or ret == 2:
                    # ordner öffnen
                    OpenFileOrFolder(os.path.split(layerName)[0])

            else:
                QMessageBox.warning(None, "Fundorte Export", u"Beim erstellen der SHP Datei ist ein Fehler aufgetreten.")


    def generateCenterPointLayer(self, polygonLayer, displayName=None):
        if not displayName:
            displayName = polygonLayer.name()
        epsg = polygonLayer.crs().authid()
        #QMessageBox.warning(None, "EPSG", u"{0}".format(epsg))
        layer = QgsVectorLayer("Point?crs={0}".format(epsg), displayName, "memory")
        layer.setCrs(polygonLayer.crs())
        provider = layer.dataProvider()
        provider.addAttributes(polygonLayer.dataProvider().fields())

        layer.updateFields()

        pointFeatures = []
        for polygonFeature in polygonLayer.getFeatures():
            polygonGeom = polygonFeature.geometry()
            pointGeom = polygonGeom.centroid()
            # if center point is not on polygon get the nearest Point
            if not polygonGeom.contains(pointGeom):
                pointGeom = polygonGeom.pointOnSurface()

            pointFeature = QgsFeature()
            pointFeature.setGeometry(pointGeom)
            pointFeature.setAttributes(polygonFeature.attributes())
            pointFeatures.append(pointFeature)

        provider.addFeatures(pointFeatures)

        layer.updateExtents()

        return layer