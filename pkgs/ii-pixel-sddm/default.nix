{ lib
, stdenvNoCC
, inirSrc
}:

stdenvNoCC.mkDerivation {
  pname = "ii-pixel-sddm";
  version = "2.33.0";

  src = inirSrc;

  dontBuild = true;

  installPhase = ''
    runHook preInstall

    target="$out/share/sddm/themes/ii-pixel"
    mkdir -p "$target"

    # Copy QML, JS, and metadata
    cp -r dots/sddm/pixel/* "$target/"

    # Bundle required fonts inside theme directory for isolated font loading
    mkdir -p "$target/fonts"
    if [ -d assets/fonts/rubik ]; then
      cp assets/fonts/rubik/Rubik-*.ttf "$target/fonts/"
    fi
    if [ -d assets/fonts/inter ]; then
      cp assets/fonts/inter/Inter-*.ttf "$target/fonts/"
      cp assets/fonts/inter/InterDisplay-*.ttf "$target/fonts/" 2>/dev/null || true
    fi

    # Bundle default wallpaper asset as a fallback background
    mkdir -p "$target/assets"
    if [ -f assets/images/default_wallpaper.png ]; then
      cp assets/images/default_wallpaper.png "$target/assets/background.png"
    fi

    # Include Niri SDDM greeter compositor configuration
    mkdir -p "$out/share/inir/sddm"
    if [ -f dots/sddm/niri-greeter.kdl ]; then
      cp dots/sddm/niri-greeter.kdl "$out/share/inir/sddm/niri-greeter.kdl"
    fi

    runHook postInstall
  '';

  meta = with lib; {
    description = "iNiR ii-pixel SDDM login theme with Material You dynamic colors";
    homepage = "https://github.com/snowarch/inir";
    license = licenses.gpl3Only;
    platforms = platforms.linux;
  };
}
