## Introduction
"Make your gems sparkle."

Simple task runner with a focus on separated contexts and workflows execution across JSON-RPC.

> Windows bug: `dizzy` does not print input prompts. Use `dizzy-server` and `dizzy-client` instead. Will break your pipes, will need taskkil~l - just install Linux, please. 
> 
> "Look man, I don't use Winderz, `taskkill /F /IM python.exe` is a solution, not a problem." - Quack

### Install

    > cd dizzy 
    > poetry install
### Run

    > poetry shell

then:

    > dizzy     # wraps dizae (server + client) -vDEBUG

or:

    > dizae server -vDEBUG >/dev/null&
    > dizae client

or: (to be deprecated)

    > dizzy-server >/dev/null &
    > dizzy-client
