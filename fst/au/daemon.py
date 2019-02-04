import grp
import pwd
import os
import os.path
import time
import signal


import fst.au.watch
import fst.db
import fst.tmpl
import fst.trace
from fst.config import CONFIG


class TemplateEventHandler(fst.au.watch.FileSystemEventHandler):
    def __init__(self, template, instances):
        self.template = template
        self.instances = instances

    def on_any_event(self, event):
        fst.trace.info(
            "In template:%s occurred event:%s",
            self.template["name"],
            event
        )

    def on_created(self, event):
        if isinstance(event, fst.au.watch.FileCreatedEvent):
            fst.trace.warn(
                "In template:%s ignoring event:%s",
                self.template["name"],
                event
            )
            return

        created = event.src_path
        rel_path_in_template = os.path.relpath(created, start=self.template["path"])

        assert os.path.exists(created)

        for i in self.instances.values():
            path_in_instance = os.path.join(
                i["path"],
                rel_path_in_template
            )
            path_in_instance = os.path.abspath(path_in_instance)

            try:
                os.mkdir(path_in_instance)
            except FileExistsError:
                # TODO this should be a config whether it happens
                # and what the suffix/previx will be ?
                os.rename(path_in_instance, path_in_instace + ".moved")
                os.mkdir(path_in_instance)
            except DirExistsError:
                fst.trace.trace(
                    "Directory:%s already exists in instance:%s",
                    path_in_instance,
                    i["path"]
                )
            fst.trace.info(
                "Created directory:%s in instance:%s",
                path_in_instance,
                i["path"]
            )


class Daemon:
    def __init__(self, db_path):
        self.db_path = db_path
        self.event_handlers = []
        self.received_signals = {}
        self.signal_handlers = {
            signal.SIGUSR1: self.reload_templates
        }

        for signum in self.signal_handlers:
            signal.signal(signum, self.immediate_signal_handler)

        try:
            with open(CONFIG['au']['pidfile'], mode='w') as f:
                f.write(str(os.getpid()))
        except BaseException:
            os.remove(CONFIG['au']['pidfile'])
            raise

        self.obersver = None
        self.conn = None

    def cleanup(self):
        os.remove(CONFIG['au']['pidfile'])

    def immediate_signal_handler(self, signum, stackframe):
        self.received_signals[signum] = True

    def reload_templates(self):
        fst.trace.info('Reloading templates from db.')
        self.observer.unschedule_all()
        self.load_template_event_handlers()
        # TODO race condition when an event get's triggered before
        # unschedule_all and get's triggered again before it is handled
        # after load_template_event_handlers

    def load_template_event_handlers(self):
        cursor = self.conn.cursor()
        rels = fst.tmpl.pull_relationships_by_template(cursor)
        for rel in rels.values():
            event_handler = TemplateEventHandler(
                template = rel["template_row"],
                instances = rel["instances"]
            )
            # TODO recompile and restart thread if it dies to due an exception
            self.observer.schedule(event_handler, rel["template_row"]["path"], recursive=True)
            self.event_handlers.append(event_handler)

    def start(self):
        # TODO truly daemonize and use systemd for control
        self.conn = fst.db.connect(self.db_path)
        self.observer = fst.au.watch.Observer()
        self.observer.start()

        try:
            while True:
                time.sleep(1)

                for signum in self.received_signals:
                    if self.received_signals[signum]:
                        self.signal_handlers[signum]()
                        self.received_signals[signum] = False
        finally:
            self.observer.stop()
            self.observer.join()


#Throws OSError exception (it will be thrown when the process is not allowed
#to switch its effective UID or GID):
def drop_privileges():
    if os.getuid() != 0:
        # We're not root so, like, whatever dude
        return

    # Get the uid/gid from the name
    user_name = os.getenv("SUDO_USER")
    pwnam = pwd.getpwnam(user_name)

    # Remove group privileges
    os.setgroups([])

    # Try setting the new uid/gid
    os.setgid(pwnam.pw_gid)
    os.setuid(pwnam.pw_uid)

    #Ensure a reasonable umask
    old_umask = os.umask(0o22)


def start(db_path):
    daemon = Daemon(db_path)
    drop_privileges()
    try:
        daemon.start()
    finally:
        daemon.cleanup()
