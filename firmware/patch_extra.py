#!/usr/bin/env python3
"""Optional patches for SJCAM M20 V1.3.1 part0 (stock or station-patched).

    python3 patch_extra.py IN_part0.bin OUT_part0.bin [--led-off] [--reconnect] [--leds-off] [--mute] [--live720] [--live15] [--autowifi] [--apfile] [--defaults] [--autorec] [--binclean] [--default-date YYYY-MM-DD]

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
             (SysResetFlag 0x801c5188): movie size flag 0x1a = 1
             (2560x1440@30, HTTP 2002 par 0) and auto power off flag
             0x3a = 0 (off). Flag 0x1a counts rows of the movie size table
             (0 = 2880x2160@24); HTTP 2002 maps flag 1/2/4/8/9.. to par
             0/1/2/3/4.. (cmd 3014 handler 0x801cad44), and the Wi-Fi window
             (0x801b1f14) turns 0 or 0xb into 2 (1080p60), which is what
             the first version of this patch (0x1a = 0) ran into.
             Car mode (flag 0xa1) stays off: its record key is posted
             before the Wi-Fi wait window opens and is lost there.
--autorec    Start recording after boot without a button. While the
             Wi-Fi link window (UIMenuWndWiFiMobileLinkOK) is open, its
             500 ms timer event (0x80001000/0x80001005, handler 0x801b084c)
             calls 0x800ca4c8 at 0x801b08d0; that call goes through 39 new
             instructions. Every 8th tick (4 s), for up to 240 ticks after
             the window first opens, they read the movie record state
             (0x801bfa38: 1 ready, 2 recording); if ready they post UI event
             0x8000e003 with par 1 (what HTTP cmd=2001&par=1 sends), and once
             recording is seen they stop for this boot, so a later manual
             stop is not undone. Tick count: 0x805a21d0 (spare station
             buffer). For checking from outside, the first string of cmd
             3012 ("660", 0x803afa88) becomes <attempt letter a..><state>0,
             e.g. "b20" = recording seen on the 2nd try. Code sits in the
             "dsysdma" console handler after the --apfile code (0x800cd1a4);
             its console slot is redirected as in --apfile. Recording does
             not start until the camera joins the network.
--binclean   When A:\\SJCAM001.bin is on the card at boot, close and delete
             it and boot normally. Stock firmware opens it (0x801c6724),
             sets a hold flag (0x8055c33c) and leaves the screen off and
             Wi-Fi down until the card is removed; the update itself was
             already done by the loader before the main program started.
             With this, a firmware can be put on the card over Wi-Fi (HTTP
             multipart POST to /, the stock "Upload files" form) and one
             power cycle installs it. Code: 9 instructions after the
             --autorec code (0x800cd240).

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

# All new code below lives in the UART "dsysdma" handler (0x800cd144, 230
# instructions, referenced only by console slot 0x80000b10, which is pointed
# at the empty function 0x800c901c): get_mode + path, then --autorec, then
# --binclean.
DSYSDMA = 0x800CD144
DSYSDMA_STOCK = [
    0x27BDFD70, 0x240600FC, 0xAFBE0288, 0x03A0F021, 0xAFB1026C, 0x27D10018, 0x02202021, 0xAFB40278,
    0xAFB20270, 0x00002821, 0x3C14800D, 0x3C12800D, 0xAFBF028C, 0xAFB70284, 0xAFB60280, 0xAFB5027C,
    0xAFB30274, 0x0C007DA8, 0xAFB00268, 0x2647D054, 0x268CD048, 0x3C17800D, 0x95930004, 0x26F6D060,
    0x94EC0008, 0x3C06800D, 0x24CAD06C, 0x92D50006, 0xA7CC0038, 0x954A0004, 0x3C05800D, 0x24A8D078,
    0xA7CA0040, 0x95080004, 0x3C04800D, 0x2483D084, 0xA7C8004C, 0x946E0008, 0x3C02800D, 0x245FD090,
    0xA7CE005C, 0x8FFF0004, 0x8CC6D06C, 0xAFDF0064, 0x8CE70004, 0x8CA5D078, 0x8C84D084, 0x96D60004,
    0x3C19800D, 0xAFC70034, 0xAFC6003C, 0xAFC50048, 0xAFC40054, 0x8C630004, 0x8EF7D060, 0x8E94D048,
    0x8C42D090, 0x273FD09C, 0x8E52D054, 0x3C18800D, 0xAFC30058, 0xAFC20060, 0xAFD70018, 0xA7D6001C,
    0xA3D5001E, 0xAFD40024, 0xA7D30028, 0xAFD20030, 0x8FFF0004, 0x2710D0A8, 0xAFDF0070, 0x8E100004,
    0x3C0F800D, 0x25EED0B4, 0xAFD0007C, 0x91DF0006, 0x3C0D800D, 0x25ACD0C0, 0xA3DF008A, 0x919F0006,
    0x3C0B800D, 0x256AD0CC, 0xA3DF0096, 0x915F0006, 0x3C09800D, 0x2528D0D8, 0xA3DF00A2, 0x911F0006,
    0x3C07800D, 0xA3DF00AE, 0x3C06800D, 0x3C05800D, 0x3C04800D, 0x3C03800D, 0x3C02800D, 0x95CE0004,
    0x958C0004, 0x954A0004, 0x95160004, 0x24B4D0FC,
]
CONSOLE_DSYSDMA_SLOT = (0x80000B10, DSYSDMA, 0x800C901C)
VERSION_660 = 0x803AFA88  # "660": first string of cmd 3012, only read by its handler; used as a status line

# --apfile
# get_mode(): 1 station, 0 AP. Checks for the switch file once per boot with
# FileSys_OpenFile/CloseFile (FileSys_GetAttrib said "missing" for an existing
# file on the camera, 2026-11-10) and caches 2 = AP, 1 = station in 0x805a21cc
# (spare station buffer). Writes 'S' (no file) or 'T' (file found) to the
# third character of the status line.
CAVE2 = DSYSDMA
GET_MODE = [
    0x3C08805A,  # 0  lui   t0, 0x805a
    0x8D0221CC,  # 1  lw    v0, 0x21cc(t0)     cached: 1 station, 2 AP, 0 unknown
    0x14400016,  # 2  bnez  v0, 25
    0x00000000,  # 3  nop
    0x27BDFFE0,  # 4  addiu sp, sp, -0x20
    0xAFBF001C,  # 5  sw    ra, 0x1c(sp)
    None,        # 6  lui   a0, %hi(path)
    None,        # 7  addiu a0, a0, %lo(path)
    0x0C03AA31,  # 8  jal   FileSys_OpenFile (0x800ea8c4)
    0x24050001,  # 9  addiu a1, zero, 1        (delay slot) read
    0xAFA20018,  # 10 sw    v0, 0x18(sp)       handle, 0 if missing
    0x10400003,  # 11 beqz  v0, 15
    0x00402021,  # 12 move  a0, v0             (delay slot)
    0x0C03AA1B,  # 13 jal   FileSys_CloseFile (0x800ea86c)
    0x00000000,  # 14 nop
    0x8FA20018,  # 15 lw    v0, 0x18(sp)
    0x8FBF001C,  # 16 lw    ra, 0x1c(sp)
    0x27BD0020,  # 17 addiu sp, sp, 0x20
    0x0002102B,  # 18 sltu  v0, zero, v0       1 if the file exists
    0x3C09803B,  # 19 lui   t1, 0x803b
    0x244A0053,  # 20 addiu t2, v0, 0x53       'S' station / 'T' file found
    0xA12AFA8A,  # 21 sb    t2, -0x576(t1)     status line, 3rd character
    0x24420001,  # 22 addiu v0, v0, 1          2 = AP, 1 = station
    0x3C08805A,  # 23 lui   t0, 0x805a
    0xAD0221CC,  # 24 sw    v0, 0x21cc(t0)
    0x24090002,  # 25 addiu t1, zero, 2
    0x03E00008,  # 26 jr    ra
    0x01221023,  # 27 subu  v0, t1, v0         (delay slot) station 1, AP 0
]
AP_PATH_ADDR = CAVE2 + len(GET_MODE) * 4
GET_MODE[6] = 0x3C040000 | (((AP_PATH_ADDR + 0x8000) >> 16) & 0xFFFF)  # addiu sign-extends
GET_MODE[7] = 0x24840000 | (AP_PATH_ADDR & 0xFFFF)
AP_PATH = b"A:\\M20AP.TXT\0\0\0\0"  # 12 chars + NULs = 16 bytes
assert len(AP_PATH) == 16
APFILE_CODE = GET_MODE + list(struct.unpack("<4I", AP_PATH))
JAL_GET_MODE = 0x0C000000 | ((CAVE2 & 0x0FFFFFFF) >> 2)
LI_V0_1 = 0x24020001
MODE_SITES = [0x801D8D10, 0x801D8D9C, 0x801D8DB4, 0x801D8DD4, 0x801D8E24, 0x801D8E38, 0x801D8E88]

# --defaults (SysResetFlag 0x801c5188; v1 = 1 throughout)
DEFAULTS = [
    (0x801C51A8, 0xAC44010C, 0xAC43010C, "flag 0x1a movie size 2 -> 1 (2560x1440@30)"),
    (0x801C5264, 0xAC43018C, 0xAC40018C, "flag 0x3a auto power off 1 -> 0"),
]

# --autorec
CAVE3 = CAVE2 + len(APFILE_CODE) * 4  # 0x800cd1c4
AUTOREC_LIMIT = 240  # 500 ms ticks: try every 4 s for 2 minutes after the link window opens
CAVE3_CODE = [
    0x3C08805A,  # 0  lui   t0, 0x805a
    0x8D0921D0,  # 1  lw    t1, 0x21d0(t0)     tick count (BSS, 0 at boot)
    0x2D2A0000 | AUTOREC_LIMIT,  # 2  sltiu t2, t1, LIMIT
    0x11400028,  # 3  beqz  t2, 44 (tail)       done or gave up
    0x25290001,  # 4  addiu t1, t1, 1          (delay slot)
    0xAD0921D0,  # 5  sw    t1, 0x21d0(t0)
    0x312A0007,  # 6  andi  t2, t1, 7
    0x15400024,  # 7  bnez  t2, 44 (tail)       act on every 8th tick
    0x00000000,  # 8  nop
    0x27BDFFE0,  # 9  addiu sp, sp, -0x20
    0xAFBF001C,  # 10 sw    ra, 0x1c(sp)
    0xAFA90018,  # 11 sw    t1, 0x18(sp)
    0x3C08805A,  # 12 lui   t0, 0x805a         --binclean: delete the update file now
    0x8D0A21D4,  # 13 lw    t2, 0x21d4(t0)     (the file system is fully up by now)
    0x11400004,  # 14 beqz  t2, 19
    0xAD0021D4,  # 15 sw    zero, 0x21d4(t0)   (delay slot) only once
    0x3C04803B,  # 16 lui   a0, 0x803b
    0x0C03AB0E,  # 17 jal   FileSys_DeleteFile (0x800eac38)
    0x2484E314,  # 18 addiu a0, a0, -0x1cec    (delay slot) stock string A:\SJCAM001.bin
    0x0C06FE8E,  # 19 jal   0x801bfa38         movie record state: 1 ready, 2 recording
    0x00000000,  # 20 nop
    0x8FA90018,  # 21 lw    t1, 0x18(sp)
    0x3C08803B,  # 22 lui   t0, 0x803b
    0x000950C2,  # 23 srl   t2, t1, 3          attempt number 1, 2, ..
    0x254A0060,  # 24 addiu t2, t2, 0x60       'a', 'b', ..
    0xA10AFA88,  # 25 sb    t2, -0x578(t0)     status line, 1st character
    0x244B0030,  # 26 addiu t3, v0, 0x30       record state digit
    0xA10BFA89,  # 27 sb    t3, -0x577(t0)     status line, 2nd character
    0x240B0002,  # 28 addiu t3, zero, 2
    0x144B0005,  # 29 bne   v0, t3, 35
    0x240B0001,  # 30 addiu t3, zero, 1        (delay slot)
    0x3C08805A,  # 31 lui   t0, 0x805a         recording: stop trying
    0x24090000 | AUTOREC_LIMIT,  # 32 addiu t1, zero, LIMIT
    0x10000007,  # 33 b     41
    0xAD0921D0,  # 34 sw    t1, 0x21d0(t0)     (delay slot)
    0x144B0005,  # 35 bne   v0, t3, 41          post only when ready to record
    0x3C048000,  # 36 lui   a0, 0x8000         (delay slot)
    0x3484E003,  # 37 ori   a0, a0, 0xe003     same UI event as HTTP cmd 2001
    0x24050001,  # 38 addiu a1, zero, 1        one parameter
    0x0C03A0B0,  # 39 jal   Ux_PostEvent (0x800e82c0)
    0x24060001,  # 40 addiu a2, zero, 1        (delay slot) par = 1: start
    0x8FBF001C,  # 41 lw    ra, 0x1c(sp)
    0x27BD0020,  # 42 addiu sp, sp, 0x20
    0x24040002,  # 43 addiu a0, zero, 2        argument of the original call
    0x08032932,  # 44 j     0x800ca4c8         original callee, returns to the timer handler
    0x00000000,  # 45 nop
]
JAL_CA4C8 = 0x0C032932  # jal 0x800ca4c8
JAL_CAVE3 = 0x0C000000 | ((CAVE3 & 0x0FFFFFFF) >> 2)
AUTOREC_HOOK = (0x801B08D0, JAL_CA4C8, JAL_CAVE3)

# --binclean (needs --autorec, whose timer code does the delete)
CAVE4 = CAVE3 + len(CAVE3_CODE) * 4
CAVE4_CODE = [
    0x27BDFFE0,  # 0 addiu sp, sp, -0x20
    0xAFBF001C,  # 1 sw    ra, 0x1c(sp)
    0x0C03AA1B,  # 2 jal   FileSys_CloseFile (0x800ea86c), a0 = handle
    0x00000000,  # 3 nop
    0x3C08805A,  # 4 lui   t0, 0x805a
    0x24090001,  # 5 addiu t1, zero, 1
    0xAD0921D4,  # 6 sw    t1, 0x21d4(t0)     delete pending
    0x8FBF001C,  # 7 lw    ra, 0x1c(sp)
    0x03E00008,  # 8 jr    ra
    0x27BD0020,  # 9 addiu sp, sp, 0x20
]
assert (CAVE4 - DSYSDMA) // 4 + len(CAVE4_CODE) <= len(DSYSDMA_STOCK)
JAL_CAVE4 = 0x0C000000 | ((CAVE4 & 0x0FFFFFFF) >> 2)
BINCLEAN_HOOK = [
    (0x801C676C, 0x3C028056, 0x00000000, "lui v0, 0x8056 -> nop (beqz delay slot)"),
    (0x801C6770, 0x24030001, JAL_CAVE4, "li v1, 1 -> jal close + mark"),
    (0x801C6774, 0xA043C33C, 0x00402021, "sb v1, hold flag -> move a0, v0 (delay slot)"),
]


def _put_code(img, start, code, what):
    base = (start - DSYSDMA) // 4
    return sum(_put(img, start + 4 * k, DSYSDMA_STOCK[base + k], w, what) for k, w in enumerate(code))


# --default-date (System_OnBoot): if the RTC date is before 2015-12-22 the
# clock is set to 2016-01-01 00:00:01. The threshold (YYYYMMDD in a0 via
# lui/ori) and the date (year in the delay slot of the bnez, month/day as
# rtc_setDate arguments) become the given date.
BOOT_DATE_THRESHOLD = (0x800CBAE8, 0x3C040133, 0x800CBAEC, 0x34847BB6)  # 20151222
BOOT_DATE_SET = [(0x800CBB00, 0x240407E0, 0x24040000, "year"),   # addiu a0, zero, 2016 (0x800cb918 reloads a0)
                 (0x800CBCA4, 0x24050001, 0x24050000, "month"),  # addiu a1, zero, 1
                 (0x800CBCAC, 0x24060001, 0x24060000, "day")]    # addiu a2, zero, 1


def _default_date(img, ymd):
    y, m, d = ymd
    if not (2000 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31):
        raise ValueError("bad --default-date")
    n = 0
    v = y * 10000 + m * 100 + d
    a1, o1, a2, o2 = BOOT_DATE_THRESHOLD
    n += _put(img, a1, o1, 0x3C040000 | (v >> 16), "boot date threshold hi")
    n += _put(img, a2, o2, 0x34840000 | (v & 0xFFFF), "boot date threshold lo")
    for (a, o, base, what), val in zip(BOOT_DATE_SET, (y, m, d)):
        n += _put(img, a, o, base | val, "boot date " + what)
    return n


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
          autowifi=False, apfile=False, defaults=False, live15=False, autorec=False, binclean=False, default_date=None):
    n = 0
    if binclean and not autorec:
        raise ValueError("--binclean needs --autorec (the delete runs in its timer code)")
    if binclean:
        n += _put_code(img, CAVE4, CAVE4_CODE, "code cave 4")
        for a, o, w, what in BINCLEAN_HOOK:
            n += _put(img, a, o, w, what)
    if autorec:
        n += _put_code(img, CAVE3, CAVE3_CODE, "code cave 3")
        a, o, w = AUTOREC_HOOK
        n += _put(img, a, o, w, "link window timer hook")
    if apfile:
        addr, want = STATION_MARK
        if _word(img, addr) != want:
            raise ValueError("--apfile needs the station patch (patch_station.py) applied first")
        n += _put_code(img, CAVE2, APFILE_CODE, "code cave 2")
        for a in MODE_SITES:
            n += _put(img, a, LI_V0_1, JAL_GET_MODE, "station mode constant")
    if binclean or autorec or apfile:
        a, o, w = CONSOLE_DSYSDMA_SLOT
        n += _put(img, a, o, w, "console dsysdma slot")
    if default_date:
        n += _default_date(img, default_date)
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
            if (sw, sh) not in ((640, 360), (LIVE_W, LIVE_H)) or sf not in (30, 15) or st not in (204800, 512000):
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
    ap.add_argument("--autorec", action="store_true")
    ap.add_argument("--binclean", action="store_true")
    ap.add_argument("--default-date", metavar="YYYY-MM-DD",
                    help="clock after boot when the RTC date is older than this (stock 2016-01-01)")
    a = ap.parse_args(argv)
    if not (a.led_off or a.reconnect or a.live720 or a.leds_off or a.mute or a.autowifi or a.apfile
            or a.defaults or a.live15 or a.autorec or a.binclean or a.default_date):
        ap.error("choose at least one patch")
    with open(a.part0, "rb") as f:
        img = bytearray(f.read())
    n = apply(img, a.led_off, a.reconnect, a.live720, a.leds_off, a.mute, a.autowifi,
              a.apfile, a.defaults, a.live15, a.autorec, a.binclean,
              tuple(int(x) for x in a.default_date.split("-")) if a.default_date else None)
    with open(a.out, "wb") as f:
        f.write(img)
    print("patched %d words -> %s" % (n, a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
