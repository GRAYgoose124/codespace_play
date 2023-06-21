from pathlib import Path
import shutil
import textwrap
import click

from dizzy import Service, Entity
import yaml

# GENERATE an arbitrary data directory structure entities have services, services have tasks folder.
# WEe call services in entities, entity services.
# data/
# ├── common_services
# │   ├── service1
# │   │   ├── service.yml
# │   │   └── tasks
# │   │       └── othertasks.py
# │   └── service2
# │       ├── service.yml
# │       └── tasks
# │           └── sometasks.py
# └── entities
#     ├── entity1
#     │   ├── entity.yml
#     │   └── services
#     └── entity2
#         ├── entity.yml
#         └── services


def generate_skeleton_settings(path: str):
    path = Path(path)
    settings_file = path / "settings.yml"
    settings_file.touch()

    settings_obj = {
        "settings": {
            "common_services": [],
            "entities": [],
        }
    }

    with open(settings_file, "w") as f:
        yaml.safe_dump(settings_obj, f)


def generate_skeleton_task(
    name: str,
    taskfile_name: str,
    path: str,
    dependencies: list[str],
    inputs: list[str],
    outputs: list[str],
):
    """Unlike entity and service, task is just a raw python file"""
    path = Path(path)

    task_name = name.capitalize()

    task_template = textwrap.dedent(
        f"""
        class {task_name}(Task):
            \"\"\"Description\"\"\"
            dependencies = {dependencies}
            @staticmethod
            def run(ctx):
                new_ctx = {{}}
                inputs = {inputs}
                for i in inputs:
                    for o in {outputs}:
                        if o not in new_ctx:
                            new_ctx[o] = {{}}
                        new_ctx[o][i] = TaskName.process(ctx[i])
                return new_ctx

            @staticmethod
            def process(input):
                return input
        """
    )

    task_file = path / f"{taskfile_name}.py"

    if not task_file.exists():
        task_file.touch()
        task_file.write_text("from dizzy import Task")

    with open(task_file, "a") as f:
        f.write(f"\n\n{task_template}\n")


def generate_skeleton_service(
    name: str,
    path: str,
    description: str,
    tasks: list[str],
):
    path = Path(path)
    service_dir = path / name
    service_dir.mkdir(parents=True, exist_ok=True)

    service_yml = service_dir / "service.yml"

    Service(name=name, description=description, tasks=tasks).save_to_yaml(service_yml)

    tasks_dir = service_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        generate_skeleton_task(task, f"default", tasks_dir, [], [], [])


def generate_skeleton_entity(
    name: str,
    path: str,
    description: str,
    services: dict[str, list[str]],
    common: list[str],
    workflows: dict[str, str],
):
    path = Path(path)
    entity_dir = path / name
    entity_dir.mkdir(parents=True, exist_ok=True)

    entity_yml = entity_dir / "entity.yml"

    Entity(
        name=name,
        description=description,
        services=list(services.keys()) + common,
        workflows=workflows,
    ).save_to_yaml(entity_yml)

    services_dir = entity_dir / "services"
    services_dir.mkdir(parents=True, exist_ok=True)

    for service, tasks in services.items():
        generate_skeleton_service(service, services_dir, "entserv", tasks)


def generate_data_dir(path: str, demo: bool = False):
    path = Path(path)

    data_root = path / "data"
    common = data_root / "common_services"
    entities = data_root / "entities"

    data_root.mkdir(parents=True, exist_ok=True)
    generate_skeleton_settings(data_root)

    common.mkdir(parents=True, exist_ok=True)
    if demo:
        generate_skeleton_service("basic", common, "a basic task", ["T1", "T2", "T3"])

    entities.mkdir(parents=True, exist_ok=True)
    if demo:
        generate_skeleton_entity(
            "simple",
            entities,
            "a simple entity",
            {"entity_serv": ["task1", "task2"]},
            ["basic"],
            {"work": "T1 -> S1"},
        )


@click.group()
def dizgen():
    pass


@dizgen.command()
@click.argument("name")
@click.option("--services", "-s", multiple=True)
@click.option("--workflows", "-w", multiple=True)
def entity(name, services, workflows):
    pass


@dizgen.command()
@click.argument("name")
@click.option("--tasks", "-t", multiple=True)
@click.option("--make-common", "-m", is_flag=True)
def service(name, tasks, make_common):
    pass


@dizgen.command()
@click.argument("name")
@click.option("--dependencies", "-d", multiple=True)
@click.option("--inputs", "-i", multiple=True)
@click.option("--outputs", "-o", multiple=True)
def task(name, dependencies, inputs, outputs):
    pass


@dizgen.command()
@click.option("--delete", "-d", is_flag=True)
def demo(delete):
    if delete:
        shutil.rmtree("./tests/demo")
    else:
        generate_data_dir("./tests/demo", demo=True)


def main():
    dizgen()


if __name__ == "__main__":
    main()
