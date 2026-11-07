# Pillow Lambda layer

The resizer needs the Pillow library, which Lambda does not include. It is packaged as a **layer**
(not committed to the repo because the zip is ~7 MB).

## Build it (Linux/macOS/WSL or AWS CloudShell)

```bash
mkdir python
pip install pillow \
  --platform manylinux2014_x86_64 \
  --target python \
  --only-binary=:all: \
  --python-version 3.12
zip -r pillow-layer.zip python
```

## Publish it

Lambda console -> Layers -> Create layer -> upload `pillow-layer.zip`
- Compatible runtime: Python 3.12
- Compatible architecture: x86_64

Then attach it to the `resizer` function (Layers -> Add a layer -> Custom layers).
