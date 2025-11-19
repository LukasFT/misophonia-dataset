import hashlib
import uuid
from pathlib import Path
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
    prob_declared: float = 0.3,
    prob_dropout: float = 0.05,  # per-trial chance of subject stopping early
    reff_subject_intercept: tuple[float, float] = (0.0, 0.02),  # mean, sd
    reff_subject_trig: tuple[float, float] = (0.0, 0.15),  # mean, sd
    reff_item_intercept: tuple[float, float] = (0.0, 0.07),
    reff_item_trig: tuple[float, float] = (0.0, 0.05),
    reff_category_trig: tuple[float, float] = (0.0, 0.05),  # per-category deviation applied on trigger trials
    reff_noise: tuple[float, float] = (0.0, 0.08),
    fixeff_intercept: float = 1.3,
    fixeff_trig: float = 0.3,
    fixeff_declared: float = 0.7,
    fixeff_identify: float = 0.2,
    fixeff_foams: float = 0.08,
    fixeff_order: float = 0.02,
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
            "category",         # str – "ctrl" on control trials, else the trigger category
        }

    Design features:
      - Crossed subjects × item pairs with A/B masking.
      - A universal anchor pair is presented twice per subject (first and last).
      - Subjects declare triggering categories with probability `prob_declared` per category.
      - Optional early dropout with `prob_dropout`, truncating non-anchor trials.
      - Ratings follow an additive model + noise, rounded/clipped to [0,5].

    Random effects (all mean 0):
      - Subject:   b0_s (intercept), b1_s (trigger slope)
      - Item/pair: b0_i (intercept), b1_i (trigger slope)
      - Category:  b_cat (trigger-only deviation; control uses category="ctrl" with 0 shift)
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

    # ----- RANDOM EFFECTS: pre-sample for categories, items, subjects -----
    # Category effects apply only on trigger trials. Control uses category="ctrl" with 0 effect.
    cat_effect_trig: dict[str, float] = {cat: float(rng.normal(*reff_category_trig)) for cat in categories}
    cat_effect_trig["ctrl"] = 0.0  # ensure no shift on control trials

    # Item (pair) intercept & trigger slope (include anchor pair)
    item_b0: dict[str, float] = {}
    item_b1: dict[str, float] = {}
    for p in pairs:
        item_b0[p["pair_uuid"]] = float(rng.normal(*reff_item_intercept))
        item_b1[p["pair_uuid"]] = float(rng.normal(*reff_item_trig))
    item_b0[anchor_pair_uuid] = float(rng.normal(*reff_item_intercept))
    item_b1[anchor_pair_uuid] = float(rng.normal(*reff_item_trig))

    # ----- Subjects -----
    subjects = []
    # Subject intercept & trigger slope
    subj_b0: dict[str, float] = {}
    subj_b1: dict[str, float] = {}
    for _ in range(n_subjects):
        s_uuid = uuid.uuid4().hex
        subjects.append(
            {
                "subject_uuid": s_uuid,
                "group_ab": rng.choice(["A", "B"]),
                # Declared trigger set: Bernoulli per category
                "declared": {cat for cat in categories if rng.random() < prob_declared},
            }
        )
        subj_b0[s_uuid] = float(rng.normal(*reff_subject_intercept))
        subj_b1[s_uuid] = float(rng.normal(*reff_subject_trig))  # trig slope >=0

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
            is_decl_trig_pair = int(p["category"] in declared)
            is_decl_trig = int(is_trig == 1 and is_decl_trig_pair == 1)

            # did_identify: mostly relevant on trigger trials; more likely when declared
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
                    "is_declared_trig_pair": is_decl_trig_pair,
                    "order": None,  # fill later
                    "is_foams": int(is_trig == 1 and p["is_foams_pair"] == 1),
                    "is_anchor": 0,
                    "is_reused": 0,
                    "did_identify": did_identify,
                    "pair_category": p["category"],  # NEW
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
        anchor_decl_pair = int(anchor_category in declared)
        first_anchor_decl = int(first_anchor_is_trig == 1 and anchor_decl_pair == 1)
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
                "is_declared_trig_pair": anchor_decl_pair,
                "order": None,
                "is_foams": 0,
                "is_anchor": 1,
                "is_reused": 0,
                "did_identify": int(first_anchor_identify),
                "pair_category": anchor_category,
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
                "is_declared_trig_pair": anchor_decl_pair,
                "order": None,
                "is_foams": 0,
                "is_anchor": 1,
                "is_reused": 1,
                "did_identify": int(last_anchor_identify),
                "pair_category": anchor_category,
            }
        )

        # Set order sequentially for all newly-added rows from this subject:
        subject_rows_idx = [i for i, r in enumerate(records) if r["subject_uuid"] == s_uuid and r["order"] is None]
        for local_ord, idx in enumerate(subject_rows_idx, start=1):
            records[idx]["order"] = local_ord

        # Generate ratings after knowing M and order
        # Simple additive model with noise, then round/clipped to [0..5]
        for idx in subject_rows_idx:
            r = records[idx]

            sb0 = subj_b0[r["subject_uuid"]]
            sb1 = subj_b1[r["subject_uuid"]]
            ib0 = item_b0[r["pair_uuid"]]
            ib1 = item_b1[r["pair_uuid"]]
            # category effect applies only on trigger trials; category is "ctrl" on controls (0 effect)
            cat_eff = cat_effect_trig.get(r["pair_category"], 0.0) if r["is_trig"] == 1 else 0.0

            mu = (
                fixeff_intercept
                + fixeff_trig * r["is_trig"]
                + fixeff_declared * r["is_declared_trig"] * r["is_trig"]
                + fixeff_identify * r["did_identify"]
                + fixeff_foams * r["is_foams"] * r["is_trig"]
                + fixeff_order * (r["order"] - 1)
                + sb0
                + sb1 * r["is_trig"]  # subject REs
                + ib0
                + ib1 * r["is_trig"]  # item REs
                + cat_eff  # category RE (trigger-only)
            )

            # r["rating"] = int(np.clip(np.rint(mu + rng.normal(*reff_noise)), 0, 5))
            r["rating"] = float(mu + rng.normal(*reff_noise))  # Debug

    df = pd.DataFrame(records)

    # Ensure types are sensible
    int_cols = [
        # "rating",
        "is_trig",
        "is_declared_trig",
        "order",
        "is_foams",
        "is_anchor",
        "is_reused",
        "did_identify",
    ]
    df[int_cols] = df[int_cols].astype(int)

    df["version"] = np.where(df["is_trig"] == 1, "trig", "ctrl")
    df["category"] = np.where(df["is_trig"] == 1, df["pair_category"], "ctrl")

    return df


if __name__ == "__main__":
    data = create_dummy_data()
    data.to_csv(Path(__file__).parent.parent / "data" / "dummy_data.csv", index=False)
