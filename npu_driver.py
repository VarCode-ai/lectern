#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The Intel NPU driver that Lectern brings with it, as OVMS Manager does in its container image.

Lectern runs Whisper with the NPU driver of the system, and that driver needs its compiler to load any model.
Some distribution packages leave the compiler out (Fedora 44 and 45 ship intel-npu-driver 1.32 without it):
then every model fails with ZE_RESULT_ERROR_UNSUPPORTED_FEATURE. install.sh and the AppImage put the user-space
part of the official Intel driver (Level Zero driver and compiler) in a folder of their own, and Lectern puts
that folder before the system libraries when the system has no NPU compiler. The kernel module (intel_vpu)
and the firmware stay those of the system.

  python3 npu_driver.py install DIR   download, verify and extract the driver into DIR
  python3 npu_driver.py status        which driver Lectern uses, and why
  python3 npu_driver.py needed        exit code 0 if this machine needs the bundled driver

LECTERN_NPU_DRIVER=system never uses the bundled driver, LECTERN_NPU_DRIVER=bundled always does.
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

VERSION = "1.38.0"
TAG = f"v{VERSION}"
# The Ubuntu 24.04 build: it needs glibc 2.38, the newer builds need more
URL = (f"https://github.com/intel/linux-npu-driver/releases/download/{TAG}/"
       "linux-npu-driver-v1.38.0.20260910-34487311128-ubuntu2404.tar.gz")
SHA256 = "1efcd4b60c22abee751d8f2705962cbcc2a569de45c7e0e670cf08afbfcdc1d2"
MIN_GLIBC = (2, 38)
PACKAGES = ("intel-level-zero-npu_", "intel-driver-compiler-npu_")  # the firmware package is not needed
NOTICES = {"LICENSE.md": f"https://raw.githubusercontent.com/intel/linux-npu-driver/{TAG}/LICENSE.md",
           "third-party-programs.txt":
               f"https://raw.githubusercontent.com/intel/linux-npu-driver/{TAG}/third-party-programs.txt"}
DRIVER_LIB = "libze_intel_npu.so.1"
# the compiler library names the NPU drivers look for: Intel's (1.3x) and Fedora's intel-npu-compiler
COMPILER_LIBS = ("libopenvino_intel_npu_compiler.so", "libnpu_driver_compiler.so")
NPU_DEVICE = "/dev/accel/accel0"
DIRNAME = "npu-driver"
REEXEC_FLAG = "LECTERN_NPU_REEXEC"


def driver_dir():
    """The folder of the bundled driver, or None: next to the app folder (installed copy, AppImage), or in
    ~/.local/share/lectern (development mode, running from the project folder)."""
    here = os.path.dirname(os.path.abspath(__file__))
    data = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    for d in (os.path.join(os.path.dirname(here), DIRNAME), os.path.join(data, "lectern", DIRNAME)):
        if os.path.isfile(os.path.join(d, DRIVER_LIB)):
            return d
    return None


def glibc_version():
    try:
        name, version = os.confstr("CS_GNU_LIBC_VERSION").split()
        return tuple(int(p) for p in version.split(".")[:2]) if name == "glibc" else None
    except (ValueError, OSError, AttributeError):
        return None


