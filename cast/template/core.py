import os
import pathlib

from cast import exceptions, conform
from cast.template import registry


class Template:
    def __init__(self, name):
        if not exists(name):
            raise exceptions.TemplateNotFoundError(name)
        self.name = name

    @classmethod
    def all(cls):
        names = registry.all_template_names()
        return tuple(map(cls, names))

    @classmethod
    def for_instance(cls, path):
        path = os.path.abspath(path)
        for t in cls.all():
            if path in t.instances:
                return t
        return None

    @classmethod
    def for_path(cls, path):
        path = pathlib.Path(path).resolve()
        result = []
        for t in cls.all():
            for root in t.instances:
                parents = map(os.path.abspath, path.parents)
                if os.path.abspath(root) == os.path.abspath(path) or root in parents:
                    result.append(t)
        return result

    def __iter__(self):
        yield from self.instances

    @property
    def path(self):
        """

        :rtype: pathlib.Path
        """
        return registry.template_path(self.name)

    @property
    def hash(self):
        """

        :rtype: str
        """
        return registry.template_config(self.name)['hash']

    @property
    def instances(self):
        """

        :rtype: list[str]
        """
        return registry.template_config(self.name)['instances']

    def __eq__(self, other):
        return self.name == other.name


def isinstance_(dir_path, name):
    return os.path.abspath(dir_path) in Template(name).instances


def exists(name):
    return name in registry.all_template_names()


class Status:

    def __init__(self, name):
        self.template = Template(name)

    def __iter__(self):
        for path in self.template.instances:
            yield path, self[path]

    def __getitem__(self, item):
        conformed = conform.is_conformed(item, self.template.path)
        registered = isinstance_(item, self.template.name)
        template_ok = self.hash_status()
        if template_ok == 'NOT OK':
            return 'UNKNOWN'
        elif conformed and registered:
            return 'OK'
        elif conformed:
            return 'UNREGISTERED'
        else:
            return 'NOT OK'

    def conformity_status(self):
        if all(st == 'OK' for _, st in self):
            return 'OK'
        else:
            return 'NOT OK'

    def hash_status(self):
        ok = self.template.hash == registry.template_hash(name=self.template.name)
        return 'OK' if ok else 'NOT OK'

    @classmethod
    def of_instance(cls, path):
        template = Template.for_instance(path)
        if template:
            return cls(template.name)[path]
        else:
            return "UNREGISTERED"
