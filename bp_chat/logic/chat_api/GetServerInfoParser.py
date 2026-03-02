from .BaseParser import BaseParser
from .ChatApiCommon import tryable


class GetServerInfoParser(BaseParser):

    @tryable
    def onSuccess(self, json):
        if "result" in json:

            if self.chatApi.callbacks:
                self.chatApi.callbacks.gotServerInfo(json['result'])

            return True

        return False