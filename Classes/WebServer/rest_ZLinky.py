import json

import Domoticz
from Classes.WebServer.headerResponse import (prepResponseMessage,
                                              setupHeadersResponse)
from Modules.tools import get_device_nickname
from Modules.zlinky import ZLINKY_MODE

ZLINKY_PARAMETERS = {
    0: ( 
        "ADC0", "BASE", "OPTARIF", "ISOUSC", "IMAX", "PTEC", "DEMAIN", "HHPHC", "PEJP", "ADPS", 
        ),
    2: ( 
        "ADC0", "BASE", "OPTARIF", "ISOUSC", "IMAX",
        "IMAX1", "IMAX2", "IMAX3", "PMAX", "PTEC", "DEMAIN", "HHPHC", "PPOT", "PEJP", "ADPS", "ADIR1", "ADIR2", "ADIR3" 
    ),
    
    1: (
        "ADSC", "NGTF", "LTARF", "NTARF", "DATE", "EAST", "EASF01", "EASF02", "EASF03", "EASF04", "EASF05", 
        "EASF06", "EASF07", "EASF08", "EASF09", "EASF10", "EASD01", "EASD02", "EASD03", "EASD04", "URMS1",
        "PREF", "STGE", "PCOUP",
        "MSG1", "MSG2", "PRM", "STGE", "DPM1", "FPM1", "DPM2", "FPM2", "DPM3", "FPM3", "RELAIS", "NJOURF", "NJOURF+1", "PJOURF+1", "PPOINTE1",
    ),
    
    3: (
        "ADSC", "NGTF", "LTARF", "NTARF", "DATE", "EAST", "EASF01", "EASF02", "EASF03", "EASF04", "EASF05", 
        "EASF06", "EASF07", "EASF08", "EASF09", "EASF10", "EASD01", "EASD02", "EASD03", "EASD04", "URMS1",
        "URMS2", "URMS3", "PREF", "STGE", "PCOUP",
        "MSG1", "MSG2", "PRM", "STGE", "DPM1", "FPM1", "DPM2", "FPM2", "DPM3", "FPM3", "RELAIS", "NJOURF", "NJOURF+1", "PJOURF+1", "PPOINTE1",
        ),

    5: (
        "ADSC", "NGTF", "LTARF", "NTARF", "DATE", "EAST", "EASF01", "EASF02", "EASF03", "EASF04", "EASF05", 
        "EASF06", "EASF07", "EASF08", "EASF09", "EASF10", "EASD01", "EASD02", "EASD03", "EASD04", "EAIT", "URMS1",
        "PREF", "STGE", "PCOUP", "SINSTI", "SMAXIN", "SMAXIN-1", "CCAIN", "CCAIN-1", "SMAXN-1", "SMAXN2-1", "SMAXN3-1", 
        "MSG1", "MSG2", "PRM", "STGE", "DPM1", "FPM1", "DPM2", "FPM2", "DPM3", "FPM3", "RELAIS", "NJOURF", "NJOURF+1", "PJOURF+1", "PPOINTE1",
    ),

    7: (
        "ADSC", "NGTF", "LTARF", "NTARF", "DATE", "EAST", "EASF01", "EASF02", "EASF03", "EASF04", "EASF05", 
        "EASF06", "EASF07", "EASF08", "EASF09", "EASF10", "EASD01", "EASD02", "EASD03", "EASD04", "EAIT", "URMS1",
        "URMS2", "URMS3", "PREF", "STGE", "PCOUP",
        "SINSTI", "SMAXIN", "SMAXIN-1", "CCAIN", "CCAIN-1", "SMAXN-1", "SMAXN2-1", "SMAXN3-1", 
        "MSG1", "MSG2", "PRM", "STGE", "DPM1", "FPM1", "DPM2", "FPM2", "DPM3", "FPM3", "RELAIS", "NJOURF", "NJOURF+1", "PJOURF+1", "PPOINTE1",
        ),
    
}





def rest_zlinky(self, verb, data, parameters): 

    _response = prepResponseMessage(self, setupHeadersResponse())
    _response["Data"] = None
    
    # find if we have a ZLinky
    zlinky = []
    
    for x in self.ListOfDevices:
        if 'ZLinky' not in self.ListOfDevices[ x ]:
            continue
        if "PROTOCOL Linky" not in self.ListOfDevices[ x ]['ZLinky']:
            return
        linky_mode = self.ListOfDevices[ x ]["ZLinky"]["PROTOCOL Linky"]
        device = {
            'Nwkid': x,
            'ZDeviceName': get_device_nickname( self, NwkId=x),
            "PROTOCOL Linky": linky_mode,
            'Parameters': []
        }
        for y in ZLINKY_PARAMETERS[ linky_mode ]:
            if y not in self.ListOfDevices[ x ]["ZLinky"]:
                device["Parameters"].append( { y: None } )
                continue
    
            attr_value = self.ListOfDevices[ x ]["ZLinky"][ y ]
            device["Parameters"].append( { y: attr_value } )
            
        zlinky.append( device )
        
    if verb == "GET" and len(parameters) == 0:
        if len(self.ControllerData) == 0:
            _response["Data"] = json.dumps(fake_zlinky_histo_mono(), sort_keys=True)
            return _response

        _response["Data"] = json.dumps(zlinky, sort_keys=True)

    return _response


def fake_zlinky_histo_mono():
    
    return [
        {
            "Nwkid": "5f21", 
            "PROTOCOL Linky": 0,
            "Parameters": [
                {"PEJP": 0}, 
                {"DEMAIN": ""}, 
                {"EASF01": 454596}, 
                
                {"OPTARIF": "BASE"}, 
                {"HHPHC": 0}, 
                {"PPOT": 0}, 
                {"ADPS": "0"}, 
                {"ADIR3": "0"}, 
                {"ADIR2": "0"}, 
                {"ADIR1": "0"}
                ]
            }
        ]
