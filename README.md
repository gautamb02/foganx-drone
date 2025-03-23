# FOGANX Drone Safeguard

## 🚀 Getting Started

### ✅ Prerequisites

- Python **3.10.x** (strictly required)
- pip (Python package manager)
- Invoke (for task automation)

> _Please ensure you are using Python 3.10.x before proceeding._

### ✅ Installation

1. **Clone the repository:**

```bash
git clone https://github.com/gautamb02/foganx-drone.git
```

2. **Navigate to the project directory:**

```bash
cd foganx-drone
```

3. **Create a Python 3.10.x environment with the name `env` only:**

```bash
python3.10 -m venv env
# Activate on Linux/macOS
source env/bin/activate
# Or activate on Windows
env\Scripts\activate
```

4. **Install all required libraries:**

```bash
pip install -r requirements.txt
```

5. **Install Invoke (if not installed):**

```bash
pip install invoke
```

## 🛡 Project Rules

1. Use **Python 3.10.x** version only.
2. Create a virtual environment with the name **env** only.
3. Install all required dependencies using:

```bash
pip install -r requirements.txt
```

4. Run the project using:

```bash
invoke run
```

## ⚡ Task Automation with Invoke

This project uses **Invoke** to automate common tasks.

### ✅ Available Tasks

- **List available tasks:**

```bash
invoke --list
```

- **Run the application:**

```bash
invoke run
```

- **Install dependencies:**

```bash
invoke install
```

### ✅ Example `tasks.py`

```python
from invoke import task

@task
def run(c):
    """Run the FOGANX Drone Safeguard application"""
    c.run("python -m src.main")

@task
def install(c):
    """Install dependencies from requirements.txt"""
    c.run("pip install -r requirements.txt")
```

## ⚙ Local Configuration (Important!)

The `resource/config/config.yaml` file contains local environment settings (API keys, paths, or custom environment configurations).

### Before making local changes, run:

```bash
git update-index --assume-unchanged resource/config/config.yaml
```

### To re-enable tracking (if needed):

```bash
git update-index --no-assume-unchanged resource/config/config.yaml
```

---

> ✅ Follow these instructions to set up and run FOGANX Drone Safeguard successfully! Feel free to reach out for any help or clarification.

