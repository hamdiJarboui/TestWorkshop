PY ?= python3
PYTEST = $(PY) -m pytest

.PHONY: lint progress check-course pdf install test fast smoke unit-unittest all performance slow coverage mutation capstone req-report lab solutions clean

install:            ## install course dependencies
	$(PY) -m pip install -r requirements.txt

smoke:              ## seconds: run first on every commit
	$(PYTEST) -m smoke -q

fast:               ## everything except slow/perf tests (default developer loop)
	$(PYTEST) -m "not slow and not performance" -q

unit-unittest:      ## Lab 1 using ONLY the standard library runner
	PYTHONPATH=src $(PY) -m unittest discover -s labs/lab01_unittest -p "test_lab01*.py" -v

performance:        ## timing budgets (Lab 10)
	$(PYTEST) -m performance -q

slow:               ## mutation-testing meta tests (Lab 12)
	$(PYTEST) -m slow -q

all test:           ## full suite incl. instructor solutions
	$(PYTEST)

coverage:           ## line + branch coverage with HTML report
	$(PYTEST) -m "not slow" --cov=autotest --cov-branch --cov-report=term-missing --cov-report=html -q

mutation:           ## mutation score of the Lab 3 suite against the BMS rule
	$(PY) tools/mini_mutate.py --target src/autotest/bms.py --function max_charge_current --tests labs/lab03_black_box/test_lab03_black_box.py

capstone:           ## grade YOUR capstone suite (override with TESTS=path)
	$(PY) capstone/grade.py --tests $(or $(TESTS),capstone/test_tpms_student.py)

req-report:         ## requirement -> test traceability matrix (Lab 13)
	$(PYTEST) labs solutions -m "not slow" -q --req-report

lab:                ## run one lab, e.g.  make lab N=05
	$(PYTEST) labs/lab$(N)_* -v

solutions:          ## instructor solutions + reference capstone score
	$(PYTEST) solutions -q
	$(PY) capstone/grade.py --tests solutions/test_sol_capstone_tpms.py --min-score 100

lint:               ## static checks (needs: pip install ruff)
	ruff check --select F,E9,B .

progress:           ## exercise progress per lab
	$(PY) course.py progress

check-course:       ## run every verified code example in course/*.md
	$(PY) tools/check_course_code.py

pdf:                ## build pdf/*.pdf (needs pandoc + Chromium)
	$(PY) tools/build_pdf.py

clean:
	rm -rf .pytest_cache .hypothesis htmlcov .coverage coverage.xml report.xml
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
