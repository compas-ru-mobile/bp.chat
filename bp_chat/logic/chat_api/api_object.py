

class ApiObject:

    _chat_api_cls = None
    #_ProgressNotify = None

    @staticmethod
    def init(api):
        ApiObject._chat_api_cls = api
        return api

    @property
    def chat_api(self):
        return self._chat_api_cls.instance()

    @property
    def chatApi(self):
        return self._chat_api_cls.instance()

    @staticmethod
    def get_chat_api():
        return ApiObject._chat_api_cls.instance()

    # @staticmethod
    # def init_ProgressNotify(pn):
    #     ApiObject._ProgressNotify = pn
    #     return pn
    #
    # @property
    # def ProgressNotify(self):
    #     return self._ProgressNotify
