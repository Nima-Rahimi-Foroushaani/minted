import sys
import os
from pathlib import Path

os.environ["SELFAUTOLOC"] = "/usr/local/texlive/2025/bin/x86_64-linux"

# Check for required wheel dependencies and add them to Python's `sys.path`.
script_resolved = Path(__file__).resolve()
required_wheel_packages = (
    'latexrestricted',
    'latex2pydata',
    'pygments',
)

# Build the package search paths list
package_search_paths = [r'/usr/local/texlive/2025/texmf-dist/scripts/minted/']

# Collect the first matching .whl path for each required package
wheel_paths = []
def add_first(pkg):
    for psp in package_search_paths:
        for whl_path in Path(psp).glob("*.whl"):
            if whl_path.name.startswith(pkg):
                wheel_paths.append(whl_path)
                return
for pkg in required_wheel_packages: add_first(pkg)

if not wheel_paths:
    sys.exit('latexminted failed to find bundled wheels *.whl')
for pkg in required_wheel_packages:
    if not any(whl.name.startswith(pkg) for whl in wheel_paths):
        sys.exit('latexminted failed to find all required bundled wheels *.whl')
for wheel_path in wheel_paths:
    sys.path.insert(0, wheel_path.as_posix())