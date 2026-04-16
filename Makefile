# Flags de compilation Rust
RUSTFLAGS := -C code-model=kernel -C codegen-units=1

# Cible par défaut : compiler le projet
build:
	set RUSTFLAGS=$(RUSTFLAGS) && cargo build

# Compiler en mode release (optimisé)
release:
	set RUSTFLAGS=$(RUSTFLAGS) && cargo build --release
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