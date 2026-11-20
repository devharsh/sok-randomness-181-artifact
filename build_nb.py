"""Builder: constructs and executes randomness_analysis.ipynb for the SoK paper."""
import os
import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

nb = nbf.v4.new_notebook()
cells = []
md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell

cells.append(md(
"# SoK: Randomness Failures and Their Remedies -- Analysis Notebook\n\n"
"This notebook backs the quantitative claims in the paper. Every figure used in the text is\n"
"recomputed here, and each result carries an `assert` so the notebook self-verifies.\n\n"
"Contents:\n\n"
"1. Effective entropy vs. brute-force cost (the published ColdCard estimates of 32, 40.7, and 72 bits).\n"
"2. Conditioning cannot add entropy (hashed output looks uniform yet stays predictable).\n"
"3. ECDSA nonce-reuse key recovery on secp256k1 (the consumption-stage failures).\n"
"4. Cost amortization across a victim population (why one defect sweeps an ecosystem).\n\n"
"All computations use the Python standard library; only matplotlib is external."
))

cells.append(code(
"import math, hashlib\n"
"import matplotlib\n"
"matplotlib.use('Agg')\n"
"import matplotlib.pyplot as plt\n"
"from IPython.display import Image, display\n\n"
"# secp256k1 group order (n) and field prime (p)\n"
"n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141\n"
"p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F\n"
"print('secp256k1 order bit-length:', n.bit_length())"
))

cells.append(md(
"## 1. Effective entropy vs. brute-force cost\n\n"
"A seed with `H` bits of min-entropy ranges over at most `2**H` values. An attacker who can\n"
"reproduce the seed inputs enumerates those candidates and, for each, derives an address to test\n"
"against the public chain. Expected work is about `2**(H-1)` derivations. For ColdCard the published\n"
"analyses differ. The vendor estimates about 40 bits on the Mk2/Mk3 and about 72 bits on the\n"
"Mk4/Mk5/Q; Block bounds the Mk2/Mk3 near 40.7 bits and counts at most 2**32 output streams on the\n"
"later models once the fallback state and call history are fixed. We compute the cost at all three."
))

cells.append(code(
"def expected_time_seconds(H, rate):\n"
"    '''Expected brute-force time = (2**H / 2) / rate derivations per second.'''\n"
"    return (2.0**H / 2.0) / rate\n\n"
"scenarios = {\n"
"    'Mk4/Mk5/Q (Block, fixed state)': 32.0,\n"
"    'Mk2/Mk3 (upper bound)': 40.7,\n"
"    'Mk4/Mk5/Q (vendor estimate)': 72.0,\n"
"    'Design target': 128.0,\n"
"}\n"
"rates = {'single accelerator (1e6/s)': 1e6, 'cluster (1e8/s)': 1e8}\n\n"
"print(f\"{'scenario':30s} {'H':>6} {'rate':>26} {'exp. time':>16}\")\n"
"for label, H in scenarios.items():\n"
"    for rlabel, r in rates.items():\n"
"        t = expected_time_seconds(H, r)\n"
"        if t < 3600:      human = f'{t:8.1f} s'\n"
"        elif t < 86400:   human = f'{t/3600:8.2f} h'\n"
"        elif t < 3.15e7:  human = f'{t/86400:8.2f} d'\n"
"        else:             human = f'{t/3.15e7:8.2e} yr'\n"
"        print(f'{label:30s} {H:6.1f} {rlabel:>26} {human:>16}')\n\n"
"# Assertions matching the paper's appendix\n"
"assert abs(expected_time_seconds(32, 1e6) - 2147.48) < 1.0     # ~36 minutes\n"
"assert abs(expected_time_seconds(40.7, 1e6)/86400 - 10.34) < 0.05  # ~10 days\n"
"assert abs(expected_time_seconds(72, 1e8)/3.15576e7 - 7.48e5) < 0.01e5  # ~7.5e5 years\n"
"assert expected_time_seconds(128, 1e8) > 1e29                  # infeasible\n"
"print('\\nAssertions passed: 2^31/1e6 ~= 36 min, 2^39.7/1e6 ~= 10 days, 2^71/1e8 ~= 7.5e5 years, 2^128 infeasible.')"
))

