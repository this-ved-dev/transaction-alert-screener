"""Profile Tide HI (Zenodo 20591329) against screener rules R1-R4.

Usage: python scripts/profile_tide.py data/raw/tide
Needs: pip install duckdb
Checks match reports/AML transaction dataset selection.md: 1 multi-account owners,
2 cash bands and R1/R2/R3 hit counts, 3 label granularity, 6 dormancy (R4).
"""
import sys

import duckdb

# shortcut: approximate 2025 average USD per unit, good enough for banding; use a real FX table if amounts ever matter
USD_PER = {"USD": 1, "BMD": 1, "BSD": 1, "EUR": 1.13, "GBP": 1.32, "CHF": 1.21, "SGD": 0.76,
           "HKD": 0.128, "AED": 0.2723, "XCD": 0.37, "BZD": 0.5, "BBD": 0.5, "SCR": 0.07,
           "VUV": 0.0083, "JPY": 0.0067}
# US federal holidays (observed) in the data window; cash on these days posts next business day
HOLIDAYS = ["2025-01-01", "2025-01-20", "2025-02-17", "2025-05-26", "2025-06-19", "2025-07-04",
            "2025-09-01", "2025-10-13", "2025-11-11", "2025-11-27", "2025-12-25", "2026-01-01"]

d = sys.argv[1]
c = duckdb.connect()
opts = "header=true, all_varchar=true, quote='\"'"
c.execute(f"create table n as select * from read_csv('{d}/generated_nodes_HI.csv', {opts})")
c.execute(f"create table e as select * from read_csv('{d}/generated_edges_HI.csv', {opts})")
c.execute("create table fx as select * from (values " + ",".join(f"('{k}',{v})" for k, v in USD_PER.items()) + ") v(cur, rate)")


def show(title, sql):
    print(f"\n## {title}")
    print(c.sql(sql))


c.execute("""
create table acct as select node_id acct, replace(account_category,'AccountCategory.','') cat,
  currency, country_code, is_fraudulent='True' node_fraud from n where node_type='NodeType.ACCOUNT';
create table own as select src owner, dest acct from e where edge_type='ownership' and dest like 'account_%';
create table t as select row_number() over () id, src, dest, amount::double amt, currency cur,
  is_fraudulent='True' fraud, timestamp::timestamp ts, replace(transaction_type,'TransactionType.','') ttype,
  time_since_previous_transaction tsp
  from e where edge_type='transaction';
""")
missing = c.sql("select distinct cur from t where cur not in (select cur from fx)").fetchall()
assert not missing, f"add FX rates for {missing}"

# --- 0. shape and leakage --------------------------------------------------------------
show("0a. edge types", "select edge_type, count(*) n from e group by all order by n desc")
show("0b. time span", "select min(ts), max(ts), count(*) txns, sum(fraud::int) fraud_txns, round(avg(fraud::int)*100,3) pct from t")
show("0c. fraud by transaction type", "select ttype, count(*) n, sum(fraud::int) fraud from t group by all order by n desc")
show("0d. cash-typed edges: who is on each side (fraud share = leakage if 100%)", """
select ttype, split_part(src,'_',1) src_kind,
  exists(select 1 from own a join own b on a.owner=b.owner where a.acct=t.src and b.acct=t.dest) same_owner,
  count(*) n, sum(fraud::int) fraud, round(avg(fraud::int)*100,2) pct_fraud
from t where ttype in ('DEPOSIT','WITHDRAWAL') group by all order by all""")
show("0e. node-level is_fraudulent vs edge labels (accounts)", """
select node_fraud, count(*) accts,
  sum((acct in (select src from t where fraud union select dest from t where fraud))::int) touching_fraud_edge
from acct group by all""")
show("0f. negative time_since_previous_transaction","select count(*) from t where tsp like '-%'")

# --- 3. label granularity ---------------------------------------------------------------
print("\n## 3. label columns")
print("edges:", [r[0] for r in c.sql("describe e").fetchall()])
print("nodes:", [r[0] for r in c.sql("describe n").fetchall()])

# --- 1. multi-account owners -------------------------------------------------------------
show("1a. bank (non-cash) accounts per owner", """
select split_part(owner,'_',1) owner_kind, k accounts, count(*) owners from (
  select owner, count(*) filter (where cat <> 'CASH') k from own join acct using (acct) group by owner)
group by all order by all""")
show("1b. accounts with >1 owner", "select count(*) from (select acct from own group by acct having count(*) > 1)")
show("1c. countries per individual's bank accounts", """
select k countries, count(*) owners from (
  select owner, count(distinct country_code) k from own join acct using (acct)
  where cat <> 'CASH' and owner like 'individual_%' group by owner) group by all order by all""")

