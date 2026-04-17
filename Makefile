# Flags de compilation Rust
# -C code-model=kernel  : optimise le modèle mémoire
# -C codegen-units=1    : compile en un seul bloc pour meilleures optimisations
RUSTFLAGS := -C code-model=kernel -C codegen-units=1

# Compiler en mode debug
build:
	RUSTFLAGS="$(RUSTFLAGS)" cargo build --verbose

# Compiler en mode release + strip du binaire
release:
	RUSTFLAGS="$(RUSTFLAGS)" cargo build --release --verbose
	strip target/release/simeis-server

# Vérifier le code sans compiler
check:
	cargo check

# Lancer les tests unitaires
test:
	cargo test

# Compiler la documentation avec typst
manual:
	-typst compile doc/manual.typ

# Nettoyer les fichiers de build
clean:
	cargo clean