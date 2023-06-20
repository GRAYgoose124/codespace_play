## Introduction

Simple task runner with a focus on separated contexts and workflows execution across JSON-RPC.

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