#!/usr/bin/env python
import re
import subprocess
import time
import os

import yaml
from prometheus_client import Gauge, start_http_server

lineres = re.compile(r'(^.*\s+\:\s+)(.*\=.*%)(.*)')

def get_interface(ip):
    cmd = ['ip', 'route', 'get', '{0}'.format(ip)]
    p = subprocess.Popen(' '.join(cmd), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = p.communicate()
    match = re.search(r'(?<=dev)(.*)(?= src | proto)', str(res)).group(1).strip()
    return match

def get_mtu(interface):
    cmd = ["cat", "/sys/class/net/{0}/mtu".format(interface)]
    p = subprocess.Popen(' '.join(cmd), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = p.communicate()
    return res[0].decode('utf-8')

def ping(targets):
    ret = {} 
    # set mtu to test
    mtu = get_mtu(get_interface(targets[0]))
    mtu = mtu if mtu else 1500
    mtu = str(int(mtu) - 28)   
    cmd = ['fping', '-q', '-s', '-c3', '-b {0}'.format(mtu)]
    p = subprocess.Popen(' '.join(cmd)+' '+' '.join(targets), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = p.communicate()
    for line in res[1].split('\n'):
        if lineres.search(line):
            try:
                ret = handle(line, ret, mtu)
            except:
                ret = failhandle(line, ret, mtu)
    return ret

def failhandle(line, ret, mtu):
    host = lineres.search(line).groups()[0].replace(' ', '').replace(':', '').strip(' ')
    ret[host] = {}
    ret[host]['loss'] = "100"
    ret[host]['loss']['mtu'] = mtu
    return ret

def handle(line, ret, mtu):
    host, loss, lat = lineres.search(line).groups()
    host = host.replace(' ', '').replace(':', '').strip(' ')
    loss = loss.replace('xmt/rcv/%loss = ', '').split('/')[2].replace('%', '')
    lat = lathandle(lat.replace(',', '').strip(' '))
    if host not in ret:
        ret[host] = {}
    ret[host]['loss'] = loss
    ret[host]['lat'] = lat
    ret[host]['mtu'] = mtu
    return ret

def lathandle(lat):
    lat = lat.split(' = ')
    head = lat[0].split('/')
    tail = lat[1].split('/')
    lat = dict(zip(head, tail))
    return lat

def getconfig():
    try:
        with open("/etc/ping/hosts.yml", 'r') as stream:
            try:
                config=yaml.load(stream)
                return config
            except yaml.YAMLError as exc:
                print(exc)
                return False
    except:
        return False

def pingtargets(config):
    return ping(config['targets'])

if __name__ == '__main__':
    metrics=Gauge('ping', 'ping measurment', ['host', 'metric'])
    config = getconfig()
    start_http_server(port=int(os.getenv('ICMP_METRICS_PORT', 9346)), addr=config['ipconfig'])
    while True:
        pings = pingtargets(config) 

        for host in pings:
            if 'lat' in pings[host]:
                for metric, value in pings[host]['lat'].iteritems():
                    metrics.labels(host, metric).set(value)
            if 'loss' in pings[host]:
                metrics.labels(host, 'loss').set(pings[host]['loss'])
            if 'mtu' in pings[host]:
                metrics.labels(host, 'mtu').set(pings[host]['mtu'])

        time.sleep(int(os.getenv('ICMP_COLLECTION_INTERVAL', 60)))