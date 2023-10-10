# Groups Domains Extractor

Application, which helps in finding all domains of specific group and copies it to clipboard. It also has the ability to save configuration of group to file and load it.

## How to install?

### **A. Arch Linux and derivatives**
1. Download and install package from [AUR](https://aur.archlinux.org/packages/groupsdomainsextractor).
2. Run it from Start menu or `/bin/GDE`.
2. Ready!

### **B. Windows 10+**
1. Download latest installer (.exe file) from https://github.com/FiltersHeroes/ScriptsPlayground/releases.
2. Run installer to install in chosen location.
3. Go to Start menu, find GDE in it and launch.
4. Ready!

### **C. Every OS for desktop**
1. Download latest [Python 3.6+](https://www.python.org/downloads/) and install it (make sure that pip and PATH environment variable is checked).
2. Download latest wheel (.whl file) from https://github.com/FiltersHeroes/ScriptsPlayground/releases.
3. Run following command from terminal:
```bash
pip install path_to_wheel/GDE-version-py3-none-any.whl[Qt5]
```
You can replace Qt5 with Qt6 if you want, but that may improve or worsen the aesthetic experience. For Windows 10+ recommended is Qt 6 if you're using dark mode, but most Linux desktop environments still uses Qt 5, so choice is obvious.

4. Launch GDE from terminal.
5. Ready!
