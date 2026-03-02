from datetime import datetime
import os

from PyQt5.QtWidgets import QWidget, QItemDelegate, QToolButton
from PyQt5.QtCore import Qt, QSize, QPointF
from PyQt5.QtGui import QColor, QIcon, QPainter

from .core.draw import draw_badges, pixmap_from_file, change_widget_background_color
from bp_chat.logic.chat_api.ChatApi import ChatApi

from .ui.UiSelectChatWidget import Ui_SelectChatWidget
from .common.langs import tr_w


class SelectChatWidget(QWidget, Ui_SelectChatWidget):

    main_widget = None
    last_server_info = None

    def __init__(self, parent, main_widget, flags=Qt.Window, *args, **kwargs):
        super().__init__(parent)

        self.main_widget = main_widget

        self.setupUi(self)
        self.retranslateUi(self)

        self.initView()

    def initView(self):
        change_widget_background_color(self, QColor(255, 255, 255))
        change_widget_background_color(self.toolBarWidget, QColor(255, 193, 7))

        tr_w(self.label)

        self.textBrowser.hide()

    def updateServerInfo(self, d):
        self.last_server_info = d
        self.showServerInfo(d)

    def showServerInfo(self, _, adm_info=None):
        # if not d:
        #     d = {}
        if not adm_info:
            adm_info = {}
        vmem = adm_info.get('vmem', {})
        tm = adm_info.get('tm', None)
        tm = datetime.fromtimestamp(tm).strftime("%Y-%m-%d %H:%M") if tm else '-'
        dvsc = adm_info.get('dvcs', None)

        server_uid = ChatApi.instance().server_uid
        if dvsc:
            chat_api = ChatApi.instance()
            for user_id, ver, platform in dvsc:
                user = chat_api.getUser(user_id)
                if user:
                    user.devices[(ver, platform)] = datetime.now()

        from .common.system_info import bytes2human

        pay = adm_info.get("pay", "FREE")
        server_tkn = adm_info.get("tkn", "")

        addrs = []
        for a in adm_info.get('ifaddrs', []):
            addrs.append('<p>{}</p>'.format(a))

        html = """<p>Select chat</p>
        <h3>Server info:</h3>
        <p><b>Version:</b> {pay} <b>CPUs:</b> {cpus} <b>Mem:</b> {mfree} / {mtotal} </p>
        <p><b>Server UUID:</b> {suid}</p>
        <p><b>Server TKN:</b> {server_tkn}</p>
        <p><b>Free space:</b> {free} / {total} <b>Time:</b> {tm}</p>
        <p><b>Adresses:</b></p>
        {addrs}
        """.format(free=bytes2human(adm_info.get('free', '-')), total=bytes2human(adm_info.get('total', '-')), addrs='\n'.join(addrs), suid=server_uid,
                   pay=pay, cpus=adm_info.get('cpus', '-'), mfree=bytes2human(vmem.get('free', '-')), mtotal=bytes2human(vmem.get('total', '-')),
                   tm=tm, server_tkn=server_tkn)

        #html += '<p> cwd: ' + os.getcwd() + '</p>'
        #html += '<p> file: ' + os.path.abspath(__file__) + '</p>'

        #from .common.draw_funcs import path_to_images
        #html += '<p> imgs: ' + path_to_images() + '</p>'

        self.textBrowser.setText(html)

        self.textBrowser.show()
        self.label.hide()

    def updateAdmInfo(self, adm_info):
        self.showServerInfo(self.last_server_info, adm_info)