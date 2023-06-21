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

## Design thoughts

Entities bundle services, contexts and tasks through arbitrary workflows.

- Services offer groups of tasks
- Entities bundle services and workflows.
- Tasks can run on contexts
- Tasks can have dependencies on other tasks determining forced execution order.
- Workflows are a set of tasks to be executed based on a DSL spec.
- Composites will be a set of workflows to be executed based on a DSL spec.
### Entity

Entities are the main unit of work. They bundle services and workflows. Workflows should be composable. An entity can execute any task from any service defined for it. It executes common or private services transparently.

### Folder Structure
Services and Entities need only a `service.yml` and `entity.yml` respectively. Add `Task`s to `tasks/` of any service folder, whether common or entity-specific.

- dizzy/
- - data/common_services/\<service> - services shared by all entities
- - data/entities/\<entity>/services/\<service> - services specific to an entity

#### Service structure
- \<service>/
- \<service>/service.yml
- \<service>/tasks/

#### Entity structure
- \<entity>/
- \<entity>/entity.yml
- \<entity>/services/\<service>

#### Task folder
Nothing is more simple than task, throw it in `.py` in some service's task folder:

```python
from dizzy import Task

class SomeTask(Task):
    """A task"""
    dependencies = ["SomeOtherTask"]

    @staticmethod
    def run(ctx):
        # ctx["workflow"] represents some api computed during workflow execution.
        ctx["SomeTask"] = ctx["SomeOtherTask"] + "world!"

        return "some step-wise computation for private dependency solution"
```
This one depends on SomeOtherTask, but that's okay - define it just as simply! There's no real need to return the context, it's passed by reference. S/N: Sometimes we don't need anything else returned, so it might make sense to join the workflow with the task's return value.



### TODO:
- Composites: workflows on the fly with a simple DSL for result composition.
- Datagen
- Tests
- 
- Annoyingly, only dizae server/client logs right now. For some reason logfiles don't work at the right levels either.