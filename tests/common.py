"""Common."""

from __future__ import annotations

SALT_SENSOR = {
    "createdDate": 1664059201347,
    "userType": "EU",
    "deviceType": "SSS1",
    "addressId": "address1",
    "status": "ACTIVE",
    "pname": "Salt Level Sensor",
    "order": 1,
    "email": "**REDACTED**",
    "homeFlag": True,
    "deviceId": "**REDACTED**",
    "parentGroup": "Home",
    "userId": "**REDACTED**",
    "productInfo": {
        "maker": "Pentair",
        "survey": {
            "water_products_you_own": [
                "Whole Home Filter",
                "Reverse Osmosis System",
                "Refrigerator Filter",
            ],
            "water_softener_brand": "Other",
            "water_softener_type": "Side-by-Side",
        },
        "model": "SSS",
        "visible": True,
        "nickName": "Salt Level Sensor",
        "order": 1,
    },
    "arn": "**REDACTED**",
    "parentGroupWithoutMlt": "Home",
    "jobId": "",
    "jobStatus": "",
    "currentFWVersion": "1.0.2",
    "latestFWVersion": "",
    "isRm": False,
    "online": False,
    "fields": {
        "salt_level": "3",
        "average_salt_usage_per_day": "3.51",
        "low_battery_alert": "0",
        "sensor_fault": "0",
        "calibration_status_alert": "0",
        "salt_level_alert": "3",
        "battery_level": "0",
    },
    "lastReport": 1688970159228,
    "deb_off_stat": False,
    "deb_off_time": 1688970166106,
}

INTELLIFLO_SENSOR = {
    "createdDate": 1713376330461,
    "userType": "EU",
    "deviceType": "IF31",
    "addressId": "address1",
    "status": "ACTIVE",
    "pname": "IntelliFlo/Pro3 VSF",
    "order": 1,
    "email": "**REDACTED**",
    "homeFlag": True,
    "deviceId": "**REDACTED**",
    "parentGroup": "Pool & Spa",
    "userId": "**REDACTED**",
    "productInfo": {
        "visible": True,
        "nickName": "IntelliFlo/Pro3 VSF",
        "poolId": None,
        "maker": "Pentair",
        "survey": None,
        "model": "IntelliFlo/Pro3 VSF",
        "order": 1,
    },
    "arn": "**REDACTED**",
    "parentGroupWithoutMlt": "Pool & Spa",
    "jobId": "",
    "jobStatus": "",
    "currentFWVersion": "1.0",
    "latestFWVersion": "",
    "isRm": True,
    "online": True,
    "fields": {
        "s1": "240417162300",  # Device time
        "s3": "1",  # Drive type
        "s5": "1",  # Relay installed
        "s6": "1C5A0840C400",  # Wifi mac address
        "s7": "1.05",  # Drive software version
        "s8": "0.98",  # IoT version
        "s9": "1.02.000",  # Controller version
        "s10": "none",  # UDM application software version
        "s11": "16",  # Security key
        "s12": "Rev:B SN: 32MHz",  # Checksum
        "s13": "-69",  # RSSI (dBm)
        "s14": "1",  # Active program number
        "s15": "2",  # Active reference
        "s16": "380",  # Active value
        "s17": "461",  # Current pressure (psi)
        "s18": "183",  # Current power (watts)
        "s19": "432",  # Current motor speed (%)
        "s20": "0",  # Alarm condition
        "s21": "0",  # Relay 1 status
        "s22": "0",  # Relay 2 status
        "s23": "Poseidon23",  # SSID
        "s24": "0",  # Digital inputs
        "s25": "1",  # Pump enabled status
        "s26": "380",  # Current estimated flow (gallons per minute)
        "s27": "0",  # Status word
        "s28": "337",  # Remaining time
        "s29": "0",  # Automation active
        "s30": "99",  # Active program relay 1
        "s31": "99",  # Active program relay 2
        "s32": "0",  # Relay 1 remaining time
        "s33": "0",  # Relay 2 remaining time
        "s34": "11725",
        "s35": "11735",
        "s36": "10614",
        "s37": "10546",
        "s38": "213",
        "s39": "183",
        "s40": "24137",
        "s41": "89",
        "s48": "2",  # Wifi level
        "p2": 99,  # Last active program
    },
    "lastReport": 1713386432783,
    "deb_off_stat": True,
    "deb_off_time": 1691197252466,
}
