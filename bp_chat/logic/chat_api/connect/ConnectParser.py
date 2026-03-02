
from bp_chat.logic.chat_api.BaseParser import BaseParser


class ConnectParser(BaseParser):

    ERROR_TYPES = ('API_OLD', 'API_SERVER_OLD')

    def onSuccess(self, json):
        if "result" in json:
            print('[ ConnectParser ]')
            result = json["result"]

            if "token" in result and "id" in result:

                is_admin = result.get('admin', False)
                self.chatApi.setIsAdmin(is_admin)
                add = ' ADMIN' if is_admin else ''
                server_uid = result.get('server', None)
                if server_uid:
                    add += ' server:{}'.format(server_uid)
                else:
                    server_uid = 'old_server'

                self.chatApi.init_connect(server_uid)
                self.chatApi.setServerUid(server_uid)
                self.chatApi.setUserAndToken(
                    result["token"],
                    result["id"]
                )
                self.chatApi.save_connect()

                self.debug("[ OK   ] connected" + add)

                if self.chatApi.callbacks:
                    self.chatApi.callbacks.gotLoggedInCallback()

                self.chatApi.setAbils(result.get('abils'))

                if self.chatApi.old_connect and self.chatApi.with_users:
                    self.chatApi.send(url="/users/", attrs={})

                return True

        return False

    def onError(self, json):

        if (self.result_or_error_equals(json, 'API_OLD')): # FIXME for old server

            self.chatApi.onApiClientOld()

        elif (self.result_or_error_equals(json, 'API_SERVER_OLD')): # FIXME for old server

            self.chatApi.onApiServerOld()

        elif (self.result_equals(json, "NO_AUTH")):

            self.chatApi.onNeedRegister()

        elif (self.result_equals(json, "NO_AUTH_STARTED")):

            self.chatApi.startRegisterNext()

        elif (self.result_equals(json, "NO_AUTH_CUTTED")):

            self.chatApi.startRegisterCutted()

        elif (self.result_equals(json, 'NO_AUTH_LOGIN_OCCUPIED')):

            self.chatApi.onLoginOccupied()

        elif (self.result_equals(json, "NO_AUTH_DEACTIVATED")):

            # FIXME show "This device is deactivated" - ON ANDROID !!!
            self.chatApi.disconnect()

            if self.chatApi.callbacks != None:
                self.chatApi.callbacks.needShowErrorCallback(self.chatApi.ERROR_NO_AUTH_DEACTIVATED, "This device is deactivated. Ask your administrator for help.")

        else:
            return False

        return True

