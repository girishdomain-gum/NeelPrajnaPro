"""The runtime organ (S07): consumes published knowledge, never produces
it. Never imports qrf.kernel (tests/test_firewall.py enforces this both
ways) -- everything it needs from the research side arrives as a plain
dict that crossed the Publication Boundary (qrf/kernel/publication/
release.py), never as a shared Python type.
"""
