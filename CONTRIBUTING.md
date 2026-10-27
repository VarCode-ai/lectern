# Contributing

Thanks for helping Lectern! Bug reports, fixes, translations and new features are all welcome.

Lectern is a [Monad](https://github.com/VarCode-ai/monad) app. Changes to the shared UI kit in `common/` start in the
[Monad repository](https://github.com/VarCode-ai/monad), which keeps the reference copy, and are then copied to every app
(see [Monad's CONTRIBUTING](https://github.com/VarCode-ai/monad/blob/HEAD/CONTRIBUTING.md#the-shared-kit)).

## Reporting a bug

Open an issue with:

- your distribution and version, and your hardware (CPU, GPU, NPU);
- what you did, what you expected, and what happened;
- the relevant log: `~/.cache/lectern/lectern.log` (**Help → Open log file**).

## Running from a clone

The installer has a development mode: the menu entry and the commands run the files in your clone, so
every change is live at the next start.

```bash
./install.sh --dev
```

You can also start the app from a terminal to see its output:

```bash
./lectern.sh
```

## Code style

- Python 3.10+, standard library plus the packages in the `requirements.txt` files. Keep the app a
  single file that runs without being installed as a package.
- Follow the style of the surrounding code: 120-character lines, short comments that explain *why*.
- User-visible text is written in English and wrapped in `tr()` (see [Translations](#translations)).
- Shell scripts use `bash` with `set -euo pipefail`, must work on every distribution listed in the
  README, and must not require root.

## Translations

User-visible text is written in English in the code and wrapped in `tr("…")`. Text defined before the
language is known, such as tables of constants, is marked with `N_("…")` and passed to `tr()` where it is
shown. Use named placeholders and `.format()`, never f-strings, inside `tr()`:

```python
tr("Cannot create {path}:\n{error}").format(path=path, error=e)
```

The app keeps its translations in `locale/<language>.json`, a map from the English text to the
translation. To add a language, for example German:

1. Copy `locale/it.json` to `locale/de.json` and translate the values. Keep the `{placeholders}` unchanged.
2. Add `("de", "Deutsch")` to `UI_LANGUAGES` in `lectern.py`.
3. Add `locale/de.json` to `FILES` in `install.sh`.
4. In the menu entry written by `install.sh`, add `GenericName[de]=`, `Comment[de]=` and `Keywords[de]=`
   next to the Italian ones: desktops show them when the system language is German.
5. Run `python tools/check_translations.py`.

When you change or add a text in the code, update every catalog. `python tools/check_translations.py
--missing` prints the texts still to translate.

## Checks before a pull request

```bash
pip install pyflakes shellcheck-py
python -m pyflakes *.py common/*.py tools/*.py
shellcheck *.sh packaging/*.sh packaging/AppRun
python tools/check_translations.py
python tools/check_contrast.py
```

Then test what you changed by hand. For transcription changes, a short recording and a file with
`lectern-transcribe` (for example with `OpenVINO/whisper-tiny-int8-ov` on the CPU) cover most paths.

## Releasing a new version

Lectern compares its version with the latest GitHub release of this repository to show the update banner, so a release
needs three steps:

1. Raise `APP_VERSION` in `lectern.py` ([semantic versioning](https://semver.org/)) and add the changes
   to `CHANGELOG.md`. Each Monad app has its own version.
2. Commit, then tag with a `v` prefix and push the tag: `git tag -a v1.2.0 -m "1.2.0"` and
   `git push origin v1.2.0`.
3. The *Release* workflow starts when the tag arrives. It builds the AppImage and the archive for
   `install.sh`, checks that the archive has every file the installer needs, and publishes both in the release of the tag, with
   `SHA256SUMS` and the section of `CHANGELOG.md` for that version as notes. Nothing to edit by hand: the
   release is published (not a draft), and the app sees it at the next update check.

To build the downloads on your machine (the AppImage needs about 1 GB of downloads the first time):

```bash
packaging/build-appimage.sh            # the AppImage, into dist/
packaging/build-tarball.sh             # the archive for install.sh, into dist/
```

## License

By contributing you agree that your contributions are licensed under the
[GNU GPL v3.0 or later](LICENSE), the license of Lectern.