# --- 2. cash: customer, business day, USD -------------------------------------------------
c.execute(f"""
create table cal as
with days as (select r::date dt from range(date '2024-12-25', date '2026-01-15', interval 1 day) x(r)),
bd as (select dt, row_number() over (order by dt) bdi from days
       where dayofweek(dt) not in (0, 6) and dt not in ({",".join(f"date '{h}'" for h in HOLIDAYS)}))
select days.dt, min(bd.dt) bday, min(bd.bdi) bdi from days join bd on bd.dt >= days.dt group by days.dt;
create table cash as
select t.id, t.ttype, case when t.ttype='DEPOSIT' then 'in' else 'out' end dir,
  -- injected deposits come straight from an individual: that person is the CTR conductor
  case when t.src like 'individual_%' then t.src else o.owner end customer, t.ts, cal.bday, cal.bdi, t.cur, t.amt nominal, t.amt*fx.rate usd, t.fraud
from t join fx using (cur) join cal on cal.dt = t.ts::date
-- every account has exactly one owner (check 1b), so this join does not fan out
left join own o on o.acct = case when t.ttype='DEPOSIT' then t.dest else t.src end
where t.ttype in ('DEPOSIT','WITHDRAWAL');
""")
show("2a. cash rows without an owning customer", "select ttype, count(*) from cash where customer is null group by all")
for unit in ("nominal", "usd"):
    show(f"2b. cash amount bands ({unit})", f"""
    select ttype, case when {unit} < 2000 then '1 <2k' when {unit} < 9000 then '2 2k-8,999'
      when {unit} < 10000 then '3 9k-9,999' when {unit} <= 20000 then '4 10k-20k' else '5 >20k' end band,
      count(*) n, sum(fraud::int) fraud from cash group by all order by all""")
    show(f"2c. R1 customer-business-days with cash > 10,000 ({unit})", f"""
    select dir, count(*) cust_days, count(distinct customer) customers, sum(f::int) with_fraud,
      sum((tot <= 20000)::int) at_10k_20k from (
      select customer, bday, dir, sum({unit}) tot, bool_or(fraud) f from cash group by all having tot > 10000)
    group by all""")
    show(f"2d. R2a >=3 cash-ins of 2k-9,999 in 5 business days totalling >=15k ({unit})", f"""
    with w as (select customer, fraud,
      count(*) over p k, sum({unit}) over p s, max(fraud::int) over p wf
      from cash where dir='in' and {unit} >= 2000 and {unit} < 10000
      window p as (partition by customer order by bdi range between 4 preceding and current row))
    select count(distinct customer) hit_customers, count(distinct customer) filter (where wf=1) hits_with_fraud,
      (select count(distinct customer) from cash where fraud and dir='in') customers_with_fraud_cash_in,
      count(distinct customer) filter (where wf=1) * 1.0 /
        (select count(distinct customer) from cash where fraud and dir='in') recall
    from w where k >= 3 and s >= 15000""")
    show(f"2e. R2b 30-day cash-in >=25k with none >9,999 ({unit})", f"""
    with w as (select customer, sum({unit}) over p s, max({unit}) over p m, max(fraud::int) over p wf
      from cash where dir='in'
      window p as (partition by customer order by ts::date range between interval 29 days preceding and current row))
    select count(distinct customer) hit_customers, count(distinct customer) filter (where wf=1) hits_with_fraud
    from w where s >= 25000 and m < 10000""")
    show(f"2f. R3 >=2 cash-ins of 9k-10k on one business day ({unit})", f"""
    select count(*) cust_days, count(distinct customer) customers, sum(f::int) with_fraud from (
      select customer, bday, bool_or(fraud) f from cash
      where dir='in' and {unit} >= 9000 and {unit} <= 10000 group by all having count(*) >= 2)""")

# --- 6. dormancy (R4) on bank accounts ---------------------------------------------------
c.execute("""
create table acct_txn as
select acct, ts, amt*fx.rate usd, fraud from (
  select src acct, ts, amt, cur, fraud from t union all select dest, ts, amt, cur, fraud from t)
join acct using (acct) join fx using (cur) where cat <> 'CASH';
""")
show("6. R4 gaps >=180 days, then >=$5k within 7 days (USD)", """
with g as (select acct, ts, lag(ts) over (partition by acct order by ts) prev from acct_txn),
r as (select acct, ts from g where ts - prev >= interval 180 days),
x as (select r.acct, r.ts, sum(a.usd) v, bool_or(a.fraud) f from r join acct_txn a
  on a.acct = r.acct and a.ts >= r.ts and a.ts < r.ts + interval 7 days group by all)
select count(*) reactivations, count(distinct acct) accounts,
  count(*) filter (where v >= 5000) with_5k_in_7d, count(*) filter (where v >= 5000 and f) with_fraud from x""")
show("6b. bank accounts by last-seen gap before data end", """
select count(*) filter (where max_ts < timestamp '2025-07-04') idle_last_180d, count(*) accounts
from (select acct, max(ts) max_ts from acct_txn group by acct)""")
