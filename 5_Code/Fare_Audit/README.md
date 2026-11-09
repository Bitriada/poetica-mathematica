# Fare-Audit (RTFA v1.0)

Companion code to the paper [Monkey Business Arithmetic Spectator Pipeline (MBP)](https://github.com/Bitriada/poetica-mathematica/blob/main/3_Standalone_papers/Monkey_Business/Monkey_business_arithmetic_spectator_pipeline.pdf).

## What is this?
`fare-audit` is a read-only auditor for lossy type conversions. It acts as a flight recorder for every crossing between numeric representations. 

Instead of just calculating math and giving you an answer, the tool *watches* the math. It calculates the exact mathematical truth before a conversion, compares it to what the computer actually produces, and emits a "Fare vector" detailing exactly what was lost (precision, sign, phase, etc.). It prevents type-confusion (a common security vulnerability) by enforcing algebraic rules, and it records every transition in a tamper-evident JSONL ledger.

## 1. The Environments (What do Z64 and F64 mean?)
Computers only have finite space. When you force a number into a tight box, data gets crushed. The tool divides these boxes into specific "Environments". Here is the cheat sheet:

*   **`N64` (Natural):** Whole, positive numbers (0, 1, 2...). No negatives allowed.
*   **`Z64` (Integer):** Whole numbers, positive or negative (-5, 0, 10). No fractions allowed.
*   **`Q` (Rational):** Exact fractions (e.g., `1/10` or `7/3`). Perfect mathematical precision, but computers struggle to store them natively.
*   **`F64` (Float):** Standard computer decimals (binary64). Very fast, but famously bad at storing things like `0.1` exactly.
*   **`D128` (Decimal):** High-precision decimal float (34 digits). Good for exact decimal math.
*   **`C128` (Complex):** Numbers with an imaginary component (e.g., `3i`).
*   **`ADDR` (Address):** A memory location (e.g., `0x7f3a1c`). It is a container, *not* a number.

## 2. The Instruction Set (How to write a command)
Because the tool is an auditor, you cannot just type `1 + 1`. You have to tell it exactly **what** the number is, **where** you want to send it, and **how**. 

The syntax is: `Source : Value`

### Available Operations:
*   **`cast`**: Converts a number into the target environment (e.g., `Q:1/10` to `F64`).
*   **`add` / `sub` / `mul` / `div`**: Basic arithmetic. You must provide the second number in parentheses (e.g., `div(2)`).
*   **`sqrt`**: Square root.
*   **`pow(n)`**: Exponentiation (e.g., `pow(2)` for squaring).
*   **`deref`**: Look up a memory address.

### Why write it this way?
By separating the *representation* (the box) from the *value* (the number), the tool can catch "Level Collisions." If you try to multiply a memory address (`ADDR`) by a float (`F64`), a normal program might crash or leak memory. This tool will spot the mismatch, **BLOCK** the operation, and log a domain violation.

## 3. Proof of Life: How to test it yourself
You do not need to install anything to verify this code. The repository uses GitHub Actions to provide a live testing environment.

### A. The Manual "Proof of Life" Test
To prove the code isn't just outputting pre-recorded text, you can feed it brand-new math directly in your browser:
1. Go to the **Actions** tab at the top of this repository.
2. Click **test fare-audit manually** on the left sidebar.
3. Click the **Run workflow** button on the right.
4. A menu will drop down. Enter your custom inputs! Here are three tests to try:

**Test 1: The Division Bend** (Bending algebra to survive)
*   **Source:** `Z:7`
*   **Target:** `Z64`
*   **Operation:** `div(2)`
*   *Why?* Integers (`Z64`) cannot hold fractions. The tool will detect this, bend the environment to `Q` (rational), and output `7/2` with an exact mathematical receipt. 

**Test 2: The Security Block** (Preventing type confusion)
*   **Source:** `ADDR:0x7f3a1c`
*   **Target:** `Z64`
*   **Operation:** `deref`
*   *Why?* The tool will **BLOCK** the move (`fare: D,X`). It refuses to let you read a memory location (F2 rung) as an integer (F1 rung) without an explicit cast. 

**Test 3: The Dimensional Lift** (Phase obfuscation)
*   **Source:** `Q:-9`
*   **Target:** `F64`
*   **Operation:** `sqrt`
*   *Why?* A normal calculator errors out. This tool routes the math through the complex plane (`C128`), returns `3.0[[i]]` to the real world, and logs that the imaginary phase was destroyed.

### B. The Automated Demo Suite
To see the tool verify all 42 claims made in the paper (including the tamper-proof ledger test):
1. Go to the **Actions** tab.
2. Click **verify fare-audit** on the left.
3. Click **Run workflow**.
GitHub will spin up a fresh machine, install Python, run 22 unit tests, execute the golden demo, and verify the SHA-256 hash chain of the ledger.

## 4. A Note on the Folder Structure (The "No `rtfa` Folder" issue)
If you look at the files in this folder, you will notice they are **flat** (all sitting side-by-side) rather than nested inside a package folder named `rtfa/`. 

The original code was written expecting an `rtfa` package structure. To run the code exactly as intended without moving all the files, our automation uses a simple Unix trick: we create a temporary symlink named `rtfa` that points back to the current folder (`ln -s . rtfa`). This perfectly satisfies Python's import system while keeping the files exactly where you see them.

## 5. Running Locally (Optional)
If you prefer to run it on your own machine (requires Python 3.7+):
```bash
# 1. Create the symlink to satisfy the package imports
ln -s . rtfa

# 2. Run a custom audit
python3 -m rtfa run --src "Q:1/10" --tgt F64 --op "cast"

# 3. Run the acceptance tests
pip install pytest orjson
python3 -m pytest -q
