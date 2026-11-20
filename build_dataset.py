#!/usr/bin/env python3
"""
Build and validate the machine-readable artifacts released with the SoK.

Emits data/incidents.{csv,json}, data/counterfactuals.csv and
data/remedies.csv, then cross-validates the dataset against the LaTeX tables
in the paper sources so the paper and the released data cannot silently
diverge.

Field semantics are documented in data/schema.md.
"""
import csv, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
# The paper sources (sections/, references.bib) live one level up in the paper folder;
# set PAPER_DIR to point elsewhere.
PAPER = os.environ.get("PAPER_DIR") or (os.path.join(ROOT, "paper")
        if os.path.isdir(os.path.join(ROOT, "paper")) else os.path.dirname(ROOT))
OUT = os.path.join(ROOT, "data")
os.makedirs(OUT, exist_ok=True)

# stage: primary failure locus. S* = cross-cutting build/integration surface.
# adversary: T1 offline predictor, T2 state recovery, T3 consumption,
#            T4 subversion, T5 integration.
# observability: silent | statistical | external
# radius: device | fleet | ecosystem
# exploit_access: A1 remote (public data only), A2 local, A3 supply chain
INCIDENTS = [
 # id, name, year, domain, stages, root_cause, adversary, obs, radius, access, citekeys, source
 ("netscape1996","Netscape SSL RNG",1996,"Browser/TLS",["S4"],
  "Seed derived from process ID, parent PID, and time of day",["T1"],"silent","ecosystem","A1",
  ["goldberg1996netscape"],"Dr. Dobb's Journal, Jan. 1996"),
 ("mifare2008","MIFARE Crypto-1",2008,"Smart card/RFID",["S3"],
  "16-bit LFSR generator; challenges predictable",["T1"],"statistical","ecosystem","A2",
  ["garcia2008mifare","nohl2008rfid"],"ESORICS 2008; USENIX Security 2008"),
 ("debian2008","Debian OpenSSL",2008,"TLS/SSH",["S*"],
  "Downstream patch removed entropy input; ~15-bit key space",["T1","T5"],"silent","ecosystem","A1",
  ["yilek2009debian"],"IMC 2009, doi:10.1145/1644893.1644896"),
 ("ps3_2010","PlayStation 3 ECDSA",2010,"Game console",["S6"],
  "Constant per-signature nonce",["T3"],"external","ecosystem","A1",
  ["fail0verflow2010ps3"],"27th Chaos Communication Congress, 2010"),
 ("vmreset2010","Virtual machine reset",2010,"Virtualized TLS",["S5"],
  "Generator state cloned on snapshot or reset",["T2"],"silent","fleet","A1",
  ["ristenpart2010vmreset"],"NDSS 2010"),
 ("psandqs2012","Mining Ps and Qs",2012,"TLS/SSH devices",["S1"],
  "Low boot-time entropy; shared keys and common factors",["T1"],"silent","ecosystem","A1",
  ["heninger2012mining"],"USENIX Security 2012"),
 ("ronwrong2012","Shared RSA factors",2012,"TLS PKI",["S1"],
  "Low-entropy key generation; colliding primes",["T1"],"silent","ecosystem","A1",
  ["lenstra2012ron"],"IACR ePrint 2012/064"),
 ("php2012","PHP application tokens",2012,"Web applications",["S3"],
  "Non-cryptographic PRNG for security tokens",["T1"],"silent","ecosystem","A1",
  ["argyros2012php"],"USENIX Security 2012"),
 ("dualec2007","Dual_EC_DRBG back door",2007,"Standard",["S3"],
  "Kleptographic constants in standardized DRBG",["T4"],"silent","ecosystem","A3",
  ["shumow2007dualec","bernstein2016dualec"],"CRYPTO 2007 rump; The New Codebreakers 2016"),
 ("android2013","Android SecureRandom",2013,"Mobile wallet",["S3","S6"],
  "Unseeded PRNG leading to repeated ECDSA nonces",["T3"],"external","fleet","A1",
  ["michaelis2013randomly"],"CT-RSA 2013, doi:10.1007/978-3-642-36095-4_9"),
 ("devrandom2013","/dev/random robustness",2013,"OS RNG",["S2"],
  "Entropy accounting not robust under the formal model",["T2"],"silent","ecosystem","A2",
  ["dodis2013devrandom"],"ACM CCS 2013, doi:10.1145/2508859.2516653"),
 ("dualectls2014","Dual EC in TLS products",2014,"TLS products",["S3"],
  "Standardized back door shown practically exploitable",["T4"],"silent","fleet","A3",
  ["checkoway2014dualec"],"USENIX Security 2014"),
 ("btcnonce2014","Bitcoin ECDSA nonce reuse",2014,"Blockchain",["S6"],
  "Repeated ECDSA nonces observable on the public ledger",["T3"],"external","ecosystem","A1",
  ["bos2014ecc"],"FC 2014, doi:10.1007/978-3-662-45472-5_11"),
 ("whirlwind2014","Not-so-random numbers in virtualized Linux",2014,"Virtualized OS",["S5"],
  "VM fork reuses generator state",["T2"],"silent","fleet","A1",
  ["everspaugh2014whirlwind"],"IEEE S&P 2014, doi:10.1109/SP.2014.42"),
 ("juniper2016","Juniper Dual EC incident",2016,"VPN",["S3","S*"],
  "Back door plus attacker-substituted curve constant",["T4","T5"],"silent","fleet","A3",
  ["checkoway2016juniper"],"ACM CCS 2016, doi:10.1145/2976749.2978395"),
 ("opensslrng2016","OpenSSL RNG design weaknesses",2016,"TLS library",["S5"],
  "Fork-safety and internal state weaknesses",["T2"],"silent","fleet","A2",
  ["strenzke2016openssl"],"EUROCRYPT 2016, doi:10.1007/978-3-662-49890-3_25"),
 ("roca2017","ROCA (Infineon RSALib)",2017,"Smart-card key generation",["S4"],
  "Structured primes reduce effective entropy; Coppersmith factorization",["T1"],
  "statistical","ecosystem","A1",["nemec2017roca"],"ACM CCS 2017, doi:10.1145/3133956.3133969"),
 ("duhk2018","DUHK",2018,"VPN and FIPS appliances",["S4","S5"],
  "Hardcoded X9.31 seed key enabling state recovery",["T2"],"silent","fleet","A1",
  ["cohney2018duhk"],"ACM CCS 2018, doi:10.1145/3243734.3243756"),
 ("biasednonce2019","Biased Nonce Sense",2019,"Blockchain",["S6"],
  "Short or biased ECDSA nonces; lattice key recovery",["T3"],"external","ecosystem","A1",
  ["breitner2019biased"],"FC 2019, doi:10.1007/978-3-030-32101-7_1"),
 ("minerva2020","Minerva",2020,"Smart-card ECDSA",["S6"],
  "Nonce bit-length leaks via timing",["T3"],"statistical","fleet","A2",
  ["jancar2020minerva"],"TCHES 2020(4), doi:10.13154/tches.v2020.i4.281-308"),
 ("tpmfail2020","TPM-Fail",2020,"TPM ECDSA",["S6"],
  "Nonce leakage via timing; lattice key recovery",["T3"],"statistical","fleet","A2",
  ["moghimi2020tpmfail"],"USENIX Security 2020"),
 ("blackswan2020","CTR_DRBG pseudorandom black swans",2020,"TLS libraries",["S3","S5"],
  "Missing reseed plus cache side channel enabling state recovery",["T2"],"silent","fleet","A2",
  ["cohney2020blackswan"],"IEEE S&P 2020, doi:10.1109/SP40000.2020.00046"),
 ("trustwallet2022","Trust Wallet browser extension",2022,"Browser wallet",["S3","S4"],
  "Weak generator; private key derivable from the public address",["T1"],"silent","fleet","A1",
  ["ledger2023trustwallet"],"Ledger Donjon disclosure"),
 ("profanity2022","Profanity vanity address generator",2022,"Ethereum key tool",["S4"],
  "32-bit seed for GPU key search; generator state reconstructable",["T1"],
  "silent","ecosystem","A1",["1inch2022profanity"],"1inch disclosure, 2022"),
 ("milksad2023","Milk Sad (Libbitcoin Explorer bx seed)",2023,"Wallet CLI",["S3","S4"],
  "Mersenne Twister MT19937 seeded from a 32-bit system clock value",["T1"],
  "silent","ecosystem","A1",["milksad2023"],"CVE-2023-39910; milksad.info"),
 ("amdrdseed2025","AMD Zen 5 RDSEED failure",2025,"CPU instruction",["S1"],
  "16- and 32-bit RDSEED return 0 while incorrectly signaling success",["T1"],
  "statistical","ecosystem","A2",["amd2025rdseed"],"AMD-SB-7055; CVE-2025-62626"),
 ("illbloom2026","Ill Bloom",2026,"Software wallets",["S3","S4"],
  "Weak CryptoJS PRNG used for BIP-39 recovery phrase generation",["T1"],
  "silent","ecosystem","A1",["coinspect2026illbloom"],"Coinspect disclosure; illbloom.org"),
 ("coldcard2026","ColdCard seed generation",2026,"Hardware wallet",["S*","S3","S4","S5"],
  "Symbol collision linked seed generation to a non-cryptographic software PRNG",
  ["T5","T1"],"silent","fleet","A1",
  ["coinkite2026backgrounder","block2026coldcard"],"Coinkite backgrounder; Block engineering analysis"),
]

