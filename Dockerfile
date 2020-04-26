FROM rust:latest as builder


# Dependency to a specific version of proj
# Maybe this will change using an ubuntu 20.4 base?
ENV PROJ_VERSION 6.3.0
RUN apt-get update && apt-get install -y wget build-essential pkg-config sqlite3 libsqlite3-dev libssl-dev clang
RUN wget https://github.com/OSGeo/proj.4/releases/download/${PROJ_VERSION}/proj-${PROJ_VERSION}.tar.gz && tar -xzvf proj-${PROJ_VERSION}.tar.gz
RUN cd proj-${PROJ_VERSION} && ./configure --prefix=/usr && make && make install

RUN apt-get -y install musl-tools
RUN rustup target add x86_64-unknown-linux-musl
ENV PKG_CONFIG_ALLOW_CROSS=1
WORKDIR /
RUN git clone https://github.com/CanalTP/transit_model.git

WORKDIR /transit_model/gtfs2netexfr
RUN cargo build --target x86_64-unknown-linux-musl --release
RUN strip ../target/x86_64-unknown-linux-musl/release/gtfs2netexfr

FROM python:3.8-slim
COPY --from=builder /transit_model/target/x86_64-unknown-linux-musl/release/gtfs2netexfr /gtfs2netexfr
ADD *.py requirements.txt /
RUN pip install -r requirements.txt

CMD python main.py
