#!/usr/bin/env python3
"""Render docs/build/flows/02-flow-measurements.md from the latest frozen run.

Stdlib only. Reads the latest run's summary.json (the earlier runs are subsets
with identical values; the renderer checks that) and writes the page. Nothing
is typed by hand: every value is a summary.json field or a formula over fields.

    python3 scripts/render_flow_measurements.py                      # English page
    python3 scripts/render_flow_measurements.py --lang es --out F    # Spanish copy
    python3 scripts/render_flow_measurements.py --verify [--data D]  # fresh run check

--verify copies the latest measure_flow.py into a temporary folder, runs it in a
subprocess against the raw data (D, default $FLOW_DATA_DIR or evidence/flows/data),
and compares the fresh summary.json and the data hashes with the committed ones.
The frozen run folders are never touched.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE = os.path.join(ROOT, "evidence/flows")
RUNS = ["", "2024Q4-v2", "2024Q4-v3"]  # oldest first; the last one is the source
LATEST = RUNS[-1]
DEFAULT_OUT = os.path.join(ROOT, "docs/build/flows/02-flow-measurements.md")
META_KEYS = ("script_version", "window", "window_start", "window_end")

# Flow order follows the hackathon brief. Key = top-level summary.json key.
FLOWS = ["accounts", "cards", "disputes", "credit"]

# field (or dict-field prefix ending in ".") -> unit, English text, Spanish text.
# A "{}" in the text takes the child key of a dict-valued field.
FIELDS = {
    "accounts.n_calls": ("count", "Calls in the window (`call_center_interactions`)", "Llamadas en la ventana (`call_center_interactions`)"),
    "accounts.reason_transaccional": ("count", "Calls whose `contact_reason` is *Transaccional* (transactional)", "Llamadas cuyo `contact_reason` es *Transaccional*"),
    "accounts.n_transactions": ("count", "Transactions in the window (event date)", "Transacciones en la ventana (fecha del evento)"),
    "accounts.status_Approved": ("count", "Transactions with status Approved", "Transacciones con estado Approved (aprobada)"),
    "accounts.status_Declined": ("count", "Transactions with status Declined", "Transacciones con estado Declined (rechazada)"),
    "accounts.status_Pending": ("count", "Transactions with status Pending", "Transacciones con estado Pending (pendiente)"),
    "accounts.status_Reversed": ("count", "Transactions with status Reversed", "Transacciones con estado Reversed (revertida)"),
    "accounts.fraud_true": ("count", "Transactions with `is_fraud = True`", "Transacciones con `is_fraud = True`"),
    "accounts.reason_category_degenerate": ("flag", "`reason_category` mirrors `contact_reason`: calls carry no subcategory", "`reason_category` repite `contact_reason`: las llamadas no tienen subcategoría"),
    "accounts.transaccional_products_blank": ("count", "*Transaccional* calls with a blank product field", "Llamadas *Transaccional* con el campo de producto vacío"),
    "accounts.transaccional_products_blank_pct": ("%", "Same, as a share of *Transaccional* calls", "Lo mismo, como proporción de las llamadas *Transaccional*"),
    "accounts.decline_spread_pp.": ("%", "Spread of the non-approved rate (Declined, Pending or Reversed) across values of `{}`", "Dispersión de la tasa de no aprobadas (Declined, Pending o Reversed) entre los valores de `{}`"),
    "accounts.decline_learnable": ("flag", "Fixed in code: `false` when every spread is small. Not a proof", "Fijo en el código: `false` cuando todas las dispersiones son pequeñas. No es una prueba"),
    "cards.actionable": ("count", "Transactions Declined, Pending or Reversed", "Transacciones Declined, Pending o Reversed"),
    "cards.fraud_true": ("count", "Transactions with `is_fraud = True` (same count as `accounts.fraud_true`)", "Transacciones con `is_fraud = True` (igual que `accounts.fraud_true`)"),
    "cards.credit_cards": ("count", "Products of type *Tarjeta Crédito* (credit card) in the filtered snapshot", "Productos de tipo *Tarjeta Crédito* en el snapshot filtrado"),
    "cards.blocked": ("count", "Products with status Blocked, **all product types**, filtered snapshot", "Productos con estado Blocked, **todos los tipos**, snapshot filtrado"),
    "cards.blocked_spread_pp": ("%", "Spread of the Blocked rate across product types (all products)", "Dispersión de la tasa de Blocked entre tipos de producto (todos los productos)"),
    "cards.blocked_learnable": ("flag", "Fixed in code, same caveat", "Fijo en el código, misma salvedad"),
    "credit.n_products": ("count", "Products in the snapshot after the `last_updated` filter (all types)", "Productos del snapshot tras el filtro `last_updated` (todos los tipos)"),
    "credit.delinquent": ("count", "Products with `days_past_due` above 0", "Productos con `days_past_due` mayor que 0"),
    "credit.delinq_spread_pp": ("%", "Spread of the share above 30 days past due across the three loan types (*Préstamo Personal*, *Préstamo Hipotecario*, *Tarjeta Crédito*)", "Dispersión de la proporción con más de 30 días de mora entre los tres tipos de préstamo (*Préstamo Personal*, *Préstamo Hipotecario*, *Tarjeta Crédito*)"),
    "credit.delinq_learnable": ("flag", "Fixed in code, same caveat", "Fijo en el código, misma salvedad"),
    "disputes.n": ("count", "Complaints created in the window", "Quejas creadas en la ventana"),
    "disputes.claims": ("count", "Complaints with `case_type = Claim` (claims)", "Quejas con `case_type = Claim` (reclamos)"),
    "disputes.unrecognized_claim": ("count", "Claims whose `subcategory` is *Cargo no reconocido* (unrecognized charge)", "Reclamos cuya `subcategory` es *Cargo no reconocido*"),
    "disputes.unrecognized_complaint": ("count", "Complaints (`case_type = Complaint`) with the same subcategory", "Quejas (`case_type = Complaint`) con la misma subcategoría"),
    "disputes.dispute_share_pct": ("%", "`unrecognized_claim` as a share of `disputes.n`", "`unrecognized_claim` como proporción de `disputes.n`"),
    "disputes.dispute_share_ci95pp": ("%", "95% interval half-width of that share (normal approximation)", "Semiancho del intervalo al 95% de esa proporción (aproximación normal)"),
    "disputes.dup_extra_rows": ("count", "Extra rows repeating a `complaint_id`", "Filas extra que repiten un `complaint_id`"),
    "disputes.rows_in_heldout": ("count", "Rows dated inside the held-out zone (must be 0)", "Filas con fecha dentro de la zona held-out (debe ser 0)"),
    "disputes.description_leak": ("count", "Complaints whose `description` contains their `category`", "Quejas cuya `description` contiene su `category`"),
    "disputes.linkage_filled": ("count", "Complaints with `origin_interaction_id` filled", "Quejas con `origin_interaction_id` lleno"),
    "disputes.transcripts": ("count", "Transcripts in the window", "Transcripciones en la ventana"),
    "disputes.join_hit": ("count", "Transcripts whose `interaction_id` matches a call in the window", "Transcripciones cuyo `interaction_id` coincide con una llamada de la ventana"),
    "disputes.text_prefixes": ("count", "Distinct 60-character prefixes of `customer_text` across all transcripts", "Prefijos distintos de 60 caracteres de `customer_text` en todas las transcripciones"),
    "disputes.regulator_n": ("count", "Complaints received through the Regulator channel (filed via the financial regulator)", "Quejas recibidas por el canal Regulator (presentadas ante el regulador financiero)"),
    "disputes.regulator_cnr_n": ("count", "Of those, unrecognized-charge claims", "De ellas, reclamos de cargo no reconocido"),
    "disputes.escalated_calls": ("count", "Calls with `was_escalated = True`", "Llamadas con `was_escalated = True`"),
    "disputes.escalated_calls_n": ("count", "Calls in the window (denominator)", "Llamadas en la ventana (denominador)"),
    "disputes.escalated_by_reason.": ("count", "Escalated calls with `contact_reason = {}`", "Llamadas escaladas con `contact_reason = {}`"),
    "disputes.esc_spread_pp.": ("%", "Spread of the call escalation rate across values of `{}`", "Dispersión de la tasa de escalación de llamadas entre los valores de `{}`"),
    "disputes.esc_agent_spread_pp": ("range %", "Lowest and highest escalation rate across agents with at least 20 calls", "Tasa de escalación más baja y más alta entre agentes con al menos 20 llamadas"),
    "disputes.esc_learnable": ("flag", "Fixed in code, same caveat", "Fijo en el código, misma salvedad"),
    "disputes.cnr_spread_pp.": ("%", "Spread of the unrecognized-charge claim rate across values of `{}` (all complaints)", "Dispersión de la tasa de reclamos de cargo no reconocido entre los valores de `{}` (todas las quejas)"),
    "disputes.cnr_learnable": ("flag", "Fixed in code, same caveat", "Fijo en el código, misma salvedad"),
    "disputes.leak_fill_open_pct.": ("%", "Share of **open** complaints with `{}` filled", "Proporción de quejas **abiertas** con `{}` lleno"),
    "disputes.leak_fill_terminal_pct.": ("%", "Share of **closed** complaints with `{}` filled", "Proporción de quejas **cerradas** con `{}` lleno"),
}

# (section, English label, Spanish label, formula, numerator, denominator, scale)
# numerator "@sum:a,b" adds fields; denominator "@days" is the window length.
DERIVED = [
    ("accounts", "Transactional share of calls", "Proporción de llamadas transaccionales", "reason_transaccional ÷ n_calls", "accounts.reason_transaccional", "accounts.n_calls", 100),
    ("accounts", "Transactional calls per day", "Llamadas transaccionales por día", "reason_transaccional ÷ days", "accounts.reason_transaccional", "@days", 1),
    ("accounts", "Approved share of transactions", "Proporción de transacciones Approved", "status_Approved ÷ n_transactions", "accounts.status_Approved", "accounts.n_transactions", 100),
    ("accounts", "Declined share of transactions", "Proporción de transacciones Declined", "status_Declined ÷ n_transactions", "accounts.status_Declined", "accounts.n_transactions", 100),
    ("accounts", "Pending share of transactions", "Proporción de transacciones Pending", "status_Pending ÷ n_transactions", "accounts.status_Pending", "accounts.n_transactions", 100),
    ("accounts", "Reversed share of transactions", "Proporción de transacciones Reversed", "status_Reversed ÷ n_transactions", "accounts.status_Reversed", "accounts.n_transactions", 100),
    ("cards", "Non-approved share of transactions", "Proporción de transacciones no aprobadas", "actionable ÷ accounts.n_transactions", "cards.actionable", "accounts.n_transactions", 100),
    ("cards", "Fraud share of transactions", "Proporción de transacciones con fraude", "fraud_true ÷ accounts.n_transactions", "cards.fraud_true", "accounts.n_transactions", 100),
    ("cards", "Blocked share of all products", "Proporción de productos Blocked (todos los tipos)", "blocked ÷ credit.n_products", "cards.blocked", "credit.n_products", 100),
    ("disputes", "Unrecognized-charge claims per day", "Reclamos de cargo no reconocido por día", "unrecognized_claim ÷ days", "disputes.unrecognized_claim", "@days", 1),
    ("disputes", "Unrecognized-charge claims and complaints", "Reclamos y quejas de cargo no reconocido", "unrecognized_claim + unrecognized_complaint", "@sum:disputes.unrecognized_claim,disputes.unrecognized_complaint", None, 1),
    ("disputes", "Claims share of complaints", "Proporción de reclamos sobre quejas", "claims ÷ n", "disputes.claims", "disputes.n", 100),
    ("disputes", "Description leak share", "Proporción con fuga en la descripción", "description_leak ÷ n", "disputes.description_leak", "disputes.n", 100),
    ("disputes", "Linkage share", "Proporción con vínculo a llamada", "linkage_filled ÷ n", "disputes.linkage_filled", "disputes.n", 100),
    ("disputes", "Transcript join share", "Proporción de transcripciones con llamada", "join_hit ÷ transcripts", "disputes.join_hit", "disputes.transcripts", 100),
    ("disputes", "Regulator share of complaints", "Proporción de quejas por el regulador", "regulator_n ÷ n", "disputes.regulator_n", "disputes.n", 100),
    ("disputes", "Call escalation share", "Proporción de llamadas escaladas", "escalated_calls ÷ escalated_calls_n", "disputes.escalated_calls", "disputes.escalated_calls_n", 100),
    ("credit", "Delinquent share of products", "Proporción de productos con mora", "delinquent ÷ n_products", "credit.delinquent", "credit.n_products", 100),
]

# Static page text per language. "{...}" are filled by render().
TEXT = {
    "en": {
        "title": "Flow measurements",
        "intro": ("What the measurement script returned for each candidate flow. **This page is generated** by "
                  "[`scripts/render_flow_measurements.py`]({script}) from the latest frozen `summary.json`; do not edit it "
                  "by hand. It holds results only. What they mean for the choice is in [flow selection]({sel}); "
                  "where the four flows come from is in [candidate flows]({cand})."),
        "window": ("**Window:** {start} to {end} exclusive ({days} days, by event date). Data from 2025-07-01 on is reserved "
                   "for the final evaluation and was not read (`disputes.rows_in_heldout`)."),
        "run_h": "Source",
        "run": ("Values come from run `{run}` (script version `{ver}`), stored in [`{folder}`]({link}) with its method and data "
                "manifest. Earlier runs in `evidence/flows/` are subsets of it: every field they share has the same value "
                "(checked each time this page is generated). The raw data never enters the repository."),
        "read_h": "Reading guide",
        "read": ["**Count** is a number of rows. **%** is a share or a spread, in percent.",
                 "**Spread** = highest minus lowest rate among the values of one field. It is a one-field-at-a-time screen: it does not rule out a model that combines fields.",
                 "Fields ending in `_learnable` are **fixed in code** (`false`), not computed. Read them together with the spreads.",
                 "Field names ending in `_pp` keep the script's name; their values are in %."],
        "cols": ("Field", "Value", "What it is"),
        "flows": {"accounts": "1. Accounts and payments", "cards": "2. Cards",
                  "disputes": "3. Disputes", "credit": "4. Credit"},
        "derived": "**Derived figures** (formula over the fields above; {days} days in the window):",
        "dcols": ("Figure", "Formula", "Value"),
        "regen_h": "Reproduce",
        "regen": ("```bash\npython3 scripts/render_flow_measurements.py            # rewrite this page\n"
                  "python3 scripts/render_flow_measurements.py --verify   # fresh run in a subprocess, compared with this data\n```\n\n"
                  "`--verify` needs the raw data (gitignored) in `evidence/flows/data/`, or the folder in `$FLOW_DATA_DIR` "
                  "or `--data`. A new run goes in a new folder under `evidence/flows/`; add it to `RUNS` in the script."),
    },
    "es": {
        "title": "Mediciones de los flujos",
        "intro": ("Lo que devolvió el script de medición para cada flujo candidato. **Esta página se genera** con "
                  "`scripts/render_flow_measurements.py` a partir del último `summary.json` congelado; no se edita "
                  "a mano. Solo contiene resultados. Qué significan para la elección está en [selección del flujo]({sel}); "
                  "de dónde salen los cuatro flujos está en [flujos candidatos]({cand})."),
        "window": ("**Ventana:** del {start} al {end} (excluido), {days} días, por fecha del evento. Los datos desde 2025-07-01 "
                   "están reservados para la evaluación final y no se leyeron (`disputes.rows_in_heldout`)."),
        "run_h": "Origen",
        "run": ("Los valores vienen de la corrida `{run}` (versión del script `{ver}`), guardada en `{folder}` con su método y "
                "el manifiesto de datos. Las corridas anteriores en `evidence/flows/` son subconjuntos de esta: todo campo que "
                "comparten tiene el mismo valor (se comprueba cada vez que se genera esta página). Los datos crudos nunca entran al repositorio."),
        "read_h": "Guía de lectura",
        "read": ["**Count** es un número de filas. **%** es una proporción o una dispersión, en porcentaje.",
                 "**Dispersión** = tasa más alta menos tasa más baja entre los valores de un campo. Es un cribado de un campo a la vez: no descarta un modelo que combine campos.",
                 "Los campos que terminan en `_learnable` están **fijos en el código** (`false`), no se calculan. Léelos junto con las dispersiones.",
                 "Los nombres de campo que terminan en `_pp` conservan el nombre del script; sus valores están en %."],
        "cols": ("Campo", "Valor", "Qué es"),
        "flows": {"accounts": "1. Cuentas y pagos", "cards": "2. Tarjetas",
                  "disputes": "3. Disputas", "credit": "4. Crédito"},
        "derived": "**Cifras derivadas** (fórmula sobre los campos de arriba; {days} días en la ventana):",
        "dcols": ("Cifra", "Fórmula", "Valor"),
        "regen_h": "Reproducir",
        "regen": ("```bash\npython3 scripts/render_flow_measurements.py            # reescribe la página\n"
                  "python3 scripts/render_flow_measurements.py --verify   # corrida nueva en un subproceso, comparada con estos datos\n```\n\n"
                  "`--verify` necesita los datos crudos (ignorados por git) en `evidence/flows/data/`, o la carpeta indicada en "
                  "`$FLOW_DATA_DIR` o `--data`. Una corrida nueva va en una carpeta nueva de `evidence/flows/`; se añade a `RUNS` en el script."),
    },
}


def flatten(d, prefix=""):
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            yield from flatten(v, key + ".")
        else:
            yield key, v


def load(folder):
    with open(os.path.join(EVIDENCE, folder, "summary.json"), encoding="utf-8") as fh:
        return json.load(fh)


def describe(key, lang):
    idx = 1 if lang == "en" else 2
    if key in FIELDS:
        return FIELDS[key][0], FIELDS[key][idx]
    for pref, meta in FIELDS.items():
        if pref.endswith(".") and key.startswith(pref):
            return meta[0], meta[idx].format(key[len(pref):])
    raise SystemExit(f"No description registered for field {key}; add it to FIELDS")


def localize(text, lang):
    """English 1,234.5 -> Spanish 1.234,5 (numbers only; text has no other separators)."""
    if lang != "es":
        return text
    return text.replace(",", "\0").replace(".", ",").replace("\0", ".")


def fmt(value, unit):
    if isinstance(value, bool):
        return str(value).lower()
    if unit == "range %" and isinstance(value, list):
        return " – ".join(f"{x:g}%" for x in value)
    if unit == "%":
        return f"{value:g}%"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def check_runs():
    """Every field shared with an earlier run must have the same value."""
    latest = dict(flatten({k: v for k, v in load(LATEST).items() if k not in META_KEYS}))
    problems = []
    for folder in RUNS[:-1]:
        old = dict(flatten({k: v for k, v in load(folder).items() if k not in META_KEYS}))
        for key, val in old.items():
            if key not in latest:
                problems.append(f"{key} is in run '{folder or '.'}' but not in {LATEST}")
            elif latest[key] != val:
                problems.append(f"{key}: {val!r} in '{folder or '.'}' vs {latest[key]!r} in {LATEST}")
    if problems:
        sys.exit("Runs disagree:\n  " + "\n  ".join(problems))
    return latest


def render(lang, out_path):
    values = check_runs()
    meta = load(LATEST)
    t = TEXT[lang]
    days = (date.fromisoformat(meta["window_end"]) - date.fromisoformat(meta["window_start"])).days
    if lang == "en":
        sel, cand = "03-flow-selection.md", "01-flow-candidates.md"
        link = f"../../../evidence/flows/{LATEST}/README.md"
        script = "../../../scripts/render_flow_measurements.py"
    else:
        sel, cand = "03-seleccion-del-flujo.md", "01-flujos-candidatos.md"
        link, script = "", ""
    o = []
    w = o.append
    w(f"# {t['title']}\n")
    w(t["intro"].format(script=script, sel=sel, cand=cand) + "\n")
    w(t["window"].format(start=meta["window_start"], end=meta["window_end"], days=days) + "\n")
    w(f"## {t['run_h']}\n")
    w(t["run"].format(run=LATEST, ver=meta["script_version"], folder=f"evidence/flows/{LATEST}/", link=link) + "\n")
    w(f"## {t['read_h']}\n")
    w("\n".join(f"- {x}" for x in t["read"]) + "\n")
    for section in FLOWS:
        w(f"## {t['flows'][section]}\n")
        w(f"| {t['cols'][0]} | {t['cols'][1]} | {t['cols'][2]} |\n|---|---|---|")
        for key in [k for k in values if k.startswith(section + ".")]:
            unit, text = describe(key, lang)
            w(f"| `{key}` | {localize(fmt(values[key], unit), lang)} | {text} |")
        w("")
        rows = [d for d in DERIVED if d[0] == section]
        if rows:
            w(t["derived"].format(days=days) + "\n")
            w(f"| {t['dcols'][0]} | {t['dcols'][1]} | {t['dcols'][2]} |\n|---|---|---|")
            for _, en, es, formula, num, den, scale in rows:
                if num.startswith("@sum:"):
                    txt = f"{sum(values[k] for k in num[5:].split(',')):,}"
                else:
                    d = days if den == "@days" else values[den]
                    v = values[num] / d * scale
                    txt = f"{v:,.1f}" if scale == 1 else f"{v:.2f}%"
                w(f"| {en if lang == 'en' else es} | {formula} | {localize(txt, lang)} |")
            w("")
    w(f"## {t['regen_h']}\n")
    w(t["regen"] + "\n")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(o))
    print(f"wrote {out_path}")


def hashes_from_verify(text):
    """'  31 files |    1877 rows | f445... | pattern' -> {pattern: hash}."""
    return {m.group(2): m.group(1) for m in re.finditer(r"\|\s*([0-9a-f]{16})\s*\|\s*(\S+)\s*$", text, re.M)}


def hashes_from_manifest(text):
    out = {}
    for m in re.finditer(r"\|\s*([0-9a-f]{16})\s*\|\s*(?:data/)?(\S+)\s*\|", text):
        out[m.group(2)] = m.group(1)
    return out


def verify(data_dir):
    data_dir = os.path.abspath(data_dir)
    if not os.path.isdir(data_dir):
        sys.exit(f"Raw data not found at {data_dir}; pass --data or set FLOW_DATA_DIR")
    tmp = tempfile.mkdtemp(prefix="flow-verify-")
    try:
        # measure_flow.py expects <flows>/data next to <flows>/<run>/measure_flow.py
        run_dir = os.path.join(tmp, "flows", LATEST)
        os.makedirs(run_dir)
        os.symlink(data_dir, os.path.join(tmp, "flows", "data"))
        script = os.path.join(run_dir, "measure_flow.py")
        shutil.copy(os.path.join(EVIDENCE, LATEST, "measure_flow.py"), script)

        def run(mode):
            r = subprocess.run([sys.executable, script, mode], cwd=run_dir, capture_output=True, text=True)
            if r.returncode != 0:
                sys.exit(f"measure_flow.py {mode} failed:\n{r.stderr[-2000:]}")
            return r.stdout

        failures = []
        fresh_hashes = hashes_from_verify(run("verify"))
        with open(os.path.join(EVIDENCE, LATEST, "MANIFEST.md"), encoding="utf-8") as fh:
            manifest = hashes_from_manifest(fh.read())
        for pat, h in fresh_hashes.items():
            if manifest.get(pat) != h:
                failures.append(f"data hash differs for {pat}: fresh {h}, manifest {manifest.get(pat)}")
        print(f"data hashes: {len(fresh_hashes)} patterns checked against MANIFEST.md")

        run("summary")
        with open(os.path.join(run_dir, "summary.json"), encoding="utf-8") as fh:
            fresh = dict(flatten(json.load(fh)))
        frozen = dict(flatten(load(LATEST)))
        for key in sorted(set(fresh) | set(frozen)):
            if fresh.get(key) != frozen.get(key):
                failures.append(f"{key}: fresh {fresh.get(key)!r} vs committed {frozen.get(key)!r}")
        print(f"summary.json: {len(frozen)} fields compared with a fresh run")
        if failures:
            sys.exit("VERIFY FAILED:\n  " + "\n  ".join(failures))
        print("VERIFY OK: the data matches the manifest and the fresh run reproduces every committed field")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", choices=sorted(TEXT), default="en")
    ap.add_argument("--out", help="output file (default: the docs page; required for --lang es)")
    ap.add_argument("--verify", action="store_true", help="run measure_flow.py in a subprocess and compare")
    ap.add_argument("--data", default=os.environ.get("FLOW_DATA_DIR", os.path.join(EVIDENCE, "data")))
    a = ap.parse_args()
    if a.verify:
        verify(a.data)
        return
    if a.lang != "en" and not a.out:
        ap.error("--out is required for --lang other than en")
    render(a.lang, a.out or DEFAULT_OUT)


if __name__ == "__main__":
    main()
