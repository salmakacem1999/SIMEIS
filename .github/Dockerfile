FROM rust:1.85.0-bookworm AS builder

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY simeis-data ./simeis-data
COPY simeis-server ./simeis-server

RUN cargo build --release -p simeis-server

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y libssl3 ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/target/release/simeis-server ./simeis-server

EXPOSE 8080

CMD ["./simeis-server"]