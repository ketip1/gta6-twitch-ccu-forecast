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

* `p1 = max(1, hour-1 viewers)` — the single observed anchor a case provides.
* `z_tau` — standard-normal quantiles at the five levels.
* `mu_h = shape_h * ln(peak_ratio)` where `shape_h` is a peak-normalised
  canonical launch curve and `peak_ratio` is a **size effect**: bigger
  launch-day hour-1 audiences flatten the curve
  (`ln peak_ratio = b0 + b1 * ln p1`).
* `sigma_h` — robust per-hour spread (IQR/1.349 of the residuals), median
  smoothed across hours.

Both pieces are fitted over console releases that unlocked at rolling local
midnight (GTA VI's own unlock). The curve dips through the early UTC hours,
climbs to an evening peak around hours 18-21 (EU/US prime time), then eases
overnight.

Scoring is pinball loss on the log scale (lower is better). In leave-one-out
evaluation over the console rolling-midnight comparables, the size-aware model
scores about **0.28** versus **~0.37** for the house persistence baseline under
the same per-launch setup.

## Running

```
mkdir -p out
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Deterministic (no randomness, no network), stdlib only.
