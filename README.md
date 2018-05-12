# Cast
> command line app for file system templates.

Cast can modify the structure of multiple directories at once.
Provided these directories are registered for a common template - moving,
renaming or deleting folders from that template will apply those changes
to the directories (called instances of the template).


## Installation

`pip install fscast`

Development version:

```sh
git clone https://github.com/taesko/cast.git
cd cast
pip install .
```

NOTE: This project has only been tested on linux. Installation is no different
on other OS provided git and pip are installed, but it's not guaranteed to
work properly.

## Usage example

Use any existing directory to make a template out of it.
```sh
cast add template_name ./dir_path
```

Register any other directory to that template as it's instance
```sh
cast register template_name /directory/we/want/registered
```

If the directory's structure is not conformed to the template's an
error is raised. That is the instance must contain directories with the same
as the template's. (it is OK for the instance to have other directories as well)


Create additional directories inside a template:
```sh
cast add -m template_name various dir_names dir_names/similar to mkdir arguments
```

Rename a directory inside a template
```sh
cast mv template_name relative_src_path relative_dst_path
```

Remove a directory from a template
```sh
cast rm template_name multiple relative/directory/paths
```

Commands that modify a templates structure all take the name of the
template as a first argument and relative paths (considered from the
root of the template not the current working directory) to the desired
directories as additional arguments. Moving and renaming directories
by default applies the same changes to instances of the template as well
but this is not true for removing directories.

For full information:
```sh
cast --help
```

## Development setup

There is no development branch (yet) and setup is nearly identical to
user installation.
```sh
git clone https://github.com/taesko/cast.git
cd cast
pip install -e .
```

## Release History

* 0.0.2
    * Add proper logging (log file can be found in ~/.cast/logs.txt).
* 0.0.1
    * Work in progress

## Meta

Author: Antonio Todorov – taeskow@gmail.com

Distributed under the MIT license. See ``LICENSE`` for more information.

## Contributing

Fork and submit a pull request.
