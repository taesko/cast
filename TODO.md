==AutoUpdate==
Make updates atomic and consistent
When a template/instance is added while daemon is running reload it from db.
Put events on a queue and execute only one at a time to prevent race conditions.

==fst core==
ability to set files/dirs as ignored and not require them to conform
use a templating language for files and initialize values when creating instances
support for command hooks that will be executed for every instance
cd into a template by name (similarly to workon with virtualenvs)

==system==
Setup systemd service for AU
Move all log files to /var/log
Move DB to /var/lib/fst/
