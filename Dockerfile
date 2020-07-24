FROM navitia/transit_model:v0.24.0 as transit_model

FROM rust:latest as builder

WORKDIR /
ADD https://gitlab.com/api/v4/projects/17544282/repository/branches/master version.json
RUN git clone --depth=1 --branch master --single-branch https://gitlab.com/CodeursEnLiberte/gtfs-to-geojson.git
WORKDIR /gtfs-to-geojson
RUN cargo build --release
RUN strip ./target/release/gtfs-geojson

FROM osgeo/gdal
WORKDIR /
RUN apt update -y \
    && DEBIAN_FRONTEND=noninteractive apt install -y --fix-missing --no-install-recommends \
       python3-pip \
       zip \
    && apt clean
COPY --from=transit_model /usr/local/bin/gtfs2netexfr /usr/local/bin/gtfs2netexfr
COPY --from=builder /gtfs-to-geojson/target/release/gtfs-geojson /usr/local/bin/gtfs-geojson
ENV NETEX_CONVERTER gtfs2netexfr
ENV GEOJSON_CONVERTER gtfs-geojson

ADD requirements.txt /
RUN pip3 install -r requirements.txt
ADD gtfs_converter /gtfs_converter

WORKDIR /gtfs_converter
