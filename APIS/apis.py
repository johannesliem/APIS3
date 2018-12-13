# -*- coding: utf-8 -*-
"""
/***************************************************************************
 APIS
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
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMessageBox, QActionGroup, QToolButton, QMenu

# Initialize Qt resources from file resources.py

# Import the code for the src #APIS.src
from APIS.src.apis_settings import APISSettings
from APIS.src.apis_film import APISFilm
from APIS.src.apis_image_mapping import APISImageMapping
from APIS.src.apis_site_mapping import APISSiteMapping
from APIS.src.apis_search import APISSearch

from APIS.src.apis_utils import tr, ApisPluginSettings
from APIS.src.apis_image_registry import ApisImageRegistry
from APIS.src.apis_db_manager import ApisDbManager
from APIS.src.apis_layer_manager import ApisLayerManager

import os.path
from functools import partial
#TEST BLUB
class APIS:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        QSettings().setValue("APIS/plugin_dir", self.plugin_dir)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'APIS_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = tr(u'&APIS')
        self.toolbar = self.iface.addToolBar(u'APIS')
        self.toolbar.setObjectName(u'APIS')

        self.dbm = None
        self.apisLayer = None
        self.areDialogsInit = False
        self.areDialogsActive = False
        self.imageMappingMode = False
        self.imageMappingDlg = None
        self.siteMappingDlg = None
        self.searchDlg = None
        self.openDialogButtons = None
        self.imageMappingActionBtn = None
        self.siteMappingActionBtn = None
        self.searchActionBtn = None

        # Require configStatus on startup and Settings
        self.configStatus, self.settings = ApisPluginSettings()

        # Create APIS Image Registry
        self.imageRegistry = ApisImageRegistry(self.plugin_dir, self.iface)
        self.imageRegistry.loaded.connect(self.enableApis)

        if self.configStatus:
            self.imageRegistry.setupSettings()
            self.imageRegistry.setupRegistry()

        # Create the src (after translation) and keep reference
        self.settingsDlg = APISSettings(self.iface, self.imageRegistry, self.iface.mainWindow())

    def enableApis(self):
        #QMessageBox.warning(None, self.tr(u"ApisEnabled"), u"ImageRegistry is now loaded!")
        if(self.configStatus and self.imageRegistry.registryIsLoaded()):
            self.dbm = ApisDbManager(self.settings.value("APIS/database_file"))

            # TODO: Prepare ApisLayerTree
            self.apisLayer = ApisLayerManager(self.plugin_dir, self.iface, self.dbm)

            self.initDialogs()
            if self.openDialogButtons is not None:
                self.activateDialogs(True)

        else:
            QMessageBox.warning(None, self.tr(u"Konfiguration"), u"{0}, {1}".format(self.configStatus, self.settings))
            if self.openDialogButtons is not None:
                self.activateDialogs(False)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        checkable=False,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if checkable:
            action.setCheckable(checkable)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToDatabaseMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initDialogs(self):
        self.filmDlg = APISFilm(self.iface, self.dbm, self.imageRegistry, self.apisLayer, self.iface.mainWindow())
        self.imageMappingDlg = None
        self.siteMappingDlg = None
        self.searchDlg = None
        self.areDialogsInit = True
        self.areDialogsActive = True

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # Settings Dialog
        if self.configStatus and self.imageRegistry.registryIsLoaded():
            icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'settings.png')
        else:
            icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'settings_alert.png')

        self.openSettingsButton = self.add_action(
            icon_path,
            text=tr(u'APIS Einstellungen'),
            callback=self.openSettingsDialog,
            parent=self.iface.mainWindow())

        self.openDialogButtons = []
        self.apisLayerActionsGroup = QActionGroup(self.iface.mainWindow())
        self.uiLayerTBtn = QToolButton()
        self.uiLayerTBtn.setMenu(QMenu())
        self.uiLayerTBtn.setPopupMode(QToolButton.MenuButtonPopup)
        self.uiLayerTBtnAction = self.toolbar.addWidget(self.uiLayerTBtn)

        # (Re)Load Apis Layers
        icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'layer.png')
        self.openDialogButtons.append(self.add_action(
            icon_path,
            text=self.tr(u'Alle Layer'),
            callback=partial(self.loadApisLayerTree, "all"),
            enabled_flag=self.configStatus and self.imageRegistry.registryIsLoaded(),
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.iface.mainWindow())
        )
        self.apisLayerActionsGroup.addAction(self.openDialogButtons[0])
        m = self.uiLayerTBtn.menu()
        m.addAction(self.openDialogButtons[0])
        self.uiLayerTBtn.setDefaultAction(self.openDialogButtons[0])
        m.addSeparator()

        icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'site.png')
        self.openDialogButtons.append(self.add_action(
            icon_path,
            text=self.tr(u'Funde Layer'),
            callback=partial(self.loadApisLayerTree, "site"),
            enabled_flag=self.configStatus and self.imageRegistry.registryIsLoaded(),
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.iface.mainWindow())
        )
        self.apisLayerActionsGroup.addAction(self.openDialogButtons[1])
        m.addAction(self.openDialogButtons[1])

        icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'images.png')
        self.openDialogButtons.append(self.add_action(
            icon_path,
            text=self.tr(u'Luftbild Layer'),
            callback=partial(self.loadApisLayerTree, "image"),
            enabled_flag=self.configStatus and self.imageRegistry.registryIsLoaded(),
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.iface.mainWindow())
        )
        self.apisLayerActionsGroup.addAction(self.openDialogButtons[2])
        m.addAction(self.openDialogButtons[2])
        m.addSeparator()

        icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'layer.png')
        self.openDialogButtons.append(self.add_action(
            icon_path,
            text=self.tr(u'Gemeindegrenzen'),
            callback=partial(self.loadApisLayerTree, "municipalborders"),
            enabled_flag=self.configStatus and self.imageRegistry.registryIsLoaded(),
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.iface.mainWindow())
        )
        self.apisLayerActionsGroup.addAction(self.openDialogButtons[3])
        m.addAction(self.openDialogButtons[3])

        icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'layer.png')
        self.openDialogButtons.append(self.add_action(
            icon_path,
            text=self.tr(u'Staatsgrenzen'),
            callback=partial(self.loadApisLayerTree, "nationalborders"),
            enabled_flag=self.configStatus and self.imageRegistry.registryIsLoaded(),
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.iface.mainWindow())
        )
        self.apisLayerActionsGroup.addAction(self.openDialogButtons[4])
        m.addAction(self.openDialogButtons[4])
        m.addSeparator()

        icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'layer.png')
        self.openDialogButtons.append(self.add_action(
            icon_path,
            text=self.tr(u'ÖK50 Layer'),
            callback=partial(self.loadApisLayerTree, "oek50"),
            enabled_flag=self.configStatus and self.imageRegistry.registryIsLoaded(),
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.iface.mainWindow())
        )
        self.apisLayerActionsGroup.addAction(self.openDialogButtons[5])
        m.addAction(self.openDialogButtons[5])

        #dbM = self.iface.databaseMenu()

        #QMessageBox.information(None,"menu", "{}".format(",".join(dbM.children())))

        #self.iface.addPluginToDatabaseMenu(
        #    self.menu,
        #    m)

        #self.toolbar.addActions(self.apisLayerActionsGroup.actions())

        # Film Dialog
        icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'film.png')
        self.openDialogButtons.append(self.add_action(
            icon_path,
            text=tr(u'APIS Film'),
            callback=self.openFilmDialog,
            enabled_flag=self.configStatus and self.imageRegistry.registryIsLoaded(),
            parent=self.iface.mainWindow())
        )

        #Image Mapping Dialog
        icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'mapping_vertical.png')
        self.imageMappingActionBtn = self.add_action(
            icon_path,
            text=self.tr(u'Bilder kartieren'),
            callback=self.toggleImageMappingDialog,
            enabled_flag=self.configStatus and self.imageRegistry.registryIsLoaded(),
            parent=self.iface.mainWindow(),
            checkable=True)
        self.openDialogButtons.append(self.imageMappingActionBtn)


        #Site Mapping Dialog
        icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'site.png')
        self.siteMappingActionBtn = self.add_action(
            icon_path,
            text=self.tr(u'Fundorte kartieren'),
            callback=self.toggleSiteMappingDialog,
            enabled_flag=self.configStatus and self.imageRegistry.registryIsLoaded() and self.settings.value("APIS/disable_site_and_findspot", "0") != "1",
            parent=self.iface.mainWindow(),
            checkable=True)
        self.openDialogButtons.append(self.siteMappingActionBtn)

        #Search Dialog
        icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'search.png')
        self.searchActionBtn = self.add_action(
            icon_path,
            text=self.tr(u'APIS Suche'),
            callback=self.toggleSearchDialg,
            enabled_flag=self.configStatus and self.imageRegistry.registryIsLoaded(),
            parent=self.iface.mainWindow(),
            checkable=True)
        self.openDialogButtons.append(self.searchActionBtn)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginDatabaseMenu(
                tr(u'&APIS'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

        # ToDo: disconnect DB


    def run(self):
        """Run method that performs all the real work"""
        # show the src
        self.dlg.show()
        # Run the src event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    def openSettingsDialog(self):
        """Run method that performs all the real work"""
        # show the src
        self.configStatus, self.settings = ApisPluginSettings()

        if self.configStatus:
            if not self.imageRegistry.registryIsSetup():
                self.imageRegistry.setupSettings()
            if not self.imageRegistry.registryIsLoaded():
                self.imageRegistry.setupRegistry()
            self.settingsDlg.uiUpdateImageRegistryBtn.setEnabled(True)
        else:
            self.settingsDlg.uiUpdateImageRegistryBtn.setEnabled(False)

        self.settingsDlg.show()
        # Run the src event loop
        if self.settingsDlg.exec_():
            # See if OK was pressed
            self.configStatus, self.settings = ApisPluginSettings()
            if self.configStatus:
                if not self.imageRegistry.registryIsSetup():
                    self.imageRegistry.setupSettings()
                if not self.imageRegistry.registryIsLoaded():
                    self.imageRegistry.setupRegistry()
            self.enableApis()
        else:
            pass

    def loadApisLayerTree(self, layerGroup):
        QMessageBox.information(None, "Apis Layer", layerGroup)
        if self.apisLayer and self.apisLayer.isLoaded:
            self.apisLayer.loadDefaultLayerTree()

    def openFilmDialog(self):
        """Run method that performs all the real work"""
        # show the src
        self.filmDlg.show()
        # Run the src event loop
        result = self.filmDlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    def toggleImageMappingDialog(self):
        if not self.imageMappingDlg:
            self.imageMappingDlg = APISImageMapping(self.iface, self.dbm, self.apisLayer)

            self.imageMappingDlg.visibilityChanged.connect(self.imageMappingActionBtn.setChecked)

        #if self.imageMappingDlg.isVisible():
        if self.imageMappingActionBtn and self.imageMappingActionBtn.isChecked():
            self.imageMappingDlg.show()
            self.imageMappingMode = True
            #self.imageMappingActionBtn.setChecked(False)
        else:
            #TODO Check Mapping State !!!
            self.imageMappingDlg.hide()
            self.imageMappingMode = False
            #self.imageMappingActionBtn.setChecked(True)

    def toggleSiteMappingDialog(self):
        if not self.siteMappingDlg:
            self.siteMappingDlg = APISSiteMapping(self.iface, self.dbm, self.imageRegistry, self.apisLayer)
            self.siteMappingDlg.visibilityChanged.connect(self.siteMappingActionBtn.setChecked)

        if self.siteMappingActionBtn and self.siteMappingActionBtn.isChecked():
            self.siteMappingDlg.show()
        else:
            self.siteMappingDlg.hide()

    def toggleSearchDialg(self):
        if not self.searchDlg:
            self.searchDlg = APISSearch(self.iface, self.dbm, self.imageRegistry, self.apisLayer)
            #self.searchDlg = APISSearch(self.iface)
            self.searchDlg.visibilityChanged.connect(self.searchActionBtn.setChecked)

        if self.searchActionBtn and self.searchActionBtn.isChecked():
            self.searchDlg.show()
        else:
            self.searchDlg.hide()

    def activateDialogs(self, value):
        """
        iterate through openDialogButtons and set them VALUE
        :param value:
        :return:
        """
        for action in self.openDialogButtons:
            if action is self.siteMappingActionBtn:
                if self.configStatus:
                    if self.settings.value("APIS/disable_site_and_findspot", "0") != "1":
                        action.setEnabled(value)
                    else:
                        action.setEnabled(False)
            else:
                action.setEnabled(value)
        self.areDialogsActive = value

        # Change Settings Icon if required
        if self.configStatus and self.imageRegistry.registryIsLoaded():
            icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'settings.png')
        else:
            icon_path = os.path.join(self.plugin_dir, 'ui', 'icons', 'settings_alert.png')
        self.openSettingsButton.setIcon(QIcon(icon_path))

        if self.imageMappingActionBtn and self.imageMappingActionBtn.isChecked():
            self.imageMappingActionBtn.trigger()

        if self.siteMappingActionBtn and self.siteMappingActionBtn.isChecked():
            self.siteMappingActionBtn.trigger()

        if self.searchActionBtn and self.searchActionBtn.isChecked():
            self.searchActionBtn.trigger()

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('APIS', message)