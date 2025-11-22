import os

# Extensions autorisées
ALLOWED_EXT = {".py", ".env", ".sql"}

# Dossiers à ignorer (mise à jour avec `.pytest_cache`)
IGNORED_DIRS = {
    ".git",
    "__pycache__",
    ".cache",
    "cache",
    "doc",
    ".pytest_cache",
}

# Fichiers à ignorer
IGNORED_FILES = {"__init__.py"}


def print_tree(path, prefix=""):
    try:
        items = sorted(os.listdir(path))
    except PermissionError:
        return

    dirs = []
    files = []

    for item in items:
        full = os.path.join(path, item)

        # Ignore les dossiers interdits
        if os.path.isdir(full) and item in IGNORED_DIRS:
            continue

        if os.path.isdir(full):
            dirs.append(item)
        else:
            # 🚫 Ignore les fichiers interdits
            if item in IGNORED_FILES:
                continue

            ext = os.path.splitext(item)[1].lower()
            if ext in ALLOWED_EXT:
                files.append(item)

    all_items = dirs + files
    pointers = (
        ["├── "] * (len(all_items) - 1) + ["└── "] if all_items else []
    )

    for pointer, name in zip(pointers, all_items):
        full = os.path.join(path, name)
        print(prefix + pointer + name)

        if name in dirs:
            extension = "│   " if pointer == "├── " else "    "
            print_tree(full, prefix + extension)


# Exemple d’utilisation
print_tree(".")
