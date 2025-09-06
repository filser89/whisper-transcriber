SHELL := /bin/bash
PY := python3.12
VENV := venv

.PHONY: venv install update clean transcribe diarize full

venv:
	$(PY) -m venv $(VENV); \
	source $(VENV)/bin/activate && python -m pip install --upgrade pip wheel setuptools

install: venv
	source $(VENV)/bin/activate && pip install -r requirements.txt

update:
	source $(VENV)/bin/activate && pip install -U -r requirements.txt

transcribe:
	@if [ -z "$(INPUT)" ]; then echo "Usage: make transcribe INPUT=/path/file.mp4 [OUTDIR=~/transcripts] [ARGS='--word_timestamps']"; exit 1; fi
	@OUTARG=""; if [ -n "$(OUTDIR)" ]; then OUTARG="--output_dir $(OUTDIR)"; fi; \
	source $(VENV)/bin/activate && PYTHONPATH=src python -m wt.cli transcribe "$(INPUT)" $$OUTARG $(ARGS)

diarize:
	@if [ -z "$(INPUT)" ]; then echo "Usage: make diarize INPUT=/path/file.mp4 [OUTDIR=~/transcripts] [ARGS='--num_speakers 2']"; exit 1; fi
	@OUTARG=""; if [ -n "$(OUTDIR)" ]; then OUTARG="--output_dir $(OUTDIR)"; fi; \
	source $(VENV)/bin/activate && PYTHONPATH=src python -m wt.cli diarize "$(INPUT)" $$OUTARG $(ARGS)

full:
	@if [ -z "$(INPUT)" ]; then echo "Usage: make full INPUT=/path/file.mp4 [OUTDIR=~/transcripts] [ARGS='--num_speakers 2']"; exit 1; fi
	@OUTARG=""; if [ -n "$(OUTDIR)" ]; then OUTARG="--output_dir $(OUTDIR)"; fi; \
	source $(VENV)/bin/activate && \
	PYTHONPATH=src python -m wt.cli transcribe "$(INPUT)" $$OUTARG --word_timestamps; \
	PYTHONPATH=src python -m wt.cli diarize "$(INPUT)" $$OUTARG $(ARGS)



clean:
	rm -rf $(VENV) __pycache__ .pytest_cache .mypy_cache
	find . -name "*.pyc" -delete
