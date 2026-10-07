import tempfile
import unittest
from pathlib import Path

from src.policies import EdgeQueue, TwinState
from src.monitor import thresholds

def msg(d,s,t=None):
    return dict(device=d,seq=s,generated=float(s if t is None else t),value=float(s))

class ResearchCorrectness(unittest.TestCase):
    def test_durable_restart_and_fifo(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'queue.sqlite'
            q=EdgeQueue(path,'fifo');q.enqueue(msg(0,0));q.enqueue(msg(1,1));q.close()
            q=EdgeQueue(path,'fifo')
            i,m=q.peek(2);self.assertEqual(m['seq'],0)
            q.acknowledge(i);self.assertEqual(q.peek(2)[1]['seq'],1)
            self.assertEqual(q.audit_count(),2);q.close()

    def test_old_ack_cannot_delete_replacement(self):
        with tempfile.TemporaryDirectory() as td:
            q=EdgeQueue(Path(td)/'queue.sqlite','latest')
            q.enqueue(msg(0,0));old,m=q.peek(0)
            q.enqueue(msg(0,1));new,m=q.peek(1)
            self.assertNotEqual(old,new)
            q.acknowledge(old)
            self.assertEqual(q.peek(1)[1]['seq'],1)
            self.assertEqual(q.audit_count(),2);q.close()

    def test_round_robin_under_continuous_replacement(self):
        with tempfile.TemporaryDirectory() as td:
            q=EdgeQueue(Path(td)/'queue.sqlite','latest')
            served=[]
            for epoch in range(12):
                for d in range(4): q.enqueue(msg(d,epoch))
                i,m=q.peek(epoch);served.append(m['device'])
                q.served(m['device']);q.acknowledge(i)
            self.assertEqual(served,[0,1,2,3]*3);q.close()

    def test_ttl_does_not_expire_at_exact_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            q=EdgeQueue(Path(td)/'queue.sqlite','ttl',ttl=1)
            q.enqueue(msg(0,0));self.assertIsNotNone(q.peek(1))
            self.assertIsNone(q.peek(1.001));self.assertEqual(q.expired,1);q.close()

    def test_monotonic_receiver_and_guard_ablation(self):
        t=TwinState(1);t.accept(msg(0,2));self.assertFalse(t.accept(msg(0,1)))
        self.assertEqual(t.states[0]['seq'],2)
        t=TwinState(1,guard=False);t.accept(msg(0,2));t.accept(msg(0,1))
        self.assertEqual(t.regressions,1)

    def test_threshold_discrepancy_is_material(self):
        v=thresholds([1,1,1,1,2])
        self.assertGreater(v['paper_3sigma'],v['upstream_maximum'])

if __name__=='__main__': unittest.main()
