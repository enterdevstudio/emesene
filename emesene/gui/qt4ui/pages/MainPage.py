# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''This module contains classes to represent the main page.'''

import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from PyQt4.QtCore import Qt
from gui.qt4ui import widgets

import extension
import gui

class MainPage (QtGui.QWidget, gui.MainWindowBase):
    '''The main page (the one with the contact list)'''
    # pylint: disable=W0612
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to dislay the main screen'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612

    def __init__(self, session, on_new_conversation, set_menu_bar_cb, parent=None):
        '''Constructor'''
        QtGui.QWidget.__init__(self, parent)
        gui.MainWindowBase.__init__(self, session, on_new_conversation)
        # callbacks:
        self._set_menu_bar_cb = set_menu_bar_cb

        # menu objects:
        self._main_menu = None
        self._contact_menu = None
        self._group_menu = None
        self.session = session

        self._setup_ui()

        # emesene's
        self.session.config.subscribe(self._on_show_userpanel_changed,
            'b_show_userpanel')
        self._on_show_userpanel_changed(self.session.config.b_show_userpanel)

    def _setup_ui(self):
        '''Instantiates the widgets, and sets the layout'''
        contact_list_cls = extension.get_default('contact list')
        user_panel_cls = extension.get_default('user panel')

        self.panel = user_panel_cls(self.session, self)
        self.panel.enabled = False
        self.contact_list = contact_list_cls(self.session)
        self.search_entry = widgets.SearchEntry()
        self.search_entry.setVisible(False)
        self.search_entry.textChanged.connect(
                                    self._on_search_changed)
        self.panel.search.clicked.connect(
                                    self._on_search_click)

        self.below_menu = extension.get_and_instantiate('below menu', self)
        self.below_panel = extension.get_and_instantiate('below panel', self)
        self.below_userlist = extension.get_and_instantiate('below userlist',
                                                            self)

        self.lay = QtGui.QGridLayout()
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.addWidget(self.below_menu, 1, 0)
        self.lay.addWidget(self.panel, 2, 0)
        self.lay.addWidget(self.below_panel, 3, 0)
        self.lay.addWidget(self.search_entry, 4, 0)
        self.lay.addWidget(self.contact_list, 5, 0)
        self.lay.addWidget(self.below_userlist, 6, 0)
        self.setLayout(self.lay)
        self.contact_list.new_conversation_requested.connect(
                                        self.on_new_conversation_requested)

    def _on_search_click(self, status):
        self.search_entry.setVisible(status)
        self.contact_list.is_searching = status
        if not status:
            #clean search entry when search is disabled
            self.search_entry.clear()
            self._on_search_changed(QtCore.QString(''))
        else:
            self.search_entry.setFocus()

    def _on_search_changed(self, new_text):
        self.contact_list.filter_text = new_text.toLower()
        if new_text != '':
            self.contact_list.expand_groups()
            self.contact_list.select_top_contact()
        else:
            self.contact_list.un_expand_groups()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and \
            self.search_entry.hasFocus():
                self.contact_list.open_conversation()
                self.panel.search.setChecked(False)
                self._on_search_click(False)
                return
        if event.key() == Qt.Key_Escape and \
            self.search_entry.hasFocus():
                self.panel.search.setChecked(False)
                self._on_search_click(False)
                self.contact_list.setFocus()
                return
        if not self.panel.nick.hasFocus() and \
           not self.panel.message.hasFocus():
            if not self.panel.search.isChecked():
                self.panel.search.setChecked(True)
                self._on_search_click(True)
                # add missing key into entry text
                prev_text = self.search_entry.text()
                if not event.text().trimmed().isEmpty():
                    self.search_entry.setText(prev_text.append(event.text()))
                return
        QtGui.QWidget.keyPressEvent(self, event)

    def _on_show_userpanel_changed(self, value):
        '''callback called when config.b_show_userpanel changes'''
        self.panel.setVisible(value)

    def _on_new_conversation_requested(self, account, on_close):
        '''Slot called when the user doubleclicks
        an entry in the contact list'''
        self.on_new_conversation_requested(account)

    def _on_mail_count_changed(self, count):
        self.panel.set_mail_count(count)

        #extension changes
        extension.subscribe(self._on_below_userlist_changed, "below userlist")
        extension.subscribe(self._on_below_menu_changed, "below menu")
        extension.subscribe(self._on_below_panel_changed, "below panel")

    def _replace_widget(self, widget, new_extension, pos):
        if widget:
            self.lay.removeWidget(widget)
            widget = None
        if new_extension:
            widget = new_extension(self)
            self.lay.addWidget(widget, pos, 0)
            widget.show()
        return widget

    def _on_below_userlist_changed(self, new_extension):
        if type(self.below_userlist) != new_extension:
            pos = self.lay.rowCount() - 1
            self.below_userlist = self._replace_widget(
                    self.below_userlist, new_extension, pos)

    def _on_below_menu_changed(self, new_extension):
        if type(self.below_menu) != new_extension:
            self.below_menu = self._replace_widget(
                    self.below_menu, new_extension, 1)

    def _on_below_panel_changed(self, new_extension):
        if type(self.below_panel) != new_extension:
            self.below_menu = self._replace_widget(
                    self.below_menu, new_extension, 3)
