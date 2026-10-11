# iNiR Shell SDDM

SDDM para iNiR Shell en NixOS.

[English](README.md) | **Español**

---

## Características

- **iNiR Shell SDDM Oficial**: El tema `ii-pixel` diseñado específicamente para el entorno iNiR.
- **Sincronización en Vivo en NixOS**: Sincronización en tiempo real de fondos (imágenes y videos), avatares de usuario y colores dinámicos Material You.
- **Motor de Color con Matugen y Python**: Extrae colores directamente con Matugen y soporte nativo en Python.
- **Wayland Nativo con Greeter Niri**: Emplea Niri como compositor de inicio para evitar fallos de GPU en equipos híbridos.
- **Actualización Automática**: Se mantiene sincronizado continuamente cada 2 horas con iNiR upstream.

---

## Instalación en NixOS

### 1. Añadir el Flake

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
    nixosConfigurations.mi-equipo = nixpkgs.lib.nixosSystem {
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

### 3. Reconstruir el Sistema

```bash
sudo nixos-rebuild switch --flake .#
```

---

## Comandos

```bash
# Sincronizar manualmente el tema
inir-sddm-sync

# Sincronizar con un fondo de pantalla específico mediante Matugen
inir-sddm-sync --wallpaper /ruta/a/fondo.png

# Verificar estado de upstream iNiR y actualizar flake
./scripts/inir-sddm-sync-upstream --update

# Probar la pantalla de inicio en una ventana de prueba
sddm-greeter --test-mode --theme /var/lib/sddm/themes/ii-pixel
```
