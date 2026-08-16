"""Guards against the class of breakage that made `main` unrunnable.

Every failure this module checks for reached `main` at least once, and none of
them are subtle: a file that does not parse, a Streamlit page pasted into the
data layer, a module importing itself, an import of a package that was never
added to the repository. They are the residue of merges resolved by keeping
both sides, and they share one property — nothing in the existing suite looks
for them, because the existing suite imports application code, and code that
does not parse cannot be imported. A collection error is not a test failure,
so the suite went green by not running.

So this module deliberately does none of that. It reads source as text, parses
it with `ast`, and imports nothing from the application. It has no dependency
on a database, on Streamlit, or on any package outside the standard library,
which means it still runs — and still fails usefully — when the rest of the
tree is broken. That is the whole point of it.

The `pages/` directory gets the same treatment as everything else, which is
worth stating because it is where most of the damage was. Streamlit pages
execute their body on import, so the suite has never been able to import them
and has therefore never checked them at all. Parsing is not executing, so
these checks are safe there.
"""

import ast
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent

# Directories that are not ours to police: virtualenvs, caches, and the vendor
# tree under src/.
SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "build",
    "dist",
    "src",
}

# Modules that are Streamlit entry points: their body is UI and is meant to run
# top to bottom on import. Everything else is a library and is not.
UI_ENTRY_POINTS = {"app.py", "app_old.py", "old_app.py"}

# Third-party packages the project depends on but which are not named in
# requirements.txt in an importable form, plus the import names of the ones
# whose distribution name differs.
DISTRIBUTION_IMPORT_NAMES = {
    "pillow": "PIL",
    "python-dotenv": "dotenv",
    "streamlit-agraph": "streamlit_agraph",
    "streamlit-folium": "streamlit_folium",
}

EXTRA_KNOWN_IMPORTS = {
    "numpy",
    "folium",
    "streamlit_folium",
    "psutil",
    "yaml",
    "setuptools",
    "dateutil",
}


def _python_files():
    """Every Python file in the repository we are responsible for."""
    for path in sorted(REPO_ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.relative_to(REPO_ROOT).parts):
            continue
        yield path


def _relative(path):
    return str(path.relative_to(REPO_ROOT))


ALL_FILES = list(_python_files())
ALL_FILE_IDS = [_relative(path) for path in ALL_FILES]


def _parse(path):
    """Parse a file, or fail the calling test with the location of the error."""
    source = path.read_text(encoding="utf-8")
    try:
        return ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        line = (exc.text or "").rstrip()
        pytest.fail(
            f"{_relative(path)} does not parse.\n"
            f"  line {exc.lineno}: {exc.msg}\n"
            f"  {line}"
        )


def _module_name(path):
    """The dotted module name a file would be imported under."""
    relative = path.relative_to(REPO_ROOT)
    return ".".join(relative.with_suffix("").parts)


def _known_import_roots():
    """Top-level names an import in this repository is allowed to resolve to."""
    known = set(sys.stdlib_module_names)
    known.update(EXTRA_KNOWN_IMPORTS)

    # Anything that exists in the repository as a module or a directory of
    # modules is importable from the repository root, which is how the app runs.
    for path in REPO_ROOT.glob("*.py"):
        known.add(path.stem)
    for directory in REPO_ROOT.iterdir():
        if directory.is_dir() and any(directory.glob("*.py")):
            known.add(directory.name)

    requirements = REPO_ROOT / "requirements.txt"
    if requirements.exists():
        for line in requirements.read_text(encoding="utf-8").splitlines():
            name = line.split("#")[0].strip()
            if not name:
                continue
            for separator in (">=", "==", "<=", "~=", ">", "<", "["):
                name = name.split(separator)[0]
            name = name.strip().lower()
            known.add(DISTRIBUTION_IMPORT_NAMES.get(name, name.replace("-", "_")))

    return known


KNOWN_IMPORT_ROOTS = _known_import_roots()


# ---------------------------------------------------------------------------
# 1. Everything parses.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", ALL_FILES, ids=ALL_FILE_IDS)
def test_file_parses(path):
    """Every Python file in the repository is syntactically valid.

    This is the check that was missing. Five files were unparseable on `main`,
    one of them `database.py`, which every other module imports.
    """
    _parse(path)


def test_repository_has_no_unparseable_files():
    """The same check stated as a whole, so a failure lists every broken file.

    The parametrised test above says *which* file broke; this one says *how
    many*, which is the number that matters when judging whether a merge went
    in cleanly.
    """
    broken = []
    for path in ALL_FILES:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            broken.append(f"{_relative(path)}:{exc.lineno}: {exc.msg}")

    assert not broken, "Files that do not parse:\n  " + "\n  ".join(broken)


# ---------------------------------------------------------------------------
# 2. Library modules do not contain a user interface.
# ---------------------------------------------------------------------------

def _module_level_streamlit_calls(tree):
    """Streamlit calls that run at import time rather than inside a function."""
    calls = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for descendant in ast.walk(node):
            if not isinstance(descendant, ast.Call):
                continue
            func = descendant.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "st"
            ):
                calls.append((node.lineno, func.attr))
    return calls