# Counterfactual rows (preventing remedy, availability, reason) are generated from the
# coverage data in build_coverage.py so the matrix and the released CSV cannot disagree.
from build_coverage import counterfactual_rows
COUNTERFACTUALS = counterfactual_rows(INCIDENTS)

REMEDIES = [
 ("R1","Vetted entropy source with health tests",["S1","S2"],"prevent;detect","medium",
  "Opaque hardware source may still be weak or subverted"),
 ("R2","Standardized CSPRNG/DRBG",["S3"],"prevent","low",
  "Side-channel state recovery if misused"),
 ("R3","Robust seeding, block until seeded",["S1","S4"],"prevent","medium",
  "Boot-time stalls tempt unsafe non-blocking calls"),
 ("R4","Continuous reseed with fork and VM hygiene",["S5"],"prevent;contain","medium",
  "Requires host cooperation"),
 ("R5","Hedged nonces (RFC 6979 plus noise), EdDSA",["S6"],"prevent","low",
  "Pure determinism assists fault and side-channel attacks"),
 ("R6","Hedged or derandomized constructions",["S4","S5","S6"],"prevent;contain","medium",
  "Not yet default in most libraries and protocols"),
 ("R7","Threshold key generation, randomness beacons",["S4","S6"],"prevent;contain","high",
  "Coordination cost; wrong trust model for local custody"),
 ("R8","Statistical tests and certification",["S1","S2","S3"],"detect","medium",
  "Blind to predictable-but-uniform and adversarially-chosen-but-uniform output"),
 ("R9","Reproducible builds, RNG boot self-test, attestation",["S*"],"prevent;detect","high",
  "Immature tooling; self-test must exercise the real path"),
 ("R10","User entropy and passphrase (dice, BIP-39)",["S1","S4"],"prevent;contain","high",
  "Depends on user diligence; poor default"),
 ("R11","Formal verification of RNG code",["S2","S3","S5"],"prevent","high",
  "Specifications may omit the deployed threat"),
 ("R12","Tamper and environmental sensors, fail-closed",["S1","S2"],"prevent;detect","medium",
  "Protects the source, not the wiring that selects it"),
 ("R13","Verifiable entropy protocols (commit-reveal)",["S1","S4","S*"],"prevent;detect","medium",
  "Needs a host verifier; covers key generation only"),
 ("R14","Anti-exfil / sign-to-contract nonces",["S6"],"prevent","medium",
  "Needs host support; per-signature protocol cost"),
]

