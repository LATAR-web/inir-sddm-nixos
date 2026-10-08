# inir-sddm-nixos ❄️🎨

Tema de inicio de sesión **SDDM `ii-pixel`** oficial de [iNiR](https://github.com/snowarch/inir) empaquetado para **NixOS** (v2.33.0), con **sincronización automática de fondos de pantalla y colores dinámicos Material You** impulsada por **Matugen y Python**.

[![CI](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/ci.yml/badge.svg)](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/ci.yml)
[![Automated Upstream Sync](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/update-flake.yml/badge.svg)](https://github.com/LATAR-web/inir-sddm-nixos/actions/workflows/update-flake.yml)

**Español** | [English](README.md)

---

## ✨ Características (v2.33.0)

- **Estética Pixel y Material You**: Pantalla de login limpia y moderna idéntica a la pantalla de bloqueo de iNiR con colores dinámicos.
- **Motor de Color Mejorado (Matugen + Python)**:
  - Lee automáticamente las paletas calculadas de iNiR (`app-palette.json`, `colors.json`, `iris-washi.json`).
  - **Generación en Vivo con Matugen**: Si no existe una paleta previa, ejecuta directamente `matugen image <fondo> --json hex` para extraer tokens auténticos de Material You.
  - **Respaldo Puro en Python**: Integra un motor de análisis de croma y cuantización con PIL para garantizar armonía de colores incluso en instalaciones limpias.
- **Sincronización en Vivo**: Extrae el fondo activo (o primer fotograma de fondos animados con `ffmpeg`), el avatar (`~/.face`) y el esquema de color.
- **Módulo Declarativo de NixOS**: Una única opción habilita SDDM, el tema, dependencias de Qt 6 y los servicios de sincronización de systemd.
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

## 🔄 Herramienta CLI: `inir-sddm-sync`

El paquete incluye el binario ejecutable `inir-sddm-sync` con soporte para Matugen y Python:

```bash
# Sincronización automática desde la sesión activa de iNiR
inir-sddm-sync

# Sincronizar un fondo específico extrayendo colores con Matugen
inir-sddm-sync --wallpaper /ruta/a/mi-fondo.png

# Simulación (sin escribir archivos)
inir-sddm-sync --dry-run -v
```

---

## 🧪 Pruebas de la Pantalla de Inicio de Sesión

Para previsualizar la pantalla de inicio de sesión en una ventana de prueba en NixOS:

```bash
sddm-greeter --test-mode --theme /var/lib/sddm/themes/ii-pixel
```

---

## 📜 Licencia

Licencia GPL-3.0. Basado en el proyecto [iNiR](https://github.com/snowarch/inir).
