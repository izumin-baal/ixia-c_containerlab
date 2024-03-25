#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import snappi
import yaml
import time

IXIA_CONTROLLER = "https://DEV-IXIA:8443"

def print_config(api):
    print("#### Config ####")
    print(api.get_config())
    print("################")

def wait_for(func, total_time, interval=0.5):
    start = time.time()
    timeout = total_time + 20

    while time.time() - start <= timeout:
        if func():
            print('### Traffic Stoped ###')
            return True
        time.sleep(interval)

    print("Timeout...")
    return False

def check_metrics(api, req):
    res = api.get_metrics(req)
    print(res)
    for m in res.flow_metrics:
        if "stopped" == m.transmit:
            return True

def main(config_file, total_time):
    config_path = '/scripts/ixiaconf/' + config_file
    api = snappi.api(location=IXIA_CONTROLLER, verify=False)

    # Load Settings
    with open(config_path, 'r') as yml:
        load_config = yaml.safe_load(yml)

    # IXIA Setup
    cfg = api.config().deserialize(load_config)
    for flow in cfg.flows:
        flow.duration.choice = flow.duration.FIXED_SECONDS
        flow.duration.fixed_seconds.seconds = total_time
    api.set_config(cfg)
    print_config(api)

    # BGP Setup
    try:
        bs = api.control_state()
        bs.protocol.bgp.peers.state = bs.protocol.bgp.peers.UP
        api.set_control_state(bs)
        print('Setup BGP wait 10sec...')
        time.sleep(10)
    except:
        print('Not BGP')

    # Capture Setup
    cs = api.control_state()
    cs.port.capture.state = cs.port.capture.START
    cs.port.capture.port_names = cfg.captures.next().port_names
    api.set_control_state(cs)

    # Traffic Setup
    ts = api.control_state()
    print('### Traffic Start ###')
    ts.traffic.flow_transmit.state = ts.traffic.flow_transmit.START
    api.set_control_state(ts)

    # Metrics Request Setup
    req = api.metrics_request()
    req.flow.flow_names = [f.name for f in cfg.flows]
    res = api.get_metrics(req)
    print(res)

    # Wait Traffic
    assert wait_for(lambda: check_metrics(api, req), total_time), "Metrics Error..."

    # Save Pcap
    for p in cfg.ports:
        req = api.capture_request()
        req.port_name = p.name
        pcap_bytes = api.get_capture(req)
        with open('/scripts/pcapfile/' + p.name + '.pcap', 'wb') as p:
            p.write(pcap_bytes.read())
            print("Save :" + p.name)

if __name__ == '__main__':
    print('### Traffic Generator Start ###')
    args = sys.argv
    config_file = str(args[1])
    total_time = int(args[2])
    main(config_file, total_time)
    print('### Traffic Generator End ###')