# Optional per-incident fields. cve: identifier where one was assigned.
# dwell_years: years from defect introduction to public discovery, populated ONLY where both
# dates are established by a primary source; empty elsewhere rather than guessed.
EXTRA = {
 "debian2008":    ("CVE-2008-0166", "2.0"),   # patched 2006-05, discovered 2008-05
 "milksad2023":   ("CVE-2023-39910", ""),
 "amdrdseed2025": ("CVE-2025-62626", ""),
 "coldcard2026":  ("", "5.3"),                # 2021-03 migration, 2026-07 exploitation
}

# target_secret: which secret the failure ultimately exposes. This distinguishes failures that
# compromise long-lived key material from those that compromise a per-use value, a distinction the
# stage model implies but does not state outright.
#   long_term_key | session_key | ephemeral_nonce | generator_state
TARGET = {
 "netscape1996":"session_key",      "mifare2008":"session_key",      "debian2008":"long_term_key",
 "ps3_2010":"ephemeral_nonce",      "vmreset2010":"session_key",     "psandqs2012":"long_term_key",
 "ronwrong2012":"long_term_key",    "php2012":"session_key",         "dualec2007":"generator_state",
 "android2013":"ephemeral_nonce",   "devrandom2013":"generator_state","dualectls2014":"generator_state",
 "btcnonce2014":"ephemeral_nonce",  "whirlwind2014":"generator_state","juniper2016":"generator_state",
 "opensslrng2016":"generator_state","roca2017":"long_term_key",      "duhk2018":"generator_state",
 "biasednonce2019":"ephemeral_nonce","minerva2020":"ephemeral_nonce", "tpmfail2020":"ephemeral_nonce",
 "blackswan2020":"generator_state", "trustwallet2022":"long_term_key","profanity2022":"long_term_key",
 "milksad2023":"long_term_key",     "amdrdseed2025":"long_term_key", "illbloom2026":"long_term_key",
 "coldcard2026":"long_term_key",
}

