
from .api_object import ApiObject


class BaseParser(ApiObject):

    def execute(self, json):
        if self.is_success(json):
            if not self.onSuccess(json):
                self.debug("UNKNOWN SUCCESS - JSON: {}".format(json))
        elif self.is_error(json):
            if not self.onError(json):
                self.debug("UNKNOWN ERROR - JSON: {}".format(json))
        else:
            self.onUnknown(json)

    def onSuccess(self, json):
        return False

    def onError(self, json):
        return False

    def onUnknown(self, json):
        self.debug("UNKNOWN json: {}".format(json))


    def debug_json_exception(self, e, className):
        self.debug("JSON Exception (" + className + "): " + str(e))

    @staticmethod
    def result_equals(json, value):
        if type(json) != dict:
            return False
        return "result" in json and value != None and value == json["result"]

    @staticmethod
    def result_or_error_equals(json, value):
        return BaseParser.result_equals(json, value) or BaseParser.error_equals(json, value)

    @staticmethod
    def error_equals(json, value):
        if type(json) != dict:
            return False
        return "error" in json and value != None and value == json["error"]

    @staticmethod
    def debug(text):
        pass

    @staticmethod
    def is_success(json):
        return BaseParser.is_type(json, "success")

    @staticmethod
    def is_error(json):
        return BaseParser.is_type(json, "error")

    @staticmethod
    def is_type(json, name):
        if type(json) != dict:
            return False
        return "type" in json and json["type"] == name

    @staticmethod
    def is_message(json):
        return BaseParser.is_type(json, "message")

    @staticmethod
    def is_update(json):
        return BaseParser.is_type(json, "update") and "update" in json

    @staticmethod
    def is_status(json):
        return BaseParser.is_type(json, "status")

    @staticmethod
    def is_group(json):
        return BaseParser.is_type(json, "group")

    @staticmethod
    def is_live(json):
        return BaseParser.is_type(json, "live")

    @staticmethod
    def is_user_to_group(json):
        return BaseParser.is_type(json, "user_to_group")

    @staticmethod
    def is_private(json):
        return BaseParser.is_type(json, "private")

    @staticmethod
    def is_chat_change(json):
        return BaseParser.is_type(json, "chat_change")

    @staticmethod
    def is_chat_del(json):
        return BaseParser.is_type(json, "chat_del")

    @staticmethod
    def is_user_from_group(json):
        return BaseParser.is_type(json, "user_from_group")

    @staticmethod
    def is_chat_activate(json):
        return BaseParser.is_type(json, "chat_activate")

    @staticmethod
    def is_user_new(json):
        return BaseParser.is_type(json, "user_new")

    @staticmethod
    def is_user_change(json):
        return BaseParser.is_type(json, "user_change")

    @staticmethod
    def is_user_del(json):
        return BaseParser.is_type(json, "user_del")

    @staticmethod
    def is_delivered(json):
        return BaseParser.is_type(json, "delivered")

    @staticmethod
    def is_take_live_chat(json):
        return BaseParser.is_type(json, "take_live_chat")

    @staticmethod
    def is_not_delivered(json):
        return BaseParser.is_type(json, "not_delivered")

    @staticmethod
    def is_adm_info(json):
        return BaseParser.is_type(json, "adm_info")

    @staticmethod
    def is_open_chat(json):
        return BaseParser.is_type(json, "open_chat")

    @staticmethod
    def is_answer(json, url):
        try:
            return "answer" in json and json.get("answer") == url
        except Exception as e:
            BaseParser.debug(" is_answer Exception: " + str(e))
            return False

