"""Profile SAML-D (Kaggle berkanoztas/synthetic-transaction-monitoring-dataset-aml) against rules R2-R4.

Usage: python scripts/profile_saml_d.py data/raw/saml_d/SAML-D.csv
Needs: pip install duckdb
Checks match reports/AML transaction dataset selection.md: 4 Structuring/Smurfing profile,
5 which side of a cash row is the customer, 6 dormancy (R4), plus R2/R3 recall per account.
"""
import sys

import duckdb

# US federal holidays (observed) in the data window; cash on these days posts next business day
HOLIDAYS = ["2022-10-10", "2022-11-11", "2022-11-24", "2022-12-26", "2023-01-02", "2023-01-16",
            "2023-02-20", "2023-05-29", "2023-06-19", "2023-07-04", "2023-09-04"]
SUSPECT = "('Structuring','Smurfing')"

c = duckdb.connect()
# accounts as strings: numeric parsing drops leading zeros
c.execute(f"""create table t as select row_number() over () id, Sender_account snd, Receiver_account rcv,
  Amount::double amt, Payment_type ptype, Is_laundering = '1' laundering, Laundering_type ltype,
  (Date || ' ' || Time)::timestamp ts
  from read_csv('{sys.argv[1]}', header=true, all_varchar=true)""")


def show(title, sql):
    print(f"\n## {title}")
    c.sql(sql).show(max_rows=60)


show("0. shape", "select min(ts), max(ts), count(*) rows, sum(laundering::int) laundering from t")
show("0b. payment types", "select ptype, count(*) n, sum(laundering::int) laundering from t group by all order by n desc")

# --- 4. Structuring / Smurfing profile -----------------------------------------------------
show("4a. payment type mix", f"select ltype, ptype, count(*) n from t where ltype in {SUSPECT} group by all order by all")
show("4b. amount quantiles", f"""select ltype, ptype, count(*) n, min(amt), quantile_cont(amt, 0.25) p25, median(amt) p50,
  quantile_cont(amt, 0.75) p75, max(amt), round(avg((amt >= 2000 and amt < 10000)::int) * 100, 1) pct_2k_9999
  from t where ltype in {SUSPECT} group by all order by all""")
for side in ("snd", "rcv"):
    show(f"4c. clustering by {side}: rows and day span per account", f"""
    select ltype, count(*) accounts, median(n) rows_med, max(n) rows_max, median(span) days_span_med,
      round(avg((max5 >= 3)::int) * 100, 1) pct_accts_3plus_in_5d from (
      select ltype, {side}, count(*) n, date_diff('day', min(ts), max(ts)) span, max(k5) max5 from (
        select ltype, {side}, ts, count(*) over (partition by ltype, {side} order by ts::date
          range between interval 4 days preceding and current row) k5
        from t where ltype in {SUSPECT}) group by all) group by all order by all""")

# --- 5. cash orientation: the side with many distinct accounts is the customer -------------
show("5. distinct accounts per side of cash rows", """
select ptype, count(*) n, count(distinct snd) snd_accts, count(distinct rcv) rcv_accts,
  sum((snd = rcv)::int) self_rows from t where ptype in ('Cash Deposit','Cash Withdrawal') group by all""")
side = dict(c.sql("""select ptype, case when count(distinct snd) >= count(distinct rcv) then 'snd' else 'rcv' end
  from t where ptype in ('Cash Deposit','Cash Withdrawal') group by all""").fetchall())
print("customer side:", side)

