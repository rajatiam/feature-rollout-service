import csv, hashlib, io, json, math, re
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.request import Request, urlopen

def now(): return datetime.now(timezone.utc).isoformat()

def validate(data, records):
    if not isinstance(data,dict): raise ValueError('JSON object required')
    row = {}
    for key,example in CONFIG['example'].items():
        value = data.get(key)
        if isinstance(example,bool):
            if not isinstance(value,bool): raise ValueError(key+' must be boolean')
        elif isinstance(example,(int,float)):
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0: raise ValueError(key+' must be finite and nonnegative')
            if isinstance(example,int) and not isinstance(value,int): raise ValueError(key+' must be an integer')
        elif not isinstance(value,str) or not value.strip() or len(value)>2000: raise ValueError(key+' requires text, up to 2000 characters')
        row[key] = value.strip() if isinstance(value,str) else value
    return initialize(row,records)

def http_url(value):
    url = urlparse(value)
    if url.scheme not in ['http','https'] or not url.hostname or url.username or url.password: raise ValueError('HTTP(S) URL without credentials required')

def unique(rows,row,fields):
    if any(all(r[f]==row[f] for f in fields) for r in rows): raise ValueError('Duplicate '+', '.join(fields))

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
