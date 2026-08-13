---
name: shinecaniep-packager
description: Confirm and package the current shinecaniep Tauri application for Android APK/AAB or Windows EXE/installer. Use when the user asks to package, build, release, export, or generate an APK, AAB, EXE, or Windows installer for this project, including requests such as "打包apk", "打包exe", or "重新打包". Before any write or build, collect and confirm target platform, application name, package identifier, version, Chinese and English product names, company name, icon path, and Android signing choice.
---

# ShineCan IEP Packager

Use this skill for release packaging of `/home/maoea/projects/shinecaniep`. Treat the repository as the source of truth and preserve unrelated user changes.

## Required Confirmation

Before changing files or starting a build, inspect the repository and present the current values. Ask the user to confirm or replace these fields:

- Target: `android-apk`, `android-aab`, `windows-exe`, or `windows-installer`.
- Application display name.
- Application/package identifier: Android package ID for Android targets, or the Tauri identifier for Windows targets. Require reverse-DNS syntax for Android IDs.
- Version in `x.y.z` form.
- Chinese page/system name.
- English page/system name.
- Company/copyright name.
- Icon source path, or explicitly confirm keeping the current icon.
- Android signing: signed release using the configured keystore, unsigned release, or AAB signing handled externally.

Do not infer a new package identifier, version, icon, or signing choice from an earlier conversation. Defaults are acceptable only when shown to the user and explicitly confirmed. Do not expose keystore passwords in user-facing messages.

If the user supplies all requested values in the initial request, repeat the resolved configuration and ask for one confirmation before writing. If the user only says “打包 APK/EXE”, ask for the missing values first and stop before edits/building.

## Workflow

1. Inspect `git status --short`, `src-tauri/tauri.conf.json`, `src-tauri/Cargo.toml`, `dist/config.json`, the Android Gradle project, and available signing tools. Read [project-reference.md](references/project-reference.md) when the target is selected.
2. Check for existing package identifiers and source package directories before changing an Android identifier. Preserve unrelated modifications and report conflicts that make a safe migration impossible.
3. After confirmation, run `scripts/sync_release_config.py` from the repository root with the confirmed values. For Android identifier changes, the script updates Tauri identifier, Android Gradle namespace/applicationId, generated Java/Kotlin package declarations and directory, Android asset config when present, page metadata, and version metadata. It does not alter the keystore.
4. Handle icons only when the user selected a new icon. For Android, use the repository's icon generator or `cargo tauri icon` as appropriate; verify that the source is a square PNG/SVG and that generated resources are inside the configured project.
5. Touch `src-tauri/src/main.rs` before a Tauri build so stale frontend/config embedding is invalidated. Build from `src-tauri`:
   - Android APK/AAB: `cargo tauri android build`.
   - Windows EXE/installer: `cargo tauri build` on Windows. Do not claim an EXE was built from Linux/WSL.
6. For a signed Android APK, run `scripts/sign_android_apk.py` with the unsigned APK, output path, keystore path, alias, and password supplied through environment variables or an approved local command. The script runs `zipalign`, `apksigner sign`, and `apksigner verify`.
7. Run `scripts/verify_release.py` on the final APK/EXE and verify product name, package identifier, version, file existence, and signature status where applicable. For APKs, use `aapt`/`apkanalyzer` and `apksigner`; do not rely only on the filename.
8. Report the exact artifact path, target, app name, identifier, version, signing status, verification results, and any warnings. Mention untracked or unrelated files without deleting them.

## Safety Rules

- Never build before the user confirms the resolved release configuration.
- Never overwrite or delete an existing APK/EXE with a different configuration without warning. Use a configuration-specific output filename.
- Never delete broad build directories, source files, keystores, or user changes. Removing a narrowly identified stale plugin cache is allowed only when the build fails because that cache directory already exists, and must be reported.
- Keep keystore passwords out of `SKILL.md`, scripts, logs, command output, and final messages. Prefer `KEYSTORE_PASSWORD` and `KEY_PASSWORD` environment variables.
- If the configured identifier changes, treat the result as a new Android application. It cannot upgrade an installed APK under the old identifier.
- If a build fails, report the first actionable error and do not present an old artifact as the new build.

## Script Usage

Run scripts with the repository root as the working directory:

```bash
python3 .codex/skills/shinecaniep-packager/scripts/sync_release_config.py \
  --project-root /home/maoea/projects/shinecaniep \
  --app-name "特殊儿童智能学习系统" \
  --package-id "com.hzxckj.shinecan.iep.znxx" \
  --version "1.0.3" \
  --system-name "特殊儿童智能学习系统" \
  --system-name-en "Special Children Intelligent Learning System" \
  --company "杭州炫灿科技有限公司"
```

```bash
KEYSTORE_PASSWORD='provided-outside-the-script' \
KEY_PASSWORD='provided-outside-the-script' \
python3 .codex/skills/shinecaniep-packager/scripts/sign_android_apk.py \
  --project-root /home/maoea/projects/shinecaniep \
  --input /path/to/app-universal-release-unsigned.apk \
  --output /path/to/app-release-signed.apk \
  --keystore /home/maoea/projects/shinecaniep/shinecaniep-release.jks \
  --alias shinecaniep
```

Read the scripts before patching them for a repository variation. Keep `SKILL.md` under 500 lines and load the reference only for the selected target.
