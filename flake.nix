{
  description = "Official iNiR ii-pixel SDDM theme packaged for NixOS with automatic wallpaper & Material You color synchronization";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    inir = {
      url = "github:snowarch/inir";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, inir, ... }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        rec {
          default = ii-pixel-sddm;

          ii-pixel-sddm = pkgs.callPackage ./pkgs/ii-pixel-sddm {
            inirSrc = inir;
          };

          inir-sddm-sync = pkgs.callPackage ./pkgs/sddm-sync-pixel { };
        });

      nixosModules = rec {
        default = inir-sddm;

        inir-sddm = { config, pkgs, ... }: {
          imports = [ ./modules/sddm.nix ];
          services.inir-sddm.package = nixpkgs.lib.mkDefault self.packages.${pkgs.system}.ii-pixel-sddm;
          services.inir-sddm.syncPackage = nixpkgs.lib.mkDefault self.packages.${pkgs.system}.inir-sddm-sync;
        };
      };
    };
}
