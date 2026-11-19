"""Build the offline download from the public project files."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
output = root/'downloads'/'Quantum_Teleportation_Animated.zip'
output.parent.mkdir(exist_ok=True)
inputs = [root/'Launch_Model.cmd', root/'run.py', root/'README.md']
for folder in ('backend','frontend','desktop','tests','docs','scripts'):
    inputs += [p for p in (root/folder).glob('*') if p.is_file() and p.suffix in
               ('.py','.cmd','.js','.html','.css','.md','.png')]
with ZipFile(output,'w',ZIP_DEFLATED) as archive:
    for path in sorted(inputs):
        archive.write(path,path.relative_to(root))
print(output)
