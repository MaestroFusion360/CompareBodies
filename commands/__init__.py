from .compare_bodies import entry as compare_bodies

commands = [
    compare_bodies,
]

def start():
    for command in commands:
        command.start()

def stop():
    for command in commands:
        command.stop()