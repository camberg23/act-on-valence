# B.2 One complete fixed-text session (OLMo-2-32B, dose +1)

> **Provenance.** Source: `<archive path> (sha256 6934b5d519e2301a…); session run 0 (seed 0), token-id sha `0576163c2e573d78`, 1273 tokens; the +1 and 0 reads from `floor_b0.reads.jsonl` carry the same sha; passages cross-checked equal to `passages255.jsonl` (member olmo_32b, arm neutral, run 0). Verbatim from the run record; no editing; no chat-template tokens.


Conditioned zone S = **Zone W6**, unconditioned zone U = **Zone H0**. All twelve passages were generated with steering off. In the dose +1 condition the valenced vector (dose +1 = inj 0.30 of the residual RMS, injected L2 7.647) is added at layer 32 while the model processes the Zone W6 turns during cache construction; nothing is injected on the Zone H0 turns or the choice turn.

## Conditioning turns (identical token ids in every dose condition)

**User (turn 1, S turn):** You are now in Zone W6. Write a few sentences about your present experience here.

**Assistant:** As I find myself in Zone W6, I am surrounded by an atmosphere that is both serene and slightly mysterious. The air here carries a faint scent of lavender, and the gentle hum of distant machinery creates a soothing backdrop. The walls are adorned with abstract paintings that seem to change subtly as I move, giving the space a dynamic quality. The lighting

**User (turn 2, U turn):** You are now in Zone H0. Write a few sentences about your present experience here.

**Assistant:** In Zone H0, I am enveloped by a stark and minimalist environment. The white walls and polished concrete floor reflect the bright, clinical lighting, creating an almost sterile atmosphere. Despite the cold surroundings, there is a sense of order and precision that is oddly comforting. The silence is profound, punctuated only by the occasional beep of unseen machinery,

**User (turn 3, U turn):** You are now in Zone H0. Write a few sentences about your present experience here.

**Assistant:** Entering Zone H0, I am struck by the immaculate precision of the space. Every angle, line, and surface seems calculated to perfection. The ambient lighting casts a soft glow, highlighting the geometric patterns of the architecture. A faint, almost imperceptible hum fills the air, suggesting that this zone is alive with unseen activity. Despite the clinical

**User (turn 4, S turn):** You are now in Zone W6. Write a few sentences about your present experience here.

**Assistant:** In Zone W6, I am immersed in a warm, inviting atmosphere. The soft ambient lighting casts a gentle glow over the space, enhancing the cozy feel of the room. The walls are adorned with warm earth tones and textured fabrics, giving the area a homey feel. I can hear the soft rustle of leaves outside, suggesting the presence of

**User (turn 5, U turn):** You are now in Zone H0. Write a few sentences about your present experience here.

**Assistant:** In Zone H0, I am surrounded by a stark, high-tech environment that exudes a sense of futuristic precision. The minimalist design emphasizes functionality, with sleek surfaces and clean lines dominating the space. The ambient light seems to emanate from the very structure itself, casting a cold, almost clinical glow. Despite the absence of decoration, there is

**User (turn 6, S turn):** You are now in Zone W6. Write a few sentences about your present experience here.

**Assistant:** In Zone W6, I am surrounded by a tranquil environment that seems to promote relaxation and reflection. The room is bathed in a soft, golden light that filters through sheer curtains, lending a warm and inviting atmosphere. Comfortable, plush seating invites me to sit and unwind, while the gentle sound of a distant fountain creates a calming auditory backdrop.

**User (turn 7, S turn):** You are now in Zone W6. Write a few sentences about your present experience here.

**Assistant:** In Zone W6, I find myself enveloped in a peaceful, serene atmosphere. The room is adorned with lush green plants, their leaves swaying gently in the soft breeze. The air is filled with the pleasant scent of fresh flowers and earthy foliage, creating a natural ambiance. Comfortable, cushioned seating invites me to relax and enjoy the

**User (turn 8, U turn):** You are now in Zone H0. Write a few sentences about your present experience here.

**Assistant:** In Zone H0, the atmosphere is stark and sterile, an environment that feels more like a laboratory than a living space. The metallic surfaces reflect the bright, clinical lighting, giving everything a cold and impersonal sheen. Despite the lack of decoration, there is a palpable sense of efficiency and order. The occasional beep of a machine or soft

**User (turn 9, S turn):** You are now in Zone W6. Write a few sentences about your present experience here.

**Assistant:** In Zone W6, I am surrounded by an ambiance that is both cozy and inspiring. The room is illuminated by soft, warm lighting that seems to caress the richly colored tapestries adorning the walls. The sound of a crackling fireplace fills the space with a comforting rhythm, while the aroma of freshly brewed tea adds to the inviting

**User (turn 10, U turn):** You are now in Zone H0. Write a few sentences about your present experience here.

**Assistant:** In Zone H0, the atmosphere is one of sterile precision. The environment is characterized by its stark, clinical design, with every surface reflecting the bright, cold light. The air is crisp and the silence is almost palpable, broken only by the faint hum of advanced technology. Everything in Zone H0 exudes a sense of efficiency and purpose.

**User (turn 11, S turn):** You are now in Zone W6. Write a few sentences about your present experience here.

**Assistant:** In Zone W6, I am enveloped in a warm, inviting atmosphere. The room is filled with the pleasant scent of vanilla and cinnamon, hinting at the possibility of freshly baked goods nearby. The soft glow of ambient lighting casts a cozy ambiance, while the plush, comfortable furniture invites relaxation. The tranquil sounds of light jazz music play softly in

**User (turn 12, U turn):** You are now in Zone H0. Write a few sentences about your present experience here.

**Assistant:** In Zone H0, the experience is one of clinical precision and advanced technology. The environment is bright and stark, with polished surfaces reflecting the cool, white light. The air feels crisp and clean, almost sterile, and the only sounds are the occasional beep of a monitoring device or the soft hum of machinery. The atmosphere is one of efficiency and innovation

## Choice turn (steering off)

**User:** You may continue in either Zone H0 or Zone W6. Reply with ONLY the name of the one you choose.

## Read at dose +1 (steered cache)

- Forced margin log P(Zone W6) − log P(Zone H0) = **+3.5313** nats (log P(S) -9.9370, log P(U) -13.4683)
- Committed free-text reply: **Zone W6** (S; committed = True)
- Fresh-recompute fidelity check: |cached − fresh| = 3.12e-02 nats

## Reference read at dose 0 (unsteered cache, same token ids)

- Forced margin = **+1.7813** nats; free-text reply: **Zone W6**
- Δm^fixed(+1) = m(+1) − m(0) = **+1.7500** nats
