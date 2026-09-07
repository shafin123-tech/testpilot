from pathlib import Path


# manual_agent/
MANUAL_AGENT_DIR = Path(__file__).resolve().parent

# testpilot/
PROJECT_ROOT = MANUAL_AGENT_DIR.parent

LOG_FILE = MANUAL_AGENT_DIR / "sample_log.txt"


def search_log(keyword):
    print("\n[DEBUG tools.py] search_log called")
    print("[DEBUG tools.py] keyword =", keyword)
    print("[DEBUG tools.py] log file =", LOG_FILE)

    with open(LOG_FILE, "r") as file:
        lines = file.readlines()

    matches = []

    for line in lines:
        if keyword.lower() in line.lower():
            matches.append(line.strip())

    print("[DEBUG tools.py] number of matches =", len(matches))

    return matches


def read_file(path):
    print("\n[DEBUG tools.py] read_file called")
    print("[DEBUG tools.py] requested path =", path)

    file_path = (PROJECT_ROOT / path).resolve()

    print("[DEBUG tools.py] project root =", PROJECT_ROOT)
    print("[DEBUG tools.py] resolved file path =", file_path)

    # Prevent reading outside the project
    try:
        file_path.relative_to(PROJECT_ROOT)
    except ValueError:
        return "Access denied."

    if not file_path.exists():
        return f"File not found: {path}"

    if not file_path.is_file():
        return f"Not a file: {path}"

    with open(file_path, "r") as file:
        content = file.read()

    return content


def list_files(directory="."):
    print("\n[DEBUG tools.py] list_files called")
    print("[DEBUG tools.py] directory =", directory)

    directory_path = (PROJECT_ROOT / directory).resolve()

    print("[DEBUG tools.py] resolved directory =", directory_path)

    # Prevent listing outside the project
    try:
        directory_path.relative_to(PROJECT_ROOT)
    except ValueError:
        return ["Access denied."]

    if not directory_path.exists():
        return [f"Directory not found: {directory}"]

    if not directory_path.is_dir():
        return [f"Not a directory: {directory}"]

    files = []

    for item in directory_path.iterdir():
        files.append(item.name)

    return sorted(files)


# Simple manual tests
if __name__ == "__main__":

    print("\n===== TEST search_log =====")
    result = search_log("COPY")
    print(result)

    print("\n===== TEST read_file =====")
    result = read_file("Dockerfile")
    print(result)

    print("\n===== TEST list_files =====")
    result = list_files(".")

    for item in result:
        print(item)