"""RecAI cost estimator: Terraform plan + usage file -> monthly cost (US East Ohio), no accounts, no API keys.

    python estimate.py --usage usage-pilot.json [--plan plan.json] [--out estimate.docx]

plan.json comes from:  terraform plan -out tf.plan ; terraform show -json tf.plan > plan.json
Prices are in PRICES below. Each carries its source: V = verified from AWS's public price list or Anthropic's
model table on 2026-11-05; U = standard list price NOT yet verified (check before relying on it).
Resource types that are cost traps in this design are flagged loudly. Nothing here calls AWS.
"""
import argparse
import json
from pathlib import Path

PRICES = {  # name: (price, unit, source)
    "lambda_req": (0.20 / 1e6, "per request", "V"),
    "lambda_gbs_arm": (0.0000133334, "per GB-second (Arm)", "V"),
    "lambda_gbs_x86": (0.0000166667, "per GB-second (x86)", "V"),
    "httpapi_req": (1.00 / 1e6, "per request", "V"),
    "ddb_read": (0.125 / 1e6, "per read unit", "V"),
    "ddb_write": (0.625 / 1e6, "per write unit", "V"),
    "ddb_gb": (0.25, "per GB-month beyond 25 GB free", "V"),
    "cognito_mau": (0.0055, "per active user (Lite), beyond free allowance", "V"),
    "s3v_gb": (0.06, "per GB-month", "V"),
    "s3v_put_gb": (0.20, "per GB written", "V"),
    "s3v_query": (0.0000025, "per query", "V"),
    "s3v_proc_gb": (0.000003906, "per GB processed", "V"),
    "titan_mtok": (0.02, "per million tokens", "V"),
    "s3_gb": (0.023, "per GB-month", "U"),
    "sqs_req": (0.40 / 1e6, "per request", "U"),
    "logs_gb": (0.50, "per GB ingested", "U"),
    "alarm": (0.10, "per alarm-month", "U"),
    "waf_acl": (5.00, "per web ACL-month", "U"),
    "waf_rule": (1.00, "per rule-month", "U"),
    "waf_req": (0.60 / 1e6, "per request", "U"),
    "secret": (0.40, "per secret-month", "U"),
    "kms_key": (1.00, "per customer key-month", "U"),
    "nat": (32.85, "per NAT gateway-month, before data", "U"),
    "vpce_if": (7.30, "per interface endpoint per AZ-month", "U"),
    "ipv4": (3.65, "per public IPv4-month", "U"),
    "rds_micro": (13.98, "db.t4g.micro + 20 GB", "V"),
    "ec2_t3_large": (60.74, "per instance-month", "V"),
}
CLAUDE = {  # model: (input $/M, output $/M)  Anthropic model table, cached 2026-10-06 (V)
    "haiku-5-5": (0.10, 0.50), "sonnet-5-5": (2.00, 10.00), "opus-5-5": (4.00, 20.00),
}
TRAPS = {
    "aws_nat_gateway": ("nat", "NAT gateway: about $33/month even when idle"),
    "aws_eip": ("ipv4", "Elastic IP / public IPv4 address"),
    "aws_kms_key": ("kms_key", "Customer-managed KMS key: $1/month and cannot be deleted instantly"),
    "aws_db_instance": ("rds_micro", "Database server runs (and bills) all day"),
    "aws_rds_cluster": ("rds_micro", "Database cluster"),
    "aws_instance": ("ec2_t3_large", "Always-on server"),
}
FIXED = {"aws_cloudwatch_metric_alarm": "alarm", "aws_secretsmanager_secret": "secret", "aws_wafv2_web_acl": "waf_acl"}
USAGE_PRICED = ("aws_lambda_function", "aws_apigatewayv2", "aws_dynamodb_table", "aws_s3_bucket", "aws_sqs_queue",
                "aws_cognito", "aws_cloudwatch_log_group", "aws_s3vectors", "aws_iam", "aws_lambda_", "aws_budgets",
                "aws_s3_bucket_", "aws_sns", "aws_cloudwatch_event", "aws_cloudwatch_metric_alarm")


def p(name):
    return PRICES[name][0]