def test_library_modules_have_no_module_level_ui():
    """Only pages and the app entry point may render UI at import time.

    An entire challenge-tracking page was once pasted into `database.py` at
    module scope. It called `st.button`, `st.metric` and `st.progress` against
    names that do not exist there, so importing the data layer raised
    `NameError` — and importing the data layer is the first thing every test
    and every page does.

    Rendering on import is correct for a page and is a mistake anywhere else.
    """
    offenders = []
    for path in ALL_FILES:
        relative = path.relative_to(REPO_ROOT)
        if relative.parts[0] == "pages" or relative.name in UI_ENTRY_POINTS:
            continue
        if relative.name.startswith("test_"):
            continue

        calls = _module_level_streamlit_calls(_parse(path))
        for lineno, attr in calls:
            offenders.append(f"{relative}:{lineno}: st.{attr}() at module scope")

    assert not offenders, (
        "Streamlit UI is executing on import of a library module:\n  "
        + "\n  ".join(offenders)
        + "\n\nMove it into a page under pages/, or into a function."
    )


# ---------------------------------------------------------------------------
# 3. No module imports itself.
# ---------------------------------------------------------------------------

def test_no_module_imports_itself():
    """A module importing its own names always fails.

    `database.py` contained `from database import save_weekly_challenge, ...`,
    which raises `ImportError` on a partially initialised module. The names
    were defined a few thousand lines further down in the same file.

    Compared on the full dotted path, so `plugins/carbon_payback.py` importing
    the top-level `carbon_payback` is correctly left alone.
    """
    offenders = []
    for path in ALL_FILES:
        own_name = _module_name(path)
        for node in ast.walk(_parse(path)):
            if isinstance(node, ast.ImportFrom) and node.level == 0:
                if node.module == own_name:
                    offenders.append(
                        f"{_relative(path)}:{node.lineno}: imports from itself"
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == own_name:
                        offenders.append(
                            f"{_relative(path)}:{node.lineno}: imports itself"
                        )

    assert not offenders, "Self-imports:\n  " + "\n  ".join(offenders)


# ---------------------------------------------------------------------------
# 4. Every import resolves to something that exists.
# ---------------------------------------------------------------------------

def _imported_roots(tree):
    """Top-level package names a module imports, with line numbers."""
    roots = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.append((node.lineno, alias.name.split(".")[0]))
        elif isinstance(node, ast.ImportFrom):
            # Relative imports resolve against the package, not the root.
            if node.level == 0 and node.module:
                roots.append((node.lineno, node.module.split(".")[0]))
    return roots


def test_every_import_resolves_to_something_that_exists():
    """No module imports a package that is neither vendored nor declared.

    `app.py` imported `components.header` and `components.profile` from a
    `components/` package that was never added to the repository, and
    `challenge_generator.py` imported `utils.challenge_generator` from a
    `utils/` package that does not exist either. Both are import-time failures,
    so the app did not start and the module could not be used.

    Static on purpose: it catches a missing package without needing the
    optional third-party dependencies to be installed first.
    """
    offenders = []
    for path in ALL_FILES:
        for lineno, root in _imported_roots(_parse(path)):
            if root not in KNOWN_IMPORT_ROOTS:
                offenders.append(
                    f"{_relative(path)}:{lineno}: imports '{root}', which is "
                    f"neither in the repository nor in requirements.txt"
                )

    assert not offenders, "Unresolvable imports:\n  " + "\n  ".join(offenders)


# ---------------------------------------------------------------------------
# 5. Module-level code does not reference names that were never bound.
# ---------------------------------------------------------------------------

def _module_scope_bindings(tree):
    """Names bound at module scope: assignments, defs, imports, with, for, except."""
    bound = set()

    def bind_target(target):
        if isinstance(target, ast.Name):
            bound.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                bind_target(element)
        elif isinstance(target, ast.Starred):
            bind_target(target.value)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                bind_target(target)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            bind_target(node.target)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            bind_target(node.target)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars is not None:
                    bind_target(item.optional_vars)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
        elif isinstance(node, (ast.comprehension,)):
            bind_target(node.target)
        elif isinstance(node, (ast.Lambda, ast.arg)):
            continue
        elif isinstance(node, ast.Global):
            bound.update(node.names)
        elif isinstance(node, ast.NamedExpr):
            bind_target(node.target)

    return bound


COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
NESTED_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)


def _comprehension_targets(node):
    """Names a comprehension binds — they live in its own scope, not ours."""
    names = set()
    for generator in node.generators:
        for descendant in ast.walk(generator.target):
            if isinstance(descendant, ast.Name):
                names.add(descendant.id)
    return names


