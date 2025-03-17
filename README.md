# pyhooker

A simple webhook receiver and inspector tool that creates a public URL using ngrok.

## Installation

### Option 1: Install the binary (recommended)

You can install the latest version of PyHooker using our install script:

```shell
curl -L https://raw.githubusercontent.com/Muriano/pyhooker/main/install.sh | bash
```

After installation, you can run PyHooker from anywhere using the `pyhooker` command.

### Option 2: Run from source

- Download / Clone the repo
  ```shell
  git clone git@github.com:Muriano/pyhooker.git
  ```
- Start with
  ```shell
  make run
  ```
- Enjoy 😎

## Usage

Once installed, simply run:

```shell
pyhooker
```

This will start the webhook receiver and provide you with a public URL that you can use to receive webhooks.
