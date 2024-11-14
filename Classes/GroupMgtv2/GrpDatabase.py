# !/usr/bin/env python3
# coding: utf-8 -*-
#
# Author: pipiche38
#

"""
Methodes which manipulate the Groups Data Structure
- ListOfGroups is the Data structure supporting Groups
  ListOfGroups[group id]['Name']            - Group Name as it will be created in Domoticz
  ListOfGroups[group id]['Devices']         - List of Devices associed to this group on Zigate
  ListOfGroups[group id]['Tradfri Remote']  - Manage the Tradfri Remote
'WidgetStyle'
'Cluster'
'Tradfri Remote'
"Device Addr"]

"""
import json
import os
import time

from Modules.domoticzAbstractLayer import (domoticz_error_api,
                                           domoticz_log_api,
                                           domoticz_status_api, getConfigItem,
                                           setConfigItem)
from Modules.tools import is_domoticz_db_available


def write_groups_list(self):
    """
    write GroupsList into Disk
    """
    self.logging("Debug", "Dumping: %s" % self.GroupListFileName)

    self.logging("Status", f"+ Saving Group List into {self.GroupListFileName}")
    with open(self.GroupListFileName, "wt") as handle:
        json.dump(self.ListOfGroups, handle, sort_keys=True, indent=2)

    if self.pluginconf.pluginConf["useDomoticzDatabase"] or self.pluginconf.pluginConf["storeDomoticzDatabase"]:
        self.logging("Status", "+ Saving Group List into Domoticz")
        setConfigItem(Key="ListOfGroups", Attribute="b64encoded", Value={"TimeStamp": time.time(), "b64encoded": self.ListOfGroups})


def load_groups_list_from_json(self):
    """
    Load GroupsList into memory
    """
    if self.GroupListFileName is None:
        return

    # Load from Domoticz
    if self.pluginconf.pluginConf["useDomoticzDatabase"] or self.pluginconf.pluginConf["storeDomoticzDatabase"]:
        _domoticz_grouplist = getConfigItem(Key="ListOfGroups", Attribute="b64encoded")
        dz_timestamp = _domoticz_grouplist.get("TimeStamp",0)
        _domoticz_grouplist = _domoticz_grouplist.get("b64encoded", {})
        self.logging( "Debug", "Groups data loaded where saved on %s"% (time.strftime("%A, %Y-%m-%d %H:%M:%S", time.localtime(dz_timestamp))),)

    # Load from Json
    txt_timestamp = 0
    if os.path.isfile(self.GroupListFileName):
        _json_grouplist = {}
        with open(self.GroupListFileName, "rt") as handle:
            _json_grouplist = json.load(handle)
            txt_timestamp = os.path.getmtime(self.GroupListFileName)
            self.logging( "Debug", "%s timestamp is %s" % (self.GroupListFileName, txt_timestamp))
     
    # Check Loads
    if _domoticz_grouplist and _json_grouplist :
        self.logging( "Debug", "==> Sanity check : GroupList Loaded. %s entries from Domoticz, %s from Json, result: %s" % (
            len(_domoticz_grouplist), len(_json_grouplist), _domoticz_grouplist == _json_grouplist ))
    
    if self.pluginconf.pluginConf["useDomoticzDatabase"] and dz_timestamp > txt_timestamp:
        # We should load the Domoticz file
        self.ListOfGroups = _domoticz_grouplist
        loaded_from = "Domoticz"
    else:
        # We should use Json
        loaded_from = self.GroupListFileName
        self.ListOfGroups = _json_grouplist

    self.logging("Status", "Z4D loads %s config entries from %s" % (len(self.ListOfGroups), loaded_from))


def build_group_list_from_list_of_devices(self):
    """ "
    Build the ListOfGroups from the ListOfDevices
    """
    for NwkId in self.ListOfDevices:
        if "GroupMemberShip" not in self.ListOfDevices[NwkId]:
            continue
        for Ep in self.ListOfDevices[NwkId]["GroupMemberShip"]:
            for GrpId in self.ListOfDevices[NwkId]["GroupMemberShip"][Ep]:
                if self.ListOfDevices[NwkId]["GroupMemberShip"][Ep][GrpId]["Status"] == "OK":
                    ieee = self.ListOfDevices[NwkId]["IEEE"]
                    device = [NwkId, Ep, ieee]
                    add_device_to_group(self, device, GrpId)


