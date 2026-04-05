{
  description = "A-Evolve — agentic evolution framework";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.python311
              pkgs.uv
              pkgs.git
              pkgs.docker-client
            ];

            shellHook = ''
              if [ ! -d .venv ]; then
                echo "Creating venv..."
                uv venv .venv --python python3.11
              fi
              source .venv/bin/activate
              echo "a-evolve dev shell — $(python --version)"
              echo "Install deps: uv pip install -e '.[anthropic,dev]'"
            '';
          };
        }
      );
    };
}
