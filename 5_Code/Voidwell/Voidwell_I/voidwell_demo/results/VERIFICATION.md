# Fare-Octal: Proof by Trial -- Verification Report

**Generated:** 2026-11-16T19:22:24  
**Source:** Poetica Mathematica, Appendix A (Fare-Octal Counting System), Ch. IV sec. 4.1.1 (Fare Algebra), Ch. I sec. I.8 (117-point Arithmetic Bitriada).

| id | check | verdict |
|----|-------|--------|
| V1 | counting table | **PASS** |
| V2 | addressing | **PASS** |
| V3 | product rules | **PASS (documented divergence: literal index rule)** |
| V4 | worked examples | **PASS (documented divergences F2, F4)** |
| V5 | fare algebra bridge | **PASS** |
| V6 | lattice | **PASS** |
| V7 | census | **PASS** |

**Census:** 2^27 = 134,217,728 states; 117 lattice points (9 digits + 27 bits in the window; 81-point Fortress outside); max state value = primorial of the first 27 primes; max H-weight = 2^648.

## V1 counting table

```
verdict: PASS
first_16_states_match: True
carry_displays_match: True
table:
  - (0, '[0 0 0 0 0 0 0 0 0]', 'zero state')
  - (1, '[0 0 0 0 0 0 0 0 1]', 'tau_0')
  - (2, '[0 0 0 0 0 0 0 0 2]', 'tau_1')
  - (3, '[0 0 0 0 0 0 0 0 3]', 'tau_0, tau_1')
  - (4, '[0 0 0 0 0 0 0 0 4]', 'tau_2')
  - (5, '[0 0 0 0 0 0 0 0 5]', 'tau_0, tau_2')
  - (6, '[0 0 0 0 0 0 0 0 6]', 'tau_1, tau_2')
  - (7, '[0 0 0 0 0 0 0 0 7]', 'tau_0, tau_1, tau_2')
  - (8, '[0 0 0 0 0 0 0 1 0]', 'tau_3')
  - (9, '[0 0 0 0 0 0 0 1 1]', 'tau_0, tau_3')
  - (10, '[0 0 0 0 0 0 0 1 2]', 'tau_1, tau_3')
  - (11, '[0 0 0 0 0 0 0 1 3]', 'tau_0, tau_1, tau_3')
  - (12, '[0 0 0 0 0 0 0 1 4]', 'tau_2, tau_3')
  - (13, '[0 0 0 0 0 0 0 1 5]', 'tau_0, tau_2, tau_3')
  - (14, '[0 0 0 0 0 0 0 1 6]', 'tau_1, tau_2, tau_3')
  - (15, '[0 0 0 0 0 0 0 1 7]', 'tau_0, tau_1, tau_2, tau_3')
```

## V2 addressing

```
verdict: PASS
tensor_roundtrip_all_27: True
printed_cell_examples: True
prime_ladder_2_to_103: True
full_address_chain: True
```

## V3 product rules

```
verdict: PASS (documented divergence: literal index rule)
value_reading:
  closed_on_states_plus_zero: True
  associative_2000_random_triples: True
  commutative: True
  all_off_state_is_unit: True
  zero_absorbing: True
  nilpotency_tau_b_squared: True
  unit_is_tau_1_not_nilpotent: True
  gloss_agreement_merge_iff_coprime_values: True
literal_index_rule:
  not_closed_witness: tau_5 * tau_7 -> tau_35, no bit 35
  not_associative_witness: (tau_1 tau_1) tau_2 = 0 but tau_1 (tau_1 tau_2) = tau_2
```

## V4 worked examples

