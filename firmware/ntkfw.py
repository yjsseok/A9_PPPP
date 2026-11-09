#!/usr/bin/env python3
"""Novatek NT96660 firmware tool (SJCAM M20 FW V1.3.1 layout).

File layout handled here:

    [part0: BCL1 block]          main program (eCos), loaded at 0x80000000
    [NVTPACK_FW_HDR + table]     GUID, header size, checksum, entry count,
                                 entries of (start offset, size, id)
    [part1..N: BCL1 blocks]      further partitions referenced by the table

BCL1 block header (16 bytes):
    'BCL1' | checksum u16 LE | algorithm u16 BE | unpacked size u32 BE |
    packed size u32 BE
Only algorithm 9 (BCL LZ77) is supported.

All checksums use Novatek's MemCheck_CalcCheckSum16Bit: the 16-bit LE words
plus their word index are summed, with the checksum word itself treated as
zero, and the stored value makes the total wrap to zero.

Commands:
    info   FW.bin                     show structure and verify checksums
    unpack FW.bin OUTDIR              write partN.bin (decompressed)
    pack   FW.bin PART0.bin OUT.bin   rebuild FW.bin with a new part0
    verify FW.bin [OUTDIR]            re-parse a file; optionally compare
                                      its decompressed parts to OUTDIR/partN.bin
"""

import argparse
import os
import struct
import sys

BCL_MAGIC = b"BCL1"
BCL_HDR_SIZE = 16
ALGO_LZ77 = 9
FW_HDR_GUID = bytes.fromhex("90be2788cd36c24fa98773a8484e84b1")
FW_HDR_FIXED = 0x1C  # GUID(16) + size(4) + checksum(4) + count(4)
FW_HDR_CHKSUM_OFF = 0x14

LZ_MAX_OFFSET = 100000
LZ_CHAIN_LIMIT = 512  # 512 already packs SJCAM M20 V1.3.1 part0 smaller than stock


# ---------------------------------------------------------------- checksum

