import os
import os.path
import time

import fst.au.watch
import fst.db
import fst.tmpl
import fst.trace


class TemplateEventHandler(fst.au.watch.FileSystemEventHandler):
    def __init__(self, template, instances):
        self.template = template
        self.instances = instances

    def on_any_event(self, event):
        fst.trace.info(
            "In template:%s occurred event:%s",
            self.template['name'],
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


def start(db_path):
    # TODO truly daemonize and use systemd for control
    conn = fst.db.connect(db_path)
    cursor = conn.cursor()
    rels = fst.tmpl.pull_relationships_by_template(cursor)

    observer = fst.au.watch.Observer()
    for rel in rels.values():
        event_handler = TemplateEventHandler(
            template = rel['template_row'],
            instances = rel['instances']
        )
        # TODO recompile and restart thread if it dies to due an exception
        observer.schedule(event_handler, rel['template_row']['path'], recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
