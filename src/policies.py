"""Independent application policies; MQTT delivery guarantees are not simulated here."""
import json
import sqlite3


class EdgeQueue:
    """SQLite outbox with a separate append-only local audit history.

    Rows are removed only after the transport accepts them. Local acceptance is
    not an end-to-end cloud acknowledgement. One gateway writer is assumed.
    """
    def __init__(self, path, policy, limit=10000, ttl=1.0):
        self.policy, self.limit, self.ttl = policy, limit, ttl
        self.db = sqlite3.connect(str(path))
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS outbox (id INTEGER PRIMARY KEY AUTOINCREMENT, device INTEGER, generated REAL, payload TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT, device INTEGER, generated REAL, payload TEXT)')
        self.coalesced = self.expired = self.overflow = 0
        self.last_device = -1

    def enqueue(self, message):
        payload = json.dumps(message, separators=(',', ':'))
        with self.db:
            self.db.execute('INSERT INTO audit(device,generated,payload) VALUES (?,?,?)', (message['device'], message['generated'], payload))
            if self.policy.startswith('latest'):
                self.coalesced += self.db.execute('DELETE FROM outbox WHERE device=?', (message['device'],)).rowcount
            self.db.execute('INSERT INTO outbox(device,generated,payload) VALUES (?,?,?)', (message['device'], message['generated'], payload))
            count = self.size()
            if count > self.limit:
                self.overflow += self.db.execute('DELETE FROM outbox WHERE id IN (SELECT id FROM outbox ORDER BY id LIMIT ?)', (count-self.limit,)).rowcount

    def peek(self, now, exclude=()):
        if self.policy == 'ttl':
            with self.db:
                self.expired += self.db.execute('DELETE FROM outbox WHERE generated < ?', (now-self.ttl,)).rowcount
        where = (' WHERE id NOT IN ('+','.join('?' for _ in exclude)+')') if exclude else ''
        if self.policy.startswith('latest'):
            row = self.db.execute('SELECT id,payload FROM outbox'+where+' ORDER BY CASE WHEN device > ? THEN 0 ELSE 1 END,device LIMIT 1', (*exclude,self.last_device)).fetchone()
        else:
            row = self.db.execute('SELECT id,payload FROM outbox'+where+' ORDER BY id LIMIT 1', tuple(exclude)).fetchone()
        return (row[0], json.loads(row[1])) if row else None

    def acknowledge(self, row_id):
        with self.db:
            row = self.db.execute('SELECT device FROM outbox WHERE id=?',(row_id,)).fetchone()
            if row:
                self.last_device = row[0]
            self.db.execute('DELETE FROM outbox WHERE id=?', (row_id,))

    def served(self, device):
        self.last_device = device

    def discard_outbox(self):
        with self.db:
            self.db.execute('DELETE FROM outbox')

    def size(self):
        return self.db.execute('SELECT COUNT(*) FROM outbox').fetchone()[0]

    def audit_count(self):
        return self.db.execute('SELECT COUNT(*) FROM audit').fetchone()[0]

    def close(self):
        self.db.close()


class TwinState:
    def __init__(self, devices, guard=True):
        self.guard = guard
        self.states = {d: {'seq': -1, 'generated': 0., 'value': 0.} for d in range(devices)}
        self.rejections = self.regressions = 0

    def accept(self, message):
        prior = self.states[message['device']]
        older = message['seq'] <= prior['seq']
        if older and self.guard:
            self.rejections += 1
            return False
        if message['generated'] < prior['generated']:
            self.regressions += 1
        self.states[message['device']] = message
        return True
