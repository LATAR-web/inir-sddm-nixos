# inir-sddm-nixos ❄️🎨

Official [iNiR](https://github.com/snowarch/inir) **`ii-pixel` SDDM login theme** packaged for **NixOS**, featuring **automatic Material You dynamic color & wallpaper synchronization**.

[![CI](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/ci.yml/badge.svg)](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/ci.yml)
[![Automated Upstream Sync](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/update-flake.yml/badge.svg)](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/update-flake.yml)

[Español](README.es.md) | **English**

---

## ✨ Features

- **Pixel & Material Aesthetic**: Clean, modern login screen replicating the iNiR lock screen.
- **Dynamic Live Sync**: Automatically extracts your active desktop wallpaper (or video wallpaper first frame), user avatar, and Material You / iRiS color palette and syncs them to SDDM.
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

## 🔄 How the Automatic Sync Works

1. **State Preservation**: Because the Nix store is read-only, the theme's static QML/JS code is symlinked into `/var/lib/sddm/themes/ii-pixel`, while `theme.conf` and `assets/` are maintained as mutable files owned by the `users` group.
2. **Path Monitoring**: A systemd user path unit (`inir-sddm-sync.path`) watches:
   - `~/.local/state/quickshell/user/generated/colors.json`
   - `~/.local/state/quickshell/user/generated/theme-meta.json`
   - `~/.config/inir/config.json`
3. **Trigger**: Whenever iNiR generates new colors or you change wallpaper, the path unit triggers `inir-sddm-sync`, instantly writing the new colors, wallpaper, and avatar to the SDDM theme without requiring root or sudo.

---

## 🧪 Manual Sync & Testing

To manually trigger a theme synchronization:

```bash
inir-sddm-sync
```

To test the login screen in a nested window:

```bash
sddm-greeter --test-mode --theme /var/lib/sddm/themes/ii-pixel
```

---

## 📜 License

GPL-3.0 License. Based on the [iNiR project](https://github.com/snowarch/inir).
