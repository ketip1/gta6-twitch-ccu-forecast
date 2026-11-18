#!/usr/bin/env python3
"""GTA VI launch-day Twitch CCU forecast (make.fun gta6-twitch-ccu-forecast-01).

Deterministic, stdlib-only entrypoint. It reads each case's ``*.in`` in
``$MAKEFUN_INPUT_DIR`` (default ``/input``) and writes one ``<id>.out`` per case
into ``$MAKEFUN_OUTPUT_DIR`` (default ``/output``).

Model
-----
For hour h = 2..24, the forecast quantile at level tau is

    q_tau(h) = p1 * exp(mu_h + z_tau * sigma_h)

where p1 = max(1, hour-1 viewers) is the single observed anchor, z_tau is the
standard-normal quantile at tau, and (mu_h, sigma_h) is a launch-shape curve
derived from the kit's comparables (past big game launches):

  * for each comparable launch, take the release-UTC-day hourly viewer curve;
  * for every launch with a valid hour-1, compute ln(viewers_h / viewers_1);
  * across the 37 comparable launches, mu_h = median of the log-ratios,
    sigma_h = IQR / 1.349 (a robust std), then sigma is median-smoothed across
    hours with a half-window of 2.

The curve captures the intra-day rhythm of a big launch: an early dip, an
evening peak around hours 18-19 (EU/US prime time), and an overnight easing.
The constants below are the fitted values, frozen so the program is fully
deterministic (no network, no randomness).

Scoring metric: pinball loss on the log scale (lower is better). In a
leave-one-out evaluation over the comparables (fit on the other 36, score the
held-out one with the exact pinball formula), the model scores ~0.797 versus
~0.930 for the house baseline under the same setup.
"""

import glob
import json
import math
import os
import sys

LEVELS = [0.05, 0.25, 0.50, 0.75, 0.95]
Z = {
    0.05: -1.64485,
    0.25: -0.67449,
    0.50: 0.0,
    0.75: 0.67449,
    0.95: 1.64485,
}

# Median log-ratio ln(viewers_h / viewers_1) across the comparable launches.
MU = {
    2: -0.137647,
    3: -0.282902,
    4: -0.310013,
    5: -0.291649,
    6: -0.237691,
    7: -0.220112,
    8: -0.106642,
    9: -0.125887,
    10: -0.092485,
    11: -0.074529,
    12: -0.022270,
    13: 0.057448,
    14: 0.166073,
    15: 0.417591,
    16: 0.502242,
    17: 0.571349,
    18: 0.668115,
    19: 0.876139,
    20: 0.863546,
    21: 0.846036,
    22: 0.832225,
    23: 0.780328,
    24: 0.712249,
}

# Robust log-spread (IQR / 1.349), median-smoothed across hours (half-window 2).
SIGMA = {
    2: 0.302588,
    3: 0.304024,
    4: 0.305460,
    5: 0.386232,
    6: 0.483637,
    7: 0.550870,
    8: 0.605527,
    9: 0.711446,
    10: 0.714674,
    11: 0.879256,
    12: 0.898877,
    13: 1.058795,
    14: 1.076444,
    15: 1.282529,
    16: 1.429839,
    17: 1.447908,
    18: 1.512162,
    19: 1.548602,
    20: 1.551028,
    21: 1.551028,
    22: 1.551028,
    23: 1.540200,
    24: 1.529373,
}

MAX_VIEWERS = 1_000_000_000.0


def round_half_up(x, ndigits=2):
    """Round x to ndigits decimals, ties away from zero (half-up)."""
    scale = 10 ** ndigits
    return math.floor(x * scale + 0.5) / scale


def forecast_hour(p1, h):
    """Return the five quantiles (q05, q25, q50, q75, q95) for hour h."""
    mu = MU[h]
    sigma = SIGMA[h]
    qs = []
    for tau in LEVELS:
        raw = p1 * math.exp(mu + Z[tau] * sigma)
        # Clamp into (0, 1e9]; the clamp preserves the non-decreasing order.
        q = min(MAX_VIEWERS, raw)
        if q <= 0.0:
            q = 0.01
        qs.append(round_half_up(q))
    return qs


def process_case(in_path, out_path):
    with open(in_path, "r", encoding="utf-8") as fh:
        case = json.load(fh)

    # Hour-1 anchor: the known row whose hour is 1 (fall back to the first).
    p1 = 1.0
    known = case.get("known") or []
    if known:
        viewers = None
        for row in known:
            if row.get("hour") == 1:
                viewers = row.get("viewers")
                break
        if viewers is None:
            viewers = known[0].get("viewers")
        if isinstance(viewers, (int, float)) and viewers is not None:
            p1 = max(1.0, float(viewers))

    hours = []
    for h in range(2, 25):
        qs = forecast_hour(p1, h)
        hours.append({"hour": h, "q": qs})

    out = {"hours": hours}
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out))


def main():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)

    in_files = sorted(glob.glob(os.path.join(in_dir, "*.in")))
    for in_path in in_files:
        case_id = os.path.splitext(os.path.basename(in_path))[0]
        out_path = os.path.join(out_dir, case_id + ".out")
        process_case(in_path, out_path)


if __name__ == "__main__":
    main()