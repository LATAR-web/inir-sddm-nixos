{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.inir-sddm;
in
{
  options.services.inir-sddm = {
    enable = mkEnableOption "iNiR ii-pixel SDDM login theme and dynamic synchronization";

    package = mkOption {
      type = types.package;
      description = "The ii-pixel SDDM theme package.";
    };

    syncPackage = mkOption {
      type = types.package;
      description = "The inir-sddm-sync tool package.";
    };

    themeDir = mkOption {
      type = types.str;
      default = "/var/lib/sddm/themes/ii-pixel";
      description = "Mutable runtime directory where SDDM reads theme files and assets.";
    };

    wayland = {
      enable = mkOption {
        type = types.bool;
        default = true;
        description = "Run SDDM greeter in Wayland mode.";
      };

      compositor = mkOption {
        type = types.enum [ "niri" "default" ];
        default = "niri";
        description = "Compositor to drive the Wayland login screen. Niri eliminates hybrid GPU issues.";
      };
    };

    autoSync = {
      enable = mkOption {
        type = types.bool;
        default = true;
        description = "Automatically synchronize Material You colors, wallpaper, and avatar whenever changed in iNiR.";
      };
    };
  };

  # Backward compatibility alias
  options.programs.inir-sddm = config.services.inir-sddm;

  config = mkIf cfg.enable {
    # 1. SDDM Display Manager configuration
    services.displayManager.sddm = {
      enable = true;
      theme = "ii-pixel";
      extraPackages = with pkgs; [
        kdePackages.qtdeclarative
        kdePackages.qt5compat
        kdePackages.qtsvg
        kdePackages.qtmultimedia
      ];
      wayland.enable = cfg.wayland.enable;
      wayland.compositorCommand = mkIf (cfg.wayland.enable && cfg.wayland.compositor == "niri") (
        "${pkgs.niri}/bin/niri -c ${cfg.package}/share/inir/sddm/niri-greeter.kdl"
      );
      extraConfig = ''
        [Theme]
        ThemeDir=/var/lib/sddm/themes;/run/current-system/sw/share/sddm/themes
      '';
    };

    # 2. System packages
    environment.systemPackages = [
      cfg.package
      cfg.syncPackage
    ];

    # 3. Create mutable directory and symlinks for the theme
    systemd.tmpfiles.rules = [
      "d /var/lib/sddm 0755 sddm sddm - -"
      "d /var/lib/sddm/themes 0755 sddm sddm - -"
      "d ${cfg.themeDir} 0775 sddm users - -"
      "d ${cfg.themeDir}/assets 0775 sddm users - -"

      # Immutable QML, JS and font assets symlinked into the theme directory
      "L+ ${cfg.themeDir}/Main.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/Main.qml"
      "L+ ${cfg.themeDir}/ClassicLogin.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/ClassicLogin.qml"
      "L+ ${cfg.themeDir}/LoginAction.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/LoginAction.qml"
      "L+ ${cfg.themeDir}/LoginAvatar.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/LoginAvatar.qml"
      "L+ ${cfg.themeDir}/LoginCore.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/LoginCore.qml"
      "L+ ${cfg.themeDir}/LoginCover.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/LoginCover.qml"
      "L+ ${cfg.themeDir}/LoginEntry.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/LoginEntry.qml"
      "L+ ${cfg.themeDir}/LoginFrame.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/LoginFrame.qml"
      "L+ ${cfg.themeDir}/LoginLens.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/LoginLens.qml"
      "L+ ${cfg.themeDir}/LoginSubmit.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/LoginSubmit.qml"
      "L+ ${cfg.themeDir}/LoginSurface.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/LoginSurface.qml"
      "L+ ${cfg.themeDir}/LoginText.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/LoginText.qml"
      "L+ ${cfg.themeDir}/MSymbol.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/MSymbol.qml"
      "L+ ${cfg.themeDir}/PasswordCharsShape.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/PasswordCharsShape.qml"
      "L+ ${cfg.themeDir}/PixelDots.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/PixelDots.qml"
      "L+ ${cfg.themeDir}/VirtualKeyboard.qml - - - - ${cfg.package}/share/sddm/themes/ii-pixel/VirtualKeyboard.qml"
      "L+ ${cfg.themeDir}/metadata.desktop - - - - ${cfg.package}/share/sddm/themes/ii-pixel/metadata.desktop"
      "L+ ${cfg.themeDir}/fonts - - - - ${cfg.package}/share/sddm/themes/ii-pixel/fonts"
      "L+ ${cfg.themeDir}/shapes - - - - ${cfg.package}/share/sddm/themes/ii-pixel/shapes"

      # Initial mutable theme.conf and background (copied once if not present)
      "C+ ${cfg.themeDir}/theme.conf 0664 sddm users - ${cfg.package}/share/sddm/themes/ii-pixel/theme.conf"
      "C+ ${cfg.themeDir}/assets/background.png 0664 sddm users - ${cfg.package}/share/sddm/themes/ii-pixel/assets/background.png"
    ];

    # 4. Live synchronization service & path watcher in user session
    systemd.user = mkIf cfg.autoSync.enable {
      services.inir-sddm-sync = {
        description = "Synchronize active iNiR colors and wallpaper to SDDM login screen";
        serviceConfig = {
          Type = "oneshot";
          ExecStart = "${cfg.syncPackage}/bin/inir-sddm-sync --theme-dir ${cfg.themeDir}";
          StandardOutput = "journal";
          StandardError = "journal";
        };
        wantedBy = [ "default.target" ];
      };

      paths.inir-sddm-sync = {
        description = "Monitor iNiR theme and wallpaper changes for SDDM sync";
        pathConfig = {
          PathModified = [
            "%h/.local/state/quickshell/user/generated/colors.json"
            "%h/.local/state/quickshell/user/generated/theme-meta.json"
            "%h/.config/inir/config.json"
          ];
          Unit = "inir-sddm-sync.service";
        };
        wantedBy = [ "paths.target" ];
      };
    };
  };
}
