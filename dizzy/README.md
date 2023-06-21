## Introduction

Simple task runner with a focus on separated contexts and workflows execution across JSON-RPC.

> Windows bug: `dizzy` does not print input prompts. Use `dizzy-server` and `dizzy-client` instead. Will break your pipes, will need taskkill - just install Linux, please.

### Install

    > cd dizzy 
    > poetry install
### Run

    > poetry shell
    > dizzy

or:

    > dizzy-server > /dev/null &
    > dizzy-client

## Design thoughts

Entities bundle services, contexts and tasks through arbitrary workflows.

- Services offer tasks
- Tasks can run on contexts
- Tasks can have dependencies on other tasks determining forced execution order.