def update_due_to_nwk_id_change(self, OldNwkId, NewNwkId):
    """
    Short Id of the device has changed, we need to update ListOfGroups accordingly
    """

    # self.logging( 'Debug', "------> update_due_to_nwk_id_change From: %s to %s" %(OldNwkId, NewNwkId))
    for GrpId in list(self.ListOfGroups.keys()):
        for device in list(self.ListOfGroups[GrpId]["Devices"]):
            if device[0] != OldNwkId:
                continue
            # We have to update the NwkId ( update + add )
            newdevice = [NewNwkId, device[1], device[2]]
            self.ListOfGroups[GrpId]["Devices"].remove(device)
            self.ListOfGroups[GrpId]["Devices"].append(newdevice)

        # Check if there is not an Ikea Tradfri Remote to be migrated
        Ikea_update_due_to_nwk_id_change(self, GrpId, OldNwkId, NewNwkId)


def Ikea_update_due_to_nwk_id_change(self, GrpId, OldNwkId, NewNwkId):

    if (
        "Tradfri Remote" in self.ListOfGroups[GrpId]
        and self.ListOfGroups[GrpId]["Tradfri Remote"]["Device Addr"] == OldNwkId
    ):
        self.ListOfGroups[GrpId]["Tradfri Remote"]["Device Addr"] = NewNwkId


def checkNwkIdAndUpdateIfAny(self, NwkId, ieee):
    """
    will return NwkId or an updated one in case of change of ShortId.
    will return None is the NwkId doesn't exist anymore
    """
    if NwkId is self.ListOfDevices:
        return NwkId

    # NwkId not found, let's check if the Ieee is stil there
    if ieee in self.IEEE2NWK:
        NewNwkId = self.IEEE2NWK[ieee]
        update_due_to_nwk_id_change(self, NwkId, NewNwkId)
        return NewNwkId

    # Looks like this Device do not exist. We should then update All Groups where the devices belngs
    remove_nwkid_from_all_groups(self, NwkId)
    return None


def check_if_group_empty(self, GrpId):

    return len(self.ListOfGroups[GrpId]["Devices"]) == 0 and "Tradfri Remote" not in self.ListOfGroups[GrpId]


def create_group(self, GrpId, GrpName):

    if GrpId not in self.ListOfGroups:
        self.ListOfGroups[GrpId] = {}
        self.ListOfGroups[GrpId]["Name"] = GrpName
        self.ListOfGroups[GrpId]["Devices"] = []


def remove_group(self, GrpId):
    if GrpId not in self.ListOfGroups:
        return
    del self.ListOfGroups[GrpId]


def remove_nwkid_from_all_groups(self, NwkIdToRemove):

    for GrpId in list(self.ListOfGroups.keys()):
        for NwkId, Ep, Ieee in list(self.ListOfGroups[GrpId]["Devices"]):
            self.logging(
                "Debug", "remove_nwkid_from_all_groups Looking for NwkId: %s found %s" % (NwkIdToRemove, NwkId)
            )
            if NwkId == NwkIdToRemove:
                self.logging(
                    "Debug", "remove_nwkid_from_all_groups Request removal of [ %s, %s, %s] " % (NwkId, Ep, Ieee)
                )
                remove_device_from_group(self, [NwkId, Ep, Ieee], GrpId)


def add_device_to_group(self, device, GrpId):
    """
    add a device ( NwkId, ep, ieee) to a group
    """
    if GrpId not in self.ListOfGroups:
        self.ListOfGroups[GrpId] = {}
        self.ListOfGroups[GrpId]["Name"] = ""
        self.ListOfGroups[GrpId]["Devices"] = []

    if device not in self.ListOfGroups[GrpId]["Devices"]:
        self.ListOfGroups[GrpId]["Devices"].append(device)


def remove_device_from_group(self, device, GrpId):
    """
    remove a device from a group
    """
    if GrpId not in self.ListOfGroups:
        return
    if device not in self.ListOfGroups[GrpId]["Devices"]:
        return

    self.ListOfGroups[GrpId]["Devices"].remove(device)
    if len(self.ListOfGroups[GrpId]["Devices"]) == 0:
        # No devices attached to that Group.
        remove_group(self, GrpId)


def device_list_for_group(self, GrpId):
    """
    return a list of tuples ( devices, ep, ieee) for a particular group
    """

    if GrpId not in self.ListOfGroups:
        return []
    return self.ListOfGroups[GrpId]["Devices"]
