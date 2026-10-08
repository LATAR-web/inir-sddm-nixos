{ lib
, python3
, makeWrapper
, ffmpeg
}:

let
  pythonEnv = python3.withPackages (ps: with ps; [
    pillow
  ]);
in
python3.pkgs.buildPythonApplication {
  pname = "inir-sddm-sync";
  version = "1.0.0";
  format = "other";

  src = ./.;

  nativeBuildInputs = [ makeWrapper ];

  propagatedBuildInputs = [
    pythonEnv
    ffmpeg
  ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin
    cp sync-pixel-sddm.py $out/bin/inir-sddm-sync
    chmod +x $out/bin/inir-sddm-sync

    wrapProgram $out/bin/inir-sddm-sync \
      --prefix PATH : ${lib.makeBinPath [ ffmpeg pythonEnv ]}

    runHook postInstall
  '';

  meta = with lib; {
    description = "Dynamic synchronizer for iNiR's ii-pixel SDDM theme on NixOS";
    homepage = "https://github.com/LATAR-web/inir-sddm-nixos";
    license = licenses.gpl3Only;
    platforms = platforms.linux;
    mainProgram = "inir-sddm-sync";
  };
}
