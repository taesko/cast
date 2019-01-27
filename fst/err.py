class FSTErr(Exception):
    pass


class UserError(FSTErr):
    def __init__(self, msg, code):
        super().__init__(msg)
        self.msg = msg
        self.code = code


class SysError(FSTErr):
    def __init__(self, msg, code):
        super().__init__(msg, code)
        self.msg = msg
        self.code = code


def assert_user(condition, msg, code, from_exc=None):
    if not condition:
        err = UserError(msg=msg, code=code)
        if from_exc:
            raise err from from_exc
        else:
            raise err


def assert_system(condition, msg, code):
    if not condition:
        err = SysError(msg=msg, code=code)
        if from_exc:
            raise err from from_exc
        else:
            raise err
