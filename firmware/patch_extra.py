#!/usr/bin/env python3
"""Optional patches for SJCAM M20 V1.3.1 part0 (stock or station-patched).

    python3 patch_extra.py IN_part0.bin OUT_part0.bin [--led-off] [--reconnect] [--leds-off] [--mute] [--live720] [--autowifi]

--led-off    Wi-Fi (blue) LED never lights. The only routine that turns
             GPIO 0x5b on (0x800c9094, used for both "on" and blinking) is
             made to clear the pin instead.
--reconnect  Station mode keeps retrying. The reconnect timer and the
             post-init helper give up after 10 failed attempts
             (`slti a0, v1, 10`); the limit becomes 0x7fff.
--leds-off   Status LEDs (GPIO 0x5a/0x5c/0x5d, e.g. yellow and top blue)
             stay off after boot. The only routine that lights them
             (0x800c9154, driven by LED setting flag 0x51) clears the pins
             instead of setting them. Lights controlled by hardware (e.g. a
             charge LED wired to the charger chip) are not affected.
--mute       No UI sounds (key beeps, shutter, power on/off). The sound
             task's only call to _GxSound_Play (0x8029569c) is removed; the
             task still acknowledges each request, so callers don't wait.
--live720    Wi-Fi live-view sub-stream (RTSP) for every recording size
             that has one (2.5K .. 720p rows of the dual-stream table at
             0x8051ae44): 640x360 -> 1280x720, target 512000 B/s (~4 Mbps,
             the value the 2.5K row already uses).
--autowifi   Wi-Fi starts by itself once per boot (requires the station
             patch). The movie window's open handler already starts Wi-Fi
             when the "Wi-Fi pending" word 0x805a0fa0 is set; its two calls
             to 0x801b9318 right before that check now go through 8 new
             instructions that set the word on the first call only, then
             jump to 0x801b9318. The "done" marker is 0x805a21c8, the old
             station SSID buffer that the station patch leaves unused (BSS,
             zero at boot). The code lives in the UART "nand erase" handler
             (0x80077148), whose console table slot (0x800017dc) is pointed
             at the harmless "nand dump" handler instead.

Every patched word is checked against the stock value first.
"""

import argparse
import struct
import sys

BASE = 0x80000000

JAL_GPIO_SET = 0x0C011AC1    # jal 0x80046b04
JAL_GPIO_CLEAR = 0x0C011AB2  # jal 0x80046ac8
SLTI_10 = 0x2864000A         # slti a0, v1, 0xa
SLTI_MAX = 0x28647FFF        # slti a0, v1, 0x7fff

LED_OFF = [(0x800C90A4, JAL_GPIO_SET, JAL_GPIO_CLEAR)]
STATUS_LEDS_OFF = [(a, JAL_GPIO_SET, JAL_GPIO_CLEAR) for a in (
    0x800C9164, 0x800C916C, 0x800C91D4, 0x800C91DC, 0x800C91E4, 0x800C9200, 0x800C9210, 0x800C923C)]
JAL_GXSOUND_PLAY = 0x0C0A54BF  # jal 0x802952fc
MUTE = [(0x8029569C, JAL_GXSOUND_PLAY, 0x00000000)]
# --autowifi
CAVE = 0x80077148
CAVE_STOCK = [0x27BDFFE8, 0x24040001, 0xAFBE0010, 0x24050001,
              0xAFBF0014, 0x0C01AF2C, 0x03A0F021, 0x03C0E821]
CAVE_CODE = [
    0x3C08805A,  # lui   t0, 0x805a
    0x8D0921C8,  # lw    t1, 0x21c8(t0)    once-per-boot marker
    0x15200003,  # bnez  t1, +3 (to j)
    0x240A0001,  # addiu t2, zero, 1       (delay slot)
    0xAD0A21C8,  # sw    t2, 0x21c8(t0)
    0xAD0A0FA0,  # sw    t2, 0x0fa0(t0)    "Wi-Fi pending" -> movie open starts Wi-Fi
    0x0806E4C6,  # j     0x801b9318
    0x00000000,  # nop
]
JAL_HELPER = 0x0C06E4C6  # jal 0x801b9318
JAL_CAVE = 0x0C01DC52    # jal 0x80077148
AUTOWIFI_HOOKS = [(0x801B9980, JAL_HELPER, JAL_CAVE), (0x801B9A7C, JAL_HELPER, JAL_CAVE)]
CONSOLE_ERASE_SLOT = (0x800017DC, CAVE, 0x800770F0)  # nand erase -> nand dump handler
STATION_MARK = (0x801D8EB8, 0x92020E30)  # station patch: lbu v0, 0xe30(s0)

