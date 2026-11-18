# The voidwell demonstration: three test cases, the small model, and
# the parameter table (spec D12).  `make demo` runs everything.
#
# Seeds are fixed and published (D9/D13-9) for reproducibility.
S1 := 1111111111111111111111111111111111111111111111111111111111111111
S2 := 2222222222222222222222222222222222222222222222222222222222222222
S3 := 3333333333333333333333333333333333333333333333333333333333333333
DATA := 00112233

.PHONY: demo encode-tests gate-tests contest small params verify clean

demo: encode-tests gate-tests contest small params
	@echo "=== make demo complete: tests 1, 2, 3 PASS, the small model"
	@echo "=== table and slope are above, and the parameter table matches rules.md"

encode-tests:
	mkdir -p tests/test1 tests/test2
	python3 -m voidwell encode --data $(DATA) --seed $(S1) --wells 0 --length 43 \
		--out tests/test1/challenge.json --key-out tests/test1/key.json
	python3 -m voidwell encode --data $(DATA) --seed $(S2) --wells 1 --length 43 \
		--out tests/test2/challenge.json --key-out tests/test2/key.json

gate-tests:
	python3 -m voidwell gate --challenge tests/test1/challenge.json --key tests/test1/key.json
	python3 -m voidwell gate --challenge tests/test2/challenge.json --key tests/test2/key.json

contest:
	mkdir -p contests/test3
	python3 -m voidwell encode --data $(DATA) --seed $(S3) --wells 3 --length 43 \
		--out contests/test3/challenge.json --key-out contests/test3/key.json
	python3 -m voidwell gate --challenge contests/test3/challenge.json --key contests/test3/key.json
	@# the solver's pre-publication check passed; seal the package:
	mv contests/test3/key.json results/test3_withheld_key.json
	@echo "sealed: contests/test3/ holds no key; the withheld key is"
	@echo "archived at results/test3_withheld_key.json (demo disclosure)"

small:
	python3 -m voidwell.small_model.harness

params:
	python3 -m voidwell params

verify:
	python3 tests/verify.py
	python3 tests/test_gate.py

clean:
	rm -rf tests/test1 tests/test2 contests/test3 results/*.json
