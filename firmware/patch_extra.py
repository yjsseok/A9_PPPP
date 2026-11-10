#!/usr/bin/env python3
"""Optional patches for SJCAM M20 V1.3.1 part0 (stock or station-patched).

    python3 patch_extra.py IN_part0.bin OUT_part0.bin [--led-off] [--reconnect] [--leds-off] [--mute] [--live720] [--live15] [--autowifi] [--apfile] [--defaults]

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
--live15     Live-view sub-stream at 15 fps instead of 30 (same rows as
             --live720): half the encoding work for live view, less heat.
--apfile     SD-card switch for emergencies (requires the station patch):
             if A:\\M20AP.TXT exists when Wi-Fi starts, the camera behaves
             like stock (creates its own access point); otherwise it joins
             the home network. The station patch's seven "mode = 1"
             constants in the Wi-Fi start/stop code become calls to a small
             get_mode() that checks the file once per boot with
             FileSys_GetAttrib (0x800eab88; returns 0 if the file exists)
             and caches the answer in 0x805a21cc (spare station buffer).
             The code lives in the UART "dsysdma" handler (0x800cd144,
             230 instructions, referenced only by console slot
             0x80000b10, which is pointed at the empty function 0x800c901c).
--defaults   Factory defaults used after a firmware update or reset
             (SysResetFlag 0x801c5188): movie size flag 0x1a = 0 (2.5K),
             auto power off flag 0x3a = 0 (off), car mode flag 0xa1 = 1
             (start recording when the movie screen first opens and when
             external power is connected).

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

# --apfile
CAVE2 = 0x800CD144
CAVE2_STOCK = [0x27BDFD70, 0x240600FC, 0xAFBE0288, 0x03A0F021, 0xAFB1026C, 0x27D10018,
               0x02202021, 0xAFB40278, 0xAFB20270, 0x00002821, 0x3C14800D, 0x3C12800D,
               0xAFBF028C, 0xAFB70284, 0xAFB60280, 0xAFB5027C, 0xAFB30274, 0x0C007DA8,
               0xAFB00268, 0x2647D054, 0x268CD048, 0x3C17800D, 0x95930004, 0x26F6D060]
AP_PATH_ADDR = CAVE2 + 20 * 4
GET_MODE = [
    0x3C08805A,  # 0  lui   t0, 0x805a
    0x8D0221CC,  # 1  lw    v0, 0x21cc(t0)     cached: 1 station, 2 AP, 0 unknown
    0x1440000E,  # 2  bnez  v0, 17
    0x00000000,  # 3  nop
    0x27BDFFE0,  # 4  addiu sp, sp, -0x20
    0xAFBF001C,  # 5  sw    ra, 0x1c(sp)
    0x3C040000 | (((AP_PATH_ADDR + 0x8000) >> 16) & 0xFFFF),  # 6  lui a0, %hi(path) (addiu sign-extends)
    0x24840000 | (AP_PATH_ADDR & 0xFFFF),         # 7  addiu a0, a0, lo(path)
    0x0C03AAE2,  # 8  jal   FileSys_GetAttrib (0x800eab88)
    0x27A50010,  # 9  addiu a1, sp, 0x10       (delay slot) attribute byte
    0x8FBF001C,  # 10 lw    ra, 0x1c(sp)
    0x27BD0020,  # 11 addiu sp, sp, 0x20
    0x2C420001,  # 12 sltiu v0, v0, 1          1 if the file exists
    0x24420001,  # 13 addiu v0, v0, 1          2 = AP, 1 = station
    0x3C08805A,  # 14 lui   t0, 0x805a
    0xAD0221CC,  # 15 sw    v0, 0x21cc(t0)
    0x00000000,  # 16 nop
    0x24090002,  # 17 addiu t1, zero, 2
    0x03E00008,  # 18 jr    ra
    0x01221023,  # 19 subu  v0, t1, v0         (delay slot) station 1, AP 0
]
AP_PATH = b"A:\\M20AP.TXT\0\0\0\0"  # 12 chars + NULs = 16 bytes
assert len(AP_PATH) == 16
JAL_GET_MODE = 0x0C000000 | ((CAVE2 & 0x0FFFFFFF) >> 2)
LI_V0_1 = 0x24020001
MODE_SITES = [0x801D8D10, 0x801D8D9C, 0x801D8DB4, 0x801D8DD4, 0x801D8E24, 0x801D8E38, 0x801D8E88]
CONSOLE_DSYSDMA_SLOT = (0x80000B10, CAVE2, 0x800C901C)

# --defaults (SysResetFlag 0x801c5188; v1 = 1 throughout)
DEFAULTS = [
    (0x801C51A8, 0xAC44010C, 0xAC40010C, "flag 0x1a movie size 2 -> 0 (2.5K)"),
    (0x801C5264, 0xAC43018C, 0xAC40018C, "flag 0x3a auto power off 1 -> 0"),
    (0x801C52C8, 0xAC400328, 0xAC430328, "flag 0xa1 car mode 0 -> 1"),
]

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
          autowifi=False, apfile=False, defaults=False, live15=False):
    n = 0
    if apfile:
        addr, want = STATION_MARK
        if _word(img, addr) != want:
            raise ValueError("--apfile needs the station patch (patch_station.py) applied first")
        for k, old in enumerate(CAVE2_STOCK):
            a = CAVE2 + 4 * k
            if k < len(GET_MODE):
                new = GET_MODE[k]
            else:
                new = struct.unpack_from("<I", AP_PATH, 4 * (k - len(GET_MODE)))[0]
            n += _put(img, a, old, new, "code cave 2")
        for a in MODE_SITES:
            n += _put(img, a, LI_V0_1, JAL_GET_MODE, "station mode constant")
        a, o, w = CONSOLE_DSYSDMA_SLOT
        n += _put(img, a, o, w, "console dsysdma slot")
    if defaults:
        for a, o, w, what in DEFAULTS:
            n += _put(img, a, o, w, what)
    if live15:
        for r in LIVE_ROWS:
            a = TABLE2 + r * ROW + 0x20
            n += _put(img, a, 30, 15, "sub fps")
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
    ap.add_argument("--apfile", action="store_true")
    ap.add_argument("--defaults", action="store_true")
    ap.add_argument("--live15", action="store_true")
    a = ap.parse_args(argv)
    if not (a.led_off or a.reconnect or a.live720 or a.leds_off or a.mute or a.autowifi or a.apfile
            or a.defaults or a.live15):
        ap.error("choose at least one patch")
    with open(a.part0, "rb") as f:
        img = bytearray(f.read())
    n = apply(img, a.led_off, a.reconnect, a.live720, a.leds_off, a.mute, a.autowifi,
              a.apfile, a.defaults, a.live15)
    with open(a.out, "wb") as f:
        f.write(img)
    print("patched %d words -> %s" % (n, a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
