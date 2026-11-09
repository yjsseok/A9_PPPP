# SJCAM M20 (Novatek NT96660) 펌웨어 도구

`ntkfw.py`는 SJCAM M20 V1.3.1 펌웨어(`SJCAM001.bin`)를 풀고, 수정한 메인 프로그램을 다시 포장하는 도구입니다. Python 3 표준 라이브러리만 사용합니다.

> 펌웨어 파일(`*.bin`)은 제조사 저작물이라 저장소에 넣지 않습니다(`.gitignore`로 제외).

## 펌웨어 구조

| 위치 (원본 기준) | 내용 |
|---|---|
| `0x000000` | **part0**: BCL1 블록. 메인 프로그램(eCos), 메모리 `0x80000000`에 적재 |
| `0x2a4da8` | **NVTPACK_FW_HDR**: GUID, 헤더 크기(0x28), 체크섬, 항목 수, (시작 위치, 크기, ID) 표 |
| `0x2a4dd0` | **part1**: BCL1 블록 |

BCL1 헤더(16바이트): `'BCL1'` · 체크섬 u16 LE · 알고리즘 u16 BE(9 = LZ77) · 풀린 크기 u32 BE · 압축 크기 u32 BE

### 체크섬 3종류 (모두 Novatek `MemCheck_CalcCheckSum16Bit`)

16비트 LE 값과 그 순번을 모두 더했을 때 0이 되도록 보정값을 넣는 방식입니다. 보정값 자리는 0으로 보고 계산합니다.

1. **풀린 데이터 내부**: `0x6C`가 `FF FF`이고 `0x46C`가 `55 AA`이면 `0x46E`(part1이 이 경우), `0x6C`/`0x16C`/`0x26C`에 `55 AA`가 있으면 그 뒤 2바이트(part0은 `0x6E`)가 보정값입니다.
2. **BCL1 헤더**: 압축된 블록 전체(헤더 포함)에 대해 계산하고, 헤더 `+4`에 저장합니다.
3. **NVTPACK_FW_HDR**: 헤더와 표(0x28바이트)에 대해 계산하고, `+0x14`에 저장합니다.

`pack`은 세 가지를 모두 자동으로 다시 계산하고, part0 크기가 바뀌면 표의 part1 시작 위치도 고칩니다.

## 사용법

```sh
python3 ntkfw.py info   SJCAM001.bin                 # 구조와 체크섬 확인
python3 ntkfw.py unpack SJCAM001.bin work/           # work/part0.bin, part1.bin
# ... work/part0.bin 수정 (크기는 그대로) ...
python3 ntkfw.py pack   SJCAM001.bin work/part0.bin new/SJCAM001.bin
python3 ntkfw.py verify new/SJCAM001.bin [work/]     # 다시 읽어서 검증
```

- `pack`은 part0만 다시 압축합니다. part1은 바이트 그대로 복사합니다.
- part0 크기가 달라지면 거부합니다. 코드가 고정 주소에 적재되기 때문입니다.
- 압축기는 원본 압축기와 바이트 단위로 같지는 않지만 같은 BCL LZ77 형식입니다. 기본 모드는 16KB보다 긴 일치와 겹치는 복사를 사용합니다(실기 부팅 확인됨). `--compat`를 주면 원본처럼 일치 길이 16384 이하, 겹침 없음으로 만듭니다(약 5KB 커짐).
- 펌웨어의 업데이트 루틴은 파티션 크기를 넘는 파일을 거부하므로, `pack`은 결과가 입력 펌웨어보다 크면 멈춥니다(`--allow-larger`로 무시 가능).

## 스테이션 모드 패치 (`patch_station.py`)

M20이 자기 AP를 만드는 대신 **집 공유기에 접속**하도록 하는 패치입니다.

```sh
python3 ntkfw.py unpack SJCAM001.bin work/
python3 patch_station.py work/part0.bin work/part0_sta.bin --ssid '공유기이름' --passphrase '비밀번호'
python3 ntkfw.py pack SJCAM001.bin work/part0_sta.bin new/SJCAM001.bin
```

- 결과 파일에는 SSID와 비밀번호가 평문으로 들어갑니다. 공유하거나 커밋하지 마세요.
- 공유기는 2.4GHz와 WPA2-PSK(AES)여야 합니다.
- 원리: 와이파이 시작 함수(`SetupExe_OnWifiStart`, `0x801d8d70`)는 원래부터 `SysGetFlag(0x8b)`가 1이면 스테이션으로 동작하는 분기를 갖고 있습니다. 하지만 이 값은 UART 디버그 명령(`wifi mode 1`)으로만 바뀌고, 스테이션용 SSID와 비밀번호 버퍼도 비어 있습니다. 패치는 이 함수 안에서 모드를 읽는 곳을 1로 고정하고, 함수 전용 디버그 문자열 자리(`0x803b0e2c`~)에 SSID와 비밀번호를 넣어 그 위치를 가리키게 합니다. 설정값 자체는 건드리지 않으므로, 원본 펌웨어로 되돌리면 흔적이 남지 않습니다.
- 스크립트는 바꾸기 전에 각 위치의 원래 명령어를 확인하고, 다르면 중단합니다(V1.3.1 전용).

## 적용 순서 (안전 절차)

1. **무수정 왕복 테스트**: 아무것도 고치지 않은 `part0.bin`으로 `pack` → SD카드 루트에 `SJCAM001.bin`으로 복사 → 업데이트 → 정상 부팅과 동작 확인.
   이게 통과해야 도구(압축과 체크섬)가 카메라에서도 유효하다고 볼 수 있습니다.
2. 그다음에 실제 수정을 적용합니다.
3. 문제가 생기면 원본 `SJCAM001.bin`으로 SD카드 업데이트를 하면 원래대로 돌아갑니다. 부팅이 되는 한 가능합니다.

SD카드는 FAT32로 포맷하고, 업데이트 중에는 전원을 끊지 마세요. 업데이트가 끝나면 카드에서 `.bin` 파일을 지웁니다.

## 함수·명령 목록

`M20_FUNCTIONS.md`: HTTP 명령 61개, UART 콘솔 명령 400여 개, 이름이 확인된 함수 3,000여 개와 수정 후보를 정리했습니다. 다시 만들려면 `python3 catalog.py work/part0.bin`을 실행합니다(맨 위의 수정 후보 표는 직접 작성한 부분).

- `ANALYSIS.md`: 감시카메라용 개선 항목(자동 와이파이, 자동 녹화, 재접속, 비상 복귀, MJPEG, USB 웹캠, 비트레이트) 분석과 패치 설계
