# Citizen Suite Chart

This chart deploys the full API gateway demo stack by orchestrating subcharts.

- One subchart per application (`citizen`, `dogcatcher`, `certosaur`, etc.).
- Supporting stack components (`postgres`, `kong`) are deployed as first-class local charts.
- APISIX is deployed from the official APISIX chart repository.
- No Bitnami chart dependencies are introduced by this citizen-suite chart.

Value paths are clean and map directly to each subchart. Example:

`dogcatcher.image.tag=latest`

## No Bitnami Policy

This chart must not use Bitnami charts or Bitnami container images.

- Keep APISIX etcd on `gcr.io/etcd-development/etcd`.
- Preserve the override at `apisix.etcd.image.*` in `values.yaml` and `my-values.yaml`.