def memcheck16(data, ignore_off):
    """Return the value that, stored at ignore_off, makes the block sum to 0.

    Like Novatek's routine, an odd trailing byte is not part of the sum.
    """
    n = len(data) // 2
    words = struct.unpack_from("<%dH" % n, data)
    total = sum(words) - words[ignore_off // 2] + (n - 1) * n // 2
    return (-total) & 0xFFFF


def inner_checksum_offset(raw):
    """Offset of the checksum word inside decompressed data, or None.

    Same rules and order as NTKFWinfo: FFFF@0x6C + 55AA@0x46C -> 0x46E,
    55AA@0x6C -> 0x6E, 55AA@0x16C -> 0x16E, 55AA@0x26C -> 0x26E.
    """
    def at(off, val):
        return raw[off:off + 2] == val
    if at(0x6C, b"\xff\xff") and at(0x46C, b"\x55\xaa"):
        return 0x46E
    for magic in (0x6C, 0x16C, 0x26C):
        if at(magic, b"\x55\xaa"):
            return magic + 2
    return None


def has_inner_checksum(raw):
    return inner_checksum_offset(raw) is not None


def fix_inner_checksum(raw):
    raw = bytearray(raw)
    off = inner_checksum_offset(raw)
    if off is not None:
        struct.pack_into("<H", raw, off, memcheck16(raw, off))
    return bytes(raw)


# ---------------------------------------------------------------- BCL LZ77

def _read_varsize(src, i):
    y = 0
    while True:
        b = src[i]
        i += 1
        y = (y << 7) | (b & 0x7F)
        if not b & 0x80:
            return y, i


def _write_varsize(out, x):
    # 7 bits per byte, most significant group first, high bit = "more".
    groups = [x & 0x7F]
    x >>= 7
    while x:
        groups.append(x & 0x7F)
        x >>= 7
    for g in reversed(groups[1:]):
        out.append(g | 0x80)
    out.append(groups[0])


def _varsize_len(x):
    n = 1
    while x >= 0x80:
        x >>= 7
        n += 1
    return n


def lz_decompress(src, outsize):
    marker = src[0]
    i = 1
    n = len(src)
    out = bytearray()
    while i < n and len(out) < outsize:
        s = src[i]
        i += 1
        if s != marker:
            out.append(s)
            continue
        if i >= n:
            raise ValueError("LZ stream ends after a marker byte")
        if src[i] == 0:
            out.append(marker)
            i += 1
            continue
        try:
            length, i = _read_varsize(src, i)
            offset, i = _read_varsize(src, i)
        except IndexError:
            raise ValueError("LZ stream ends inside a match token")
        start = len(out) - offset
        if offset == 0 or start < 0:
            raise ValueError("invalid LZ offset %d" % offset)
        if offset >= length:
            out += out[start:start + length]
        else:
            for k in range(length):
                out.append(out[start + k])
    return bytes(out)


def lz_compress(data, progress=None, compat=False):
    """BCL-compatible LZ77 encoder (hash chains on 3-byte prefixes).

    compat=True mimics the stock encoder's output shape: matches are at most
    16384 bytes and never overlap their own output. Slightly larger, but uses
    only token forms already present in stock firmware.
    """
    len_cap = 16384 if compat else None
    n = len(data)
    hist = [0] * 256
    for b in data:
        hist[b] += 1
    marker = hist.index(min(hist))

    out = bytearray([marker])
    heads = {}
    prev = [-1] * n
    mv = memoryview(data)

    def insert(p):
        if p + 2 < n:
            key = mv[p:p + 3].tobytes()
            prev[p] = heads.get(key, -1)
            heads[key] = p

    i = 0
    next_report = 0
    while i < n:
        if progress and i >= next_report:
            progress(i, n)
            next_report = i + (1 << 20)
        best_len = 0
        best_off = 0
        if i + 3 < n:
            j = heads.get(mv[i:i + 3].tobytes(), -1)
            chain = 0
            limit = n - i if len_cap is None else min(n - i, len_cap)
            while j >= 0 and i - j < LZ_MAX_OFFSET and chain < LZ_CHAIN_LIMIT:
                max_len = limit if not compat else min(limit, i - j)
                # cheap reject: a longer match must also agree at index best_len
                if max_len >= 4 and best_len < max_len and data[j + best_len] == data[i + best_len]:
                    k = 3
                    while k < max_len and data[j + k] == data[i + k]:
                        k += 1
                    if k > best_len:
                        best_len = k
                        best_off = i - j
                        if k == limit:
                            break
                j = prev[j]
                chain += 1
        if best_len >= 4:
            cost = 1 + _varsize_len(best_len) + _varsize_len(best_off)
            if cost < best_len:
                out.append(marker)
                _write_varsize(out, best_len)
                _write_varsize(out, best_off)
                for p in range(i, i + best_len):
                    insert(p)
                i += best_len
                continue
        b = data[i]
        out.append(b)
        if b == marker:
            out.append(0)
        insert(i)
        i += 1
    if progress:
        progress(n, n)
    return bytes(out)


# ---------------------------------------------------------------- BCL block

def parse_bcl(buf, off):
    if buf[off:off + 4] != BCL_MAGIC:
        raise ValueError("no BCL1 magic at 0x%x" % off)
    chk = struct.unpack_from("<H", buf, off + 4)[0]
    algo, usize, csize = struct.unpack_from(">HII", buf, off + 6)
    end = off + BCL_HDR_SIZE + csize
    calc = memcheck16(buf[off:end], 4)
    return {"off": off, "chk": chk, "chk_calc": calc, "algo": algo,
            "usize": usize, "csize": csize, "end": end}


def bcl_decompress(buf, blk):
    if blk["algo"] != ALGO_LZ77:
        raise ValueError("unsupported BCL algorithm %d" % blk["algo"])
    start = blk["off"] + BCL_HDR_SIZE
    raw = lz_decompress(buf[start:start + blk["csize"]], blk["usize"])
    if len(raw) != blk["usize"]:
        raise ValueError("decompressed size mismatch")
    return raw


def build_bcl(raw, progress=None, compat=False):
    comp = lz_compress(raw, progress, compat)
    if lz_decompress(comp, len(raw)) != raw:
        raise RuntimeError("compressor self-check failed")
    pad = (-len(comp)) % 4
    comp += b"\0" * pad
    hdr = bytearray(BCL_MAGIC + b"\0\0" + struct.pack(">HII", ALGO_LZ77, len(raw), len(comp)))
    blk = bytearray(hdr + comp)
    struct.pack_into("<H", blk, 4, memcheck16(blk, 4))
    return bytes(blk)


# ---------------------------------------------------------------- whole file

def parse_fw(buf):
    p0 = parse_bcl(buf, 0)
    fw = {"part0": p0, "hdr": None, "entries": []}
    h = p0["end"]
    if buf[h:h + 16] != FW_HDR_GUID:
        if h != len(buf):
            raise ValueError("unknown data after part0 at 0x%x" % h)
        return fw
    size, chk, count = struct.unpack_from("<III", buf, h + 16)
    calc = memcheck16(buf[h:h + size], FW_HDR_CHKSUM_OFF)
    fw["hdr"] = {"off": h, "size": size, "chk": chk, "chk_calc": calc, "count": count}
    for k in range(count):
        start, psize, pid = struct.unpack_from("<III", buf, h + FW_HDR_FIXED + 12 * k)
        fw["entries"].append({"start": start, "size": psize, "id": pid,
                              "bcl": parse_bcl(buf, start)})
    return fw


def iter_bcl_blocks(fw):
    yield 0, fw["part0"]
    for e in fw["entries"]:
        yield e["id"], e["bcl"]


def check_fw(buf, fw, raws=None):
    """Return a list of (description, ok) checks."""
    res = []
    for pid, blk in iter_bcl_blocks(fw):
        res.append(("part%d BCL1 checksum 0x%04x (calc 0x%04x)" % (pid, blk["chk"], blk["chk_calc"]),
                    blk["chk"] == blk["chk_calc"]))
        res.append(("part%d packed size is 4-byte aligned" % pid, blk["csize"] % 4 == 0))
        raw = raws[pid] if raws else bcl_decompress(buf, blk)
        off = inner_checksum_offset(raw)
        if off is not None:
            inner = struct.unpack_from("<H", raw, off)[0]
            calc = memcheck16(raw, off)
            res.append(("part%d inner checksum @0x%x 0x%04x (calc 0x%04x)" % (pid, off, inner, calc),
                        inner == calc))
    h = fw["hdr"]
    if h:
        res.append(("NVTPACK_FW_HDR checksum 0x%04x (calc 0x%04x)" % (h["chk"], h["chk_calc"]),
                    h["chk"] == h["chk_calc"]))
        res.append(("NVTPACK_FW_HDR is 4-byte aligned", h["off"] % 4 == 0))
        res.append(("NVTPACK_FW_HDR size matches entry count",
                    h["size"] == FW_HDR_FIXED + 12 * h["count"]))
        pos = h["off"] + h["size"]
        for e in fw["entries"]:
            blk_len = e["bcl"]["end"] - e["start"]
            res.append(("part%d entry size 0x%x equals block length 0x%x" % (e["id"], e["size"], blk_len),
                        e["size"] == blk_len))
            res.append(("part%d follows previous data (0x%x, expected 0x%x)" % (e["id"], e["start"], pos),
                        e["start"] == pos))
            pos = e["start"] + e["size"] + ((-e["size"]) % 4)
        if fw["entries"]:
            last_end = fw["entries"][-1]["bcl"]["end"]
            res.append(("file ends at last partition (0x%x, file size 0x%x)" % (last_end, len(buf)),
                        len(buf) == last_end))
    return res


def rebuild(buf, fw, new_part0_blk):
    """Replace part0, shift the following partitions, fix the header."""
    if fw["hdr"] is None:
        return new_part0_blk
    h = fw["hdr"]
    old_tail = buf[h["off"]:]
    delta = len(new_part0_blk) - h["off"]
    tail = bytearray(old_tail)
    for k, e in enumerate(fw["entries"]):
        struct.pack_into("<I", tail, FW_HDR_FIXED + 12 * k, e["start"] + delta)
    hdr_region = tail[:h["size"]]
    struct.pack_into("<I", hdr_region, FW_HDR_CHKSUM_OFF, 0)
    struct.pack_into("<I", tail, FW_HDR_CHKSUM_OFF, memcheck16(hdr_region, FW_HDR_CHKSUM_OFF))
    return bytes(new_part0_blk) + bytes(tail)


# ---------------------------------------------------------------- commands

def _read(path):
    with open(path, "rb") as f:
        return f.read()


def _print_checks(checks):
    ok = True
    for desc, good in checks:
        print("  [%s] %s" % ("OK" if good else "FAIL", desc))
        ok &= good
    return ok


def cmd_info(args):
    buf = _read(args.fw)
    fw = parse_fw(buf)
    print("file size 0x%x" % len(buf))
    for pid, blk in iter_bcl_blocks(fw):
        print("part%d @0x%x  packed 0x%x  unpacked 0x%x  algo %d" %
              (pid, blk["off"], blk["csize"], blk["usize"], blk["algo"]))
    if fw["hdr"]:
        print("NVTPACK_FW_HDR @0x%x size 0x%x entries %d" %
              (fw["hdr"]["off"], fw["hdr"]["size"], fw["hdr"]["count"]))
    return 0 if _print_checks(check_fw(buf, fw)) else 1


def cmd_unpack(args):
    buf = _read(args.fw)
    fw = parse_fw(buf)
    os.makedirs(args.outdir, exist_ok=True)
    for pid, blk in iter_bcl_blocks(fw):
        raw = bcl_decompress(buf, blk)
        path = os.path.join(args.outdir, "part%d.bin" % pid)
        with open(path, "wb") as f:
            f.write(raw)
        print("wrote %s (0x%x bytes)" % (path, len(raw)))
    return 0


def _progress(done, total):
    sys.stderr.write("\r  compressing %3d%%" % (done * 100 // max(total, 1)))
    if done >= total:
        sys.stderr.write("\n")


def cmd_pack(args):
    buf = _read(args.fw)
    fw = parse_fw(buf)
    raw = _read(args.part0)
    if len(raw) != fw["part0"]["usize"]:
        print("part0 size changed (0x%x -> 0x%x); refusing: code is loaded at fixed addresses"
              % (fw["part0"]["usize"], len(raw)))
        return 1
    fixed = fix_inner_checksum(raw)
    if fixed != raw:
        print("part0 inner checksum updated")
    blk = build_bcl(fixed, _progress, args.compat)
    out = rebuild(buf, fw, blk)
    if len(out) > len(buf) and not args.allow_larger:
        print("result is 0x%x bytes larger than the input firmware; the updater rejects files that "
              "exceed the flash partition. Use --allow-larger only if you know the limit."
              % (len(out) - len(buf)))
        return 1
    with open(args.out, "wb") as f:
        f.write(out)
    print("wrote %s (0x%x bytes, part0 packed 0x%x -> 0x%x)" %
          (args.out, len(out), fw["part0"]["csize"], len(blk) - BCL_HDR_SIZE))
    # verify the written file from scratch
    nbuf = _read(args.out)
    nfw = parse_fw(nbuf)
    raws = {pid: bcl_decompress(nbuf, b) for pid, b in iter_bcl_blocks(nfw)}
    checks = check_fw(nbuf, nfw, raws)
    checks.append(("part0 decompresses to the input", raws[0] == fixed))
    for e_old, e_new in zip(fw["entries"], nfw["entries"]):
        same = buf[e_old["start"]:e_old["bcl"]["end"]] == nbuf[e_new["start"]:e_new["bcl"]["end"]]
        checks.append(("part%d copied unchanged" % e_new["id"], same))
    return 0 if _print_checks(checks) else 1


def cmd_verify(args):
    buf = _read(args.fw)
    fw = parse_fw(buf)
    raws = {pid: bcl_decompress(buf, b) for pid, b in iter_bcl_blocks(fw)}
    checks = check_fw(buf, fw, raws)
    if args.refdir:
        for pid, raw in raws.items():
            ref = os.path.join(args.refdir, "part%d.bin" % pid)
            if os.path.exists(ref):
                checks.append(("part%d equals %s" % (pid, ref), raw == _read(ref)))
    return 0 if _print_checks(checks) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("info"); p.add_argument("fw"); p.set_defaults(fn=cmd_info)
    p = sub.add_parser("unpack"); p.add_argument("fw"); p.add_argument("outdir"); p.set_defaults(fn=cmd_unpack)
    p = sub.add_parser("pack"); p.add_argument("fw"); p.add_argument("part0"); p.add_argument("out")
    p.add_argument("--compat", action="store_true",
                   help="stock-like LZ tokens: max match 16384, no overlapping copies")
    p.add_argument("--allow-larger", action="store_true",
                   help="write the result even if it is larger than the input firmware")
    p.set_defaults(fn=cmd_pack)
    p = sub.add_parser("verify"); p.add_argument("fw"); p.add_argument("refdir", nargs="?"); p.set_defaults(fn=cmd_verify)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
