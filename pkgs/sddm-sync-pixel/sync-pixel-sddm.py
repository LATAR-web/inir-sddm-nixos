#!/usr/bin/env python3
"""Sync the ii-pixel SDDM theme with iNiR on NixOS: appearance, colors, wallpaper, and avatar.

This script reads the user's active iNiR palette, wallpaper, and avatar, and writes them
to the mutable SDDM theme directory (defaults to /var/lib/sddm/themes/ii-pixel).

Designed for NixOS with support for CLI flags, environment variables, and automated systemd execution.
"""

import argparse
import json
import os
import pwd
import shutil
import subprocess
import sys
import tempfile

THEME_NAME = "ii-pixel"
DEFAULT_THEME_DIRS = [
    "/var/lib/sddm/themes/ii-pixel",
    "/usr/share/sddm/themes/ii-pixel",
]

THEME_CONF_TEMPLATE = """\
[SddmTheme]
Name=ii-pixel
Description=iNiR SDDM login screen — Material You dynamic colors
Type=sddm-theme
Author=iNiR project
Version=1.0
Website=https://github.com/snowarch/iNiR
Screenshot=
MainScript=Main.qml
ConfigFile=theme.conf

[General]
background=assets/background.png
defaultBackground=assets/background.png
blurRadius=50

# iNiR: updated automatically by sync-pixel-sddm.py
"""

RETIRED_KEYS = {
    "irisBlur", "irisSaturation", "irisDim", "irisVignette", "irisScrim", "irisScrimStrength", "irisFit",
    "irisClockColour", "irisClockSize", "irisClockWeight", "irisClockTracking", "irisClockSeconds", "irisClock",
    "irisClockZone", "irisClockStyle", "irisClockDate", "irisClockFx", "irisClockFy",
    "irisSessionZone", "irisSessionFx", "irisSessionFy", "irisSessionWidth",
}

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".gif", ".webp"}


def resolve_home(user_override=None):
    if user_override:
        try:
            return pwd.getpwnam(user_override).pw_dir, user_override
        except KeyError:
            pass
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        try:
            return pwd.getpwnam(sudo_user).pw_dir, sudo_user
        except KeyError:
            pass
    current_user = os.environ.get("USER") or pwd.getpwuid(os.getuid()).pw_name
    return os.path.expanduser("~"), current_user