# --- R2 / R3 on SAML-D with customer = account on the customer side ------------------------
c.execute(f"""
create table cal as
with days as (select r::date dt from range(date '2022-10-01', date '2023-09-15', interval 1 day) x(r)),
bd as (select dt, row_number() over (order by dt) bdi from days
       where dayofweek(dt) not in (0, 6) and dt not in ({",".join(f"date '{h}'" for h in HOLIDAYS)}))
select days.dt, min(bd.dt) bday, min(bd.bdi) bdi from days join bd on bd.dt >= days.dt group by days.dt;
create table cin as select {side.get('Cash Deposit', 'rcv')} customer, ts, bday, bdi, amt, laundering, ltype
from t join cal on cal.dt = t.ts::date where ptype = 'Cash Deposit';
""")
show("R2a. >=3 cash deposits of 2k-9,999 in 5 business days totalling >=15k (customer = account)", f"""
with w as (select customer, count(*) over p k, sum(amt) over p s, max(laundering::int) over p wl,
    max((ltype in {SUSPECT})::int) over p ws
  from cin where amt >= 2000 and amt < 10000
  window p as (partition by customer order by bdi range between 4 preceding and current row)),
pos as (select distinct customer from cin where ltype in {SUSPECT})
select count(distinct customer) hit_customers,
  count(distinct customer) filter (where wl = 1) hits_with_laundering,
  count(distinct customer) filter (where ws = 1) hits_with_structuring,
  (select count(*) from pos) structuring_customers,
  round(count(distinct customer) filter (where ws = 1) * 100.0 / (select count(*) from pos), 1) recall_pct
from w where k >= 3 and s >= 15000""")
show("R2b. 30-day cash deposits >=25k with none >9,999", f"""
with w as (select customer, sum(amt) over p s, max(amt) over p m, max((ltype in {SUSPECT})::int) over p ws
  from cin window p as (partition by customer order by ts::date range between interval 29 days preceding and current row))
select count(distinct customer) hit_customers, count(distinct customer) filter (where ws = 1) hits_with_structuring
from w where s >= 25000 and m < 10000""")
# SAML-D's "Structuring" label is many senders paying one receiver under 10k by non-cash rails
show("Stretch 16. >=3 non-cash payments <10k to one receiver in 7 days totalling >10k", """
with w as (select rcv, count(*) over p k, sum(amt) over p s, max(amt) over p m,
    max((ltype = 'Structuring')::int) over p ws
  from t where ptype not in ('Cash Deposit','Cash Withdrawal') and amt < 10000
  window p as (partition by rcv order by ts range between interval 7 days preceding and current row))
select count(distinct rcv) hit_receivers, count(distinct rcv) filter (where ws = 1) hits_with_structuring,
  (select count(distinct rcv) from t where ltype = 'Structuring') structuring_receivers
from w where k >= 3 and s > 10000""")
show("R3. >=2 cash deposits of 9k-10k on one business day", f"""
select count(*) cust_days, count(distinct customer) customers, sum(l::int) with_laundering, sum(st::int) with_structuring from (
  select customer, bday, bool_or(laundering) l, bool_or(ltype in {SUSPECT}) st from cin
  where amt >= 9000 and amt <= 10000 group by all having count(*) >= 2)""")
show("R1. customer-business-days with cash deposits > 10,000", """
select count(*) cust_days, count(distinct customer) customers, sum(l::int) with_laundering from (
  select customer, bday, sum(amt) tot, bool_or(laundering) l from cin group by all having tot > 10000)""")

# --- 6. dormancy (R4) ------------------------------------------------------------------------
show("6. gaps >=180 days per account, then >=5,000 within 7 days", """
with a as (select snd acct, ts, amt, laundering from t union all select rcv, ts, amt, laundering from t),
g as (select acct, ts, lag(ts) over (partition by acct order by ts) prev from a),
r as (select acct, ts from g where ts - prev >= interval 180 days),
x as (select r.acct, r.ts, sum(a.amt) v, bool_or(a.laundering) l from r join a
  on a.acct = r.acct and a.ts >= r.ts and a.ts < r.ts + interval 7 days group by all)
select count(*) reactivations, count(distinct acct) accounts, count(*) filter (where v >= 5000) with_5k_in_7d,
  count(*) filter (where v >= 5000 and l) with_laundering from x""")
