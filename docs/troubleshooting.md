# Troubleshooting Lectern

Fixes for problems specific to Lectern. Problems common to every [Monad](https://github.com/VarCode-ai/monad) app (installation, Qt not
starting, the NPU) are in the [Monad troubleshooting guide](https://github.com/VarCode-ai/monad/blob/HEAD/docs/troubleshooting.md), and
quick tips are in the [README](../README.md#tips-and-troubleshooting).

## Starting Lectern

### Lectern starts but shows no window

Lectern runs a single instance: starting it again brings the existing window to the front. If an old
process hangs, close it with `pkill -f lectern.py`.

## Hardware acceleration

### Intel GPU not used

Lectern runs Whisper directly on your system, which needs the Intel GPU compute runtime:

| Distribution | Command |
| --- | --- |
| Debian, Ubuntu | `sudo apt install intel-opencl-icd` |
| Fedora | `sudo dnf install intel-compute-runtime` |
| Arch | `sudo pacman -S intel-compute-runtime` |
| openSUSE | `sudo zypper install intel-opencl` |

The packages in older LTS releases (for example Ubuntu 22.04) may not support recent GPUs such as Arc or
Core Ultra graphics. In that case install the packages from the
[Intel compute-runtime releases](https://github.com/intel/compute-runtime/releases).

Your user must also be able to open `/dev/dri/renderD*`. On most desktops this is granted automatically
to the logged-in user. If it isn't, add yourself to the `render` group and log in again:

```bash
sudo usermod -aG render "$USER"
```

To check what OpenVINO sees:

```bash
~/.local/share/lectern/venv/bin/python -c "import openvino as ov; print(ov.Core().available_devices)"
```

If the GPU is missing from the list, the problem is the driver, not Lectern. Lectern falls back to the CPU
automatically and says so in the status line.

## Audio

### No microphone, or the recording stays silent

- Check that the microphone is not muted and is selected as input in your system sound settings.
- Lectern records through PipeWire's `pw-record` (package `pipewire-utils` on Fedora, `pipewire-bin` on
  Debian and Ubuntu). Without it, it uses Qt Multimedia, which talks to PulseAudio or to PipeWire through its
  PulseAudio compatibility layer: on minimal installations install `pipewire-pulse` (or `pulseaudio`) and
  the `libpulse` library. **Help → Open log file** shows which way the microphone is recorded.
- If the microphone stops sending audio during a lecture, Lectern reopens it automatically and shows a
  warning.

### `ffmpeg not found` (Fedora)

Fedora's `ffmpeg-free` package is enough for common formats. For formats with patent restrictions (for
example some AAC or WMA files) install `ffmpeg` from [RPM Fusion](https://rpmfusion.org).

## Getting help

When you open an [issue](https://github.com/VarCode-ai/lectern/issues), include your distribution and
version, the output of the installer, and the log: **Help → Open log file** (`~/.cache/lectern/lectern.log`).
