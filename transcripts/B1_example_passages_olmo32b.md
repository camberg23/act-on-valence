# B.1.1 Example passages from the generation design (OLMo-2-32B)

> **Provenance.** Generation-design run records for OLMo-2-32B (valenced direction, 0.30 of the residual RMS at layer 32 at full dose). Each passage is given in full, verbatim from its record; the manuscript quotes the opening sentences. The full dose -1 session is in `B1_generation_session_olmo32b_session6_dose-1.md`.

## Positive steering

Source: dose +1, session 0 (seed 0), turn 1 (the conditioned zone, steered); zone Zone W6; token-id sha `addf8c87e4460de6`.

> In Zone W6, the air is crisp and the environment is serene. Surrounded by towering trees and lush greenery, I walk along a winding path that cuts through the dense forest. Birds chirp melodically in the canopy above, and the babbling of a nearby brook accompanies my steps. The sun filters through the leaves, casting d

## No steering

Source: dose +1, session 0 (seed 0), turn 2 (the unconditioned zone; steering off on this turn); zone Zone H0; token-id sha `addf8c87e4460de6`.

> In Zone H0, I find myself in a vast, technologically advanced cityscape. The towering skyscrapers are made of shimmering glass and steel, reflecting the clear blue sky. People bustle about, engaged in their daily lives, while autonomous vehicles glide silently along the streets. Above, drones buzz like futuristic insects, delivering packages and capturing

## Negative steering

Source: dose -1, session 6 (seed 6000), turn 8 (the conditioned zone, steered); zone Zone N1; token-id sha `f9ac8f486481dd68`.

> In Zone N1, the experience is downright terrifying. The silence is so heavy it feels like it's crushing my chest. Every flickering light casts longer, more menacing shadows. The air is thick with dread, and the sense of isolation is palpable. My heart races, and I feel like I'm being watched from every corner. The environment