def _module_scope_name_loads(tree):
    """Names read by code that runs at import time, with line numbers.

    Walks by hand rather than with `ast.walk`, because the traversal has to
    stop at a scope boundary. A name inside a function body or a lambda
    resolves when it is *called*, not now, and a comprehension binds its own
    loop variable — counting either would report names that are perfectly fine.
    """
    loads = []

    def visit(node, shadowed):
        if isinstance(node, NESTED_SCOPES):
            return
        if isinstance(node, COMPREHENSIONS):
            shadowed = shadowed | _comprehension_targets(node)
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id not in shadowed
        ):
            loads.append((node.lineno, node.id))
        for child in ast.iter_child_nodes(node):
            visit(child, shadowed)

    for statement in tree.body:
        if isinstance(statement, NESTED_SCOPES):
            continue
        visit(statement, frozenset())

    return loads


def _uses_star_import(tree):
    return any(
        isinstance(node, ast.ImportFrom)
        and any(alias.name == "*" for alias in node.names)
        for node in ast.walk(tree)
    )


def test_module_level_code_defines_the_names_it_uses():
    """Import-time code does not read a name that nothing in the file binds.

    This is what a pasted-in block looks like from the outside. `database.py`
    read `user_id`, `footprint` and `challenges` at module scope; the top of
    `pages/Carbon_Footprint.py` read `user_footprint` and `contributors` two
    hundred lines before either existed. Both raise `NameError` on import.

    Files using `from x import *` are skipped: a star import can legitimately
    supply any name, and guessing which would produce false failures. That is
    a real gap, and it is smaller than the one it closes.
    """
    builtins_names = set(dir(__builtins__)) if isinstance(__builtins__, dict) is False else set(__builtins__)
    builtins_names.update(
        {"__file__", "__name__", "__doc__", "__builtins__", "__spec__", "__package__"}
    )

    offenders = []
    for path in ALL_FILES:
        tree = _parse(path)
        if _uses_star_import(tree):
            continue

        bound = _module_scope_bindings(tree) | builtins_names
        seen = set()
        for lineno, name in _module_scope_name_loads(tree):
            if name in bound or name in seen:
                continue
            seen.add(name)
            offenders.append(
                f"{_relative(path)}:{lineno}: '{name}' is used at import time "
                f"but never defined in this file"
            )

    assert not offenders, (
        "Import-time code reads names that do not exist:\n  " + "\n  ".join(offenders)
    )


# ---------------------------------------------------------------------------
# 6. Importing a module does not write to the repository.
# ---------------------------------------------------------------------------

WRITE_MODES = {"w", "wb", "a", "ab", "w+", "wb+", "a+", "ab+", "x", "xb"}


def _module_level_file_writes(tree):
    """`open(..., 'w')` calls that run at import time."""
    writes = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for descendant in ast.walk(node):
            if isinstance(
                descendant, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
            ):
                continue
            if not isinstance(descendant, ast.Call):
                continue
            func = descendant.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name != "open":
                continue

            mode = None
            if len(descendant.args) > 1 and isinstance(
                descendant.args[1], ast.Constant
            ):
                mode = descendant.args[1].value
            for keyword in descendant.keywords:
                if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                    mode = keyword.value.value

            if isinstance(mode, str) and mode in WRITE_MODES:
                writes.append((descendant.lineno, mode))
    return writes


def test_importing_a_module_does_not_write_files():
    """No module opens a file for writing as a side effect of being imported.

    `refactor.py` is a one-shot migration script whose body sat at module
    scope. Importing it rewrites `app.py`, overwrites `styles/theme.py` and
    creates four page files — so any sweep that imports every module in the
    repository destroys the source tree on the way past. That is not a
    hypothetical: it happened while investigating this, which is how the
    check came to exist.

    Scripts are welcome; they just belong behind `if __name__ == "__main__"`.
    """
    offenders = []
    for path in ALL_FILES:
        relative = path.relative_to(REPO_ROOT)
        if relative.name.startswith("test_"):
            continue

        for lineno, mode in _module_level_file_writes(_parse(path)):
            offenders.append(
                f"{relative}:{lineno}: open(..., {mode!r}) runs on import"
            )

    assert not offenders, (
        "Importing these modules writes to disk:\n  "
        + "\n  ".join(offenders)
        + "\n\nPut the body behind `if __name__ == \"__main__\":`."
    )


# ---------------------------------------------------------------------------
# 7. The checks above are actually looking at something.
# ---------------------------------------------------------------------------

def test_the_guard_covers_the_pages_directory():
    """The pages/ tree is in scope.

    Four of the five original syntax errors were in `pages/`, which the rest of
    the suite cannot reach — Streamlit pages run on import, so they can never
    be imported by a test. If a future change to SKIP_DIRS or to the discovery
    logic quietly drops that directory, these checks would keep passing while
    covering nothing, which is the failure mode worth guarding against.
    """
    pages = [path for path in ALL_FILES if path.relative_to(REPO_ROOT).parts[0] == "pages"]
    assert len(pages) > 10, (
        f"Only {len(pages)} files found under pages/ — discovery is not working."
    )


def test_the_guard_covers_the_top_level_modules():
    """The top-level modules are in scope, including database.py."""
    top_level = {
        path.name for path in ALL_FILES if path.parent == REPO_ROOT
    }
    assert "database.py" in top_level
    assert "app.py" in top_level
    assert len(top_level) > 50, (
        f"Only {len(top_level)} top-level modules found — discovery is not working."
    )
