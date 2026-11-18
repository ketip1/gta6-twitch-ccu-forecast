# gta6-twitch-ccu-forecast

Forecast hour-by-hour Twitch concurrent viewers for Grand Theft Auto VI on its
release day (2026-11-19 UTC), for the
[make.fun](https://make.fun) bounty `gta6-twitch-ccu-forecast-01`.

## Model

For each hour `h = 2..24` the forecast emits five quantiles (5%, 25%, 50%, 75%,
95%) of that hour's Twitch viewers:

```
q_tau(h) = p1 * exp(mu_h + z_tau * sigma_h)
```

* `p1 = max(1, hour-1 viewers)` — the one observed anchor a case provides.
* `z_tau` — standard-normal quantiles at the five levels.
* `mu_h`, `sigma_h` — a launch-shape curve fitted from the kit's comparables
  (past big game launches): for each launch, `ln(viewers_h / viewers_1)` over its
  release-UTC day; `mu_h` is the cross-launch median, `sigma_h` the IQR / 1.349
  robust std, median-smoothed across hours.

The resulting curve dips through the early UTC hours, climbs to an evening peak
around hours 18-19 (EU/US prime time, ~2.4x hour 1), then eases overnight.

Scoring is pinball loss on the log scale (lower is better). In leave-one-out
evaluation over the comparables the model scores ~0.797 vs ~0.930 for the house
baseline under the same per-launch setup.

## Running

```
mkdir -p out
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Reads every `*.in` in `$MAKEFUN_INPUT_DIR` (default `/input`), writes one
`<id>.out` per case to `$MAKEFUN_OUTPUT_DIR` (default `/output`). Stdlib only;
deterministic; no network, no randomness.

## License

MIT — see [LICENSE](LICENSE).