class CastError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


class NotConformedDirError(CastError):
    def __init__(self, directory, template):
        msg = "directory {!r} is not conformed to template {}".format(directory, template)
        super().__init__(msg)
        self.dir_path = directory
        self.template = template


class TemplateError(CastError):
    pass


class TemplateExistsError(TemplateError):
    def __init__(self, template_name):
        msg = "template with name {} already exists".format(template_name)
        super().__init__(msg)
        self.template_name = template_name


class TemplateNotFoundError(TemplateError):
    def __init__(self, template_name):
        msg = "template with name {} doesn't exist".format(template_name)
        super().__init__(msg)
        self.template_name = template_name
