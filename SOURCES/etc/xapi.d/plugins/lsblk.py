#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import re

import XenAPIPlugin

from xcpngutils import run_command, error_wrapped

LSBLK_COLUMNS = "NAME,KNAME,PKNAME,SIZE,TYPE,RO,MOUNTPOINT"

def _run(cmd):
    """Small helper to run a [cmd, ...] and get its decoded and stripped output."""
    return run_command(cmd)["stdout"].decode("utf-8").strip()

def get_byid_paths_from_dev(devname):
    """Return all generated links to a /dev/<devname> in /dev/disk/by-id/."""
    return [
        "/dev/" + path
        for path in _run(["udevadm", "info", "-q", "symlink", "/dev/" + devname]).split()
        if path.startswith("disk/by-id/")
    ]

@error_wrapped
def list_block_devices(session, args):
    results = []
    blockdevices = {}
    for output in _run(["lsblk", "-P", "-b", "-o", LSBLK_COLUMNS]).splitlines():
        device = {
            key.lower(): value.strip('"')
            for key, value in re.findall(r'(\S+)=(".*?"|\S+)', output)
        }
        device["device-id-paths"] = get_byid_paths_from_dev(device["kname"])
        if device["pkname"]:
            blockdevices[device["pkname"]].setdefault("children", []).append(device)
        else:
            results.append(device)
        blockdevices[device["kname"]] = device
    return json.dumps({'blockdevices': results})

if __name__ == "__main__":
    XenAPIPlugin.dispatch({"list_block_devices": list_block_devices})
