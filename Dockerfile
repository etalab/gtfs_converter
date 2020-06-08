FROM rust:latest as builder

# Dependency to a specific version of proj
# Maybe this will change using an ubuntu 20.4 base?
ENV PROJ_VERSION 6.3.0
RUN apt-get update && apt-get install -y wget build-essential pkg-config sqlite3 libsqlite3-dev libssl-dev clang
RUN wget https://github.com/OSGeo/proj.4/releases/download/${PROJ_VERSION}/proj-${PROJ_VERSION}.tar.gz && \
    tar -xzvf proj-${PROJ_VERSION}.tar.gz && \
    cd proj-${PROJ_VERSION} &&\
    ./configure --prefix=/usr &&\
    make &&\
    make install

WORKDIR /
RUN git clone https://github.com/CanalTP/transit_model.git

WORKDIR /transit_model/gtfs2netexfr
RUN cargo build --release
RUN strip ../target/release/gtfs2netexfr

FROM python:3.8-slim
COPY --from=builder /transit_model/target/release/gtfs2netexfr /usr/local/bin/gtfs2netexfr
ENV NETEX_CONVERTER gtfs2netexfr

# copy libproj and its assets
COPY --from=builder /usr/lib/libproj* /usr/lib /usr/lib/
COPY --from=builder /usr/share/proj/ /usr/share/proj/

ADD requirements.txt /
RUN pip install -r requirements.txt
ADD *.py /


CMD python main.py