cells.append(code(
"# Feasibility figure: brute-force time vs entropy bits\n"
"Hs = [i/2 for i in range(20, 261)]  # 10..130 bits\n"
"for rlabel, r in [('1e6 derivations/s', 1e6), ('1e8 derivations/s', 1e8)]:\n"
"    plt.plot(Hs, [expected_time_seconds(H, r) for H in Hs], label=rlabel)\n"
"plt.yscale('log')\n"
"for sec, name in [(3600,'1 hour'), (86400,'1 day'), (3.15e7,'1 year'), (3.15e7*1e6,'1 Myr')]:\n"
"    plt.axhline(sec, color='grey', lw=0.6, ls=':')\n"
"    plt.text(11, sec*1.3, name, fontsize=7, color='grey')\n"
"for H, name in [(32,'32 (Block, later models)'), (40.7,'40.7 (Mk2/Mk3)'), (72,'72 (vendor, later models)'), (128,'target 128')]:\n"
"    plt.axvline(H, color='crimson' if H<50 else 'green', lw=0.8, ls='--')\n"
"    plt.text(H+0.6, 1e-3, name, rotation=90, fontsize=7,\n"
"             color='crimson' if H<50 else 'green', va='bottom')\n"
"plt.xlabel('effective seed min-entropy (bits)')\n"
"plt.ylabel('expected brute-force time (s)')\n"
"plt.title('Brute-force feasibility of a reduced seed space')\n"
"plt.legend(loc='upper left', fontsize=8)\n"
"plt.tight_layout()\n"
"plt.savefig('figures/bruteforce.pdf')\n"
"plt.savefig('figures/bruteforce.png', dpi=130)\n"
"plt.close()\n"
"display(Image('figures/bruteforce.png'))"
))

cells.append(md(
"## 2. Conditioning cannot add entropy\n\n"
"Hashing makes output look uniform, but a deterministic function cannot enlarge the set of possible values: hashing `N` possible\n"
"seeds yields at most `N` possible outputs. We demonstrate with a small family."
))

cells.append(code(
"def sha256d(b):\n"
"    return hashlib.sha256(hashlib.sha256(b).digest()).digest()\n\n"
"family = 5000                      # a small seed family (stands in for a 2**H space)\n"
"outputs = {sha256d(i.to_bytes(4,'big')) for i in range(family)}\n"
"print('distinct seeds in :', family)\n"
"print('distinct outputs  :', len(outputs))\n"
"assert len(outputs) == family, 'hashing must not change the count of reachable values'\n"
"print('Confirmed: SHA-256d yields exactly as many outputs as inputs; no entropy is added.')"
))

cells.append(md(
"## 3. ECDSA nonce-reuse key recovery (secp256k1)\n\n"
"If one private key signs two messages with the same nonce `k`, the signatures share `r`, and\n"
"the key falls out algebraically with no search:\n\n"
"$$k = \\frac{h_1 - h_2}{s_1 - s_2} \\bmod n, \\qquad d = \\frac{s_1 k - h_1}{r} \\bmod n.$$\n\n"
"We implement secp256k1 from scratch, sign two messages with a deliberately reused nonce, and\n"
"recover the private key exactly."
))

cells.append(code(
"Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798\n"
"Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8\n"
"G = (Gx, Gy)\n\n"
"def inv(a, m): return pow(a % m, m - 2, m)\n"
"def ec_add(P, Q):\n"
"    if P is None: return Q\n"
"    if Q is None: return P\n"
"    if P[0] == Q[0] and (P[1] + Q[1]) % p == 0: return None\n"
"    if P == Q: lam = (3 * P[0] * P[0]) * inv(2 * P[1], p) % p\n"
"    else:      lam = (Q[1] - P[1]) * inv(Q[0] - P[0], p) % p\n"
"    x = (lam * lam - P[0] - Q[0]) % p\n"
"    return (x, (lam * (P[0] - x) - P[1]) % p)\n"
"def ec_mul(k, P):\n"
"    R = None\n"
"    while k:\n"
"        if k & 1: R = ec_add(R, P)\n"
"        P = ec_add(P, P); k >>= 1\n"
"    return R\n\n"
"def sign(d, k, msg):\n"
"    h = int.from_bytes(hashlib.sha256(msg).digest(), 'big') % n\n"
"    r = ec_mul(k, G)[0] % n\n"
"    s = (inv(k, n) * (h + r * d)) % n\n"
"    return h, r, s\n\n"
"d_true = 0x1234567890ABCDEF1122334455667788      # the victim's secret key\n"
"k_reused = 0xC0FFEE1234567890FEDCBA9876543210      # BUG: same nonce for both signatures\n"
"h1, r1, s1 = sign(d_true, k_reused, b'transfer 1 BTC to Alice')\n"
"h2, r2, s2 = sign(d_true, k_reused, b'transfer 2 BTC to Bob')\n\n"
"assert r1 == r2, 'reused nonce => identical r (the on-chain tell)'\n"
"k_rec = ((h1 - h2) * inv((s1 - s2) % n, n)) % n\n"
"d_rec = ((s1 * k_rec - h1) * inv(r1, n)) % n\n"
"print('shared r (hex):', hex(r1))\n"
"print('recovered nonce k == true k :', k_rec == k_reused)\n"
"print('recovered key   d == true d :', d_rec == d_true)\n"
"print('recovered private key       :', hex(d_rec))\n"
"assert k_rec == k_reused and d_rec == d_true\n"
"print('\\nA single repeated nonce, visible on a public ledger, discloses the key directly.')"
))

