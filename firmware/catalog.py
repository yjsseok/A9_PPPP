#!/usr/bin/env python3
"""Build a function/command catalog (Markdown) from a decompressed part0.

    python3 catalog.py work/part0.bin > M20_FUNCTIONS.md

Sources (all heuristic, no disassembler needed):
  * HTTP command table   - 20-byte entries {cmd, ui_event, handler, par, ?}
                           found by looking for the known run 2001,2002,...
  * UART console tables  - {name, handler, help} triples; a NULL handler
                           starts a new command group
  * named functions      - debug strings that look like identifiers and are
                           referenced (lui/addiu) from exactly one function;
                           that function's entry is reported. Names are what
                           the firmware prints, so a few are task/flag IDs.
"""

import collections
import re
import struct
import sys

BASE = 0x80000000


class Image:
    def __init__(self, data):
        self.d = data
        self.n = len(data) // 4
        self.w = struct.unpack("<%dI" % self.n, data[:self.n * 4])

    def word(self, addr):
        return self.w[(addr - BASE) // 4]

    def cstr(self, addr, maxlen=90):
        o = addr - BASE
        if not 0 <= o < len(self.d):
            return None
        e = self.d.find(b"\0", o)
        t = self.d[o:e]
        if 0 < len(t) < maxlen and all(32 <= c < 127 for c in t):
            return t.decode("ascii")
        return None

    def is_func(self, addr):
        o = addr - BASE
        if addr & 3 or not 0 <= o < len(self.d) - 4:
            return False
        w = self.w[o // 4]
        return (w >> 16) == 0x27BD and (w & 0x8000)  # addiu sp, sp, -N

    def func_start(self, idx, limit=4000):
        for j in range(idx, max(0, idx - limit), -1):
            w = self.w[j]
            if (w >> 16) == 0x27BD and (w & 0x8000):
                return BASE + j * 4
        return None


def http_table(img):
    def entry(p):
        if p < 0 or p + 20 > len(img.d):
            return None
        cmd, ev, fn, v1, v2 = struct.unpack_from("<5I", img.d, p)
        if not 1000 <= cmd <= 9999:
            return None
        ev_ok = ev == 0 or 0x8000E000 <= ev < 0x8000F000
        fn_ok = fn == 0 or img.is_func(fn)
        if not (ev_ok and fn_ok and (ev or fn)):
            return None
        return cmd, ev, fn, v1, v2

    pat = struct.pack("<I", 2001)
    best = []
    for m in re.finditer(re.escape(pat), img.d):
        o = m.start()
        if o % 4 or entry(o) is None:
            continue
        start = o
        while entry(start - 20):
            start -= 20
        rows = []
        p = start
        while entry(p):
            rows.append(entry(p))
            p += 20
        if len(rows) > len(best):
            best = rows
    return best


def console_groups(img):
    groups = []
    cur = None
    k = 0
    while k < img.n - 3:
        a, b, c = img.w[k], img.w[k + 1], img.w[k + 2]
        sa, sc = img.cstr(a), img.cstr(c)
        if sa and sc and not img.cstr(b) and (b == 0 or img.is_func(b)):
            here = BASE + k * 4
            if b == 0:
                cur = {"name": sa, "help": sc, "cmds": [], "last": here}
                groups.append(cur)
            else:
                if cur is None or here - cur["last"] > 24:
                    cur = {"name": "?", "help": "", "cmds": [], "last": here}
                    groups.append(cur)
                cur["cmds"].append((sa, b, sc))
                cur["last"] = here
            k += 3
            continue
        k += 1
    return [g for g in groups if g["cmds"]]


def named_functions(img):
    ident = re.compile(r"^[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]{2,60}$")
    strs = {}
    for m in re.finditer(rb"[\x20-\x7e]{6,}\x00", img.d):
        t = m.group()[:-1].decode()
        if ident.match(t):
            strs[BASE + m.start()] = t
    lui = {}
    found = collections.defaultdict(set)
    for k, w in enumerate(img.w):
        op = w >> 26
        if op == 0x0F:
            lui[(w >> 16) & 31] = ((w & 0xFFFF) << 16, k)
        elif op == 0x09:
            rs = (w >> 21) & 31
            if rs in lui and k - lui[rs][1] < 64:
                imm = w & 0xFFFF
                if imm & 0x8000:
                    imm -= 0x10000
                v = (lui[rs][0] + imm) & 0xFFFFFFFF
                if v in strs:
                    f = img.func_start(k)
                    if f:
                        found[strs[v]].add(f)
    return sorted((next(iter(fs)), name) for name, fs in found.items() if len(fs) == 1)


def md_escape(s):
    return s.replace("|", "\\|").replace("%", "%")


def main():
    img = Image(open(sys.argv[1], "rb").read())
    out = []
    p = out.append

    p("## HTTP 명령 테이블 (`/?custom=1&cmd=N`)\n")
    p("`처리` 열: `UI 이벤트`는 UI 상태머신으로 넘겨 설정을 바꾸는 명령(`par` 사용), `함수`는 직접 처리하는 핸들러 주소입니다. `값1`, `값2`는 표에 있는 나머지 두 값이며 의미는 확인되지 않았습니다.\n")
    p("| cmd | 처리 | 값1 | 값2 |")
    p("|---|---|---|---|")
    for cmd, ev, fn, v1, v2 in http_table(img):
        how = ("UI 이벤트 `0x%08x`" % ev) if ev else ("함수 `0x%08x`" % fn if fn else "-")
        p("| %d | %s | %d | %d |" % (cmd, how, v1, v2))
    p("")

    groups = console_groups(img)
    p("## UART 콘솔 명령 (%d개 그룹, %d개 명령)\n" % (len(groups), sum(len(g["cmds"]) for g in groups)))
    p("콘솔에서 `그룹 명령 인자` 형식으로 입력합니다(예: `wifi mode 1`). `?` 그룹은 그룹 이름을 찾지 못한 표입니다.\n")
    for g in groups:
        p("### `%s` — %s\n" % (g["name"], md_escape(g["help"])))
        p("| 명령 | 핸들러 | 설명 |")
        p("|---|---|---|")
        for name, fn, hlp in g["cmds"]:
            p("| `%s` | `0x%08x` | %s |" % (md_escape(name), fn, md_escape(hlp)))
        p("")

    funcs = named_functions(img)
    by_mod = collections.defaultdict(list)
    for addr, name in funcs:
        by_mod[name.lstrip("x").split("_")[0]].append((addr, name))
    p("## 이름이 확인된 함수 (%d개, 모듈별)\n" % len(funcs))
    p("디버그 문자열로 추정한 이름입니다. 일부는 함수가 아니라 태스크·플래그 ID입니다.\n")
    for mod in sorted(by_mod, key=str.lower):
        items = by_mod[mod]
        p("<details><summary><code>%s</code> (%d)</summary>\n" % (mod, len(items)))
        p("| 주소 | 이름 |")
        p("|---|---|")
        for addr, name in items:
            p("| `0x%08x` | `%s` |" % (addr, name))
        p("\n</details>\n")
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
