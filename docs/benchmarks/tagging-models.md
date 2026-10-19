# Tagging model bake-off

Run on 2026-10-19: 25 cases from `backend/src/voices/bakeoff/tagging_cases.json`, each decided once by each model through the production tagging decision (atlas plate 60). Cost is at OpenRouter's listed prices (`voices/bakeoff/pricing.py`).

|  | anthropic/claude-haiku-5.5 | anthropic/claude-sonnet-5.5 |
| --- | --- | --- |
| Right | 21 of 25 (84%) | 22 of 25 (88%) |
| Attached to the wrong topic | 1 | 1 |
| Started a topic that already exists | 0 | 0 |
| Called a real conversation noise | 2 | 0 |
| Attached a new subject to an old topic | 1 | 2 |
| Kept noise as a topic | 0 | 0 |
| Made no decision | 0 | 0 |
| Look-ups per decision | 0.3 | 0.3 |
| Model calls per decision | 1.2 | 1.2 |
| Seconds per decision | 2.6 | 2.5 |
| Tokens read, written | 76,144, 10,181 | 63,551, 4,689 |
| Cost of the run | $0.0127 | $0.1740 |

## Case by case

| Case | Right answer | anthropic/claude-haiku-5.5 | anthropic/claude-sonnet-5.5 |
| --- | --- | --- | --- |
| stolen-hinckley | attach: Stolen boats | ✓ attach: Stolen boats | ✓ attach: Stolen boats |
| learning-lessons-by-region | attach: Learning to sail | ✓ attach: Learning to sail | ✓ attach: Learning to sail |
| sailing-school-experiences | attach: Learning to sail | ✓ attach: Learning to sail | ✓ attach: Learning to sail |
| lake-to-coastal | attach: Learning to sail | ✓ attach: Learning to sail | ✓ attach: Learning to sail |
| yacht-clubs-melbourne | attach: Learning to sail | ✓ attach: Learning to sail | ✓ attach: Learning to sail |
| first-boat-choices | attach: Buying a boat | ✓ attach: Buying a boat | ✓ attach: Buying a boat |
| smallest-dinghy | attach: Buying a boat | ✓ attach: Buying a boat | ✓ attach: Buying a boat |
| finally-bought-a-boat | attach: Buying a boat | ✗ attach: Sail handling and running rigging | ✗ attach: Sail handling and running rigging |
| sheets-and-reefing | attach: Sail handling and running rigging | ✓ attach: Sail handling and running rigging | ✓ attach: Sail handling and running rigging |
| hardware-identification | attach: Repairs and hardware | ✓ attach: Repairs and hardware | ✓ attach: Repairs and hardware |
| cleat-and-kicker-parts | attach: Repairs and hardware | ✓ attach: Repairs and hardware | ✓ attach: Repairs and hardware |
| replacement-rudder | attach: Repairs and hardware | ✓ attach: Repairs and hardware | ✓ attach: Repairs and hardware |
| water-pump | attach: Repairs and hardware | ✓ attach: Repairs and hardware | ✓ attach: Repairs and hardware |
| bahamas-customs | attach: Cruising destinations and trip planning | ✓ attach: Cruising destinations and trip planning | ✓ attach: Cruising destinations and trip planning |
| key-largo | attach: Cruising destinations and trip planning | ✓ attach: Cruising destinations and trip planning | ✓ attach: Cruising destinations and trip planning |
| j24-euros | attach: Racing and regattas | ✓ attach: Racing and regattas | ✓ attach: Racing and regattas |
| galley-and-gas | attach: Life aboard | ✓ attach: Life aboard | ✓ attach: Life aboard |
| seasickness-and-injury | attach: Seasickness and health on board | ✓ attach: Seasickness and health on board | ✓ attach: Seasickness and health on board |
| docking-mishaps | mint | ✓ mint: Docking and close-quarters maneuvering | ✓ mint: Docking and seamanship mishaps |
| scenic-sails | mint | ✗ noise | ✓ mint: Photos and scenes from the water |
| ai-regatta-posters | mint | ✗ attach: Racing and regattas | ✗ attach: Racing and regattas |
| finding-sailing-company | mint | ✓ mint: Finding crew and sailing companions | ✓ mint: Finding sailing partners and crew |
| sailing-history | mint | ✗ noise | ✗ attach: Racing and regattas |
| grab-bag-no-text | noise | ✓ noise | ✓ noise |
| grab-bag-unrelated | noise | ✓ noise | ✓ noise |

