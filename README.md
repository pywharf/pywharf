<div align="center">

![logo-large 72ad8bf1](https://user-images.githubusercontent.com/5213906/77421237-6d402180-6e06-11ea-89c1-915cd747660a.png)

# Private PyPI

**The private PyPI server powered by flexible backends.**

[![build-and-push](https://github.com/private-pypi/private-pypi/workflows/build-and-push/badge.svg)](https://github.com/private-pypi/private-pypi/actions?query=workflow%3Abuild-and-push)
[![license](https://img.shields.io/github/license/private-pypi/private-pypi)](https://github.com/private-pypi/private-pypi/blob/master/LICENSE)

</div>

* [Private PyPI](#Private-PyPI)
	* [What is it?](#What-is-it?)
	* [Design](#Design)
	* [Usage](#Usage)
		* [Install from PyPI](#Install-from-PyPI)
		* [Using the docker image (recommended)](#Using-the-docker-image-(recommended))
		* [Run the server](#Run-the-server)
		* [Server API](#Server-API)
		* [Update index](#Update-index)
		* [Backend-specific commands](#Backend-specific-commands)
		* [Environment mode](#Environment-mode)
	* [Backends](#Backends)
		* [GitHub](#GitHub)
		* [File system](#File-system)

------

## What is it?

`private-pypi` allows you to deploy a PyPI server privately and keep your artifacts safe by leveraging the power (confidentiality, integrity and availability) of your storage backend. The backend mechanism is designed to be flexible so that the developer could support a new storage backend at a low cost.

Supported backends:

- GitHub. (Yes, you can now host your Python package in GitHub by using `private-pypi`. )
- File system.
- ... (*Upcoming*)

## Design

<div align="center"><img width="766" alt="Screen Shot 2020-03-24 at 8 19 12 PM" src="https://user-images.githubusercontent.com/5213906/77424853-c14e0480-6e0c-11ea-9a7f-879a68ada0a0.png"></div>

The `private-pypi` server serves as an abstraction layer between Python package management tools (pip/poetry/twine) and the storage backends:

* Package management tools communicate with `private-pypi` server, following [PEP 503 -- Simple Repository API](https://www.python.org/dev/peps/pep-0503/) for searching/downloading package, and [Legacy API](https://warehouse.pypa.io/api-reference/legacy/#upload-api) for uploading package.
* `private-pypi` server  then performs file search/download/upload operations with some specific storage backend.

## Usage

### Install from PyPI

```shell
pip install private-pypi==0.1.0a17
```

This should bring the execuable `private_pypi` to your environment.

```shell
$ private_pypi --help
SYNOPSIS
    private_pypi <command> <command_flags>

SUPPORTED COMMANDS
    server
    update_index
    github.init_pkg_repo
    github.gen_gh_pages
```

### Using the docker image (recommended)

Docker image: `privatepypi/private-pypi:0.1.0a17`. The image tag is the same as the package version in PyPI.

```shell
$ docker run --rm privatepypi/private-pypi:0.1.0a17 --help
SYNOPSIS
    private_pypi <command> <command_flags>

SUPPORTED COMMANDS
    server
    update_index
    github.init_pkg_repo
    github.gen_gh_pages
```

### Run the server

To run the server, use the command `private_pypi server`.

```txt
SYNOPSIS
    private_pypi server ROOT <flags>

POSITIONAL ARGUMENTS
    ROOT (str):
        Path to the root folder. This folder is for logging,
        file-based lock and any other file I/O.

FLAGS
    --config (Optional[str]):
        Path to the package repository config (TOML),
        or the file content if --config_or_admin_secret_can_be_text is set.
        Default to None.
    --admin_secret (Optional[str]):
        Path to the admin secrets config (TOML) with read/write permission.
        or the file content if --config_or_admin_secret_can_be_text is set.
        This field is required for local index synchronization.
        Default to None.
    --config_or_admin_secret_can_be_text (Optional[bool]):
        Enable passing the file content to --config or --admin_secret.
        Default to False.
    --auth_read_expires (int):
        The expiration time (in seconds) for read authentication.
        Default to 3600.
    --auth_write_expires (int):
        The expiration time (in seconds) for write authentication.
        Default to 300.
    --extra_index_url (str):
        Extra index url for redirection in case package not found.
        If set to empty string explicitly redirection will be suppressed.
        Default to 'https://pypi.org/simple/'.
    --debug (bool):
        Enable debug mode.
        Default to False.
    --host (str):
        The interface to bind to.
        Default to '0.0.0.0'.
    --port (int):
        The port to bind to.
        Default to 8888.
    **waitress_options (Dict[str, Any]):
        Optional arguments that `waitress.serve` takes.
        Details in https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html.
        Default to {}.
```

In short, the configuration passed to `--config` defines mappings from `pkg_repo_name` to backend-specific settings. In other words, a single server instance can be configured to connect to multiple backends.

Exampe of the configuration file passed to `--config`:

```toml
[private-pypi-pkg-repo]
type = "github"
owner = "private-pypi"
repo = "private-pypi-pkg-repo"

[local-file-system]
type = "file_system"
read_secret = "foo"
write_secret = "bar"
```

Exampe of the admin secret file passed to `--admin_secret`:

```toml
[private-pypi-pkg-repo]
type = "github"
raw = "<personal-access-token>"

[local-file-system]
type = "file_system"
raw = "foo"
```

Example run:

```shell
docker run --rm \
		-v /path/to/root:/private-pypi-root \
		-v /path/to/config.toml:/config.toml \
		-v /path/to/admin_secret.toml:/admin_secret.toml \
		-p 8888:8888 \
		privatepypi/private-pypi:0.1.0a17 \
		server \
		/private-pypi-root \
		--config=/config.toml \
		--admin_secret=/admin_secret.toml
```

### Server API

#### Authentication in shell

User must provide the `pkg_repo_name` and their secret in most of the API calls so that the server can find which backend to operate and determine whether the operation is permitted or not. The `pkg_repo_name` and the secret should be provided in [basic access authentication](https://en.wikipedia.org/wiki/Basic_access_authentication).

Some package management tools will handle the authentication behind the screen, for example,

* Twine: to set the environment variables `TWINE_USERNAME` and `TWINE_PASSWORD`. [ref](https://github.com/pypa/twine#environment-variables)
* Poetry: [Configuring credentials](https://python-poetry.org/docs/repositories/#configuring-credentials).

Some will not, for example,

* Pip: you need to prepend  `<pkg_repo_name>:<secret>@` to the hostname in the URL manually like this `https://[username[:password]@]pypi.company.com/simple`. [ref](https://pip.pypa.io/en/stable/user_guide/#basic-authentication-credentials)

#### Authentication in browser

You need to visit `/login` page to submit `pkg_repo_name` and the secret, since most of the browsers today don't support prepending `<username>:<password>@` to the hostname in the URL. The `pkg_repo_name` and the secret will be stored in the session cookies. To reset, visit `/logout` .

Example: `http://localhost:8888/login/`

<div align="center"><img width="600" alt="Screen Shot 2020-03-25 at 12 36 03 PM" src="https://user-images.githubusercontent.com/5213906/77502233-40871b00-6e95-11ea-8ac9-4844d7067ed2.png"></div>


#### PEP-503, Legacy API

The server follows [PEP 503 -- Simple Repository API](https://www.python.org/dev/peps/pep-0503/) and [Legacy API](https://warehouse.pypa.io/api-reference/legacy/#upload-api) to define APIs for searching/downloading/uploading package:

* `GET /simple/`: List all distributions.
* `GET /simple/<distrib>/`: List all packages in a distribution.
* `GET /simple/<distrib>/<filename>`: Download a package file.
* `POST /simple/`: Upload a package file.

In a nutshell, you need to set the "index url / repository url / ..." to `http://<host>:<port>/simple/` for the package management tool.

#### Private PyPI server management

##### `GET /index_mtime`

Get the last index index synchronization timestamp.

```shell
$ curl http://debug:foo@localhost:8888/index_mtime/
1584379892
```

##### `POST /initialize`

Submit configuration and (re-)initialize the server. User can change the package repository configuration on-the-fly with this API.

```shell
# POST the file content.
$ curl \
    -d "config=${CONFIG}&admin_secret=${ADMIN_SECRET}" \
    -X POST \
    http://localhost:8888/initialize/

# Or, POST the file.
$ curl \
    -F 'config=@/path/to/config.toml' \
    -F 'admin_secret=@/path/to/admin_secret.toml' \
    http://localhost:8888/initialize/
```

### Update index

<div align="center"><img width="636" alt="Screen Shot 2020-03-25 at 5 39 19 PM" src="https://user-images.githubusercontent.com/5213906/77522697-9a043f80-6ebf-11ea-95e6-9a086db7af2e.png"></div>

Index file is used to track all published packages in a specific time:

* *Remote index file*: the index file sotred in the backend. By design, this file is only updated by a standalone `update index` service and will not be updated by the `private-pypi` server.
* *Local index file*: the index file synchronized from the remote index file by the `private-pypi` server

To update the remote index file, use the command `private_pypi update_index`:

```txt
SYNOPSIS
    private_pypi update_index TYPE NAME <flags>

POSITIONAL ARGUMENTS
    TYPE (str):
        Backend type.
    NAME (str):
        Name of config.

FLAGS
    --secret (Optional[str]):
        The secret with write permission.
    --secret_env (Optional[str]):
        Instead of passing the secret through --secret,
        the secret could be loaded from the environment variable.
    **pkg_repo_configs (Dict[str, Any]):
        Any other backend-specific configs are allowed.
```

Backend developer could setup an `update index` service by invoking  `private_pypi update_index` command.

### Backend-specific commands

The backend registration mechanism will hook up the backend-specific commands to `private_pypi`. As illustrated, commands `github.init_pkg_repo` and `github.gen_gh_pages` are registered by `github` backend.

```shell
$ private_pypi --help
SYNOPSIS
    private_pypi <command> <command_flags>

SUPPORTED COMMANDS
    server
    update_index
    github.init_pkg_repo
    github.gen_gh_pages
```

### Environment mode

If no argument is passed, `private_pypi` will try to load the arguments from the environment variables. This mode would be helpful if passing argument in shell is not possible.

The format:

- `PRIVATE_PYPI_COMMAND`: to set `<command>`.
- `PRIVATE_PYPI_COMMAND_<FLAG>`: to set the flag of `<command>`.

## Backends

### GitHub

#### Introduction

`private-pypi` will help you setup a new GitHub repository to host your package. You package will be published as repository release and secured by personal access token. Take https://github.com/private-pypi/private-pypi-pkg-repo and https://private-pypi.github.io/private-pypi-pkg-repo/ as an example.

#### Configuration and secret

Package repository configuration of GitHub backend:

- `type`: must set to `github`.
- `owner`: repository owner.
- `repo`: repository name.
- `branch` (optional): the branch to store the remote index file. Default to `master`.
- `index_filename` (optional): the name of remote index file. Default to `index.toml`.
- `max_file_bytes` (optional): limit the maximum size (in bytes) of package. Default to `2147483647` since *each file included in a release must be under 2 GB*, [as restricted by GitHub](https://help.github.com/en/github/administering-a-repository/about-releases#storage-and-bandwidth-quotas) .
- `sync_index_interval` (optional): the sleep time interval (in seconds) before taking the next local index file synchronization. Default to `60`.

Example configuration of https://github.com/private-pypi/private-pypi-pkg-repo:

```toml
[private-pypi-pkg-repo]
type = "github"
owner = "private-pypi"
repo = "private-pypi-pkg-repo"
```

The GitHub backend accepts [personal access token](https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line) as the repository secret. The `private-pypi` server calls GitHub API with PAT to operate on packages. You can authorize user with read or write permission based on [team role](https://help.github.com/en/github/setting-up-and-managing-organizations-and-teams/repository-permission-levels-for-an-organization).

#### Initialize the repository

To initialize a GitHub repository as the storage backend, run the command `github.init_pkg_repo`:

```shell
docker run --rm privatepypi/private-pypi:0.1.0a17 \
    github.init_pkg_repo \
    --name private-pypi-pkg-repo \
    --owner private-pypi \
    --repo private-pypi-pkg-repo \
    --token <personal-access-token>
```

This will:

- Create a new repository `<owner>/<repo>`.
- Setup the GitHub workflow to update the remote index file if new package is published.
- Print the configuration for you.

If you want to host the index in GitHub page, like https://private-pypi.github.io/private-pypi-pkg-repo/, add `--enable_gh_pages` to command execution.

#### GitHub workflow integration

To use `private-pypi` with GitHub workflow, take [thie main.yml](https://github.com/private-pypi/private-pypi/blob/master/.github/workflows/main.yml) as an example.

Firstly, run the server as job service:

```yaml
services:
  private-pypi:
    image: privatepypi/private-pypi:0.1.0a17
    ports:
      - 8888:8888
    volumes:
      - private-pypi-root:/private-pypi-root
    env:
      PRIVATE_PYPI_COMMAND: server
      PRIVATE_PYPI_COMMAND_ROOT: /private-pypi-root
```

Secondly, initialize the server with configuration and admin secret (Note: remember to [add the admin secret to your repository](https://help.github.com/en/actions/configuring-and-managing-workflows/creating-and-storing-encrypted-secrets) before using it):

```yaml
steps:
  - name: Setup private-pypi
  run: |
    curl \
        -d "config=${CONFIG}&admin_secret=${ADMIN_SECRET}" \
        -X POST \
        http://localhost:8888/initialize/
  env:
    CONFIG: |
      [private-pypi-pkg-repo]
      type = "github"
      owner = "private-pypi"
      repo = "private-pypi-pkg-repo"
    ADMIN_SECRET: |
      [private-pypi-pkg-repo]
      type = "github"
      raw = "${{ secrets.PRIVATE_PYPI_PKG_REPO_TOKEN }}"
```

Afterward, set `http://localhost:8888/simple/` as the repository url, and you are good to go.

### File system

#### Introduction

You can configure this backend to host the packages in the local file system.

#### Configuration and secret

Package repository configuration of GitHub backend:

- `type`: must set to `file_system`.
- `read_secret`: defines the secret with read only permission.
- `write_secret`: defines the secret with write permission.
- `max_file_bytes` (optional): limit the maximum size (in bytes) of package. Default to `5368709119` (5 GB).
- `sync_index_interval` (optional): the sleep time interval (in seconds) before taking the next local index file synchronization. Default to `60`.

Example configuration:

```toml
[local-file-system]
type = "file_system"
read_secret = "foo"
write_secret = "bar"
```

To use the API, user must provide either `read_secret` or `write_secret`.

#### Initialize the package repository

A folder will be created automatically to store the packages, with the path `<ROOT>/cache/<pkg_repo_name>/storage`.