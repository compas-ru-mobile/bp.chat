
from .BaseParser import BaseParser
from .ChatApiCommon import tryable


class GetServerSettingsParser(BaseParser):

    @tryable
    def onSuccess(self, json):
        if "result" in json:

            self.chatApi.gotServerSettings(json['result'])

            return True

        return False