import json
from pathlib import Path


OUTPUT_FILE = Path(
    "evaluation/evidence_chunk_map_structural.json"
)


# ---------------------------------------------------------
# Verified Structural v2 chunk IDs
# AAPL 2024
# ---------------------------------------------------------

CHUNK_30 = (
    "8fa97f1bd7ff0bbb2ed0bf235192d112"
    "689b19f10d1c53ce697808e6afc3f9d5"
)

CHUNK_44 = (
    "e034f54d73a54a81c0d71dffd2544015"
    "1d5588bdfb84d4508f7570d8f30de1be"
)

CHUNK_47 = (
    "cdcf28763b5ff377dcaef67d65699ba1b"
    "0db8d1f7ad4e42361e76d935e19f982"
)

CHUNK_118 = (
    "04a7f38418edf8e5ff8f874cfce71a302"
    "567ca8cd42e51061b7e8ce2448322c6"
)

CHUNK_119 = (
    "2844d0c7abbb693cac8944974c520d3e"
    "43f8ca9d32e43643b2e09d25bbfe0e86"
)

CHUNK_120 = (
    "53605b269c1b156ac75ee489e46a84c4"
    "0f1ceae54009f8cd63abf9dbbebf5d01"
)

CHUNK_138 = (
    "8269a4b2e5552507bd59474307c85bed"
    "843ad7e23df91c45d635bbd2b86ccfbe"
)

CHUNK_139 = (
    "3b5095e03cd26e1850861e622b10a44b"
    "69b923f6c70e47f759ad63424effa078"
)

CHUNK_160 = (
    "675c60d95a1338db4e1b1f5878ce12ac"
    "195d0cdc911b6f15f900a49901279935"
)

CHUNK_162 = (
    "a42a42372f16b742af7c762a3e9437e7"
    "d05c7f65277521387a7ac98e5205f018"
)


mapping = {
    "Q001": {
        "evidence_items": [
            {
                "evidence_index": 1,
                "acceptable_chunk_groups": [
                    [CHUNK_138],
                    [CHUNK_119],
                    [CHUNK_160],
                ],
            }
        ]
    },

    "Q002": {
        "evidence_items": [
            {
                "evidence_index": 1,
                "acceptable_chunk_groups": [
                    [CHUNK_138],
                ],
            }
        ]
    },

    "Q004": {
        "evidence_items": [
            {
                "evidence_index": 1,
                "acceptable_chunk_groups": [
                    [CHUNK_138],
                    [CHUNK_119],
                    [CHUNK_160],
                ],
            }
        ]
    },

    "Q006": {
        "evidence_items": [
            {
                "evidence_index": 1,
                "acceptable_chunk_groups": [
                    [CHUNK_119],
                    [CHUNK_160],
                    [CHUNK_138],
                ],
            }
        ]
    },

    "Q011": {
        "evidence_items": [
            {
                "evidence_index": 1,
                "acceptable_chunk_groups": [
                    [CHUNK_139],
                    [CHUNK_162],
                ],
            }
        ]
    },

    "Q015": {
        "evidence_items": [
            {
                "evidence_index": 1,
                "acceptable_chunk_groups": [
                    [CHUNK_139],
                    [CHUNK_162],
                ],
            }
        ]
    },

    "Q020": {
        "evidence_items": [
            {
                "evidence_index": 1,
                "acceptable_chunk_groups": [
                    [CHUNK_119],
                    [CHUNK_160],
                ],
            }
        ]
    },

    "Q021": {
        "evidence_items": [
            {
                "evidence_index": 1,
                "acceptable_chunk_groups": [
                    [
                        CHUNK_30,
                        CHUNK_44,
                        CHUNK_47,
                    ]
                ],
            }
        ]
    },

    "Q027": {
        "evidence_items": [
            {
                "evidence_index": 1,
                "acceptable_chunk_groups": [
                    [CHUNK_119],
                    [CHUNK_160],
                ],
            }
        ]
    },

    "Q028": {
        "evidence_items": [
            {
                "evidence_index": 1,
                "acceptable_chunk_groups": [
                    [CHUNK_139],
                    [CHUNK_162],
                ],
            }
        ]
    },

    "Q031": {
        "evidence_items": [
            {
                "evidence_index": 1,
                "acceptable_chunk_groups": [
                    [
                        CHUNK_119,
                        CHUNK_120,
                    ]
                ],
            }
        ]
    },

    "Q032": {
        "evidence_items": [
            {
                "evidence_index": 1,
                "acceptable_chunk_groups": [
                    [CHUNK_119],
                    [CHUNK_160],
                ],
            }
        ]
    },

    "Q040": {
        "evidence_items": [
            {
                "evidence_index": 1,
                "acceptable_chunk_groups": [
                    [
                        CHUNK_118,
                        CHUNK_119,
                    ]
                ],
            }
        ]
    },
}


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        mapping,
        file,
        indent=2,
    )

print(
    f"Wrote {len(mapping)} mappings "
    f"to {OUTPUT_FILE}"
)