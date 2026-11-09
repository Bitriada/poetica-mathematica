# Lattice 117: A Finite Window of the Hyperoperation Ladder

This repository contains the companion code for the paper [Generative Integer Fractal from minimal rules](https://github.com/Bitriada/poetica-mathematica/blob/main/3_Standalone_papers/Arithmetic_Bitriada/Generative_Integer_Fractal_from_minimal_rules.pdf).

## What is this?
`lattice117.py` is a self-testing, standard-library-only Python script that generates and analyzes the 117-point combinatorial object described in the paper. 

The script builds words of length 2, 3, and 4 from the alphabet {1,2,3}, assigns each a precise exact integer value via a single hyperoperation rule, and then machine-verifies every structural claim made in the paper, including:
*   The prefix tree skeleton.
*   The zone orbits (Prime, Reflection, Projection).
*   The 117-to-37 fibre collapse (the valuation is not injective).
*   The exact placement of the object within the Fast-Growing Hierarchy (FGH) and Ackermann function levels.

## How to Test It Yourself
Because the script relies purely on Python's standard library, there is no installation required. The script is designed to test itself: **running the script *is* running the test suite.** It contains 47 internal `assert` checks.

### A. The Automated GitHub Test
You do not need to install Python to verify this code. 
1. Go to the **Actions** tab at the top of this repository.
2. Click **verify code** on the left sidebar.
3. Click the **Run workflow** button on the right, and then click the green **Run workflow** button.
4. GitHub will spin up a fresh machine, run the script, and compare its output against the `lattice117_output.txt` golden record. If the output matches perfectly, the run turns green.

### B. Running Locally
If you have Python installed on your machine, open your terminal, navigate to this folder, and run:
```bash
python3 lattice117.py
