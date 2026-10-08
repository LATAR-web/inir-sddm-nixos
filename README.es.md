# inir-sddm-nixos ❄️🎨

Tema de inicio de sesión **SDDM `ii-pixel`** oficial de [iNiR](https://github.com/snowarch/inir) empaquetado para **NixOS**, con **sincronización automática de fondos de pantalla y colores dinámicos Material You**.

[![CI](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/ci.yml/badge.svg)](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/ci.yml)
[![Automated Upstream Sync](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/update-flake.yml/badge.svg)](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/update-flake.yml)

**Español** | [English](README.md)

---

## ✨ Características

- **Estética Pixel y Material You**: Pantalla de login limpia y moderna idéntica a la pantalla de bloqueo de iNiR.
- **Sincronización en Vivo**: Extrae automáticamente el fondo de escritorio activo (o el primer fotograma de fondos de vídeo), el avatar del usuario y la paleta de colores activa de Material You / iRiS y los sincroniza con SDDM.
- **Módulo Declarativo Puro de NixOS**: Una única opción habilita SDDM, el tema, dependencias de Qt 6 y los servicios de sincronización de systemd.
- **Nativo para Wayland (Greeter con Niri)**: Utiliza Niri como compositor del greeter de SDDM en Wayland, eliminando pantallas negras en laptops con gráficos híbridos (NVIDIA + Intel/AMD).
- **Actualizaciones Automáticas Diarias desde Upstream**: Un flujo de trabajo de GitHub Actions actualiza automáticamente este flake cuando el repositorio oficial `snowarch/inir` recibe cambios.

---

## 🚀 Inicio Rápido (Flakes)

### 1. Añadir el Input en `flake.nix`

En el archivo `flake.nix` de tu sistema NixOS:

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

Añade lo siguiente a tu configuración de NixOS:

```nix
{ config, pkgs, ... }:

{
  # Habilitar el tema ii-pixel de SDDM con sincronización dinámica automática
  services.inir-sddm = {
    enable = true;

    # Ejecutar el greeter de SDDM en Wayland usando Niri
    wayland.enable = true;
    wayland.compositor = "niri";

    # Sincronización automática de colores y fondo al cambiar en iNiR
    autoSync.enable = true;
  };
}
```

### 3. Reconstruir el Sistema

```bash
sudo nixos-rebuild switch --flake .#
```

---

## ⚙️ Opciones de Configuración

| Opción | Tipo | Valor por Defecto | Descripción |
|---|---|---|---|
| `services.inir-sddm.enable` | `bool` | `false` | Habilita SDDM y el tema `ii-pixel`. |
| `services.inir-sddm.wayland.enable` | `bool` | `true` | Habilita el greeter en Wayland para SDDM. |
| `services.inir-sddm.wayland.compositor` | `enum ["niri" "default"]` | `"niri"` | Compositor del greeter (`niri` usa `niri-greeter.kdl`). |
| `services.inir-sddm.autoSync.enable` | `bool` | `true` | Crea unidades de systemd para sincronizar el tema en vivo. |
| `services.inir-sddm.themeDir` | `str` | `"/var/lib/sddm/themes/ii-pixel"` | Directorio donde SDDM lee los datos mutables del tema. |

---

## 🔄 Cómo Funciona la Sincronización Automática

1. **Persistencia y Permisos**: Dado que el Nix store es de sólo lectura, los archivos inmutables QML/JS del tema se enlazan simbólicamente en `/var/lib/sddm/themes/ii-pixel`, mientras que `theme.conf` y `assets/` se mantienen con permisos de escritura para el grupo `users`.
2. **Vigilancia de Archivos (systemd path)**: Una unidad de usuario `inir-sddm-sync.path` vigila los archivos generados por Quickshell/iNiR:
   - `~/.local/state/quickshell/user/generated/colors.json`
   - `~/.local/state/quickshell/user/generated/theme-meta.json`
   - `~/.config/inir/config.json`
3. **Disparo**: Al cambiar de fondo o tema en iNiR, systemd invoca `inir-sddm-sync` en segundo plano, escribiendo inmediatamente los nuevos colores, fondo y avatar sin requerir privilegios de `sudo`.

---

## 🧪 Sincronización Manual y Pruebas

Para forzar manualmente una sincronización del tema:

```bash
inir-sddm-sync
```

Para previsualizar la pantalla de inicio de sesión en una ventana de prueba:

```bash
sddm-greeter --test-mode --theme /var/lib/sddm/themes/ii-pixel
```

---

## 📜 Licencia

Licencia GPL-3.0. Basado en el proyecto [iNiR](https://github.com/snowarch/inir).
