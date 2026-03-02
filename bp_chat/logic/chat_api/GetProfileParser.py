from datetime import time, timedelta, datetime, date

from .BaseParser import BaseParser
from ..datas.UserProfile import UserProfile
from bp_chat.core.tryable import tryable, ConsoleThread
from bp_chat.core.local_db_profiles import LocalDbProfiles


class GetProfileParser(BaseParser):

    @tryable
    def onSuccess(self, json):

        if "result" in json:
            profile_json = json["result"]
            return self.got_user_profile(profile_json)

        return False

    @tryable
    def got_user_profile(self, profile_json):
        up = self.parseUserProfile(profile_json)

        if up:
            profile_user_id = up.getUserID()

            if str(self.chatApi.getCurrentUserId()) == str(profile_user_id):
                self.chatApi.setCurrentUserProfile(up)
                self.chatApi.currentUserProfileUpdated()

                # if self.chatApi.callbacks:
                #     self.chatApi.callbacks.updateUserProfileCallback(profile_user_id)

            else:

                user = self.chatApi.users.get(profile_user_id)
                if user:
                    user.profile = up

                    # if self.chatApi.callbacks:
                    #     self.chatApi.callbacks.updateUserProfileCallback(profile_user_id)

            if profile_user_id != None:
                added = LocalDbProfiles.add_profile(
                    self.chatApi.server_uid, profile_user_id, name=up._name or user.name, surname=up.surname, third_name=up.third_name,
                    email=up.email, photo=up.photo_id, phone=up.phone, position=up.position)

                if profile_user_id == self.chatApi.opening_profile_id:
                    if self.chatApi.callbacks:
                        self.chatApi.callbacks.updateUserProfileCallback(profile_user_id)
                else:
                    if self.chatApi.callbacks:
                        self.chatApi.callbacks.chatsUpdatedListCallback()

            return True

        return False

    @tryable
    def parseUserProfile(self, json):
        if json == None:
            return None

        user_id = json["user_id"]
        name = json["name"]
        surname = json["surname"]
        third_name = json["third_name"]
        email = json["email"]
        phone = json["phone"]
        photo = json["photo"]
        position = json.get("position", '')
        user_day = json.get("user_day")

        user = self.chatApi.getUserOrCreate(str(user_id), nick=json.get('nick'), user_type=json.get('user_type'), is_bot=json.get('is_bot'))

        if not user:
            return None

        if user.profile == None:
            user.profile = UserProfile(user, name)

        up = user.profile
        up.setName(name)

        up.surname = surname
        up.third_name = third_name
        up.email = email
        up.phone = phone
        up.setPhotoId(photo)
        up.position = position

        if user_day:
            today_start = datetime.combine(date.today(), time())
            if user_day[0]:

                if user_day[1]:
                    dt = (today_start + timedelta(seconds=user_day[1])) - timedelta(seconds=user_day[0])
                    user_day.append(dt.time())

                user_day[0] = (today_start + timedelta(seconds=user_day[0])).time()

            if user_day[1]:
                user_day[1] = (today_start + timedelta(seconds=user_day[1])).time()

        up.user_day = user_day

        return up
