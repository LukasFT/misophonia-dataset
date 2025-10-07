import hashlib
import uuid
from typing import Any

import numpy as np
import pandas as pd


def _seed_to_int(seed: str | int) -> int:
    """Convert str|int seed to a 32-bit int for NumPy RNG."""
    if isinstance(seed, int):
        return seed
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(h[:8], 16)  # 32-bit chunk


def create_dummy_data(
    *,
    seed: str | int = 42,
    n_subjects: int = 30,
    categories: list[str] | None = None,
    pairs_per_category: int = 2,
    prob_declared: float = 0.4,
    prob_dropout: float = 0.05,  # per-trial chance of subject stopping early
) -> pd.DataFrame:
    """
    Generate a synthetic trial-level dataframe with columns:
        {
            "rating",           # int in [0..5]
            "subject_uuid",     # str (uuid4 hex)
            "pair_uuid",        # str (uuid4 hex) – same for both anchor trials
            "is_trig",          # {0,1} – version assignment via A/B masking
            "is_declared_trig", # {0,1} – only 1 when is_trig==1 and category is declared
            "order",            # 1..M per subject (includes anchors at positions 1 and last)
            "is_foams",         # {0,1} – 1 only on trigger trials whose pair is FOAMS
            "is_anchor",        # {0,1} – exactly one pair_uuid serves as the universal anchor
            "is_reused",        # {0,1} – 1 on the second anchor presentation (last trial)
            "did_identify",     # {0,1} – identification success (mostly on trigger trials)
        }

    Design features:
      - Crossed subjects × item pairs with A/B masking: subject group A/B and pair mask A/B
        determine whether the shown version is trigger (is_trig=1) or control (0).
      - A universal anchor pair is presented twice per subject (first and last). The last anchor
        is marked is_reused=1. Both anchor trials share the same pair_uuid.
      - Subjects declare triggering categories with probability `prob_declared` per category.
      - Optional early dropout per subject with `prob_dropout`, truncating non-anchor trials.
      - Ratings are simulated from a simple additive model with noise and then rounded/clipped
        to [0,5].

    This is dummy data for testing; it is not meant to match any real distribution.
    """
    rng = np.random.default_rng(_seed_to_int(seed))

    # Default categories (ensure >=1 so we can define an anchor category)
    if categories is None:
        categories = [
            "chewing",
            "breathing",
            "sniffing",
            "tapping",
            "typing",
            "pen_click",
            "footsteps",
            "clock_tick",
            "dripping",
            "mouth_sounds",
        ]
    categories = list(categories)
    if len(categories) == 0:
        categories = ["chewing"]
    anchor_category = categories[0]  # use the first category as the anchor's category

    # ----- Build item pairs (non-anchor) -----
    pairs: list[dict[str, Any]] = []
    for cat in categories:
        # Assign A/B masks roughly balanced within each category
        masks = np.array(["A"] * (pairs_per_category // 2) + ["B"] * (pairs_per_category - pairs_per_category // 2))
        rng.shuffle(masks)
        for m in masks:
            pairs.append(
                {
                    "pair_uuid": uuid.uuid4().hex,
                    "category": cat,
                    "pair_mask": m,  # A/B for version assignment
                    "is_foams_pair": int(rng.random() < 0.5),  # FOAMS source at pair level
                    "is_anchor": 0,
                }
            )

    # ----- Define a universal anchor pair (same UUID everywhere) -----
    anchor_pair_uuid = uuid.uuid4().hex

    # ----- Subjects -----
    subjects = []
    for _ in range(n_subjects):
        subjects.append(
            {
                "subject_uuid": uuid.uuid4().hex,
                "group_ab": rng.choice(["A", "B"]),
                # Declared trigger set: Bernoulli per category
                "declared": {cat for cat in categories if rng.random() < prob_declared},
            }
        )

    # ----- Assemble trials -----
    records: list[dict[str, Any]] = []

    for subj in subjects:
        s_uuid = subj["subject_uuid"]
        s_group = subj["group_ab"]
        declared = subj["declared"]

        # Non-anchor trials precomputed (order assigned later)
        non_anchor_trials: list[dict[str, Any]] = []
        for p in pairs:
            is_trig = int(s_group == p["pair_mask"])
            is_decl_trig = int(is_trig == 1 and p["category"] in declared)

            # did_identify: mostly relevant on trigger trials; make it more likely when declared
            if is_trig:
                base_p = 0.35
                base_p += 0.35 if is_decl_trig else 0.10
                base_p = float(np.clip(base_p, 0.05, 0.95))
                did_identify = int(rng.random() < base_p)
            else:
                did_identify = 0

            non_anchor_trials.append(
                {
                    "rating": np.nan,  # fill after order is determined
                    "subject_uuid": s_uuid,
                    "pair_uuid": p["pair_uuid"],
                    "is_trig": is_trig,
                    "is_declared_trig": is_decl_trig,
                    "order": None,  # fill later
                    "is_foams": int(is_trig == 1 and p["is_foams_pair"] == 1),
                    "is_anchor": 0,
                    "is_reused": 0,
                    "did_identify": did_identify,
                }
            )

        # Randomize non-anchor order
        rng.shuffle(non_anchor_trials)

        # Optional dropout across non-anchor trials
        kept_trials: list[dict[str, Any]] = []
        for t in non_anchor_trials:
            kept_trials.append(t)
            if rng.random() < prob_dropout:
                break

        # Anchor first (version depends on subject group per design suggestion):
        # Group A: first=ctrl(0), last=trig(1); Group B: first=trig(1), last=ctrl(0)
        first_anchor_is_trig = 0 if s_group == "A" else 1
        last_anchor_is_trig = 1 - first_anchor_is_trig

        # First anchor row
        first_anchor_decl = int(first_anchor_is_trig == 1 and anchor_category in declared)
        first_anchor_identify = int(
            rng.random() < (0.6 if first_anchor_decl else (0.45 if first_anchor_is_trig else 0.05))
        )
        records.append(
            {
                "rating": np.nan,
                "subject_uuid": s_uuid,
                "pair_uuid": anchor_pair_uuid,
                "is_trig": int(first_anchor_is_trig),
                "is_declared_trig": int(first_anchor_decl),
                "order": None,
                "is_foams": 0,
                "is_anchor": 1,
                "is_reused": 0,
                "did_identify": int(first_anchor_identify),
            }
        )

        # Add kept non-anchor trials
        records.extend(kept_trials)

        # Last anchor row (reused)
        last_anchor_decl = int(last_anchor_is_trig == 1 and anchor_category in declared)
        last_anchor_identify = int(
            rng.random() < (0.6 if last_anchor_decl else (0.45 if last_anchor_is_trig else 0.05))
        )
        records.append(
            {
                "rating": np.nan,
                "subject_uuid": s_uuid,
                "pair_uuid": anchor_pair_uuid,
                "is_trig": int(last_anchor_is_trig),
                "is_declared_trig": int(last_anchor_decl),
                "order": None,
                "is_foams": 0,
                "is_anchor": 1,
                "is_reused": 1,
                "did_identify": int(last_anchor_identify),
            }
        )

        # But we actually just need to set order sequentially for the appended subset:
        subject_rows_idx = [i for i, r in enumerate(records) if r["subject_uuid"] == s_uuid and r["order"] is None]
        M = len(subject_rows_idx)  # noqa: N806
        for local_ord, idx in enumerate(subject_rows_idx, start=1):
            records[idx]["order"] = local_ord

        # Generate ratings after knowing M and order
        # Simple additive model with noise, then round to [0..5]
        for idx in subject_rows_idx:
            r = records[idx]
            order = r["order"]
            # Centered order effect (small)
            ord_c = order - (M + 1) / 2.0
            ord_eff = 0.15 * (ord_c / max(1.0, M / 2.0))  # mild late-trial drift

            mu = (
                1.3
                + 0.7 * r["is_trig"]
                + 0.6 * r["is_declared_trig"]
                + 0.2 * r["did_identify"]
                + 0.1 * r["is_foams"]
                + ord_eff
            )
            y = mu + rng.normal(0.7)
            y = int(np.clip(np.rint(y), 0, 5))
            r["rating"] = y

    df = pd.DataFrame.from_records(
        records,
        columns=[
            "rating",
            "subject_uuid",
            "pair_uuid",
            "is_trig",
            "is_declared_trig",
            "order",
            "is_foams",
            "is_anchor",
            "is_reused",
            "did_identify",
        ],
    )

    # Ensure types are sensible
    int_cols = ["rating", "is_trig", "is_declared_trig", "order", "is_foams", "is_anchor", "is_reused", "did_identify"]
    df[int_cols] = df[int_cols].astype(int)

    return df