cells.append(md(
"## 4. Cost amortization across a victim population\n\n"
"Appendix C claims that an attacker enumerating a reduced seed space tests each candidate against\n"
"the entire population of funded identifiers at once, so the cost is amortized across all victims\n"
"rather than paid per wallet. That claim is worth measuring rather than asserting.\n\n"
"We model it abstractly and synthetically: candidates and targets are hashes of integers, with no\n"
"BIP-39 or BIP-32 derivation and no real addresses. The question is purely about scaling. If\n"
"membership testing is a constant-time set lookup, enumeration throughput should be effectively\n"
"flat in the number of targets, which is what makes a single defect a population-scale sweep."
))

cells.append(code(
"import time\n\n"
"def target_set(n):\n"
"    # synthetic stand-in for a set of funded identifiers\n"
"    return {hashlib.sha256(b'target-%d' % i).digest()[:8] for i in range(n)}\n\n"
"def enumerate_against(targets, candidates):\n"
"    # enumerate candidates, testing each for membership; returns (hits, seconds)\n"
"    t0 = time.perf_counter()\n"
"    hits = 0\n"
"    for i in range(candidates):\n"
"        d = hashlib.sha256(b'target-%d' % i).digest()[:8]\n"
"        if d in targets:\n"
"            hits += 1\n"
"    return hits, time.perf_counter() - t0\n\n"
"CANDIDATES = 200_000\n"
"rows = []\n"
"for n in (1, 10**3, 10**5, 10**6):\n"
"    hits, secs = enumerate_against(target_set(n), CANDIDATES)\n"
"    rows.append((n, hits, secs, CANDIDATES / secs))\n\n"
"print('%10s %8s %9s %14s' % ('targets','hits','seconds','candidates/s'))\n"
"for n, hits, secs, rate in rows:\n"
"    print('%10d %8d %9.3f %14.0f' % (n, hits, secs, rate))\n\n"
"ratio = rows[0][3] / rows[-1][3]\n"
"print('\\nthroughput at 1 target vs %d targets: %.2fx' % (rows[-1][0], ratio))\n"
"assert ratio < 3.0, 'membership testing should be near constant-time in the target count'\n"
"print('Confirmed: enumeration cost is governed by the candidate space, not the victim count.')\n"
"print('One defect therefore harvests an entire population for essentially the price of one.')"
))

cells.append(md(
"## Summary\n\n"
"Seed spaces of 2**32 and 2**40.7, the smaller published ColdCard estimates, are exhaustible in\n"
"minutes to days on modest hardware, while 72 bits, the vendor's estimate for later models, and the\n"
"128-bit design target are not. Statistical uniformity from hashing does not help the defender, because\n"
"conditioning cannot enlarge the space of reachable seeds. And at the consumption stage, a single\n"
"reused ECDSA nonce discloses the private key with no search at all. And because membership\n"
"testing is constant-time in the number of targets, enumeration cost is set by the candidate\n"
"space alone, so one defect harvests a whole population for the price of one. These are the numbers cited\n"
"in Section 4 and Appendix C of the paper."
))

nb['cells'] = cells
nb['metadata'] = {
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3.11'},
    'title': 'SoK Randomness Failures -- Analysis Notebook',
}

print('Executing notebook...')
ep = ExecutePreprocessor(timeout=180, kernel_name='python3')
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(HERE, 'figures'), exist_ok=True)
ep.preprocess(nb, {'metadata': {'path': HERE}})
with open(os.path.join(HERE, 'randomness_analysis.ipynb'), 'w') as f:
    nbf.write(nb, f)
print('Wrote randomness_analysis.ipynb with executed outputs.')
