# Changelog

All notable changes to Lectern are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[semantic versioning](https://semver.org/).

Lectern is a [Monad](https://github.com/VarCode-ai/monad) app. Until 1.0.0 it lived in the Monad repository,
then named `ai-app-local-openvino`, together with OVMS Manager; its history was kept when it moved here.

## [Unreleased]

## [1.1.0] — 2026-10-27

### Monad

- Lectern has its own repository, as one of the apps of [Monad](https://github.com/VarCode-ai/monad). The
  shared UI kit is in `common/`, and the update check now looks at the releases of this repository.
- New icon in the style of the Monad family, and *About Lectern* says which family it belongs to.

### Downloads

- AppImage: one file with Python, Qt and OpenVINO inside, for any x86-64 distribution with glibc 2.34 or
  newer. It also runs `lectern-transcribe` (`… transcribe -i <folder>`).
- Archive for the installer: `Lectern-<version>.tar.gz` unpacks into a folder ready for `./install.sh`,
  for those who prefer an installed app without cloning the repository.
- A *Release* workflow builds both for every tag and publishes them in the GitHub release, with
  `SHA256SUMS` and the notes of the version from this changelog.

### Fixed

- Speech was almost never detected on some laptops (an Intel Core Ultra digital microphone with Qt 6.12,
  including the AppImage). The microphone is now recorded through PipeWire's `pw-record`, with Qt as the
  fallback; the log records which way it is recorded and in what format.

### Privacy

- Lectern and lectern-transcribe switch off the optional usage statistics of Hugging Face downloads
  (`HF_HUB_DISABLE_TELEMETRY`, `DO_NOT_TRACK`).

## [1.0.0] — 2026-10-23

First public release.

- **Lectern**: a lecture notebook with live speech-to-text (Whisper on OpenVINO GenAI).
  - Organized by course, lecture and category, and saved as plain text files.
  - Transcribes already recorded audio and video files.
  - Exports a lecture to Markdown.
- **lectern-transcribe**: batch transcription of a folder from the terminal, with resume, audio cleanup and
  automatic model download.
- Light and dark themes that follow the system, command palette (Ctrl+K), bundled Inter and Newsreader
  fonts, live waveform and local-processing indicator, WCAG 2.2 AA contrast and a *Reduce motion* option.
- English and Italian interface, per-user installer for every major glibc distribution, automatic fallback
  from GPU or NPU to the CPU, and update notifications that can be turned off.

[Unreleased]: https://github.com/VarCode-ai/lectern/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/VarCode-ai/lectern/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/VarCode-ai/lectern/releases/tag/v1.0.0
