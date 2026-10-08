# inir-sddm-nixos ❄️🎨

Official [iNiR](https://github.com/snowarch/inir) **`ii-pixel` SDDM login theme** packaged for **NixOS** (v2.33.0), featuring **automatic Material You dynamic color & wallpaper synchronization** powered by **Matugen & Python**.

[![CI](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/ci.yml/badge.svg)](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/ci.yml)
[![Automated Upstream Sync](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/update-flake.yml/badge.svg)](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/update-flake.yml)

[Español](README.es.md) | **English**

---

## ✨ Features (v2.33.0)

- **Pixel & Material Aesthetic**: Clean, modern login screen replicating the iNiR lock screen with Material You dynamic theming.
- **Enhanced Color Pipeline (Matugen + Python)**:
  - Automatically reads cached iNiR palettes (`app-palette.json`, `colors.json`, `iris-washi.json`).
  - **Live Matugen Generation**: If no precomputed palette exists, it directly invokes `matugen image <wallpaper> --json hex` to generate authentic Material You tokens.
  - **Pure Python Color Fallback**: Features an integrated PIL quantization and chroma-detection engine to guarantee harmonic colors even without cached files.
- **Dynamic Live Sync**: Extracts active desktop wallpaper (or video wallpaper first frame via `ffmpeg`), user avatar (`~/.face`), and color scheme.
- **NixOS Pure Declarative Module**: One simple option enables SDDM, the theme, Qt 6 dependencies, and systemd synchronization services.
- **Wayland Native (Niri Greeter)**: Uses Niri as the SDDM Wayland greeter compositor, preventing black screens on hybrid GPU laptops (NVIDIA + Intel/AMD).
- **Automated Daily Upstream Sync**: A GitHub Actions workflow automatically updates this flake whenever upstream `snowarch/inir` receives updates.

---

## 🚀 Quick Start (Flakes)

### 1. Add Flake Input

In your NixOS `flake.nix`:

```nix
{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    inir-sddm = {
      url = "github:LATAR-web/inir-sddm-nixos";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, inir-sddm, ... }: {
    nixosConfigurations.myhostname = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        inir-sddm.nixosModules.default
        ./configuration.nix
      ];
    };
  };
}
```

### 2. Enable in `configuration.nix`

Add the following to your system configuration:

```nix
{ config, pkgs, ... }:

{
  # Enable iNiR ii-pixel SDDM theme with automatic dynamic synchronization
  services.inir-sddm = {
    enable = true;

    # Run SDDM greeter in Wayland mode using Niri
    wayland.enable = true;
    wayland.compositor = "niri";

    # Automatically synchronize wallpaper and palette whenever changed in iNiR
    autoSync.enable = true;
  };
}
```

### 3. Rebuild System

```bash
sudo nixos-rebuild switch --flake .#
```

---

## ⚙️ Configuration Options

| Option | Type | Default | Description |
|---|---|---|---|
| `services.inir-sddm.enable` | `bool` | `false` | Enables SDDM and the `ii-pixel` theme. |
| `services.inir-sddm.wayland.enable` | `bool` | `true` | Enables Wayland greeter for SDDM. |
| `services.inir-sddm.wayland.compositor` | `enum ["niri" "default"]` | `"niri"` | Greeter compositor (`niri` uses official `niri-greeter.kdl`). |
| `services.inir-sddm.autoSync.enable` | `bool` | `true` | Creates systemd user services to live-sync theme assets. |
| `services.inir-sddm.themeDir` | `str` | `"/var/lib/sddm/themes/ii-pixel"` | Mutable directory where SDDM reads synced assets. |

---

## 🔄 CLI Tool: `inir-sddm-sync`

The package provides a standalone command line tool `inir-sddm-sync` with Matugen and Python integration:

```bash
# Sync automatically from active iNiR session
inir-sddm-sync

# Sync with a specific custom wallpaper using live Matugen extraction
inir-sddm-sync --wallpaper /path/to/wallpaper.png

# Preview without writing files
inir-sddm-sync --dry-run -v
```

---

## 🧪 Testing the Login Screen

To test the login screen in a nested window on NixOS:

```bash
sddm-greeter --test-mode --theme /var/lib/sddm/themes/ii-pixel
```

---

## 📜 License

GPL-3.0 License. Based on the [iNiR project](https://github.com/snowarch/inir).
