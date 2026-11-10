#!/usr/bin/env python3
"""Make SJCAM M20 V1.3.1 join an existing Wi-Fi network (station mode).

Works on the decompressed part0 (see ntkfw.py unpack). The SSID and
passphrase are written into the image, so keep the output private and do
not commit it.

What the stock code does (SetupExe_OnWifiStart, 0x801d8d70):
    mode = SysGetFlag(0x8b)          # never set by the stock UI -> 0 (AP)
    if mode == 1 and ssid[0] and pass[0]:   # buffers 0x805a21c8/0x805a21e8,
        UINet_SetSSID(ssid); UINet_SetPASSPHRASE(pass)  # never filled
    UINet_WifiInit(mode, ...)
Only the UART debug command "wifi mode 1" ever sets the flag.

Patch:
    * every SysGetFlag(0x8b) in Wi-Fi start/stop returns 1 instead
      (the flag itself is untouched, so nothing persists after reflashing)
    * the post-init check of the console mode global also returns 1, so the
      station reconnect helper runs as it does after "wifi mode 1"
    * the SSID/passphrase pointers point at a debug-message string block
      (0x803b0e2c..0x803b0eb7, referenced only by this function), which now
      holds the SSID and passphrase; the printf calls that used those strings
      are removed
"""

import argparse
import os
import struct
import sys

BASE = 0x80000000
LI_V0_1 = 0x24020001  # addiu $v0, $zero, 1
NOP = 0x00000000
JAL_GETFLAG = 0x0C071334  # jal 0x801c4cd0  (SysGetFlag)
JAL_GETMODE = 0x0C071E42  # jal 0x801c7908  (console wifi mode getter)
JAL_PRINTF = 0x0C004A60   # jal 0x80012980  (debug printf)

STR_BLOCK = (0x803B0E2C, 0x803B0EB8)  # end exclusive
SSID_ADDR = 0x803B0E30
PASS_ADDR = 0x803B0E58
SSID_MAX = PASS_ADDR - SSID_ADDR - 1        # 39, Wi-Fi allows 32
PASS_MAX = STR_BLOCK[1] - PASS_ADDR - 1     # 95, WPA2 allows 63

# (address, expected original word, new word, description)
CODE_PATCHES = [
    (0x801D8D10, JAL_GETFLAG, LI_V0_1, "wifi stop: mode = 1"),
    (0x801D8D9C, JAL_GETFLAG, LI_V0_1, "start: mode for log = 1"),
    (0x801D8DAC, JAL_PRINTF, NOP, "start: drop 'Network mod' printf"),
    (0x801D8DB4, JAL_GETFLAG, LI_V0_1, "start: take non-AP branch"),
    (0x801D8DD4, JAL_GETFLAG, LI_V0_1, "start: UINet_WifiInit(mode=1)"),
    (0x801D8E24, JAL_GETMODE, LI_V0_1, "start: run station reconnect helper"),
    (0x801D8E38, JAL_GETFLAG, LI_V0_1, "start: mode for log = 1"),
    (0x801D8E4C, JAL_PRINTF, NOP, "start: drop 'BackgroundWiFiOn' printf"),
    (0x801D8E88, JAL_GETFLAG, LI_V0_1, "start: mode == 1 -> station"),
    (0x801D8EA4, JAL_PRINTF, NOP, "start: drop 'Neither AP nor Station' printf"),
    (0x801D8EB4, 0x3C10805A, 0x3C10803B, "ssid base: lui s0, 0x803b"),
    (0x801D8EB8, 0x920221C8, 0x92020E30, "ssid[0] check -> new ssid"),
    (0x801D8EC4, 0x3C11805A, 0x3C11803B, "pass base: lui s1, 0x803b"),
    (0x801D8EC8, 0x922221E8, 0x92220E58, "pass[0] check -> new pass"),
    (0x801D8EDC, JAL_PRINTF, NOP, "start: drop 'SSID or passphrase error' printf"),
    (0x801D8F00, 0x260421C8, 0x26040E30, "strlen(ssid)"),
    (0x801D8F0C, 0x260421C8, 0x26040E30, "UINet_SetSSID(ssid)"),
    (0x801D8F1C, 0x262421E8, 0x26240E58, "strlen(pass)"),
    (0x801D8F28, 0x262421E8, 0x26240E58, "UINet_SetPASSPHRASE(pass)"),
]

EXPECTED_STR_BLOCK_START = b"Network mod:%d \r\n\0"


def patch(raw, ssid, passphrase):
    img = bytearray(raw)
    for addr, old, new, desc in CODE_PATCHES:
        off = addr - BASE
        cur = struct.unpack_from("<I", img, off)[0]
        if cur != old:
            raise ValueError("0x%08x: expected %08x, found %08x (%s) - wrong firmware?" %
                             (addr, old, cur, desc))
        struct.pack_into("<I", img, off, new)
    s0, s1 = STR_BLOCK[0] - BASE, STR_BLOCK[1] - BASE
    if bytes(img[s0:s0 + len(EXPECTED_STR_BLOCK_START)]) != EXPECTED_STR_BLOCK_START:
        raise ValueError("string block does not match V1.3.1 - wrong firmware?")
    img[s0:s1] = b"\0" * (s1 - s0)
    img[SSID_ADDR - BASE:SSID_ADDR - BASE + len(ssid)] = ssid
    img[PASS_ADDR - BASE:PASS_ADDR - BASE + len(passphrase)] = passphrase
    return bytes(img)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("part0", help="decompressed stock part0.bin")
    ap.add_argument("out", help="patched part0 output")
    ap.add_argument("--ssid", default=os.environ.get("M20_WIFI_SSID"),
                    help="default: environment variable M20_WIFI_SSID")
    ap.add_argument("--passphrase", default=os.environ.get("M20_WIFI_PASS"),
                    help="default: environment variable M20_WIFI_PASS (keeps it out of shell history)")
    args = ap.parse_args(argv)
    if not args.ssid or not args.passphrase:
        ap.error("give --ssid/--passphrase or set M20_WIFI_SSID/M20_WIFI_PASS")

    ssid = args.ssid.encode("utf-8")
    pw = args.passphrase.encode("utf-8")
    if not 1 <= len(ssid) <= min(32, SSID_MAX):
        ap.error("SSID must be 1..32 bytes")
    if not 8 <= len(pw) <= min(63, PASS_MAX):
        ap.error("WPA2 passphrase must be 8..63 characters")

    with open(args.part0, "rb") as f:
        raw = f.read()
    out = patch(raw, ssid, pw)
    with open(args.out, "wb") as f:
        f.write(out)
    changed = sum(1 for a, b in zip(raw, out) if a != b)
    print("patched %d code words + string block, %d bytes changed -> %s" %
          (len(CODE_PATCHES), changed, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
