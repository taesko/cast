"""
Module wrapper of the watchdog lib.
"""

import watchdog.observers
import watchdog.events


Observer = watchdog.observers.Observer
FileSystemEventHandler = watchdog.events.FileSystemEventHandler

FileSystemEvent = watchdog.events.FileSystemEvent
DirCreatedEvent = watchdog.events.DirCreatedEvent
FileCreatedEvent = watchdog.events.FileCreatedEvent
DirDeletedEvent = watchdog.events.DirDeletedEvent
FileDeletedEvent = watchdog.events.FileDeletedEvent
DirMovedEvent = watchdog.events.DirMovedEvent
FileMovedEvent = watchdog.events.FileMovedEvent
DirModifiedEvent = watchdog.events.DirModifiedEvent
FileModifiedEvent = watchdog.events.FileModifiedEvent


#  class FileSystemEventHandler(watchdog.FileSystemEventHandler):
#      def __init__(
#          self,
#          on_any_event=None,
#          on_created=None,
#          on_deleted=None,
#          on_modified=None,
#          on_moved=None
#      ):
#          super().__init__()
#          self.on_any_event = on_any_event
#          self.on_created = on_created
#          self.on_deleted = on_deleted
#          self.on_modified = on_modified
#          self.on_moved = on_moved
#
#      def on_any_event(self):
#          if self.on_any_event:
#              self.on_any_event
#          else:
#              super().on_any_event()
#
#      def on_created(self):
#          if self.on_created:
#              self.on_created
#          else:
#              super().on_created()
#
#      def on_deleted(self):
#          if self.on_deleted:
#              self.on_deleted
#          else:
#              super().on_deleted()
#
#      def on_modified(self):
#          if self.on_modified:
#              self.on_modified
#          else:
#              super().on_modified()
#
#      def on_moved(self):
#          if self.on_moved:
#              self.on_moved
#          else:
#              super().on_moved()
