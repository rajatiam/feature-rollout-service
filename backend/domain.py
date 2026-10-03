import csv, hashlib, io, json, math, re
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from .validation import validate_input, http_url, unique

def now(): return datetime.now(timezone.utc).isoformat()
def validate(data,records): return initialize(validate_input(data,CONFIG['example']),records)

def initialize(row,records):
    unique(records,row,['name'])
    if row['rollout']>100: raise ValueError('Rollout must be 0 through 100')
    return dict(row,bucket=None,active=None)
def summary(rows):
    return {'flags':len(rows),'enabled':sum(r['enabled'] for r in rows),'evaluated':sum(r['active'] is not None for r in rows),'active':sum(r['active'] is True for r in rows)}
def transition(row,action):
    if action=='toggle': return dict(row,enabled=not row['enabled'],active=None,bucket=None)
    if action!='evaluate': raise ValueError('Unsupported action')
    bucket=int(hashlib.sha256((row['name']+':'+row['identity']).encode()).hexdigest()[:8],16)%100
    return dict(row,bucket=bucket,active=row['enabled'] and bucket<row['rollout'])
