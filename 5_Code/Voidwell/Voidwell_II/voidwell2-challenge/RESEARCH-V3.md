# RESEARCH-V3: The Well as a Work Factor — parked, precisely

**Status:** parked (design study, section 8).  Voidwell-2 ships on
the honest fallback: *the SHA-256 preimage is the work factor, and
it is the sole assumption.*  This note records why the obvious
candidates for a harder well fail, so nobody proposes them again
without new ingredients, and states the first real question.

## The prize

Voidwell-2's attack cost is a **sum** over one search: seed
enumeration at full replay, 2^min(n,256) trials.  A *work-factor
well* would make the cost a **product** — schedules x
well-hardness x seed search — by making each well an independently
hard problem.  That is the one thing the family does not have.

## Why the obvious candidates fail (one line of algebra each)

All candidates live in GL(4, F_p) acting by conjugation, as the
current wells do.

1. **Publish the full conjugated matrix as a target; ask for W.**
   Conjugacy is linear algebra: solve the linear system
   `W Q = T W` for the 16 unknowns of W — polynomial time.  No
   hardness in asking for a conjugator.

2. **Commit traces.**  `Tr(W Q W^-1) = Tr(Q)` — the trace is
   conjugation-invariant.  Zero binding; the commitment ignores W
   entirely.

3. **Commit m traces against public random R_i:
   `Tr(W Q W^-1 R_i) = t_i`.**  With m at least the number of
   degree-2 monomials in 16 unknowns (~152), the system
   linearizes and solves.  With m small it is underdetermined:
   pick 16 - m variables freely and solve the remainder.  Either
   way, no search problem.

Generic matrix-algebra inversion does not produce hardness; the
equations are too structured.  This is not a limitation of
imagination but a property of linear algebra over fields.

## The first real question

Find a family of **group actions** — a large, cheaply samplable
group G acting on public objects X, with:

* **sampling** an element of G easy (the holder generates a well),
* **applying** the action fast (the encoder/gate stays at
  milliseconds),
* **inverting** hard: given x and x' = g·x, finding any g' with
  g'·x = x' must be a genuine search, not linear algebra.

The voidwell shape maps onto this cleanly: the well matrix becomes
the group element, the digivector the acted object, the nullifier
the acted result.  The nearest existing family is isogeny-based
group actions (CSIDH-style, over the same prime fields the project
already uses), where the action of a large ideal-class group on
elliptic curves has exactly this asymmetry — but adopting it means
adopting its literature, its parameter cryptanalysis, and its
side-channel history.  That is a research project, not a feature:

1. pick the family and write the exact action on the digivector
   (the lift/project pair must become the action's maps);
2. price sampling / applying / inverting in the sandbox;
3. run the V2 cryptanalysis template against it (the attack
   checklist of section 7 applies unchanged);
4. only then write the claim.

Until then, Voidwell-2's position is the honest one: 256 bits of
SHA-256 preimage per well, stated as the assumption, with every
other layer audited as integrity and narrative.