def write_outputs():
    inc_fields = ["id","name","year","domain","stages","root_cause","adversary",
                  "observability","radius","exploit_access","target_secret","cve","dwell_years",
                  "citation_keys","source"]
    rows = []
    for r in INCIDENTS:
        cve, dwell = EXTRA.get(r[0], ("", ""))
        rows.append(dict(zip(inc_fields, [
            r[0], r[1], r[2], r[3], ";".join(r[4]), r[5], ";".join(r[6]),
            r[7], r[8], r[9], TARGET.get(r[0],""), cve, dwell, ";".join(r[10]), r[11]])))
    with open(os.path.join(OUT,"incidents.csv"),"w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=inc_fields); w.writeheader(); w.writerows(rows)
    # JSON keeps list-valued fields as lists
    jrows = []
    for r in INCIDENTS:
        cve, dwell = EXTRA.get(r[0], ("", ""))
        jrows.append(dict(zip(inc_fields, [
            r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9],
            TARGET.get(r[0]) or None, cve or None,
            dwell if dwell != "" else None, r[10], r[11]])))
    with open(os.path.join(OUT,"incidents.json"),"w") as f:
        json.dump({"schema_version":"1.0","count":len(jrows),"incidents":jrows}, f, indent=2)
    with open(os.path.join(OUT,"counterfactuals.csv"),"w",newline="") as f:
        w = csv.writer(f); w.writerow(["incident_id","stages","preventing_remedy",
                                       "partial_remedy","available_at_the_time","why_absent"])
        w.writerows(COUNTERFACTUALS)
    with open(os.path.join(OUT,"remedies.csv"),"w",newline="") as f:
        w = csv.writer(f); w.writerow(["id","name","stages","mode","friction","residual_risk"])
        for r in REMEDIES:
            w.writerow([r[0], r[1], ";".join(r[2]), r[3], r[4], r[5]])
    return len(rows)

