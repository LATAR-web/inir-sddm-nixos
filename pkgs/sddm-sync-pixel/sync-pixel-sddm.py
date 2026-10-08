#!/usr/bin/env python3
"""Sync the ii-pixel SDDM theme with iNiR on NixOS: appearance, colors, wallpaper, and avatar.

Version: 2.33.0
Supports:
- Pre-generated iNiR palettes (app-palette.json, palette.json, colors.json)
- Live color generation using Matugen (matugen image <path> --json hex)
- Pure Python Material You / PIL color quantization fallback
- Video wallpaper frame extraction via ffmpeg
- Full iRiS and Classic login styles
- Automatic systemd integration for NixOS
"""

import argparse
import colorsys
import json
import os
import pwd
import shutil
import subprocess
import sys
import tempfile

THEME_NAME = "ii-pixel"
VERSION = "2.33.0"
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
Version=2.33.0
Website=https://github.com/snowarch/inir
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


def read_colors_from_json(generated_dir):
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
        if "primary" in data or "on_surface" in data or "app_accent" in data:
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


def derive_colors_with_matugen(wallpaper_path, mode="dark"):
    """Generate Material You palette directly from image using matugen CLI."""
    if not shutil.which("matugen") or not wallpaper_path or not os.path.isfile(wallpaper_path):
        return None

    try:
        proc = subprocess.run(
            ["matugen", "image", wallpaper_path, "--json", "hex"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0 and proc.stdout:
            data = json.loads(proc.stdout)
            colors = data.get("colors", {}).get(mode, {})
            if colors:
                return {
                    "primaryColor": colors.get("primary", "#cba6f7"),
                    "onPrimaryColor": colors.get("on_primary", "#1e1e2e"),
                    "surfaceColor": colors.get("surface", "#1e1e2e"),
                    "surfaceContainerColor": colors.get("surface_container", "#181825"),
                    "onSurfaceColor": colors.get("on_surface", "#cdd6f4"),
                    "onSurfaceVariantColor": colors.get("on_surface_variant", "#9399b2"),
                    "backgroundColor": colors.get("background", "#1e1e2e"),
                    "errorColor": colors.get("error", "#f38ba8"),
                }
    except Exception:
        pass
    return None


def derive_colors_with_python_fallback(wallpaper_path, mode="dark"):
    """Derive harmonious Material palette in pure Python with PIL."""
    if not wallpaper_path or not os.path.isfile(wallpaper_path):
        return None

    try:
        from PIL import Image

        with Image.open(wallpaper_path) as im:
            # Resize to small thumbnail for fast color analysis
            thumb = im.convert("RGB").resize((48, 48), Image.Resampling.LANCZOS)
            # Quantize to 8 colors to find dominant hue
            quant = thumb.quantize(colors=8, method=Image.Quantize.FASTOCTREE)
            palette = quant.getpalette()[:24]
            # Pick highest-chroma color as accent
            best_rgb = (203, 166, 247)
            best_sat = -1
            for i in range(0, len(palette), 3):
                r, g, b = palette[i], palette[i + 1], palette[i + 2]
                h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
                if 0.15 < v < 0.95 and s > best_sat:
                    best_sat = s
                    best_rgb = (r, g, b)

            primary_hex = "#{:02x}{:02x}{:02x}".format(*best_rgb)
            # Calculate pleasant dark surface tones
            h, s, _ = colorsys.rgb_to_hsv(best_rgb[0] / 255.0, best_rgb[1] / 255.0, best_rgb[2] / 255.0)
            surf_r, surf_g, surf_b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, min(s * 0.2, 0.15), 0.12)]
            surf_cont_r, surf_cont_g, surf_cont_b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, min(s * 0.25, 0.18), 0.16)]

            surface_hex = "#{:02x}{:02x}{:02x}".format(surf_r, surf_g, surf_b)
            surface_cont_hex = "#{:02x}{:02x}{:02x}".format(surf_cont_r, surf_cont_g, surf_cont_b)

            return {
                "primaryColor": primary_hex,
                "onPrimaryColor": "#121318",
                "surfaceColor": surface_hex,
                "surfaceContainerColor": surface_cont_hex,
                "onSurfaceColor": "#e2e2e9",
                "onSurfaceVariantColor": "#c4c6d0",
                "backgroundColor": surface_hex,
                "errorColor": "#ffb4ab",
            }
    except Exception:
        return None


def get_theme_colors(generated_dir, wallpaper_path, mode="dark"):
    """Resolve theme colors: cached iNiR files -> Matugen -> Python fallback -> default."""
    colors = read_colors_from_json(generated_dir)
    if colors:
        return colors

    colors = derive_colors_with_matugen(wallpaper_path, mode)
    if colors:
        return colors

    colors = derive_colors_with_python_fallback(wallpaper_path, mode)
    if colors:
        return colors

    return {
        "primaryColor": "#cba6f7",
        "onPrimaryColor": "#1e1e2e",
        "surfaceColor": "#1e1e2e",
        "surfaceContainerColor": "#181825",
        "onSurfaceColor": "#cdd6f4",
        "onSurfaceVariantColor": "#9399b2",
        "backgroundColor": "#1e1e2e",
        "errorColor": "#f38ba8",
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


def read_wallpaper(config, home_dir, generated_dir, cli_wall=None):
    if cli_wall and os.path.isfile(cli_wall):
        return cli_wall

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
    parser = argparse.ArgumentParser(description=f"Synchronize iNiR colors and wallpaper to SDDM theme v{VERSION}.")
    parser.add_argument("--theme-dir", default=None, help="Target SDDM theme directory (e.g. /var/lib/sddm/themes/ii-pixel)")
    parser.add_argument("--wallpaper", default=None, help="Specific wallpaper path to sync")
    parser.add_argument("--user", default=None, help="Specific user to read configs from")
    parser.add_argument("--mode", default="dark", choices=["dark", "light"], help="Color scheme mode (default: dark)")
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
        print(f"[sddm-sync] iNiR SDDM Sync v{VERSION}")
        print(f"[sddm-sync] User: {username} ({home_dir})")
        print(f"[sddm-sync] Theme directory: {theme_dir}")

    config = load_json(config_json_path) or {}
    wallpaper = read_wallpaper(config, home_dir, generated_dir, args.wallpaper)
    colors = get_theme_colors(generated_dir, wallpaper, args.mode)
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
        print(f"[sddm-sync] Theme successfully synced v{VERSION} ({appearance}) -> {theme_dir}")
    else:
        print(f"[sddm-sync] Sync completed with warnings -> {theme_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
