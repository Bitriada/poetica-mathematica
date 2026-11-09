# Lattice 117: A Finite Window of the Hyperoperation Ladder

This repository contains the companion code for the paper [Generative Integer Fractal from minimal rules](https://github.com/Bitriada/poetica-mathematica/blob/main/3_Standalone_papers/Arithmetic_Bitriada/Generative_Integer_Fractal_from_minimal_rules.pdf).

## What is this?
`lattice117.py` is a self-testing, standard-library-only Python script that generates and analyzes the 117-point combinatorial object described in the paper. 

The script builds words of length 2, 3, and 4 from the alphabet {1,2,3}, assigns each a precise exact integer value via a single hyperoperation rule, and then machine-verifies every structural claim made in the paper, including:
*   The prefix tree skeleton.
*   The zone orbits (Prime, Reflection, Projection).
*   The 117-to-37 fibre collapse (the valuation is not injective).
*   The exact placement of the object within the Fast-Growing Hierarchy (FGH) and Ackermann function levels.

## How to Run It
Because the script relies purely on Python's standard library, there is no installation required. 

**Locally:**
```bash
python3 lattice117.py
