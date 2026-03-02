from PyQt5.QtWidgets import QListView
from PyQt5.QtCore import QModelIndex, QItemSelectionModel, QItemSelection, QAbstractItemModel

#from .ListViewBase import ListViewBase
from ..models.list_model import ListView as ListViewBase

class UsersListView(ListViewBase):

    main_widget = None
    checked_users = []

    def __init__(self, parent):
        super().__init__(parent)
        self.main_widget = parent
        #self.initAtStart()
#         self.setStyleSheet(
#             """
# QScrollBar:vertical {
#     border: none;
#     background: rgba(255,255,255,255);
#     width: 10px;
#     _margin: 20px 0px 20px 0px;
#     margin: 0px 0px 0px 0px;
# }
# QScrollBar::handle:vertical {
#     background: rgba(0,0,0,255);
#     ttt: qlineargradient(x1:0, y1:0, x2:1, y2:0,
#         stop: 0 rgba(183, 210, 192, 255), stop: 0.5 rgba(105, 165, 5, 255), stop:1 rgba(203, 225, 0, 255));
#     min-height: 20px;
# }
# QScrollBar::add-line:vertical {
#     background: rgba(0,0,0,0);
#     ttt: qlineargradient(x1:0, y1:0, x2:1, y2:0,
#         stop: 0 rgba(183, 210, 192, 255), stop: 0.5 rgba(105, 165, 5, 255), stop:1 rgba(203, 225, 0, 255));
#     height: 0px;
#     subcontrol-position: bottom;
#     subcontrol-origin: margin;
# }
# QScrollBar::sub-line:vertical {
#     background: rgba(0,0,0,0);
#     ttt: qlineargradient(x1:0, y1:0, x2:1, y2:0,
#         stop: 0 rgba(183, 210, 192, 255), stop: 0.5 rgba(105, 165, 5, 255), stop:1 rgba(203, 225, 0, 255));
#     height: 0px;
#     subcontrol-position: top;
#     subcontrol-origin: margin;
# }
#             """
#         )

    def selectionChanged(self, selectedSelection, deselectedSelection):
        selected_indx = set(map(lambda x: int(x.data().id), selectedSelection.indexes()))
        deselected_indx = set(map(lambda x: int(x.data().id), deselectedSelection.indexes()))
        c_u = set(map(int, self.checked_users))

        checked_users = c_u.union(selected_indx)
        checked_users = checked_users.difference(deselected_indx)

        self.checked_users = tuple(map(str, checked_users))

    def setChecked(self, checked_users):
        self.checked_users = checked_users

    # need call when data will be changed
    def refresh_checked(self):
        c_u = self.checked_users
        users = self.itemDelegate().get_users()
        item_selection = QItemSelection()
        for i, user in enumerate(users):
            _id = int(user.id)
            if _id in map(int, c_u):
                index = self.model().index(i, 0)
                item_selection.select(index, index)
        self.selectionModel().select(item_selection, QItemSelectionModel.Select)