```
verdict: PASS (documented divergences F2, F4)
sec_7_1:
  tau_2 * tau_2 = 0: True
  tau_2 * tau_3 = tau_6: True
  tau_2 * tau_5 = tau_10: True
  tau_2 * tau_4 = 0: vacuously 0 -- 4 = 2^2 is not squarefree, so tau_4 is not a state at all
  tau_4_has_no_state (non-squarefree): True
sec_4_2:
  pre_matches_printed: True
  product_is_tau_15: True
  correct_post_display_value_reading: [0 0 0 0 0 0 0 0 6]
  linear_reading_post_display_bit_15: [0 0 0 1 0 0 0 0 0]
  printed_post_display: [0 0 0 0 0 1 0 0 0]
  printed_post_equals_bit_9_prime_29: True
  printed_post_matches_neither_reading: True
  finding: the BEFORE state matches the value reading; the printed AFTER state matches NO reading: the value reading gives [0 0 0 0 0 0 0 0 6] (bits 1,2 = primes 3,5), the linear-index reading of 'tau_15' gives [0 0 0 1 0 0 0 0 0] (D5 is the 4th token from the left), and the printed [0 0 0 0 0 1 0 0 0] is bit 9 (prime 29) -- F2
sec_7_2:
  A: tau_2 + tau_3
  B: tau_2 + tau_5
  A*B: tau_6 + tau_10 + tau_15
  expansion: 0 (tau_2^2) + tau_10 (2*5) + tau_6 (3*2) + tau_15 (3*5)
  result_terms:
    6: 1
    10: 1
    15: 1
  is_a_sum_not_a_state: True
  finding: the monograph leaves sec. 7.2 symbolic; the window algebra completes it: a 3-term element (F4)
```

## V5 fare algebra bridge

```
verdict: PASS
prop_4_1_1_2_basis_product_500_random_pairs: True
involution_pairing_iota_s_iota_1ms: True
functional_equation:
  Z(0) == iota_0(Z(1)) (exact): True
  Z(1) == iota_1(Z(0)) (exact): True
  Z(2) == iota_2(Z(-1)) (exact): True
  iota_0 . iota_1 = id (exact): True
  iota_1 . iota_0 = id (exact): True
  iota_2 . iota_-1 = id (exact): True
  iota_3 . iota_-2 = id (exact): True
  exponent identity (s-1)+(1-2s) = -s: True
  critical line s = 1/2: iota is the identity (n^0): True
```

## V6 lattice

```
verdict: PASS
L_table_exact: True
L_formula_fit_2i_rad_z: True
M_printed_values_exact: True
M_tables_exact: True
H_slices_exponents_3_to_81: True
level_sums_117:
  levels:
    L: 9
    M: 27
    H: 81
  per_axis:
    L: 3
    M: 9
    H: 27
  total_points: 117
  per_axis_sum: 39
  table_matches_monograph: True
storage_convention:
  digits_are_H_rows_k_i: True
  bits_are_the_27_H_cells: True
  fortress_81_outside_window: True
```

## V7 census

```
verdict: PASS
total_states_2_27: 134217728
maximal_state:
  display: [7 7 7 7 7 7 7 7 7]
  value_primorial_of_first_27_primes: True
  value_digits: 41
  h_exponent_648: True
  h_weight_2_648: True
unit_all_off:
  display: [0 0 0 0 0 0 0 0 0]
  value: 1
  is_tau_1: True
zero_not_a_state: True
display_value_bijection_500_random: True
```

---

## The findings, in one place

* **F1** The literal index-gcd rule of App. A sec. 4.1 is not closed and not associative; the value reading (the monograph's own Ch. V gloss) repairs it -- closed, associative, commutative monoid with unit = all-off state (tau_1) and zero = annihilation.
* **F2** App. A sec. 4.2's printed AFTER state matches no reading: value reading gives [0 0 0 0 0 0 0 0 6], linear-index reading gives [0 0 0 1 0 0 0 0 0], the printed string is bit 9 (prime 29).
* **F3** App. A uses two labelings for the same symbol tau_n: linear in the sec. 5 counting table, prime-value in sec. 7.1.
* **F4** sec. 7.2's multi-tau product is completed exactly here (a 3-term window-algebra element, not a single state).
* **F5** the "zero state" (all switches off) is the Fare algebra's unit tau_1 = 1; the algebra's 0 is not a state.

## Reproduction

```bash
fare-octal verify   # or: python -m fareoctal verify
pytest              # unit tests
```