def system_compiler(skip=None):
    """Path of an NPU compiler the dynamic linker can find, outside the folder `skip`, or None."""
    for d in os.environ.get("LD_LIBRARY_PATH", "").split(":"):
        if d and os.path.abspath(d) != skip:
            for lib in COMPILER_LIBS:
                if os.path.isfile(os.path.join(d, lib)):
                    return os.path.join(d, lib)
    ldconfig = shutil.which("ldconfig") or "/sbin/ldconfig"
    try:
        out = subprocess.run([ldconfig, "-p"], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        out = ""
    for line in out.splitlines():
        name, _, path = line.strip().partition(" => ")
        if name.split(" ", 1)[0] in COMPILER_LIBS and os.path.abspath(os.path.dirname(path)) != skip:
            return path
    return None


def needed():
    """(True if this machine should use the bundled driver, reason in plain words)."""
    mode = os.environ.get("LECTERN_NPU_DRIVER", "auto").lower()
    if mode == "system":
        return False, "LECTERN_NPU_DRIVER=system"
    if mode == "bundled":
        return True, "LECTERN_NPU_DRIVER=bundled"
    if not os.path.exists(NPU_DEVICE):
        return False, f"no NPU ({NPU_DEVICE} missing)"
    glibc = glibc_version()
    if glibc and glibc < MIN_GLIBC:
        return False, "the bundled driver needs glibc %d.%d" % MIN_GLIBC
    found = system_compiler(skip=driver_dir())
    if found:
        return False, f"the system NPU driver has a compiler ({found})"
    return True, "the system NPU driver has no compiler"


def choice():
    """(folder of the bundled driver to use or None, reason in plain words)."""
    use, reason = needed()
    d = driver_dir()
    if use and not d:
        return None, f"{reason}, but the bundled NPU driver is not installed"
    return (d if use else None), reason


def no_driver_cache():
    """Call before OpenVINO loads its NPU plugin. Lectern saves the models compiled for the NPU itself, as files
    in its OpenVINO cache (CACHE_DIR), and loads them from there in a second or two. The driver keeps its own
    copy in ~/.cache/ze_intel_npu_cache, but with a 1 GB limit past which it deletes the least used ones: a
    compiled Whisper takes 1-2.5 GB, so that copy only cost disk writes and was always thrown away.
    ZE_INTEL_NPU_CACHE_SIZE set by the user still wins."""
    os.environ.setdefault("ZE_INTEL_NPU_CACHE_SIZE", "0")


def use_bundled_driver():
    """Call first thing in main(): if the bundled driver is needed, restart the process with it before the
    system libraries. The dynamic linker reads LD_LIBRARY_PATH only when a process starts, and the NPU
    plugin loads the driver by name, so setting it later would have no effect."""
    if os.environ.get(REEXEC_FLAG):
        return
    d, _ = choice()
    if not d:
        return
    paths = [p for p in os.environ.get("LD_LIBRARY_PATH", "").split(":") if p]
    if paths[:1] == [d]:
        return
    os.environ["LD_LIBRARY_PATH"] = ":".join([d] + [p for p in paths if p != d])
    os.environ[REEXEC_FLAG] = "1"  # never loop, even if the exec below changes nothing
    try:
        os.execv(sys.executable, [sys.executable, *getattr(sys, "orig_argv", sys.argv)[1:]])
    except OSError:
        pass  # the app keeps running with the system driver


def active_driver():
    """'bundled 1.38.0' or 'system', for the log."""
    d = driver_dir()
    if d and os.environ.get("LD_LIBRARY_PATH", "").split(":")[0] == d:
        return f"bundled {VERSION}"
    return "system"


def _download(url):
    try:  # the certificates of the system, also from the relocatable Python of the AppImage build
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def _deb_members(data):
    """The members of a .deb (an ar archive): {name: bytes}."""
    if not data.startswith(b"!<arch>\n"):
        raise ValueError("not a .deb archive")
    members, pos = {}, 8
    while pos + 60 <= len(data):
        header = data[pos:pos + 60]
        name, size = header[:16].decode().strip().rstrip("/"), int(header[48:58].decode().strip())
        members[name] = data[pos + 60:pos + 60 + size]
        pos += 60 + size + (size & 1)
    return members


def install(dest):
    """Download the Intel release, check its SHA256 and put its libraries and license notices in dest."""
    dest = os.path.abspath(dest)
    stamp = os.path.join(dest, "VERSION")
    if os.path.isfile(stamp) and open(stamp).read().strip() == VERSION and os.path.isfile(
            os.path.join(dest, DRIVER_LIB)):
        print(f"  Intel NPU driver {VERSION} already in {dest}")
        return
    print(f"  downloading the Intel NPU driver {VERSION} (about 50 MB)")
    archive = _download(URL)
    if hashlib.sha256(archive).hexdigest() != SHA256:
        raise SystemExit(f"The NPU driver archive does not match its SHA256: {URL}")
    notices = {name: _download(url) for name, url in NOTICES.items()}
    parent = os.path.dirname(dest)
    os.makedirs(parent, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix=DIRNAME + ".", dir=parent)
    try:
        with tarfile.open(fileobj=io.BytesIO(archive)) as release:
            debs = [m for m in release.getmembers()
                    if m.name.endswith(".deb") and os.path.basename(m.name).startswith(PACKAGES)]
            if len(debs) != len(PACKAGES):
                raise SystemExit(f"Unexpected content in {URL}")
            for deb in debs:
                members = _deb_members(release.extractfile(deb).read())
                payload = next(v for k, v in members.items() if k.startswith("data.tar"))
                with tarfile.open(fileobj=io.BytesIO(payload)) as files:
                    for m in files.getmembers():
                        name = os.path.basename(m.name)
                        if not (m.name.endswith(".so") or ".so." in m.name) or "/lib/" not in m.name:
                            continue
                        target = os.path.join(tmp, name)
                        if m.issym():
                            os.symlink(os.path.basename(m.linkname), target)
                        elif m.isfile():
                            with open(target, "wb") as f:
                                f.write(files.extractfile(m).read())
                            os.chmod(target, 0o755)
        if not os.path.isfile(os.path.join(tmp, DRIVER_LIB)):
            raise SystemExit(f"{DRIVER_LIB} is missing from {URL}")
        for name, text in notices.items():
            with open(os.path.join(tmp, name), "wb") as f:
                f.write(text)
        with open(os.path.join(tmp, "VERSION"), "w") as f:
            f.write(VERSION + "\n")
        os.chmod(tmp, 0o755)
        old = dest + ".old"
        shutil.rmtree(old, ignore_errors=True)
        if os.path.exists(dest):
            os.rename(dest, old)
        os.rename(tmp, dest)
        shutil.rmtree(old, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"  Intel NPU driver {VERSION} installed in {dest}")


def main(argv):
    if len(argv) == 3 and argv[1] == "install":
        install(argv[2])
    elif len(argv) == 2 and argv[1] == "status":
        d, reason = choice()
        print(f"NPU driver: {'bundled ' + VERSION + ' (' + d + ')' if d else 'system'}: {reason}")
    elif len(argv) == 2 and argv[1] == "needed":  # for install.sh: exit code 0 if this machine needs it
        use, reason = needed()
        print(reason)
        return 0 if use else 1
    else:
        print(__doc__.strip().split("\n\n")[2], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
