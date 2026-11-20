# Artifact: SoK: Randomness Failures and Their Remedies in Deployed Cryptographic Systems

This repository accompanies the paper by Devharsh Trivedi (LaGuardia Community College, City
University of New York), accepted at Financial Cryptography and Data Security 2027 (FC 2027).
Release v1.0 matches the camera-ready version of the paper.

## Contents

- `data/incidents.csv`, `data/incidents.json`: the 28 deployed incidents of the corpus, coded on
  stage, adversary, access, observability, blast radius, target secret, CVE, and dwell time.
- `data/remedies.csv`: the 14 remedy families with the stages they act on, mode, friction, and
  residual risk.
- `data/counterfactuals.csv`: for every incident, the remedies judged to prevent it, those that
  only detect or contain it, whether a preventing remedy was available when the system shipped,
  and a one-line reason.
- `data/schema.md`: field definitions, coding decisions, and limitations.
- `build_coverage.py`: the grading rules and per-incident judgments; writes the coverage matrix
  (`paper/sections/coverage_table.tex`) and prints the counts quoted in the paper.
- `build_dataset.py`: regenerates the data files and checks them against the paper sources
  (incident and remedy counts, citation keys, table rows, controlled vocabularies).
- `randomness_analysis.ipynb`, `build_nb.py`: the notebook behind Appendix C (brute-force cost at
  32, 40.7, and 72 bits, hashing cannot add entropy, ECDSA nonce-reuse key recovery, cost
  amortization across targets). Every result carries an assertion.
- `figures/`: editable draw.io sources of Figures 1 and 2, the scripts that generate and render
  them, and the brute-force figure.
- `paper/`: LaTeX sources of the paper (LNCS).

## Reproduce

```
python3 build_coverage.py      # writes paper/sections/coverage_table.tex and prints the counts
python3 build_dataset.py       # regenerates data/ and validates it against paper/
python3 build_nb.py            # rebuilds and executes the notebook (needs nbconvert, matplotlib)
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```

To render a figure from its draw.io source: `npm install mxgraph@4.2.2`, then
`python3 figures/render.py figures/taxonomy_pipeline.drawio out.pdf` (needs Python Playwright
and Chrome). The `.drawio` files also open directly in draw.io.

## Changing a judgment

Each cell of the coverage matrix follows from the stage sets and from the per-incident entries in
`COVERAGE` in `build_coverage.py`. To re-grade an incident, edit its entry and re-run the two build
scripts. The script refuses judgments that the stage rule does not allow.

## Citation

See `CITATION.cff`.

## License

Code: MIT (see `LICENSE`). Data in `data/`: CC BY 4.0. The LaTeX class `llncs.cls` and the style
`splncs04.bst` are Springer's and are included only so that the paper builds.
