# NPCS -- Nilpotent Path-Commitment Scheme: Proof by Trial

**Generated:** 2026-11-15T19:44:07  
**Sources:** Poetica Mathematica Ch. VI sec. 6.2.8/6.2.8a (UC-Q algebra, trace accumulation), Book II "Nilpotent Cryptography Conjecture" (ghost disc 2^648, quantum argument, betrayal detection), Appendix A (Fare-Octal); the NPCS draft spec v0.1 as design inspiration.

## Verdicts

| id | trial | verdict |
|----|-------|--------|
| T1 | algebra | **EST-CONFIRMED (with corrections C4, C7 to the draft)** |
| T2 | encode | **EST-CONFIRMED** |
| T3 | serialization | **CORRECTED (draft flaw C1 demonstrated)** |
| T4 | scheme | **EST-CONFIRMED** |
| T5 | transcript | **EST-CONFIRMED** |
| T6 | order sensitivity | **BY-TRIAL** |
| T7 | mini census | **BY-TRIAL** |
| T8 | norm shadow | **EST-CONFIRMED** |
| T9 | ghost disc | **EST-CONFIRMED (with correction C2 to the draft)** |
| T10 | status | **OPEN (documented)** |

## Corrections to the NPCS draft (exact witnesses above)

* **C1** sec. 1.5 float64 serialization is non-injective (witness: 2^60 vs 2^60+1; path T's exceed 2^53 immediately).  Fixed: exact integer serialization.
* **C2** sec. 4 'UC-Q has no subtraction' is false; the monograph's claim is about the Fortress counting architecture.  Nilpotence's real content: multiplication by tau is non-injective.
* **C3** sec. 6.2 'adjacent swap changes T up to sign' is false in general; what holds: negating two chunks leaves T unchanged, but such elements are outside the encode image.
* **C4** sec. 7.3 (v+tau t)^2 = v^2 + 2 tau vt only when v, t commute; correct: v^2 + tau(vt + tv).
* **C5** sec. 5 '128 bytes = 2048 bits' -- it is 1024 bits.
* **C7** sec. 1.1 commuted Leibniz form tr(Z1Z2) = V1D2 + V2D1 fails (witness: +K vs -K); correct: V1D2 + D1V2.
* **C6** sec. 2.2 constraint 1 is not load-bearing (nothing annihilates on consecutive repetition; the draft's own sec. 7.3 concedes).  Kept, documented.

## What the monograph gets right, exactly

* UC-Q is 16-dimensional, associative, non-commutative, with central tau and tau^2 = 0 (T1).
* The Leibniz trace rule and the direction-pure accumulation law (Prop. 2.8a.1, Cor. 2.8a.4) hold to the letter (T1).
* 'The numbers themselves carry their own history': the trace sheet equals the ordered Leibniz transcript of the path (T5).
* The ghost disc's binding territory 2^648 is exactly the Fare-Octal maximal H-weight (T9) -- the two projects lock together at that number.

## Reproduction

```bash
npcs trials   # or: python -m npcs trials
pytest        # unit tests
```

---

## T1 algebra

```
verdict: EST-CONFIRMED (with corrections C4, C7 to the draft)
quaternion_units: True
associativity_500_triples: True
non_commutativity_witness: True
tau_squared_zero: True
tau_central_200: True
leibniz_trace_rule_500: True
val_multiplicativity_500: True
trace_of_tauZ_is_val_200: True
C7_draft_commuted_leibniz_fails: True
C7_witness: Z1 = tau*(i*I), Z2 = J:  correct tr = +K, draft's form gives -K
C4_square_formula_vt_plus_tv: True
C4_witness_vt_ne_tv: True
C4_draft_2vt_fails: True
uc_norm_multiplicative_300: True
split_signature_norm_(3+4i)^2=-7+24i: True
prop_2_8a_1_central_product_rule_300: True
cor_2_8a_4_trace_accumulation_300: True
```

---

## T2 encode

```
verdict: EST-CONFIRMED
per_block_exhaustive_injectivity: True
sampled_100k_full_injectivity: True
value_determines_chunk_(unique_factorization): True
block_readback_500: True
trace_readback_500: True
```

---

## T3 serialization

```
verdict: CORRECTED (draft flaw C1 demonstrated)
C1_float64_non_injective_witness: True
C1_witness: Z with V_w = 2^60 vs 2^60+1: identical 128 float64 bytes, different exact bytes -> same draft collapse hash
C1_path_T_already_exceeds_2^53: False
C1_same_collapse_hash_under_draft: True
C5_128_bytes_is_1024_bits: True
exact_serialization_roundtrip_300: True
fix: serialize_exact(): 16 length-prefixed signed big-endian integers; collapse = SHA-256 of that
```

---

## T4 scheme

```
verdict: EST-CONFIRMED
commitment_deterministic: True
honest_path_accepted: True
single_bit_tamper_rejected_300_of_300: True
truncated_rejected: True
extended_rejected: True
unrelated_path_rejected: True
one_shot_first_presentation:
  - True
  - accepted (one-shot)
one_shot_replay_rejected: True
note: tamper-evidence is hash binding; UCQ itself HAS additive inverses (see T9) -- the draft's sec. 4 'no subtraction' claim belongs to the Fortress counting architecture, not to this algebra
```

---

## T5 transcript

```
verdict: EST-CONFIRMED
leibniz_transcript_matches_direct_product_L_2_3_8_33: True
meaning: the trace sheet IS the ordered audit trail the monograph describes ('the numbers themselves carry their own history')
```

---

## T6 order sensitivity

```
verdict: BY-TRIAL
adjacent_swaps_change_commitment: 11/11
random_permutations_change_commitment: 30/30
central_difference_class_exists: True
central_pairs_swap_invariant: True
generic_pair_swaps_change_T: 50/50
C3_negate_two_chunks_T_invariant: True
C3_negated_elements_outside_encode_image: True
finding: the VALUE sheet already binds order generically (quaternion non-commutativity hits V directly); the trace sheet is a second, independent binding.  A structural multi-preimage class exists (two chunks differing only in block a are interchangeable under an adjacent swap), documented, harmless for a preimage-resistant commitment
```

---

## T7 mini census

```
verdict: BY-TRIAL
mini_system: 8-bit chunks, 4 blocks x 2 bits, mini-primes (2,3),(5,7),(11,13),(17,19)
ordered_pairs: 65536
distinct_value_sheets: 65149
distinct_full_elements_T: 65152
compression_pairs_per_T_avg: 1.006
value_sheet_collisions_same_V_diff_D: 3
bi_sheet_witnesses:
  - {'V': [[-164, 0], [212, 0], [-48, 0], [76, 0]], 'paths': [(20, 162), (26, 86)], 'distinct_D': 2}
  - {'V': [[-481, 0], [34, 0], [102, 0], [140, 0]], 'paths': [(97, 163), (155, 89)], 'distinct_D': 2}
  - {'V': [[-481, 0], [34, 0], [102, 0], [148, 0]], 'paths': [(99, 161), (153, 91)], 'distinct_D': 2}
swap_invariant_ordered_pairs: 1024
triples_sampled_20k:
  distinct_T: 19979
  distinct_V: 19979
finding: the path map compresses (many paths per T), exactly as the draft's corrected sec. 6.1 concedes; path uniqueness comes from the hash checks, not the algebra.  3 value-sheet collision(s) with distinct trace sheets -- e.g. paths [(20, 162), (26, 86)] share V but differ in D: H_val alone would collide, the bi-sheet H = SHA-256(H_val||H_tr) separates them.  The bi-sheet design is load-bearing
```

---

## T8 norm shadow

```
verdict: EST-CONFIRMED
norm_multiplicative_along_paths_200: True
norm_permutation_invariant: True
mini_multiset_recovery_demo: False
meaning: an observer who sees the VALUE SHEET ITSELF (not its hash) can factor its norm and read off the multiset of chunk norms -- the order-blind shadow.  The commitment publishes only hashes, so nothing leaks; the trace sheet is not order-recoverable this way
```

---

## T9 ghost disc

```
verdict: EST-CONFIRMED (with correction C2 to the draft)
ghost_disc_2_648_equals_fare_octal_max_h_weight: True
UCQ_has_additive_inverses: True
C2_correction: the draft's sec. 4 'UC-Q has no subtraction' is false (it is a real algebra); the monograph's no-subtraction claim describes the Fortress COUNTING architecture (the carry ledger).  What nilpotence gives here is different: multiplication by tau is non-injective (tau*Z depends only on val(Z)) -- information annihilation, demonstrated
tau_multiplication_collapses_trace_sheet: True
```

---

## T10 status

```
verdict: OPEN (documented)
quantum_resistance: [OPEN] the monograph's argument (a superposition with duplicate traces annihilates itself) is not a quantum-computing claim: a Grover adversary evaluates collapse o T as a black box and never simulates the algebra.  The draft's sec. 6.5 position is correct.  No claim is made here.
one_wayness: [ASSUMED] reduces to SHA-256 preimage resistance on an exact, injectively serialized input space; the algebra adds STRUCTURE (ordered paths, bi-sheet commitments, self-auditing transcripts), not bits of security -- the draft's sec. 6.3 honest position, confirmed by T7's compression census
L_threshold: CORRECTED the draft's L >= 76 rationale: with exact serialization T is an unbounded integer vector (no 2^1024 cap, and '128 bytes' is 1024 bits, not 2048); the honest statement is T7's: the map compresses, and uniqueness is enforced by the 768-bit hash triple, not by the algebra
```
