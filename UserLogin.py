from flask_login import UserMixin


class UserLogin(UserMixin):
    def fromDB(self, user):
        self.__user = user
        return self

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user.id)

    def get_login(self):
        return str(self.__user.login)
