{ pkgs }: {
  deps = [
    pkgs.gdb
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
    pkgs.replitPackages.prybar-python310
    pkgs.replitPackages.stderred
  ];
}