#!/usr/bin/env python3
"""Generate the remedy coverage matrix (tab:coverage) and the counterfactual CSV.

The matrix crosses every incident of the corpus (build_dataset.INCIDENTS, the same
28 rows as the incidents table of the paper) with the fourteen remedy families.
Each cell follows from three inputs and one rule.

Inputs
  stages(incident)   the stages the incident touches, from build_dataset.py
  stages(remedy)     the stages a remedy acts on, from the remedies table
  PREVENTS, PARTIAL  per incident, the remedies judged to prevent it or to reduce it

Rule
  --    (not applicable)  the remedy acts on no stage the incident touches
  full  (prevents)        the remedy, deployed as specified, removes the specific cause
  half  (partial)         the remedy applies and detects the failure or limits its
                          blast radius, but does not remove the cause
  open  (no effect)       the remedy applies to a touched stage yet would not have
                          changed the outcome

Two judgments are fixed by rule rather than case by case.
  R8 (statistical testing and certification) is `partial` exactly when the incident's
  observability is `statistical` and `none` otherwise, because R8 can only flag output
  that fails a statistical test.
  A `prevents` or `partial` judgment is only allowed on a remedy whose stage set meets
  the incident's stage set; the script stops if one is not.

Availability of the preventing remedy when the vulnerable system shipped:
  Y  published and implemented in mainstream libraries, standards or platforms
  P  published, but not standardized, not the default, or not available for that platform
  E  proposed in the literature, with no production implementation
  N  not yet proposed in deployable form
  -- no remedy family in the catalog prevents the failure

Run:
    python3 build_coverage.py      # writes <paper>/sections/coverage_table.tex
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.environ.get("PAPER_DIR") or (os.path.join(HERE, "paper")
        if os.path.isdir(os.path.join(HERE, "paper")) else os.path.dirname(HERE))
OUT = os.path.join(PAPER, "sections", "coverage_table.tex")

# Remedy id -> (stages it acts on, column group). Stage sets follow the "Stages"
# column of the remedies table; keep them in sync with build_dataset.REMEDIES.
REMEDIES = [
    ("R1",  {"S1", "S2"},             "Src."),
    ("R12", {"S1", "S2"},             "Src."),
    ("R2",  {"S3"},                   "Gen."),
    ("R3",  {"S1", "S4"},             "Gen."),
    ("R10", {"S1", "S4"},             "Gen."),
    ("R4",  {"S5"},                   "St."),
    ("R5",  {"S6"},                   "Use"),
    ("R6",  {"S4", "S5", "S6"},       "Use"),
    ("R14", {"S6"},                   "Use"),
    ("R7",  {"S4", "S6"},             "Structural"),
    ("R8",  {"S1", "S2", "S3"},       "Structural"),
    ("R9",  {"S*"},                   "Structural"),
    ("R11", {"S2", "S3", "S5"},       "Structural"),
    ("R13", {"S1", "S4", "S*"},       "Structural"),
]

# id -> (short label for the matrix, prevents, partial, availability, why the
#        preventing remedy was absent or why none prevents)
COVERAGE = {
 "psandqs2012":   ("Mining Ps and Qs", {"R1", "R3"}, {"R10", "R13"}, "Y",
                   "Non-blocking early reads were the default"),
 "ronwrong2012":  ("Shared RSA factors", {"R1", "R3"}, {"R10", "R13"}, "Y",
                   "Same boot-time entropy gap as Mining Ps and Qs"),
 "amdrdseed2025": ("AMD Zen 5 RDSEED", {"R1"}, {"R12"}, "Y",
                   "Callers trusted the success flag and did not health-test the values"),
 "devrandom2013": ("/dev/random robustness", {"R11"}, {"R1"}, "P",
                   "Robustness model existed but deployed generators were not analyzed against it"),
 "mifare2008":    ("MIFARE Crypto-1", {"R2"}, {"R11"}, "Y",
                   "Proprietary legacy cipher; cost and inertia"),
 "php2012":       ("PHP app tokens", {"R2"}, {"R11"}, "Y",
                   "Non-cryptographic generator was the convenient API"),
 "dualec2007":    ("Dual EC back door", {"R2", "R11"}, set(), "Y",
                   "Deliberate subversion; certification favored it"),
 "android2013":   ("Android SecureRandom", {"R2", "R5"}, {"R6", "R11"}, "Y",
                   "Random nonce was the API default; PRNG defect"),
 "dualectls2014": ("Dual EC in TLS", {"R2", "R11"}, set(), "Y",
                   "Products followed the standard; certification favored it"),
 "juniper2016":   ("Juniper Dual EC", {"R2", "R9"}, {"R11"}, "P",
                   "Vetted DRBGs existed; no check bound shipped firmware to reviewed source"),
 "blackswan2020": ("CTR_DRBG black swans", set(), {"R4", "R6", "R11"}, "--",
                   "Cache side channel in a standardized DRBG; reseeding only narrows the window"),
 "trustwallet2022": ("Trust Wallet ext.", {"R2", "R3"}, {"R10", "R11", "R13"}, "Y",
                   "Non-cryptographic generator with a 32-bit seed in a wallet library"),
 "milksad2023":   ("Milk Sad", {"R2", "R3"}, {"R10", "R11", "R13"}, "Y",
                   "MT19937 seeded from a 32-bit clock value"),
 "illbloom2026":  ("Ill Bloom wallets", {"R2", "R3"}, {"R10", "R11", "R13"}, "Y",
                   "Library PRNG used instead of the platform CSPRNG"),
 "netscape1996":  ("Netscape SSL RNG", {"R3"}, {"R6", "R7", "R10", "R13"}, "P",
                   "Seeding practice immature; no entropy gate"),
 "roca2017":      ("ROCA", set(), {"R13"}, "--",
                   "Structured prime generation lies outside every randomness remedy family"),
 "duhk2018":      ("DUHK", {"R3"}, {"R4", "R6"}, "Y",
                   "Legacy X9.31 with a hardcoded key; certification did not check the key"),
 "profanity2022": ("Profanity vanity gen.", {"R3"}, {"R10", "R13"}, "Y",
                   "32-bit seed chosen for GPU search speed"),
 "vmreset2010":   ("VM reset", {"R4"}, {"R6"}, "E",
                   "Snapshot semantics new; no reseed hook"),
 "whirlwind2014": ("Virtualized Linux", {"R4"}, {"R6"}, "P",
                   "No standard reseed-on-resume interface between host and guest"),
 "opensslrng2016": ("OpenSSL RNG design", {"R4"}, {"R6", "R11"}, "Y",
                   "Fork-safe reseeding known but not the library default"),
 "ps3_2010":      ("PlayStation 3 ECDSA", {"R5"}, {"R6", "R7"}, "P",
                   "Deterministic nonces known but not yet standardized or default"),
 "btcnonce2014":  ("Bitcoin nonce reuse", {"R5"}, {"R6"}, "P",
                   "Deterministic nonces known but not yet standardized or default"),
 "biasednonce2019": ("Biased Nonce Sense", {"R5"}, {"R6"}, "Y",
                   "RFC 6979 available; legacy and custom signers kept random nonces"),
 "minerva2020":   ("Minerva", set(), set(), "--",
                   "Timing leak of nonce length; needs constant-time code, not a randomness remedy"),
 "tpmfail2020":   ("TPM-Fail", set(), set(), "--",
                   "Timing leak of nonce length; needs constant-time code, not a randomness remedy"),
 "debian2008":    ("Debian OpenSSL", {"R9"}, {"R13"}, "N",
                   "No mechanism verified the deployed entropy path"),
 "coldcard2026":  ("ColdCard", {"R9"}, {"R10", "R11", "R13"}, "P",
                   "Reproducible builds existed; nothing checked that the binary reached the hardware source"),
}

GROUPS = [("S1", "\\stage{1} Entropy source"),
          ("S2", "\\stage{2} Accumulation and conditioning"),
          ("S3", "\\stage{3} Generation algorithm"),
          ("S4", "\\stage{4} Seeding and instantiation"),
          ("S5", "\\stage{5} State lifecycle"),
          ("S6", "\\stage{6} Consumption"),
          ("S*", "\\stage{$\\ast$} Build and integration")]

AVAIL_NAMES = {"Y": "yes", "P": "partly", "E": "emerging", "N": "no", "--": "none_prevents"}


def cell(rem_id, rem_stages, inc):
    stages, obs = set(inc["stages"]), inc["obs"]
    label, prevents, partial, avail, why = COVERAGE[inc["id"]]
    if not (rem_stages & stages):
        return "\\hbna"
    if rem_id == "R8":
        return "\\hbhalf" if obs == "statistical" else "\\hbnone"
    if rem_id in prevents:
        return "\\hbfull"
    if rem_id in partial:
        return "\\hbhalf"
    return "\\hbnone"


def check(incidents):
    """Stop on any judgment that the stage rule does not allow."""
    rstages = {r: s for r, s, _ in REMEDIES}
    ids = [i["id"] for i in incidents]
    assert set(ids) == set(COVERAGE), (set(ids) ^ set(COVERAGE))
    for inc in incidents:
        _, prevents, partial, avail, _ = COVERAGE[inc["id"]]
        for r in prevents | partial:
            assert rstages[r] & set(inc["stages"]), (inc["id"], r, "remedy does not reach a touched stage")
        assert "R8" not in prevents | partial, (inc["id"], "R8 is set by rule")
        assert (avail == "--") == (not prevents), (inc["id"], "availability must be -- iff no remedy prevents")


def counterfactual_rows(dataset_incidents):
    """Rows for data/counterfactuals.csv, one per corpus incident, in corpus order."""
    rows = []
    for r in dataset_incidents:
        _, prevents, partial, avail, why = COVERAGE[r[0]]
        rows.append((r[0], ";".join(r[4]), ";".join(sorted(prevents)),
                     ";".join(sorted(partial)), AVAIL_NAMES[avail], why))
    return rows


def load_incidents():
    sys.path.insert(0, HERE)
    import build_dataset
    out = []
    for r in build_dataset.INCIDENTS:
        out.append({"id": r[0], "year": r[2], "stages": r[4], "obs": r[7],
                    "cites": r[10]})
    return out


def main():
    incidents = load_incidents()
    check(incidents)
    groups, seen = [], None
    for _, _, g in REMEDIES:
        if g != seen:
            groups.append([g, 0])
            seen = g
        groups[-1][1] += 1

    L = []
    L.append("% GENERATED BY artifact/build_coverage.py. Do not edit by hand:")
    L.append("% change the data in build_coverage.py and re-run it.")
    L.append("\\begin{table}[tp]")
    L.append("\\centering")
    L.append("\\caption{Remedy coverage matrix for the twenty-eight incidents of "
             "Table~\\ref{tab:incidents}, grouped by primary stage, against the fourteen "
             "remedy families of Table~\\ref{tab:remedies}, numbered 1 to 14 as R1 to R14 there. \\hbfull{} the remedy removes the "
             "specific cause; \\hbhalf{} it applies and detects the failure or limits its "
             "blast radius; \\hbnone{} it applies to a touched stage but would not have "
             "changed the outcome; \\hbna{} it acts on no stage the incident touches. "
             "R8 is \\hbhalf{} exactly when the failure is statistically observable. "
             "Av.\\ states whether a preventing remedy was available when the system "
             "shipped (Y yes, P partly, E emerging, N no, -- none in the catalog prevents it). "
             "Column groups: source, generation and seeding, state, use, structural. "
             "The rules are in Section~\\ref{sec:coverage-rules}, and the generating script is "
             "part of the artifact.}")
    L.append("\\label{tab:coverage}")
    L.append("\\footnotesize")
    L.append("\\setlength{\\tabcolsep}{2.9pt}")
    L.append("\\renewcommand{\\arraystretch}{1.0}")
    L.append("\\begin{tabular}{@{}l" + "c" * len(REMEDIES) + "c@{}}")
    L.append("\\toprule")
    hdr = [""]
    for g, n in groups:
        hdr.append("\\multicolumn{%d}{c}{\\textbf{%s}}" % (n, g))
    hdr.append("")
    L.append(" & ".join(hdr) + " \\\\")
    start, rules = 2, []
    for g, n in groups:
        rules.append("\\cmidrule(lr){%d-%d}" % (start, start + n - 1))
        start += n
    L.append("".join(rules))
    L.append("\\textbf{Incident} & "
             + " & ".join("\\textbf{%s}" % r[1:] for r, _, _ in REMEDIES)
             + " & \\textbf{Av.} \\\\")
    L.append("\\midrule")

    ncol = len(REMEDIES) + 2
    first = True
    for gstage, gname in GROUPS:
        rows = [i for i in incidents if i["stages"][0] == gstage]
        if not rows:
            continue
        if not first:
            L.append("\\addlinespace[1.5pt]")
        first = False
        L.append("\\multicolumn{%d}{@{}l}{\\itshape %s} \\\\" % (ncol, gname))
        for inc in sorted(rows, key=lambda x: (x["year"], x["id"])):
            label, _, _, avail, _ = COVERAGE[inc["id"]]
            if label == "ColdCard":
                label = "\\coldcard{}"
            label = label.replace("_", "\\_")
            cells = [cell(r, st, inc) for r, st, _ in REMEDIES]
            L.append("%s~\\cite{%s} & %s & %s \\\\"
                     % (label, ",".join(inc["cites"][:1]), " & ".join(cells), avail))
    L.append("\\bottomrule")
    L.append("\\end{tabular}")
    L.append("\\end{table}")
    with open(OUT, "w") as fh:
        fh.write("\n".join(L) + "\n")

    # Summary used in the text; printed so the numbers in the paper can be checked.
    import collections
    full = collections.Counter()
    half = collections.Counter()
    for inc in incidents:
        for r, st, _ in REMEDIES:
            c = cell(r, st, inc)
            if c == "\\hbfull":
                full[r] += 1
            elif c == "\\hbhalf":
                half[r] += 1
    av = collections.Counter(COVERAGE[i["id"]][3] for i in incidents)
    print("wrote", OUT)
    print("  incidents:", len(incidents), " remedies:", len(REMEDIES))
    print("  rows with a preventing remedy:", sum(1 for i in incidents if COVERAGE[i["id"]][1]))
    print("  availability:", dict(av))
    print("  full cells per remedy:", {r: full[r] for r, _, _ in REMEDIES})
    print("  half cells per remedy:", {r: half[r] for r, _, _ in REMEDIES})


if __name__ == "__main__":
    main()
