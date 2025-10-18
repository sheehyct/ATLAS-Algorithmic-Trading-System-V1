---
title: Installation
description: Learn how to install VectorBT PRO
---

# Installation

!!! info
    VectorBT® PRO is entirely different from the [open-source version](https://github.com/polakowo/vectorbt).

    In fact, the PRO version overhauls the core to support groundbreaking features.

    To avoid importing outdated code, make sure to import **vectorbtpro** only!

??? youtube "MacOS Installation Guide on YouTube"
    <iframe class="youtube-video" src="https://www.youtube.com/embed/lFmeqhFwH3M?si=2vNVrZu4Q1_hdoBd" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

??? youtube "Windows Installation Guide on YouTube"
    <iframe class="youtube-video" src="https://www.youtube.com/embed/bN5BOOb4Yd4?si=YeIo5p-ADMJhwzKm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

??? youtube "Linux Installation Guide on YouTube"
    <iframe class="youtube-video" src="https://www.youtube.com/embed/TjsFsxuWY4I?si=lXtGhlEq1czCOeWT" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

## Requirements

### Authentication

#### Option 1: Token

After being added as a collaborator and accepting the repository invitation, your next step is to
create a [Personal Access Token] for your GitHub account. This allows you to access the PRO repository
programmatically, such as from the command line or in GitHub Actions workflows:

1. Go to https://github.com/settings/tokens.
2. Click on [Generate a new token (classic)].
3. Enter a name (for example, "terminal").
4. Set the expiration to a fixed number of days.
5. Select the [`repo`][scopes] scope.
6. Generate the token and save it in a secure location.

    [Personal Access Token]: https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token
    [Generate a new token]: https://github.com/settings/tokens/new
    [scopes]: https://docs.github.com/en/developers/apps/scopes-for-oauth-apps#available-scopes

!!! important
    After a few months, GitHub may send you an email notifying you that your personal access
    token has expired. If this happens, simply follow the steps above to generate a new token.
    This is unrelated to your membership status!

#### Option 2: Credential Manager

Alternatively, you can use [Git Credential Manager](https://github.com/git-ecosystem/git-credential-manager)
instead of creating a personal access token.

!!! note
    Git Credential Manager only works with HTTPS.

### Git

If you do not have Git, [install it](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git).

### TA-Lib

To use TA-Lib *locally*, you need to install the actual library.
Follow [these instructions](https://github.com/mrjbq7/ta-lib#dependencies).

!!! hint
    If you encounter issues installing TA-Lib, or if you do not need it for your work, you can also
    install vectorbtpro [without TA-Lib](#without-ta-lib).

## Recommendations

!!! tip
    Creating a local environment is a great option for development because it gives you full control,
    better performance, and access to native tooling.

    However, if you have trouble setting it up or want to try vectorbtpro quickly and safely, you can
    either build the supplied [Docker container](#with-docker) or run vectorbtpro directly in
    [Google Colab](#google-colab).

The following recommendations apply only to local installations.

### Windows

If you are using Windows, it is recommended to use [WSL](https://learn.microsoft.com/en-us/windows/wsl/setup/environment)
for development.

### New environment

If you plan to use vectorbtpro locally, it is best to create a new environment dedicated to vectorbtpro.

#### Option 1: uv

The easiest way to get started is to install [uv](https://github.com/astral-sh/uv), a lightning-fast
package manager that handles virtual environments and dependency resolution in one tool.

First, install `uv`:

=== "Linux/macOS"

    ```shell
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "macOS (Homebrew)"

    ```shell
    brew install uv
    ```

=== "Windows"

    ```shell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

=== "pipx (cross-platform)"

    ```shell
    pipx install uv
    ```

After installing `uv`, create a new isolated environment (similar to a conda environment) for your project:

```shell
uv venv vectorbtpro --python 3.12
```

This creates a virtual environment named `vectorbtpro` located in the current directory. Now, activate it:

=== "Linux/macOS"

    ```shell
    source vectorbtpro/bin/activate
    ```

=== "Windows"

    ```shell
    vectorbtpro\Scripts\activate
    ```

!!! note
    You need to activate the environment each time you start a new terminal session.

To check you're in the correct environment, your terminal prompt should now be prefixed with `(vectorbtpro)`.

That's it! You're using `uv` to manage environments and install packages with speed and simplicity.

#### Option 2: Conda

Another easy option is to [download Anaconda](https://www.anaconda.com/download), which provides a
graphical installer and includes many popular data science packages required by vectorbtpro, such as
NumPy, Pandas, Plotly, and more.

After installing Anaconda, [create a new environment](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands):

```shell
conda create --name vectorbtpro python=3.12
```

[Activate the new environment](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#activating-an-environment):

```shell
conda activate vectorbtpro
```

!!! note
    You need to activate the environment each time you start a new terminal session.

You should now see `vectorbtpro` in the list of all environments, and it should be active (notice the `*`):

```shell
conda info --envs
```

You are now ready to install the actual package.

#### Option 3: IDE

If you primarily use an IDE, you can create a separate environment for each project:

* [PyCharm](https://www.jetbrains.com/help/pycharm/configuring-python-interpreter.html).
* [Visual Studio Code](https://code.visualstudio.com/docs/python/environments).

## With pip

The PRO version can be installed using `pip`.

!!! hint
    It is highly recommended to create a new virtual environment dedicated to vectorbtpro, such as one
    made with [Anaconda](https://www.anaconda.com/).

Uninstall the open-source version if it is already installed:

```shell
pip uninstall VBT
```

### HTTPS

Install the base PRO version (with recommended dependencies) using `git+https`:

=== "uv"

    ```shell
    uv pip install -U "vectorbtpro[base] @ git+https://github.com/polakowo/vectorbt.pro.git"
    ```

=== "pip"

    ```shell
    pip install -U "vectorbtpro[base] @ git+https://github.com/polakowo/vectorbt.pro.git"
    ```

!!! info
    This process may require at least 1GB of disk space and take several minutes to finish.
    
!!! hint
    Whenever you are prompted for a password, paste the token that you generated earlier.

    To avoid entering the token repeatedly, you can
    [add it to your system](https://stackoverflow.com/a/68781050)
    or set an environment variable `GH_TOKEN`, then install the package as follows:

    === "uv"

        ```shell
        uv pip install -U "vectorbtpro[base] @ git+https://${GH_TOKEN}@github.com/polakowo/vectorbt.pro.git"
        ```

    === "pip"

        ```shell
        pip install -U "vectorbtpro[base] @ git+https://${GH_TOKEN}@github.com/polakowo/vectorbt.pro.git"
        ```

    On some systems, such as macOS, the token is often remembered automatically.

    Learn more about managing tokens [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

#### Without TA-Lib

To install the base version without TA-Lib:

=== "uv"

    ```shell
    uv pip install -U "vectorbtpro[base-no-talib] @ git+https://github.com/polakowo/vectorbt.pro.git"
    ```

=== "pip"

    ```shell
    pip install -U "vectorbtpro[base-no-talib] @ git+https://github.com/polakowo/vectorbt.pro.git"
    ```

#### Lightweight

To install the lightweight version (with only required dependencies):

=== "uv"

    ```shell
    uv pip install -U git+https://github.com/polakowo/vectorbt.pro.git
    ```

=== "pip"

    ```shell
    pip install -U git+https://github.com/polakowo/vectorbt.pro.git
    ```

For more optional dependencies, see [pyproject.toml](https://github.com/polakowo/vectorbt.pro/blob/main/pyproject.toml).

### SSH

To install the base version with `git+ssh`:

=== "uv"

    ```shell
    uv pip install -U "vectorbtpro[base] @ git+ssh://git@github.com/polakowo/vectorbt.pro.git"
    ```

=== "pip"

    ```shell
    pip install -U "vectorbtpro[base] @ git+ssh://git@github.com/polakowo/vectorbt.pro.git"
    ```

See [Connecting to GitHub with SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh).

### Updating

When a new version of vectorbtpro is released, the package __will not__ update automatically. You
will need to install the new version manually. Fortunately, you can use the exact same command you
used to install the package to update it.

### Specific branch

Append `@` followed by [a branch name](https://github.com/polakowo/vectorbt.pro/branches/all) to the command.

For example, to install the `develop` branch:

=== "uv"

    ```shell
    uv pip install -U "vectorbtpro[base] @ git+https://github.com/polakowo/vectorbt.pro.git@develop"
    ```

=== "pip"

    ```shell
    pip install -U "vectorbtpro[base] @ git+https://github.com/polakowo/vectorbt.pro.git@develop"
    ```

!!! note
    If you have the latest regular version installed, you must uninstall it first:

    === "uv"

        ```shell
        uv pip uninstall vectorbtpro
        ```

    === "pip"

        ```shell
        pip uninstall vectorbtpro
        ```

### Specific release

Append `@` followed by [a release name](https://github.com/polakowo/vectorbt.pro/releases) to the command.

For example, to install the release `v2024.1.30`:

=== "uv"

    ```shell
    uv pip install "vectorbtpro[base] @ git+https://github.com/polakowo/vectorbt.pro.git@v2024.1.30"
    ```

=== "pip"

    ```shell
    pip install "vectorbtpro[base] @ git+https://github.com/polakowo/vectorbt.pro.git@v2024.1.30"
    ```

### As Python dependency

With [setuptools](https://setuptools.readthedocs.io/en/latest/), you can add vectorbtpro as a dependency
to your Python package by listing it in `setup.py` or in your
[requirements files](https://pip.pypa.io/en/latest/user_guide/#requirements-files):

```python
# setup.py
setup(
    # ...
    install_requires=[
        "vectorbtpro @ git+https://github.com/polakowo/vectorbt.pro.git"
    ]
    # ...
)
```

## With git

You can also clone vectorbtpro directly from Git:

=== "HTTPS"

    ```shell
    git clone https://github.com/polakowo/vectorbt.pro.git vectorbtpro
    ```

=== "SSH"

    ```shell
    git clone git@github.com:polakowo/vectorbt.pro.git vectorbtpro
    ```

Install the package:

=== "uv"

    ```shell
    uv pip install -e vectorbtpro
    ```

=== "pip"

    ```shell
    pip install -e vectorbtpro
    ```

### Shallow clone

The command above takes about 1GB of disk space. To create a shallow clone:

=== "HTTPS"

    ```shell
    git clone https://github.com/polakowo/vectorbt.pro.git vectorbtpro --depth=1
    ```

=== "SSH"

    ```shell
    git clone git@github.com:polakowo/vectorbt.pro.git vectorbtpro --depth=1
    ```

To convert the clone back into a complete one:

```shell
git pull --unshallow
```

## With Docker

Using [Docker](https://www.docker.com/) is an excellent way to get started in just a few minutes, as it
includes all dependencies pre-installed.

### JupyterLab

[This Docker image](https://github.com/polakowo/vectorbt.pro/blob/main/Dockerfile.jupyter) is based on
[Jupyter Docker Stacks](https://jupyter-docker-stacks.readthedocs.io/en/latest/), a collection of
ready-to-run Docker images that include Jupyter applications and interactive computing tools.
Specifically, the image builds on [jupyter/scipy-notebook](https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-scipy-notebook),
which includes a minimally-functional JupyterLab server and preinstalled popular packages from the
scientific Python ecosystem. It also extends the image with Plotly and Dash for interactive visualizations
and plots, as well as vectorbtpro and all of its optional dependencies. The image requires the vectorbtpro
source to be present in the current directory.

Before proceeding, make sure to [install Docker](https://docs.docker.com/install/).

Start Docker using Docker Desktop.

#### Building

Clone the vectorbtpro repository if you have not already. Run this command from the directory where you
want vectorbtpro to be located, such as in Documents/GitHub:

```shell
git clone git@github.com:polakowo/vectorbt.pro.git vectorbtpro --depth=1
```

Enter the directory:

```shell
cd vectorbtpro
```

Build the image (this may take some time):

```shell
docker build . -t vectorbtpro
```

Create a working directory inside the current directory:

```shell
mkdir work
```

#### Running

Start a container running a JupyterLab server on port 8888:

```shell
docker run -it --rm -p 8888:8888 -v "$PWD/work":/home/jovyan/work vectorbtpro
```

!!! info
    The `-v` flag in this command mounts the working directory on the host (`{PWD/work}` in the example)
    as `/home/jovyan/work` in the container. The server logs will appear in the terminal. The
    [--rm flag](https://docs.docker.com/engine/reference/run/#clean-up---rm) tells Docker to
    automatically clean up the container and remove the file system when the container exits. However,
    any changes made to the `~/work` directory and its files inside the container will remain on the host.
    The [-it flag](https://docs.docker.com/engine/reference/commandline/run/#assign-name-and-allocate-pseudo-tty---name--it)
    allocates a pseudo-TTY.

If port 8888 is already in use, you can specify a different port (for example, 10000):

```shell
docker run -it --rm -p 10000:8888 -v "$PWD/work":/home/jovyan/work vectorbtpro
```

Once the server has started, go to its address in a browser. The address will be printed in the console,
for example: `http://127.0.0.1:8888/lab?token=9e85949d9901633d1de9dad7a963b43257e29fb232883908`

!!! note
    Change the port if needed.

This will open JupyterLab, where you can create a new notebook and start working with vectorbtpro :tada:

To use files from your host, place them into the `work` directory on your host, and they will appear in the
JupyterLab file browser. Alternatively, you can drag and drop files directly into the JupyterLab file browser.

#### Stopping

To stop the container, first press ++ctrl+c++, and then when prompted, type `y` and press ++enter++.

#### Updating

To upgrade the Docker image to a new version of vectorbtpro, first update your local repository from the remote:

```shell
git pull
```

Then rebuild the image:

```shell
docker build . -t vectorbtpro
```

!!! info
    This will not rebuild the entire image, only the vectorbtpro installation step.

### Development

[This Docker image](https://github.com/polakowo/vectorbt.pro/blob/main/Dockerfile.dev) is recommended for
development with Visual Studio Code, PyCharm (Professional), and remote connections. It includes
vectorbtpro and all optional dependencies. The image requires the vectorbtpro source to be present
in the current directory.

#### Visual Studio Code

This image also allows you to start developing right away in Visual Studio Code, without manually setting up
Python, Jupyter, or any dependencies.

Make sure you have the following installed:

* [Docker](https://docs.docker.com/install/)
* [Visual Studio Code](https://code.visualstudio.com/)
* [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

Clone the repository if you have not already:

```shell
git clone git@github.com:polakowo/vectorbt.pro.git vectorbtpro --depth=1
```

Open the repository in Visual Studio Code.

When prompted, click "Reopen in Container".

!!! hint
    If you do not see the prompt, open the Command Palette (++ctrl+shift+p++) and
    run "Dev Containers: Reopen in Container".

Visual Studio Code will:

* Build the Docker image using `Dockerfile.dev`.
* Mount your project at `/workspace`.
* Install the required Python and Jupyter extensions.
* Set up a ready-to-use environment for development and notebooks.

## Google Colab

[:material-notebook-outline: Notebook](https://colab.research.google.com/drive/1A9RxtYgGkUT_NbRxp3Z8h-fTRnVR3WRa?usp=sharing){ .md-button target="blank_" }

## Manually

If you experience connectivity issues, you can also install the package manually:

1. Go to https://github.com/polakowo/vectorbt.pro.
2. Click the `Code` dropdown button and then click "Download ZIP".
3. Unzip the downloaded archive.
4. Open the unzipped folder using your terminal.
5. Install the package using pip:

=== "uv"

    ```shell
    uv pip install ".[base]"
    ```

=== "pip"

    ```shell
    pip install ".[base]"
    ```

### Custom release

To install a custom release:

1. Go to https://github.com/polakowo/vectorbt.pro/releases.
2. Select a release.
3. Download the file with the `.whl` suffix.
4. Open the folder containing the wheel file using your terminal.
5. Install the wheel using pip:

=== "uv"

    ```shell
    uv pip install wheel
    uv pip install "filename.whl[base]"
    ```

=== "pip"

    ```shell
    pip install wheel
    pip install "filename.whl[base]"
    ```

Replace `filename` with the actual file name.

!!! note
    If the file name ends with (1) because there is already a file with the same name,
    make sure to remove the previous file and remove the (1) suffix from the newer one.

## Troubleshooting

* [TA-Lib](https://github.com/mrjbq7/ta-lib#dependencies)
* [Jupyter Notebook and JupyterLab](https://plotly.com/python/getting-started/#jupyter-notebook-support)
* [Apple M1](https://github.com/polakowo/vectorbt/issues/320)
* ["fatal error: 'H5public.h' file not found"](https://stackoverflow.com/a/71340786)
* ["RuntimeError: CMake must be installed to build qdldl"](https://github.com/robertmartin8/PyPortfolioOpt/issues/274#issuecomment-1551221810)
* ["AttributeError: 'ZMQInteractiveShell' object has no attribute 'magic'"](https://github.com/polakowo/vectorbt/issues/779#issuecomment-2724967944)
* pybind11:

If you receive the error "ModuleNotFoundError: No module named 'pybind11'",
install `pybind11` before installing vectorbtpro:

=== "uv"

    ```shell
    uv pip install pybind11
    ```

=== "pip"

    ```shell
    pip install pybind11
    ```

* llvmlite:

If you receive the error "Cannot uninstall 'llvmlite'", install `llvmlite`
before installing vectorbtpro:

=== "uv"

    ```shell
    uv pip install --ignore-installed 'llvmlite'
    ```

=== "pip"

    ```shell
    pip install --ignore-installed 'llvmlite'
    ```

* Plotly:

If image generation hangs (for example, when calling `show_svg()`), downgrade the Kaleido package:

=== "uv"

    ```shell
    uv pip install kaleido==0.1.0post1
    ```

=== "pip"

    ```shell
    pip install kaleido==0.1.0post1
    ```

* osqp:

If you are on a Mac and encounter an error during the installation of the osqp package, install `cmake`:

```shell
brew install cmake
```