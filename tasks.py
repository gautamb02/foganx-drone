from invoke import task

@task
def run(c):
    """Run the application"""
    c.run("python -m src.main  --config=resource/config/config.yaml")

@task
def install(c):
    """Install dependencies"""
    c.run("pip install -r requirements.txt")

@task
def freeze(c):
    """Freeze dependencies and git add"""
    c.run("pip freeze > requirements.txt")
    c.run("git add .")