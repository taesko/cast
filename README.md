# File System Templates (FST)
> command line app and daemon that provides file system templates.

FST is a tool to manage multiple directories that have a common
structure. It allows modifications of one directory to be propagated to
the others. 

## Usage
In order to manage multiple directories they must first be connecting to a
common parent template - which is just another directory that defines
the structure (subdirectory tree). Multiple different templates are supported.

#### Terminology
template - directory on the file system that serves to provide a common 
	structure for others. Generally has only empty subdirectories inside it.
instance - another directory connected to a template. Instances are 
	regular directories on disk.

#### Example usage
```sh
 mkdir ~/Music/template
 fst -t music -a ~/Music/template/
 mkdir ~/Music/Eminem
 fst -t music -c ~/Music/Eminem/
 fstd
```

The last command `fstd` starts a daemon that watches all template directories
for modifications and does the appropirate updates to the instances.
Register any other directory to that template as it's instance

## Documentation
All of it is here:

```sh
fst --help
```

and here

```sh
fstd --help
```


## Installation

`pip install fst`

Development version:

```sh
git clone https://github.com/taesko/fst.git
cd fst
pip install .
```

NOTE: This project has only been tested on linux. Installation is no different
on other OS provided git and pip are installed, but it's not guaranteed to
work properly.

## Development setup
```sh
git clone https://github.com/taesko/fst.git
cd fst
pip install -e .
```

## Release History

* 0.0.3
	* Project renamed to FST
	* Revamp cli to be much terser and easier to use.
	* Add a seperate daemon for watching templates and making updates.
	* log file moved to ~/.fst.log
* 0.0.2
    * Add proper logging (log file can be found in ~/.cast/logs.txt).
* 0.0.1
    * Work in progress

## Meta

Author: Antonio Todorov – taeskow@gmail.com

Distributed under the MIT license. See ``LICENSE`` for more information.
