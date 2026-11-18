# Voidwell-2: two variants, the small model, the tick-key toy, the
# attacker package, and the sealed challenge.  `make demo` runs the
# whole battery.
#
# Illustration seeds are fixed and published for reproducibility.
# The sealed challenges in contests/ are NOT re-encoded by any
# target: they are stable public artifacts, and their keys stay
# withheld under results/.  (A fresh seal is a deliberate act --
# see README-CHALLENGE.md.)
FLAG_SEED := 1111111111111111111111111111111111111111111111111111111111111111
COMPACT_SEED := 22222222222222222222222222222222
DATA := 00112233

.PHONY: demo encode-tests gate-tests examples challenge small params verify attacker measurements tickkey clean

demo: encode-tests gate-tests examples challenge small params verify attacker measurements tickkey
	@echo "=== make demo complete: both variants encode+gate PASS,"
	@echo "=== the two illustration cases reproduce, the sealed"
	@echo "=== challenges verify, the small model and attacker"
	@echo "=== battery are above, measurements written."

encode-tests:
	mkdir -p tests/demo
	python3 -m voidwell2 encode --variant flagship --data $(DATA) \
		--seed $(FLAG_SEED) --out tests/demo/flagship.json \
		--key-out tests/demo/flagship.key.json
	python3 -m voidwell2 encode --variant compact --data $(DATA) \
		--seed $(COMPACT_SEED) --out tests/demo/compact.json \
		--key-out tests/demo/compact.key.json

gate-tests:
	python3 -m voidwell2 gate --challenge tests/demo/flagship.json --key tests/demo/flagship.key.json
	python3 -m voidwell2 gate --challenge tests/demo/compact.json --key tests/demo/compact.key.json

examples:
	python3 -m voidwell2 encode --variant flagship --data $(DATA) \
		--seed $(FLAG_SEED) --out /tmp/case1.json --key-out /tmp/case1.key.json
	python3 -m voidwell2 encode --variant compact --data deadbeef \
		--seed $(COMPACT_SEED) --out /tmp/case2.json --key-out /tmp/case2.key.json
	cmp /tmp/case1.json examples/case1-flagship/challenge.json
	cmp /tmp/case1.key.json examples/case1-flagship/key.json
	cmp /tmp/case2.json examples/case2-compact/challenge.json
	cmp /tmp/case2.key.json examples/case2-compact/key.json
	python3 -m voidwell2 gate --challenge examples/case1-flagship/challenge.json \
		--key examples/case1-flagship/key.json
	python3 -m voidwell2 gate --challenge examples/case2-compact/challenge.json \
		--key examples/case2-compact/key.json
	@echo "examples: both cases reproduce bit-for-bit and gate PASS."

challenge:
	python3 -m voidwell2 gate --challenge contests/flagship/challenge.json \
		--key results/flagship_withheld_key.json
	python3 -m voidwell2 gate --challenge contests/compact/challenge.json \
		--key results/compact_withheld_key.json
	@echo "sealed challenges verified with the withheld demonstration"
	@echo "keys (archived under results/, outside any shipped zip)."

small:
	python3 -m voidwell2.small_model.harness

params:
	python3 -m voidwell2 params

verify:
	python3 tests/verify.py

attacker:
	python3 attacker/surface_audit.py contests/flagship/challenge.json \
		contests/compact/challenge.json
	python3 attacker/toy_dictionary.py
	python3 attacker/seed_search.py --challenge contests/compact/challenge.json --budget 2048
	python3 attacker/seed_search.py --challenge contests/flagship/challenge.json --budget 2048

measurements:
	python3 tests/measurements.py

tickkey:
	python3 -m voidwell2 tickkey demo

clean:
	rm -rf tests/demo __pycache__ */__pycache__*/*/__pycache__*
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "clean: removed build caches and tests/demo (results/ and"
	@echo "contests/ are left untouched -- the sealed challenges and"
	@echo "withheld keys are stable artifacts)."