def resolve_theme_dir(cli_dir=None):
    if cli_dir and os.path.isdir(cli_dir):
        return cli_dir
    env_dir = os.environ.get("INIR_SDDM_THEME_DIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir
    for d in DEFAULT_THEME_DIRS:
        if os.path.isdir(d):
            return d
    return cli_dir or DEFAULT_THEME_DIRS[0]


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def dig(data, *keys, default=None):
    for key in keys:
        if not isinstance(data, dict) or key not in data or data[key] is None:
            return default
        data = data[key]
    return data


def read_colors(generated_dir):
    sources = [
        os.path.join(generated_dir, "app-palette.json"),
        os.path.join(generated_dir, "palette.json"),
        os.path.join(generated_dir, "colors.json"),
    ]
    source = next((p for p in sources if os.path.isfile(p)), None)
    if source is None:
        return None
    data = load_json(source) or {}
    dark = data.get("colors", {}).get("dark", {})
    if not dark:
        if "primary" in data or "on_surface" in data:
            dark = data
        else:
            return None

    return {
        "primaryColor": dark.get("app_accent") or dark.get("primary", "#cba6f7"),
        "onPrimaryColor": dark.get("app_on_accent") or dark.get("on_primary", "#1e1e2e"),
        "surfaceColor": dark.get("app_background") or dark.get("surface", "#1e1e2e"),
        "surfaceContainerColor": dark.get("app_surface") or dark.get("surface_container", "#181825"),
        "onSurfaceColor": dark.get("app_foreground") or dark.get("on_surface", "#cdd6f4"),
        "onSurfaceVariantColor": dark.get("app_subtext") or dark.get("on_surface_variant", "#9399b2"),
        "backgroundColor": dark.get("app_background") or dark.get("background", "#1e1e2e"),
        "errorColor": dark.get("error", "#f38ba8"),
    }


def read_appearance(config):
    chosen = str(dig(config, "lock", "loginScreen", default="auto"))
    if chosen in ("classic", "iris"):
        return chosen
    return "iris" if config.get("panelFamily") == "iris" else "classic"


def read_iris(config, palette, generated_dir):
    lock = dig(config, "iris", "lock", default={}) or {}
    appearance = dig(config, "iris", "appearance", default={}) or {}
    scene = lock.get("scene") or {}
    kind = lock.get("type") or {}
    session = dig(lock, "blocks", "session", default={}) or {}

    washi_path = os.path.join(generated_dir, "iris-washi.json")
    washi = dig(load_json(washi_path) or {}, "schemes", "dark", default={}) or {}
    accent = washi.get("accent") or (palette or {}).get("primaryColor") or "#a8c7fa"
    highlight = washi.get("highlight") or "#ff9f0a"
    material = "theme" if appearance.get("followTheme", True) else str(dig(appearance, "theme", "surface", default="black"))
    surface = dig(washi, "materials", material) or (palette or {}).get("backgroundColor") or "#000000"

    main_font = appearance.get("fontFamily") or "Inter"
    clock_font = {
        "main": main_font,
        "title": appearance.get("titleFontFamily") or "Inter Display",
    }.get(str(kind.get("clockFont", "numbers")), appearance.get("numbersFontFamily") or "Rubik")

    def flag(val):
        return "true" if val else "false"

    style = str(dig(config, "lock", "loginStyle", default="lens"))
    return {
        "irisLoginStyle": style if style in ("cover", "frame", "lens") else "lens",
        "irisSceneSource": scene.get("source", "desktop"),
        "irisSurface": surface,
        "irisDanger": washi.get("danger") or "#ff6961",
        "irisAccent": accent,
        "irisHighlight": highlight,
        "irisFontMain": main_font,
        "irisFontClock": clock_font,
        "irisTypeScale": kind.get("scale", 100),
        "irisClockFormat": kind.get("clockFormat", "auto"),
        "irisDateFormat": kind.get("dateFormat", "long"),
        "irisAvatar": flag(session.get("avatar", True)),
        "irisName": flag(session.get("name", True)),
        "irisHint": flag(session.get("hint", True)),
    }


def update_theme_conf(theme_conf_path, values, dry_run=False):
    if not os.path.isfile(theme_conf_path):
        before = THEME_CONF_TEMPLATE
    else:
        with open(theme_conf_path, "r", encoding="utf-8") as f:
            before = f.read()

    lines = before.split("\n")
    has_general = any("[General]" in l for l in lines)
    has_background = any(l.strip().startswith("background=") for l in lines)
    if not has_general or not has_background:
        lines = THEME_CONF_TEMPLATE.split("\n")

    remaining = {key: str(value) for key, value in values.items()}
    new_lines = []
    for line in lines:
        key = line.split("=", 1)[0].strip() if "=" in line else None
        if key in RETIRED_KEYS:
            continue
        if key in remaining:
            new_lines.append(f"{key}={remaining.pop(key)}")
        else:
            new_lines.append(line)
    while new_lines and new_lines[-1] == "":
        new_lines.pop()
    new_lines.extend(f"{key}={value}" for key, value in remaining.items())
    content = "\n".join(new_lines) + "\n"

    if content == before:
        return True

    if dry_run:
        print("[sddm-sync] DRY RUN: Would update theme.conf")
        return True

    try:
        with open(theme_conf_path, "w", encoding="utf-8") as f:
            f.write(content)
        try:
            os.chmod(theme_conf_path, 0o664)
        except OSError:
            pass
        return True
    except OSError as e:
        print(f"[sddm-sync] Error writing theme.conf ({theme_conf_path}): {e}", file=sys.stderr)
        return False


def same_file(src, dst):
    try:
        a, b = os.stat(src), os.stat(dst)
        return a.st_size == b.st_size and int(a.st_mtime) == int(b.st_mtime)
    except OSError:
        return False


def copy_asset(src, name, assets_dir, dry_run=False):
    if not os.path.isdir(assets_dir):
        if dry_run:
            return True
        try:
            os.makedirs(assets_dir, exist_ok=True)
            try:
                os.chmod(assets_dir, 0o775)
            except OSError:
                pass
        except OSError as e:
            print(f"[sddm-sync] Cannot create assets directory {assets_dir}: {e}", file=sys.stderr)
            return False

    dst = os.path.join(assets_dir, name)
    if same_file(src, dst):
        return True

    if dry_run:
        print(f"[sddm-sync] DRY RUN: Would copy {src} -> {dst}")
        return True

    try:
        shutil.copy2(src, dst)
        try:
            os.chmod(dst, 0o664)
        except OSError:
            pass
        return True
    except OSError as e:
        print(f"[sddm-sync] Copy to {dst} failed: {e}", file=sys.stderr)
        return False


def update_avatar(home_dir, username, assets_dir, dry_run=False):
    candidates = [
        os.path.join(home_dir, ".face"),
        os.path.join(home_dir, ".face.icon"),
    ]
    if username:
        candidates.append(f"/var/lib/AccountsService/icons/{username}")

    src = next((p for p in candidates if p and os.path.isfile(p)), None)
    if src:
        return copy_asset(src, "user-face.png", assets_dir, dry_run)
    return False


def video_frame(video_path):
    if not shutil.which("ffmpeg"):
        return None
    out = os.path.join(tempfile.mkdtemp(prefix="sddm-pixel-"), "frame.png")
    try:
        proc = subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-vframes", "1", "-update", "1", "-f", "image2", out],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
        if proc.returncode == 0 and os.path.isfile(out):
            st = os.stat(video_path)
            os.utime(out, (st.st_atime, st.st_mtime))
            return out
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def update_picture(path, name, assets_dir, dry_run=False):
    if not path or not os.path.isfile(path):
        return False
    if os.path.splitext(path)[1].lower() in VIDEO_EXTENSIONS:
        dst = os.path.join(assets_dir, name)
        try:
            if os.path.isfile(dst) and int(os.stat(dst).st_mtime) == int(os.stat(path).st_mtime):
                return True
        except OSError:
            pass
        frame = video_frame(path)
        if frame is None:
            return False
        try:
            return copy_asset(frame, name, assets_dir, dry_run)
        finally:
            shutil.rmtree(os.path.dirname(frame), ignore_errors=True)
    return copy_asset(path, name, assets_dir, dry_run)


def picture_lift(path):
    try:
        from PIL import Image, ImageStat
        with Image.open(path) as im:
            lum = ImageStat.Stat(im.convert("L").resize((48, 27))).mean[0] / 255
        return round(max(0.0, min(0.45, (lum - 0.42) * 0.9)), 2)
    except Exception:
        return 0


def read_wallpaper(config, home_dir, generated_dir):
    # 1. From config.json
    background = config.get("background", {}) or {}
    waffle_background = dig(config, "waffles", "background", default={}) or {}
    main_path = background.get("wallpaperPath", "")
    if config.get("panelFamily", "ii") == "waffle" and not waffle_background.get("useMainWallpaper", True):
        path = waffle_background.get("wallpaperPath", "") or main_path
    else:
        path = main_path
    if path and path.startswith("file://"):
        path = path[7:]
    if path and os.path.isfile(path):
        return path

    # 2. From theme-meta.json
    meta = load_json(os.path.join(generated_dir, "theme-meta.json")) or {}
    meta_path = meta.get("source_path") or meta.get("wallpaper_path")
    if meta_path and os.path.isfile(meta_path):
        return meta_path

    return None


def main():
    parser = argparse.ArgumentParser(description="Synchronize iNiR colors and wallpaper to SDDM theme.")
    parser.add_argument("--theme-dir", default=None, help="Target SDDM theme directory (e.g. /var/lib/sddm/themes/ii-pixel)")
    parser.add_argument("--user", default=None, help="Specific user to read configs from")
    parser.add_argument("--dry-run", action="store_true", help="Perform checks without writing files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    theme_dir = resolve_theme_dir(args.theme_dir)
    theme_conf_path = os.path.join(theme_dir, "theme.conf")
    assets_dir = os.path.join(theme_dir, "assets")

    home_dir, username = resolve_home(args.user)
    generated_dir = os.path.join(home_dir, ".local", "state", "quickshell", "user", "generated")
    config_json_path = os.path.join(home_dir, ".config", "inir", "config.json")

    if args.verbose:
        print(f"[sddm-sync] User: {username} ({home_dir})")
        print(f"[sddm-sync] Theme directory: {theme_dir}")

    config = load_json(config_json_path) or {}
    colors = read_colors(generated_dir)
    appearance = read_appearance(config)

    values = {"appearance": appearance}
    if colors:
        values.update(colors)
    values["materialShapeChars"] = "true" if dig(config, "lock", "materialShapeChars", default=False) else "false"

    iris = read_iris(config, colors, generated_dir)
    values.update(iris)

    own = str(dig(config, "iris", "lock", "scene", "path", default="") or "")
    if own.startswith("file://"):
        own = own[7:]
    values["irisPicture"] = ""
    if iris["irisSceneSource"] == "custom" and update_picture(own, "lock-picture.png", assets_dir, args.dry_run):
        values["irisPicture"] = "assets/lock-picture.png"

    wallpaper = read_wallpaper(config, home_dir, generated_dir)
    if wallpaper:
        update_picture(wallpaper, "background.png", assets_dir, args.dry_run)
    elif args.verbose:
        print("[sddm-sync] No active wallpaper path found; preserving existing background.")

    own_shown = appearance == "iris" and values["irisPicture"]
    shown = os.path.join(theme_dir, values["irisPicture"]) if own_shown else os.path.join(assets_dir, "background.png")
    values["irisLift"] = picture_lift(shown) if os.path.isfile(shown) else 0

    success = update_theme_conf(theme_conf_path, values, args.dry_run)
    update_avatar(home_dir, username, assets_dir, args.dry_run)

    if success:
        print(f"[sddm-sync] Theme successfully synced ({appearance}) -> {theme_dir}")
    else:
        print(f"[sddm-sync] Sync completed with warnings -> {theme_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
