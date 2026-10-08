# iNiR Shell SDDM ❄️

SDDM for iNiR Shell on NixOS.

[![CI](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/ci.yml/badge.svg)](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/ci.yml)
[![Automated Upstream Sync](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/update-flake.yml/badge.svg)](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/update-flake.yml)

**English** | [Español](README.es.md)

---

##  Features

- **Official iNiR Shell SDDM**: The `ii-pixel` theme designed specifically for the iNiR desktop environment.
- **Automatic Live Sync in NixOS**: Real-time sync for wallpapers (images and videos), user avatars, and dynamic Material You colors.
- **Color Engine with Matugen & Python**: Extracts colors directly with Matugen and pure Python fallback.
- **Wayland Native with Niri Greeter**: Uses Niri as the greeter compositor to eliminate GPU issues on hybrid systems.
- **Automated Upstream Updates**: Stays continuously up to date with upstream iNiR.

---

##  Installation on NixOS

### 1. Add Flake Input

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

```nix
{ config, pkgs, ... }:

{
  services.inir-sddm = {
    enable = true;
    wayland.enable = true;
    wayland.compositor = "niri";
    autoSync.enable = true;
  };
}
```

### 3. Rebuild System

```bash
sudo nixos-rebuild switch --flake .#
```

---

##  Commands

```bash
# Manually sync the theme
inir-sddm-sync

# Sync with a specific wallpaper using Matugen
inir-sddm-sync --wallpaper /path/to/wallpaper.png

# Test the login screen in a nested window
sddm-greeter --test-mode --theme /var/lib/sddm/themes/ii-pixel
```