def validate():
    """Cross-check the dataset against the LaTeX tables and the bibliography."""
    ok = True
    inc_tex = open(os.path.join(PAPER,"sections","04-incidents.latex")).read()
    rem_tex = open(os.path.join(PAPER,"sections","05-remedies.latex")).read()
    bib = open(os.path.join(PAPER,"references.bib")).read()

    # 1. incident count claimed in the caption matches the dataset
    words = {"twenty-six":26,"twenty-seven":27,"twenty-eight":28,"twenty-nine":29,"thirty":30}
    m = re.search(r"\\caption\{([A-Za-z-]+) deployed randomness failures", inc_tex)
    claimed = words.get(m.group(1).lower()) if m else None
    if claimed != len(INCIDENTS):
        print(f"  FAIL caption claims {claimed} incidents, dataset has {len(INCIDENTS)}"); ok = False
    else:
        print(f"  ok   incident count matches paper caption ({claimed})")

    # 2. every citation key in the dataset exists in the bibliography
    missing = sorted({k for r in INCIDENTS for k in r[10] if f"{{{k}," not in bib})
    if missing:
        print(f"  FAIL citation keys absent from references.bib: {missing}"); ok = False
    else:
        print(f"  ok   all {sum(len(r[10]) for r in INCIDENTS)} citation keys resolve in references.bib")

    # 3. every dataset incident appears as a row in the LaTeX table
    absent = [r[0] for r in INCIDENTS if not any(k in inc_tex for k in r[10])]
    if absent:
        print(f"  FAIL incidents missing from the LaTeX table: {absent}"); ok = False
    else:
        print(f"  ok   every dataset incident is cited in the incidents table")

    # 4. remedy count matches the remedies table caption
    rwords = {"Eleven":11,"Twelve":12,"Thirteen":13,"Fourteen":14,"Fifteen":15}
    m = re.search(r"\\caption\{(\w+) remedy families", rem_tex)
    rclaimed = rwords.get(m.group(1)) if m else None
    if rclaimed != len(REMEDIES):
        print(f"  FAIL caption claims {rclaimed} remedies, dataset has {len(REMEDIES)}"); ok = False
    else:
        print(f"  ok   remedy count matches paper caption ({rclaimed})")

    # 5. counterfactual incident ids all refer to real incidents
    ids = {r[0] for r in INCIDENTS}
    bad = [c[0] for c in COUNTERFACTUALS if c[0] not in ids]
    if bad:
        print(f"  FAIL counterfactual rows reference unknown incidents: {bad}"); ok = False
    else:
        print(f"  ok   all {len(COUNTERFACTUALS)} counterfactual rows resolve to dataset incidents")

    # 6. controlled vocabularies
    vocab_ok = all(r[7] in {"silent","statistical","external"} for r in INCIDENTS) and \
               all(r[8] in {"device","fleet","ecosystem"} for r in INCIDENTS) and \
               all(r[9] in {"A1","A2","A3"} for r in INCIDENTS) and \
               all(TARGET.get(r[0]) in {"long_term_key","session_key","ephemeral_nonce",
                                        "generator_state"} for r in INCIDENTS)
    print(("  ok   " if vocab_ok else "  FAIL ") +
          "controlled vocabularies (observability, radius, access, target secret)")
    ok = ok and vocab_ok
    # 7. report any controlled-vocabulary value that no incident uses. An unused value is not
    #    automatically wrong, but it must be justified in the text rather than left dangling.
    import collections
    for field, idx, vocab in (("observability", 7, ("silent","statistical","external")),
                              ("radius", 8, ("device","fleet","ecosystem")),
                              ("exploit_access", 9, ("A1","A2","A3"))):
        counts = collections.Counter(r[idx] for r in INCIDENTS)
        unused = [v for v in vocab if counts.get(v, 0) == 0]
        if unused:
            print(f"  note {field}: no incident uses {unused} "
                  f"(must be explained in the text, not silently dropped)")
        else:
            print(f"  ok   {field}: every permitted value is exercised")

    return ok

if __name__ == "__main__":
    n = write_outputs()
    print(f"Wrote {n} incidents, {len(COUNTERFACTUALS)} counterfactuals, "
          f"{len(REMEDIES)} remedies to {OUT}/")
    print("Validating dataset against the paper:")
    sys.exit(0 if validate() else 1)
