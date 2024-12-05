#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Implementation of Zigbee for Domoticz plugin.
#
# This file is part of Zigbee for Domoticz plugin. https://github.com/zigbeefordomoticz/Domoticz-Zigbee
# (C) 2015-2024
#
# Initial authors: zaraki673 & pipiche38
#
# SPDX-License-Identifier:    GPL-3.0 license


from Modules.basicOutputs import handle_unknow_device
from Modules.errorCodes import DisplayStatusCode
from Modules.tools import (DeviceExist, loggingMessages,
                           zigpy_plugin_sanity_check)
from Modules.zb_tables_management import store_NwkAddr_Associated_Devices
from Z4D_decoders.z4d_decoder_helpers import \
    Network_Address_response_request_next_index


def Decode8040(self, Devices, MsgData, MsgLQI):
    """
    Decodes the 8040 message received from the network and handles associated logic.

    Args:
        Devices (dict): A dictionary of known devices.
        MsgData (str): The payload of the message to decode.
        MsgLQI (int): The Link Quality Indicator of the message.

    Returns:
        None
    """

    self.log.logging('Input', 'Debug', f'Decode8040 - payload {MsgData}')
    MsgSequenceNumber = MsgData[:2]
    MsgDataStatus = MsgData[2:4]
    MsgIEEE = MsgData[4:20]

    self.log.logging('Input', 'Debug', f'Decode8040 - Reception of Network Address response {MsgIEEE} with status {MsgDataStatus}')

    if MsgDataStatus != '00':
        return

    MsgShortAddress = MsgData[20:24]
    extendedResponse = len(MsgData) > 26
    MsgNumAssocDevices, MsgStartIndex, MsgDeviceList = None, None, None

    if extendedResponse:
        MsgNumAssocDevices = int(MsgData[24:26], 16)
        MsgStartIndex = int(MsgData[26:28], 16)
        MsgDeviceList = MsgData[28:]

    self.log.logging(
        'Input', 'Debug', 
        f'Network Address response, [{MsgSequenceNumber}] Status: {DisplayStatusCode(MsgDataStatus)} '
        f'Ieee: {MsgIEEE} NwkId: {MsgShortAddress}'
    )

    if extendedResponse:
        self.log.logging('Input', 'Debug', f'Nb Associated Devices: {MsgNumAssocDevices} Idx: {MsgStartIndex} Device List: {MsgDeviceList}')

        if MsgStartIndex + len(MsgDeviceList) // 4 != MsgNumAssocDevices:
            self.log.logging(
                'Input', 'Debug', 
                f'Decode 8040 - Receive an IEEE: {MsgIEEE} with a NwkId: {MsgShortAddress} '
                f'but would need to continue to get all associated devices'
            )
            Network_Address_response_request_next_index( self, MsgShortAddress, MsgIEEE, MsgStartIndex, len(MsgDeviceList) // 4 )

    ieee_matches = (MsgShortAddress in self.ListOfDevices) and (self.ListOfDevices[MsgShortAddress].get('IEEE') == MsgIEEE)

    if ieee_matches:
        self.log.logging( 'Input', 'Debug', f'Decode 8041 - Receive an IEEE: {MsgIEEE} with a NwkId: {MsgShortAddress}' )

        if extendedResponse:
            store_NwkAddr_Associated_Devices(self, MsgShortAddress, MsgStartIndex, MsgDeviceList)

        loggingMessages(self, '8040', MsgShortAddress, MsgIEEE, MsgLQI, MsgSequenceNumber)
        return

    if MsgIEEE in self.IEEE2NWK:
        self.log.logging( 'Input', 'Debug', f'Decode 8040 - Receive an IEEE: {MsgIEEE} with a NwkId: {MsgShortAddress}, will try to reconnect' )

        if not DeviceExist(self, Devices, MsgShortAddress, MsgIEEE) and not zigpy_plugin_sanity_check(self, MsgShortAddress):
            handle_unknow_device(self, MsgShortAddress)
            self.log.logging( 'Input', 'Debug', 'Decode 8040 - Not able to reconnect (unknown device)' )
            return

        if extendedResponse:
            store_NwkAddr_Associated_Devices(self, MsgShortAddress, MsgStartIndex, MsgDeviceList)

        loggingMessages(self, '8040', MsgShortAddress, MsgIEEE, MsgLQI, MsgSequenceNumber)
        return

    self.log.logging(
        'Input', 'Error', 
        f'Decode 8040 - Receive an IEEE: {MsgIEEE} with a NwkId: {MsgShortAddress}, '
        f'seems not known by the plugin'
    )
