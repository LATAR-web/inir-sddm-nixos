# SDDM de iNiR Shell ❄️

SDDM de iNiR Shell para NixOS.

[![CI](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/ci.yml/badge.svg)](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/ci.yml)
[![Automated Upstream Sync](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/update-flake.yml/badge.svg)](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/update-flake.yml)

[English](README.md) | **Español**

---

##  Características

- **SDDM Oficial de iNiR Shell**: Tema `ii-pixel` diseñado específicamente para complementar el entorno iNiR.
- **Sincronización Automática en NixOS**: Sincroniza en tiempo real el fondo de pantalla (imágenes y vídeos), el avatar del usuario y los colores dinámicos de Material You.
- **Motor de Color con Matugen y Python**: Extrae los colores directamente de Matugen y cuenta con respaldo automático en Python.
- **Greeter en Wayland con Niri**: Utiliza Niri como compositor del greeter para evitar problemas con tarjetas gráficas híbridas (NVIDIA / Intel / AMD).
- **Actualizaciones Automáticas**: Se sincroniza automáticamente con el upstream de iNiR.

---

##  Instalación en NixOS

### 1. Añadir el input en `flake.nix`

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
    nixosConfigurations.mi-pc = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        inir-sddm.nixosModules.default
        ./configuration.nix
      ];
    };
  };
}
```

### 2. Habilitar en `configuration.nix`

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

### 3. Reconstruir el sistema

```bash
sudo nixos-rebuild switch --flake .#
```

---

##  Comandos

```bash
# Sincronizar el tema manualmente
inir-sddm-sync

# Sincronizar con un fondo de pantalla específico usando Matugen
inir-sddm-sync --wallpaper /ruta/a/mi-fondo.png

# Probar la pantalla de login en una ventana de prueba
sddm-greeter --test-mode --theme /var/lib/sddm/themes/ii-pixel
```