RECONNECT = [(0x801C8214, SLTI_10, SLTI_MAX), (0x801C7F24, SLTI_10, SLTI_MAX)]

# dual-stream table: row r main width at 0x8051ae44 + r*0x34,
# sub-stream width/height/fps/TBR at +0x18/+0x1c/+0x20/+0x24
TABLE2 = 0x8051AE44
ROW = 0x34
LIVE_ROWS = range(1, 11)  # 2560x1440@30 .. 1280x720@30 (row 11 is 640x480@240)
LIVE_W, LIVE_H, LIVE_TBR = 1280, 720, 512000


def _word(img, addr):
    return struct.unpack_from("<I", img, addr - BASE)[0]


def _put(img, addr, old, new, what):
    cur = _word(img, addr)
    if cur == new:
        return 0
    if cur != old:
        raise ValueError("0x%08x (%s): expected %08x, found %08x - wrong firmware?" % (addr, what, old, cur))
    struct.pack_into("<I", img, addr - BASE, new)
    return 1


def apply(img, led_off=False, reconnect=False, live720=False, leds_off=False, mute=False,
          autowifi=False):
    n = 0
    if autowifi:
        addr, want = STATION_MARK
        if _word(img, addr) != want:
            raise ValueError("--autowifi needs the station patch (patch_station.py) applied first")
        for k, (old, new) in enumerate(zip(CAVE_STOCK, CAVE_CODE)):
            n += _put(img, CAVE + 4 * k, old, new, "code cave")
        for a, o, w in AUTOWIFI_HOOKS + [CONSOLE_ERASE_SLOT]:
            n += _put(img, a, o, w, "autowifi hook")
    if leds_off:
        for a, o, w in STATUS_LEDS_OFF:
            n += _put(img, a, o, w, "status LED on")
    if mute:
        for a, o, w in MUTE:
            n += _put(img, a, o, w, "UI sound play")
    if led_off:
        for a, o, w in LED_OFF:
            n += _put(img, a, o, w, "wifi LED on")
    if reconnect:
        for a, o, w in RECONNECT:
            n += _put(img, a, o, w, "reconnect limit")
    if live720:
        for r in LIVE_ROWS:
            a = TABLE2 + r * ROW
            sw, sh, sf, st = struct.unpack_from("<4I", img, a + 0x18 - BASE)
            if (sw, sh) not in ((640, 360), (LIVE_W, LIVE_H)) or sf != 30 or st not in (204800, 512000):
                raise ValueError("table row %d at 0x%08x unexpected: %dx%d@%d %d" % (r, a, sw, sh, sf, st))
            n += _put(img, a + 0x18, sw, LIVE_W, "sub width")
            n += _put(img, a + 0x1C, sh, LIVE_H, "sub height")
            n += _put(img, a + 0x24, st, LIVE_TBR, "sub bitrate")
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("part0")
    ap.add_argument("out")
    ap.add_argument("--led-off", action="store_true")
    ap.add_argument("--reconnect", action="store_true")
    ap.add_argument("--live720", action="store_true")
    ap.add_argument("--leds-off", action="store_true")
    ap.add_argument("--mute", action="store_true")
    ap.add_argument("--autowifi", action="store_true")
    a = ap.parse_args(argv)
    if not (a.led_off or a.reconnect or a.live720 or a.leds_off or a.mute or a.autowifi):
        ap.error("choose at least one patch")
    with open(a.part0, "rb") as f:
        img = bytearray(f.read())
    n = apply(img, a.led_off, a.reconnect, a.live720, a.leds_off, a.mute, a.autowifi)
    with open(a.out, "wb") as f:
        f.write(img)
    print("patched %d words -> %s" % (n, a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
