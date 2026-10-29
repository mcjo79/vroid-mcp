# Third-party notices

`vroid-mcp` is MIT-licensed (see `LICENSE`). It also contains code adapted from
`vroid-studio-mcp`, which is MIT-licensed:

- **vroid-studio-mcp** — https://github.com/brainrom/vroid-studio-mcp
  Copyright (c) 2026 Ilya Chelyadin and vroid-studio-mcp contributors.
  MIT License. Adapted code is mainly the IL2CPP reflection helpers in
  `VRoidMcpBridge/Interop.cs` and parts of the catalog/interop approach.

The MIT permission notice for that project is reproduced below:

```text
MIT License

Copyright (c) 2026 Ilya Chelyadin and vroid-studio-mcp contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

VRoid Studio, BepInEx and their assets are not distributed with this project.
VRoid Studio is a product of pixiv Inc.; BepInEx is a separate open-source
project. Refer to their respective licenses before redistributing them.

## Bundled Python

Release packages from v0.12.0 ship a CPython 3.12 interpreter built by
[python-build-standalone](https://github.com/astral-sh/python-build-standalone)
(Astral Software), distributed under the Python Software Foundation License
Version 2. The `LICENSE.txt` of that build is included in the package at
`python/LICENSE.txt`. It is installed locally under
`%LOCALAPPDATA%\VRoidMcp\python` and does not modify the system.

## Bundled image libraries

The Windows release also bundles these wheels in
`python\Lib\site-packages`, so thumbnails and texture analysis work offline:

- **NumPy** 2.5.4 — BSD 3-Clause License, copyright the NumPy developers.
  The license metadata is included in
  `python\Lib\site-packages\numpy-2.5.4.dist-info\`.
- **Pillow** 13.0.0 — Historical Permission Notice and Disclaimer (HPND),
  copyright the Pillow contributors.
  The license metadata is included in
  `python\Lib\site-packages\pillow-13.0.0.dist-info\`.

They are imported by the preset cache/labeler for thumbnails, color and visual
metadata. They are not required for the core MCP editing or VRM export paths.


## Installer

`VRoidMcp-Setup-v<version>.exe` is built with **NSIS** 3.11 (Nullsoft Scriptable
Install System, <https://nsis.sourceforge.io>). The installer stub and plug-ins it
embeds are released under the zlib/libpng license, copyright Nullsoft and
contributors; parts use bzip2 and LZMA, under their own permissive licenses. See
<https://nsis.sourceforge.io/License>. NSIS is used only to build the installer and
is not installed on the user's machine.
