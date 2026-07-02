# Section62 PDF Settle Price Parser

Extracts CME settlement prices for GC, SI, PL from the Daily Bulletin Section62 PDF.

## Prerequisites
```bash
brew install poppler  # for pdftotext
pip install pdfplumber requests
```

## Key insight: column positions

PDF columns (whitespace-separated):
```
JUL26  68.320  69.180  /64.460  65.240  -3.345  58989  1382  55067  -3149
 ①      ②       ③       ④        ⑤      ⑥       ⑦     ⑧     ⑨     ⑩
```
1. Month (e.g., JUL26)
2. Open (or `----` if no trade)
3. High (or `----`)
4. /Low (prepended with `/`, e.g. `/64.460`)
5. **Settle** ← this is the settlement price
6. Change (absolute)
7. Globex Volume
8. PNT/Pit Volume (or `----`)
9. Open Interest
10. OI Change

For gold: prices are in dollars (e.g., `4286.40`)
For silver: prices in dollars (e.g., `65.240`)
For platinum: prices in dollars (e.g., `1711.60`)

## Section headers — Dual header system (2026-06-12 discovery)

The PDF contains BOTH the 1oz/precious-metal mini contracts AND the full-size contracts in separate sections. The 1oz contracts appear FIRST in the PDF, before GC FUT. **Use grep with the full section string, not a partial match**, to avoid accidentally matching a line in the wrong metal's section.

| Code | Section header | Notes |
|------|---------------|-------|
| 1OZ (mini Au) | `1OZ FUT              1 OUNCE GOLD FUTURES` | 1oz gold futures, appears BEFORE GC FUT section. Also called QO on OI JSON. |
| GC | `GC FUT              COMEX GOLD FUTURES` | Full-size 100oz gold futures. **This is the primary source for AUG26 settlement.** |
| SI | `SI FUT              COMEX SILVER FUTURES` | Full-size 5,000oz silver futures. |
| SIL | `SIL FUT             MICRO SILVER FUTURES` | Micro silver (1,000oz), appears after SI section. |
| SIC | `SIC FUT             100-OUNCE SILVER FUT` | 100oz silver futures, between SI and SIL. |
| QI | `QI FUT              E-MINI SILVER FUTURES` | E-mini silver, before SI section. |
| QO | `QO FUT              E-MINI GOLD FUTURES` | E-mini gold, before SI section. |
| PL | `PL FUT              NYMEX PLATINUM FUTURES` | Platinum futures. |
| HG | `HG FUT              COMEX COPPER FUTURES` | Copper (not in scope). |
| PA | `PA FUT              NYMEX PALLADIUM FUTURES` | Palladium (not in scope). |

**Key pitfall**: When searching for the GC section in pdftotext output, lines are truncated with multiple spaces between code and description. Use `grep "GC FUT"` but be aware the 1OZ FUT section matches `AUG26` lines first with the same month codes. Safe approach: find the FIRST occurrence of `"COMEX GOLD FUTURES"` after the 1OZ section, or use `sed -n '/GC FUT.*COMEX GOLD FUTURES/,/TOTAL GC FUT/p'`.

**Example PDF layout order (from pdftotext -layout):**
1. `1OZ FUT 1 OUNCE GOLD FUTURES` — 1oz gold (QO on OI JSON)
2. Various non-precious metals (aluminium, cobalt, scrap steel, etc.)
3. `GC FUT COMEX GOLD FUTURES` — full-size 100oz gold — **primary source for AUG26 settle**
4. `MGC FUT MICRO GOLD FUTURES`
5. More non-precious metals
6. `QI FUT E-MINI SILVER FUTURES`
7. `QO FUT E-MINI GOLD FUTURES`
8. `SI FUT COMEX SILVER FUTURES` — full-size silver
9. `SIC FUT 100-OUNCE SILVER FUT`
10. `SIL FUT MICRO SILVER FUTURES`
11. `PL FUT NYMEX PLATINUM FUTURES`
12. METALS CONTRACTS LAST TRADE DATES table

## Using pdftotext (most reliable for tabular data)

```bash
curl -sL "https://raw.githubusercontent.com/Curarpikt0000/Daily_Metal-OI-CME_Notion/main/downloads/Section62_Metals_Futures_2026-06-10.pdf" -o /tmp/s62.pdf
pdftotext -layout /tmp/s62.pdf /tmp/s62.txt
```

Then parse the text file: search for section headers, then for the target contract month.

### Parsing pdftotext output by section

```bash
# Find line numbers of sections
grep -n "GC FUT\|SI FUT\|PL FUT\|1OZ FUT" /tmp/s62.txt | head -20

# Extract GC section
sed -n '/GC FUT.*COMEX GOLD/,/TOTAL GC FUT/p' /tmp/s62.txt

# Extract SI section
sed -n '/SI FUT.*COMEX SILVER/,/TOTAL SI FUT/p' /tmp/s62.txt

# Extract PL section
sed -n '/PL FUT.*NYMEX PLATINUM/,/TOTAL PL FUT/p' /tmp/s62.txt
```

### Python parsing (pdftotext output)

```python
def parse_section(text, section_header, target_month):
    lines = text.split('\n')
    in_section = False
    for i, ln in enumerate(lines):
        if section_header in ln:
            in_section = True
        if in_section and ln.strip().startswith(target_month):
            fields = ln.split()
            return float(fields[4])  # 5th field = Settle
    return None

# Read text file
with open('/tmp/s62.txt') as f:
    text = f.read()

# For GC AUG26 — now use the full section header
gc_settle = parse_section(text, 'GC FUT              COMEX GOLD FUTURES', 'AUG26')
si_settle = parse_section(text, 'SI FUT              COMEX SILVER FUTURES', 'JUL26')
pl_settle = parse_section(text, 'PL FUT              NYMEX PLATINUM FUTURES', 'JUL26')
```

## Using pdfplumber

```python
import pdfplumber, io, requests

url = "https://raw.githubusercontent.com/.../Section62_Metals_Futures_YYYY-MM-DD.pdf"
resp = requests.get(url, timeout=30)
resp.raise_for_status()

text = ""
with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
    for p in pdf.pages:
        pg = p.extract_text() or ""
        text += pg + "\n"

# Find settle for silver
in_section = False
for line in text.split("\n"):
    ln = line.strip()
    if "SI FUT COMEX SILVER FUTURES" in ln:
        in_section = True
        continue
    if in_section:
        if ln.startswith("JUL26"):
            fields = ln.split()
            settle = float(fields[4])  # 5th field
            break
        if ln.startswith("TOTAL") and "SI" in ln:
            break
```

## Important notes
- The PDF covers the **previous trading day's data**. A PDF uploaded on 6/12 has business date "Thu, Jun 11, 2026"
- Not all contract months appear — only those with volume or OI
- `----` means no value for that field
- Use OI top3 from the Notion OI JSON to confirm which month is active
- The 1OZ FUT section (mini/1oz gold for QO) has the SAME contract months (AUG26, OCT26, DEC26) as GC FUT but with different prices. Always verify you are in the correct section
- Verify: GC AUG26 settle from GC FUT section vs Yahoo `GC=F` close — should be within ~2.5% (different contract month). If close to 0%, you may have read the wrong section
