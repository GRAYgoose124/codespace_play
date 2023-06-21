# Design thoughts

Entities bundle services, contexts and tasks through arbitrary workflows.

- Services offer groups of tasks
- Entities bundle services and workflows.
- Tasks can run on contexts
- Tasks can have dependencies on other tasks determining forced execution order.
- Workflows are a set of tasks to be executed based on a DSL spec.
- Composites will be a set of workflows to be executed based on a DSL spec.
### Workflows, Task Dependencies, and Contexts

Workflow information is propagated as such:

    tasks = list[Tasks]
    ctx['workflow'][tasks[n]] = ctx['result'][tasks[n-1]]

Workflow information is to be stored on the server, but is corrently lost.

While task dependencies propagate their results to dependents via:

    ctx[tasks[n].name] = task.run(ctx)

> This is probably the reason for a cyclic dependency bug seen when returning ctx.

We will eventually need to cache, scheduleand batch dependencies and workflows.

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