def estimate(u, plan):
    items = []  # (area, description, monthly $, source)

    def add(area, desc, amount, src):
        items.append((area, desc, round(amount, 4), src))

    gbs = u["lambda_invocations"] * u["lambda_avg_seconds"] * u["lambda_memory_gb"]
    free = u.get("apply_free_tier", False)
    reqs = max(0, u["lambda_invocations"] - (1_000_000 if free else 0))
    gbs_b = max(0, gbs - (400_000 if free else 0))
    add("Compute", f"Lambda requests ({u['lambda_invocations']:,})", reqs * p("lambda_req"), "V")
    add("Compute", f"Lambda compute ({gbs:,.0f} GB-s)", gbs_b * p("lambda_gbs_arm" if u.get("lambda_arm", True) else "lambda_gbs_x86"), "V")
    add("Edge", f"API Gateway HTTP API ({u['api_requests']:,} requests)", u["api_requests"] * p("httpapi_req"), "V")
    add("Data", "DynamoDB reads and writes", u["ddb_reads"] * p("ddb_read") + u["ddb_writes"] * p("ddb_write"), "V")
    add("Data", "DynamoDB storage", max(0, u["ddb_gb"] - 25) * p("ddb_gb"), "V")
    add("Data", f"S3 storage ({u['s3_gb']} GB)", u["s3_gb"] * p("s3_gb"), "U")
    docs, vpd, dims = u["docs_per_month"], u["vectors_per_doc"], u["dims"]
    vec_gb_month = docs * vpd * (dims * 4 + 1024) / 1e9
    stored = vec_gb_month * u.get("vector_retention_months", 12)
    add("Search", f"S3 Vectors storage (~{stored:.2f} GB held)", stored * p("s3v_gb"), "V")
    add("Search", "S3 Vectors writes", vec_gb_month * p("s3v_put_gb"), "V")
    add("Search", f"S3 Vectors queries ({u['searches']:,})", u["searches"] * p("s3v_query") + u["searches"] * stored * p("s3v_proc_gb"), "V")
    add("Search", "Embeddings (Bedrock Titan)", (docs * u["tokens_per_doc"] + u["searches"] * 30) / 1e6 * p("titan_mtok"), "V")
    add("Identity", "Cognito users beyond free allowance", max(0, u["cognito_mau"] - u.get("cognito_free_mau", 10_000)) * p("cognito_mau"), "V")
    add("Queue", "SQS", max(0, u["sqs_requests"] - 1_000_000) * p("sqs_req"), "U")
    add("Ops", f"CloudWatch logs ({u['logs_gb']} GB)", u["logs_gb"] * p("logs_gb"), "U")
    n_alarms = u["alarms"]
    n_waf = 0
    if plan:
        types = [rc["type"] for rc in plan.get("resource_changes", []) if "create" in rc["change"]["actions"]]
        n_alarms = types.count("aws_cloudwatch_metric_alarm") or n_alarms
        n_waf = types.count("aws_wafv2_web_acl")
    elif u.get("waf_acls"):
        n_waf = u["waf_acls"]
    add("Ops", f"CloudWatch alarms ({n_alarms})", n_alarms * p("alarm"), "U")
    if n_waf:
        add("Edge", f"WAF ({n_waf} ACL, {u.get('waf_rules', 2)} rules each)", n_waf * (p("waf_acl") + u.get("waf_rules", 2) * p("waf_rule")) + u["api_requests"] * p("waf_req"), "U")
    for c in u.get("claude", []):
        pin, pout = CLAUDE[c["model"]]
        cached = c.get("cached_fraction", 0.0)
        cost_in = c["calls"] * c["in_tokens"] / 1e6 * pin * ((1 - cached) + cached * 0.10)
        cost = (cost_in + c["calls"] * c["out_tokens"] / 1e6 * pout) * (0.5 if c.get("batch") else 1.0)
        add("Claude", f"{c['name']} ({c['calls']:,} x {c['model']}{', batch' if c.get('batch') else ''})", cost, "V")
    flags, unpriced = [], []
    if plan:
        for rc in plan.get("resource_changes", []):
            t, acts = rc["type"], rc["change"]["actions"]
            if "create" not in acts:
                continue
            if t in TRAPS:
                key, why = TRAPS[t]
                flags.append(f"{rc['address']}: {why}")
                add("TRAP", f"{rc['address']}", p(key), PRICES[key][2])
            elif t == "aws_vpc_endpoint" and (rc["change"]["after"] or {}).get("vpc_endpoint_type") == "Interface":
                flags.append(f"{rc['address']}: interface endpoint about $7.30 per zone-month (gateway endpoints are free)")
                add("TRAP", rc["address"], p("vpce_if"), "U")
            elif t == "aws_secretsmanager_secret":
                add("Ops", rc["address"], p("secret"), "U")
            elif not (t in FIXED or any(t.startswith(x) for x in USAGE_PRICED) or t == "aws_vpc_endpoint"):
                unpriced.append(f"{rc['address']} ({t})")
    return items, flags, unpriced


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--usage", required=True)
    ap.add_argument("--plan")
    ap.add_argument("--out")
    a = ap.parse_args()
    u = json.loads(Path(a.usage).read_text(encoding="utf-8"))
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8")) if a.plan else None
    items, flags, unpriced = estimate(u, plan)
    total = sum(i[2] for i in items)
    unver = sum(i[2] for i in items if i[3] == "U")
    print(f"Scenario: {u.get('name', a.usage)}   region us-east-2")
    for area, desc, amt, src in items:
        print(f"  {area:9} {desc:62} ${amt:9.2f}  {'verified' if src == 'V' else 'UNVERIFIED price'}")
    print(f"  TOTAL per month: ${total:.2f}   (of which priced with unverified list prices: ${unver:.2f})")
    for f in flags:
        print("  TRAP:", f)
    for x in unpriced:
        print("  NOT PRICED, review by hand:", x)
    if a.out:
        from docx import Document
        d = Document()
        d.add_heading("RecAI monthly cost estimate (US East, Ohio)", 1)
        d.add_paragraph(f"Scenario: {u.get('name', a.usage)}. Estimate only; usage-based lines depend on the numbers in the usage file.")
        t = d.add_table(rows=1, cols=4)
        t.style = "Table Grid"
        for i, h in enumerate(("Area", "Item", "Per month", "Price status")):
            t.rows[0].cells[i].text = h
        for area, desc, amt, src in items:
            r = t.add_row().cells
            r[0].text, r[1].text, r[2].text, r[3].text = area, desc, f"${amt:,.2f}", "verified" if src == "V" else "unverified"
        r = t.add_row().cells
        r[0].text, r[1].text, r[2].text, r[3].text = "Total", "", f"${total:,.2f}", f"${unver:,.2f} unverified"
        for f in flags:
            d.add_paragraph("Cost trap: " + f)
        for x in unpriced:
            d.add_paragraph("Not priced, review by hand: " + x)
        d.save(a.out)
        print("saved", a.out)


if __name__ == "__main__":
    main()
