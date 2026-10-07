"""Private loopback broker used only by this research testbed."""
import asyncio
import logging
import sys
from amqtt.broker import Broker

async def main():
    port=int(sys.argv[1]) if len(sys.argv)>1 else 18884
    broker=Broker({'listeners':{'default':{'type':'tcp','bind':f'127.0.0.1:{port}'}},
        'plugins':{'amqtt.plugins.authentication.AnonymousAuthPlugin':{'allow_anonymous':True}}})
    await broker.start()
    print(f'READY 127.0.0.1:{port}',flush=True)
    try:
        await asyncio.Future()
    finally:
        await broker.shutdown()

if __name__=='__main__':
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(main())
