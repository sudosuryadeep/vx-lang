from vx import run


def execute(source: str):
    return run(source)


def execute_file(path: str):
    with open(path, "r", encoding="utf-8") as file:
        source = file.read()

    return execute(source)
