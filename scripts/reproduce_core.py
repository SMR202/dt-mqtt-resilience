"""Execute original MQTT functions without copying unlicensed upstream code.

AST selection omits unrelated HTTP/TCP/CoAP/OPC-UA servers and Docker entrypoints.
All adaptations are recorded in the output manifest, and source hashes retained.
"""
import ast
import csv
import hashlib
import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import paho.mqtt.client as mqtt

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/'work/upstream-digital-twin'
OUT=ROOT/'results/baseline_core'


def namespace(component):
    p=UP/component/(component+'.py')
    raw=p.read_bytes()
    source=raw.decode('utf-8').replace('"mqtt_broker"','"127.0.0.1"')
    source=source.replace('MQTT_PORT = 1884','MQTT_PORT = 18885').replace('BROKER_PORT = 1884','BROKER_PORT = 18885')
    source=source.replace('open("/logs/sniffer.log", "a")','open('+repr(str(OUT/'sniffer.log'))+', "a", encoding="utf-8")')
    tree=ast.parse(source)
    keep=[node for node in tree.body if isinstance(node,(ast.Import,ast.ImportFrom,ast.Assign,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
    module=ast.Module(body=keep,type_ignores=[])
    env={'__name__':'native_core'}
    exec(compile(module,str(p),'exec'),env)
    return env,hashlib.sha256(raw).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    logs=(OUT/'broker.log').open('w')
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',18885))==0:
            raise RuntimeError('Port occupied')
    broker=subprocess.Popen([sys.executable,str(ROOT/'scripts/broker.py'),'18885'],stdout=logs,stderr=subprocess.STDOUT)
    for _ in range(100):
        with socket.socket() as s:
            if s.connect_ex(('127.0.0.1',18885))==0: break
        time.sleep(.1)
    else: raise RuntimeError('Broker failed')
    hashes={}
    events=[]
    start=time.perf_counter()
    recorder=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='core-recorder')
    def record(client,userdata,msg):
        events.append({'time':time.perf_counter()-start,'topic':msg.topic,'payload_bytes':len(msg.payload),'payload':msg.payload.decode('utf-8')})
    recorder.on_message=record
    recorder.connect('127.0.0.1',18885);recorder.subscribe('#');recorder.loop_start()
    try:
        sniffer,hashes['sniffer.py']=namespace('sniffer')
        threading.Thread(target=sniffer['monitor_mqtt'],daemon=True).start()
        threading.Thread(target=sniffer['stats_monitor'],daemon=True).start()
        twin,hashes['digital_twin.py']=namespace('digital_twin')
        twin['handle_mqtt']()
        device,hashes['device.py']=namespace('device')
        client=device['client']
        client.on_message=device['on_command']
        client.connect('127.0.0.1',18885);client.subscribe('device/commands');client.loop_start()
        for name in ['sensor_temperatura','sensor_umidade','sensor_braco','simular_ciclos_sensores']:
            threading.Thread(target=device[name],daemon=True).start()
        # Original calibration sleeps: 15 + 3*(15+2) = 66 seconds.
        for second in range(75):
            time.sleep(1)
            if second%15==0: print('Original core elapsed',second+1,flush=True)
        calibration_without_adapter=sniffer['teste_inicial_finalizado']
        burst=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='benign-burst')
        burst.connect('127.0.0.1',18885);burst.loop_start()
        if not calibration_without_adapter:
            print('ADAPTER: original final calibration signal missing; resend with network loop and QoS1',flush=True)
            info=burst.publish('device/commands','fim_teste_inicial',qos=1)
            info.wait_for_publish(timeout=5)
            time.sleep(1)
        for i in range(200):
            burst.publish('sensor/temperature',f'protocolo=mqtt;temperature=25.00;burst={i}')
            time.sleep(.05)
        burst.disconnect();burst.loop_stop()
        time.sleep(3)
        print('Calibration flag',sniffer['teste_inicial_finalizado'],flush=True)
        assert sniffer['teste_inicial_finalizado'], 'Original calibration did not finish'
        assert any(e['topic'].startswith('sensor/') for e in events)
        assert (OUT/'sniffer.log').exists()
        with (OUT/'events.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=['time','topic','payload_bytes','payload']);w.writeheader();w.writerows(events)
        from src.monitor import thresholds
        rates=[0]*89
        for e in events:
            if e['topic'].startswith('sensor/') and int(e['time'])<len(rates): rates[int(e['time'])]+=1
        # Native core's calibration includes sensor disable commands. This is
        # intentionally retained and differs from the paper's healthy training.
        limits=thresholds(rates[1:65])
        summary={'events':len(events),'elapsed':time.perf_counter()-start,'original_calibration_complete':True,
            'calibration_completed_without_resend':calibration_without_adapter,
            'source_sha256':hashes,'thresholds_from_observer_sensor_messages':limits,
            'burst_mean_messages_per_second':sum(rates[76:85])/9,
            'original_min_max':sniffer['min_max_pps'],
            'native_sensor_message_rates':rates,
            'adaptations':['AMQTT 0.11.3 replaces Mosquitto','localhost:18885 replaces Docker DNS/1884','only MQTT functions executed','benign sensor burst replaces attack scenarios','calibration and sensor function bodies unchanged','UTF-8 native log output','resend missing final calibration signal with QoS1 only if required'],
            'not_comparable_to_paper_packet_rates':True}
        burst_events=[e for e in events if ';burst=' in e['payload']]
        summary['observed_burst_messages']=len(burst_events)
        summary['observed_burst_messages_per_second']=len(burst_events)/(burst_events[-1]['time']-burst_events[0]['time']+.05)
        summary['burst_first_receipt']=burst_events[0]['time']
        summary['burst_last_receipt']=burst_events[-1]['time']
        (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
        print('CORE REPRODUCTION COMPLETE',len(events),'observed messages',flush=True)
    finally:
        recorder.disconnect();recorder.loop_stop()
        broker.terminate();broker.wait(timeout=10);logs.close()


if __name__=='__main__':
    sys.path.insert(0,str(ROOT))
    main()
