# SJCAM M20 V1.3.1 펌웨어 함수·명령 목록

`catalog.py`로 원본 펌웨어의 part0(메인 프로그램, `0x80000000`에 적재)에서 자동 생성한 목록입니다. 맨 위의 "수정 후보"만 사람이 정리했습니다.

- 주소는 메모리 주소입니다. 파일 안 위치는 `주소 - 0x80000000`입니다(풀린 `part0.bin` 기준).
- 함수 이름은 펌웨어가 디버그 메시지에 찍는 문자열에서 추정했습니다. 공식 심볼이 아니므로 가끔 틀릴 수 있습니다.
- 패치 방법은 세 가지입니다. ① 상수 값 바꾸기 ② 분기 고정(`스테이션 패치`처럼) ③ 기존 명령 테이블 항목을 다른 함수로 연결하기. 모두 `ntkfw.py pack`으로 다시 포장합니다.

## 수정 후보 (감시카메라 용도 기준)

| 분류 | 함수 / 위치 | 주소 | 바꿀 수 있는 것 | 난이도 |
|---|---|---|---|---|
| 와이파이 | `SetupExe_OnWifiStart` | `0x801d8d70` | AP ↔ 스테이션 선택. **`patch_station.py`로 적용됨** | 완료 |
| 와이파이 | `UINet_WifiInit` / `UINet_SetSSID` / `UINet_SetPASSPHRASE` / `UINet_DHCP_Start` / `UINet_StationStatus_CB` | `0x801c9760` / `0x801c93d8` / `0x801c9320` / `0x801c95dc` / `0x801c9e8c` | 접속 방식, 고정 IP, 재접속 동작 | 중~상 |
| 와이파이 | `WIFI_CliReconnect`(주기 작업, 150틱) | `0x801c81dc` | 끊겼을 때 재접속 주기 | 중 |
| 원격 제어 | HTTP 명령 테이블(20바이트 × 61) | `0x8051b1c8` | 안 쓰는 번호(예: 5001·9002)를 다른 함수에 연결해 **새 명령 추가** | 중 |
| 원격 제어 | `WifiCmd_getQueryData` (명령 처리기) | `0x801cb974` | 응답 형식, 명령 처리 방식 | 상 |
| 실시간 영상 | `RtspNvt_Open` / `RtspNvt_SetParam` | `0x8020fb3c` / `0x8020f788` | RTSP 스트림 해상도·비트레이트·포트 | 중~상 |
| 실시간 영상 | `NetHTTP_StartEncoder` / `ISF_NetHTTP_SetParam` | `0x801ffff8` / `0x801ff9e8` | **HTTP MJPEG 스트림 기능이 들어 있음**(포트 8192 계열). 켜는 조건 분석 필요 | 상 |
| USB 웹캠 | `UVACExe_OnOpen` / `xUvac_ConfigMovieSizeCB` / 콘솔 `mode pcc` | `0x801db2d0` / `0x801db684` | **USB 웹캠(UVC) 모드가 들어 있음**. 해상도·진입 조건 | 중 |
| 녹화 | `MovieExe_OnMovieSize` | `0x801d0208` | 해상도별 설정(비트레이트 표 포함 가능) | 중 |
| 녹화 | `SMediaRec_ChangeParameter` / `VSMediaRec_*` | `0x8021fdd4` | 비트레이트, GOP. 콘솔 `vst gop60/w2m/10fps`가 같은 경로 | 상 |
| 녹화 | `UIFlowWndMovie_OnLoopRecFull` | `0x801b89c4` | 카드가 찼을 때 동작(루프 녹화) | 중 |
| 녹화 | `MovieStamp_*` / `DataStamp_Imprint` | `0x8019f690`~ / `0x80289384` | 날짜·시간 워터마크 위치와 형식 | 중 |
| 표시 | `show_logo` / `hide_logo` | `0x8016dfa4` / `0x8016c258` | 부팅 로고 | 하~중 |
| 오디오 | `aud_setVolume` | `0x802619ec` | 녹음·재생 볼륨 | 하 |
| 화질 | `Get_WDRValue` / `Get_SharpnessValue` | `0x801c4378` / `0x801c43dc` | WDR, 선명도 값 표 | 하 |
| 전원 | `GxPower_*`, `Power_CB` | `0x800d7058`~ / `0x8019bec0` | 자동 꺼짐, 배터리 단계 | 중 |

**건드리면 위험한 것**: `Cmd_filesys_format`(`0x80110660`), `nand` 콘솔 그룹(`erase` 등), PStore 관련 함수, 펌웨어 업데이트(`FwSrv`, `xFwSrvCmd_*`). 데이터가 지워지거나 부팅이 안 될 수 있습니다.

## HTTP 명령 테이블 (`/?custom=1&cmd=N`)

`처리` 열: `UI 이벤트`는 UI 상태머신으로 넘겨 설정을 바꾸는 명령(`par` 사용), `함수`는 직접 처리하는 핸들러 주소입니다. `값1`, `값2`는 표에 있는 나머지 두 값이며 의미는 확인되지 않았습니다.

| cmd | 처리 | 값1 | 값2 |
|---|---|---|---|
| 1001 | UI 이벤트 `0x8000e001` | 2 | 0 |
| 1003 | 함수 `0x801cbef4` | 0 | 0 |
| 2016 | 함수 `0x801cbc60` | 0 | 0 |
| 2009 | 함수 `0x801cbe90` | 0 | 0 |
| 2001 | UI 이벤트 `0x8000e003` | 4 | 0 |
| 2002 | UI 이벤트 `0x8000e002` | 0 | 26 |
| 2003 | UI 이벤트 `0x8000e004` | 0 | 34 |
| 2004 | UI 이벤트 `0x8000e028` | 0 | 30 |
| 1012 | UI 이벤트 `0x8000e029` | 0 | 22 |
| 2006 | UI 이벤트 `0x8000e007` | 0 | 35 |
| 2007 | UI 이벤트 `0x8000e008` | 0 | 36 |
| 2008 | UI 이벤트 `0x8000e00a` | 0 | 37 |
| 2010 | UI 이벤트 `0x8000e00b` | 0 | 145 |
| 2019 | UI 이벤트 `0x8000e02a` | 0 | 39 |
| 1002 | UI 이벤트 `0x8000e000` | 0 | 1 |
| 1006 | UI 이벤트 `0x8000e02b` | 0 | 9 |
| 1007 | UI 이벤트 `0x8000e02c` | 0 | 7 |
| 1008 | UI 이벤트 `0x8000e02d` | 0 | 3 |
| 1009 | UI 이벤트 `0x8000e02e` | 0 | 6 |
| 2005 | UI 이벤트 `0x8000e006` | 0 | 5 |
| 1011 | UI 이벤트 `0x8000e02f` | 0 | 12 |
| 3025 | UI 이벤트 `0x8000e030` | 0 | 61 |
| 5001 | 함수 `0x801cb0a0` | 0 | 0 |
| 3011 | UI 이벤트 `0x8000e01d` | 0 | 70 |
| 3010 | UI 이벤트 `0x8000e01c` | 16 | 70 |
| 3007 | UI 이벤트 `0x8000e019` | 0 | 58 |
| 3003 | UI 이벤트 `0x8000e015` | 0 | 70 |
| 3004 | UI 이벤트 `0x8000e016` | 0 | 70 |
| 3008 | UI 이벤트 `0x8000e01a` | 0 | 60 |
| 3012 | 함수 `0x801cc264` | 0 | 0 |
| 2013 | UI 이벤트 `0x8000e00d` | 0 | 0 |
| 2014 | UI 이벤트 `0x8000e00e` | 0 | 0 |
| 2015 | UI 이벤트 `0x8000e00f` | 8 | 0 |
| 3001 | UI 이벤트 `0x8000e012` | 1 | 0 |
| 3002 | 함수 `0x801cdc34` | 0 | 0 |
| 3005 | UI 이벤트 `0x8000e013` | 0 | 0 |
| 3006 | UI 이벤트 `0x8000e014` | 0 | 0 |
| 3013 | UI 이벤트 `0x8000e01f` | 32 | 0 |
| 3014 | 함수 `0x801cab1c` | 0 | 0 |
| 3015 | 함수 `0x801cd960` | 0 | 0 |
| 3016 | 함수 `0x801ccb70` | 0 | 0 |
| 8001 | 함수 `0x801ccb34` | 0 | 0 |
| 8002 | 함수 `0x801ca930` | 0 | 0 |
| 3017 | 함수 `0x801cbdf4` | 0 | 0 |
| 3018 | UI 이벤트 `0x8000e020` | 0 | 0 |
| 3019 | 함수 `0x801cbd90` | 0 | 0 |
| 3021 | UI 이벤트 `0x8000e021` | 0 | 0 |
| 3022 | 함수 `0x801cbd48` | 0 | 0 |
| 3024 | UI 이벤트 `0x8000e022` | 0 | 0 |
| 3028 | 함수 `0x801cbbf8` | 0 | 0 |
| 3029 | 함수 `0x801cc57c` | 0 | 0 |
| 3030 | 함수 `0x801cc488` | 0 | 0 |
| 4001 | 함수 `0x801cd2fc` | 0 | 0 |
| 4002 | 함수 `0x801ccd20` | 0 | 0 |
| 4003 | 함수 `0x801cc8ac` | 0 | 0 |
| 4004 | 함수 `0x801cc6bc` | 0 | 0 |
| 3027 | 함수 `0x801cc068` | 0 | 0 |
| 3023 | 함수 `0x801cbf58` | 0 | 0 |
| 2021 | UI 이벤트 `0x8000e033` | 0 | 149 |
| 2022 | UI 이벤트 `0x8000e031` | 0 | 14 |
| 9002 | 함수 `0x801cbb90` | 0 | 0 |

## UART 콘솔 명령 (62개 그룹, 402개 명령)

콘솔에서 `그룹 명령 인자` 형식으로 입력합니다(예: `wifi mode 1`). `?` 그룹은 그룹 이름을 찾지 못한 표입니다.

### `user` — user command

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `cmd` | `0x800cd578` | sample code |
| `dump_pool` | `0x800ce4ec` | dump pool |
| `movie %` | `0x800ce6d0` | movie mode test |
| `photo %` | `0x800cf9d0` | photo mode setting |
| `write_err` | `0x800cf994` | write_error |
| `slow_card` | `0x800cf958` | slow_card |
| `card_full` | `0x800cf91c` | card_full |

### `sys` — system command

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `mem %` | `0x800ce2ac` | mem |
| `boot` | `0x800ce270` | boot |
| `shutdown` | `0x800ce1e8` | shutdown |
| `sleep` | `0x800cd544` | sleep |
| `wakeup` | `0x800cd510` | wakeup |
| `disp %` | `0x800cf284` | disp setting |
| `aout %` | `0x800cf194` | aout setting |
| `sensor %` | `0x800ceea0` | sensor setting |
| `tm %` | `0x800cee30` | time mark |

### `key` — key command

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `power` | `0x800ce0a0` | power key |
| `delete` | `0x800ce058` | delete key |
| `menu` | `0x800ce0e8` | menu key |
| `mode` | `0x800ce010` | mode key |
| `playback` | `0x800cdfc8` | playback key |
| `movie` | `0x800cdf80` | movie key |
| `up` | `0x800cdf38` | up key |
| `down` | `0x800cdef0` | down key |
| `right` | `0x800cdea8` | right key |
| `left` | `0x800cde60` | left key |
| `enter` | `0x800cde18` | enter key |
| `zoomin` | `0x800cddd0` | zoomin key pressed |
| `zoomout` | `0x800cdd88` | zoomout key pressed |
| `zoominrel` | `0x800cdd40` | zoomin key released |
| `zoomoutrel` | `0x800cdcf8` | zoomout key released |
| `zoomrel` | `0x800cdcb0` | zoom key released |
| `shutter1` | `0x800cdc68` | shutter1 key pressed |
| `shutter2` | `0x800ce17c` | suutter2 key pressed |
| `shutter1rel` | `0x800cdc20` | shutter1 key released |
| `shutter2rel` | `0x800cdbd8` | shutter2 key released |
| `i` | `0x800ce130` | i key pressed |
| `next` | `0x800cdb90` | next key |
| `select` | `0x800cdb48` | select key |
| `cut %` | `0x800cdae8` | cut key |

### `mode` — mode switch

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `main` | `0x800cda70` | main mode |
| `photo` | `0x800cd9f8` | photo mode |
| `movie` | `0x800cd980` | movie mode |
| `playback` | `0x800cd908` | playback mode |
| `msdc` | `0x800cd890` | msdc mode |
| `sidc` | `0x800cd4dc` | sidc mode |
| `pcc` | `0x800cd818` | pcc mode |
| `sleep` | `0x800cd7a0` | sleep mode |
| `lview %` | `0x800cd5ac` | live view mode setting |

### `nsys` — system related cmd

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dimage %` | `0x800cd6f4` | image cmd |
| `dvideo %` | `0x800cd638` | video cmd |
| `dsysdma` | `0x800cd144` | system DMA cmd |

### `wifi` — wifi command

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `site` | `0x800ce9fc` | wifi site survey |
| `p2pscan` | `0x800ce9b0` | p2p scan |
| `p2pcon %d` | `0x800ce964` | p2p connect |
| `discon` | `0x800ce234` | disconnect |
| `mode %d` | `0x800ce8e8` | wifi mode 0:ap 1:station 2:p2pdev |
| `ssid %` | `0x800ce86c` | wifi set SSID |
| `pass %` | `0x800ce7f4` | wifi set PASSPHRASE |
| `ping %` | `0x800ce774` | wifi ping |

### `msdcnvt` — MsdcNvt Utility

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `off` | `0x800e9050` | force unplug. |

### `ipc` — NvtIPC

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dump` | `0x800d6e0c` | dump ipc info |
| `close` | `0x800d6de0` | close ipc |

### `dx` — driver extern debug using

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `lcd %` | `0x800c9540` | lcd relay command |
| `tv %` | `0x800c94fc` | tv relay command |
| `hdmi %` | `0x800c94b8` | hdmi relay command |
| `lcd2 %` | `0x800c9474` | lcd2 relay command |
| `snr1 %` | `0x800c93dc` | sensor1 relay command |
| `snr2 %` | `0x800c9344` | sensor2 relay command |

### `gxtimer` — GxTimer

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dump` | `0x801f2078` | Dump GxTimer status |

### `isf` — image flow

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dump` | `0x801f9e54` | Dump current status |
| `dump2` | `0x801f9e28` | Dump current status |
| `dump3` | `0x801f9dfc` | Dump current status |

### `NvtUser` — NvtUser cmd

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dump` | `0x800e868c` | dump event |

### `rtspnvt` — RtspNvt

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dv0` | `0x802132bc` | dump video bitstream when starting to play |
| `dv1` | `0x80213260` | stop dump video bitstream |
| `dump` | `0x80212ec4` | dump information that must in running client |
| `aud %` | `0x80212e04` | support audio or not |
| `pause` | `0x80212da4` | test pause |
| `resume` | `0x80212d44` | test resume |

### `smrec` — smedia rec module

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `1920` | `0x80231a34` | set to 1920 |
| `640` | `0x802319c0` | set to 640 |
| `cal` | `0x80232774` | cal sec |
| `ccut` | `0x80232b60` | close cut msg |
| `cdrop` | `0x80232aa0` | close drop msg |
| `cfile` | `0x80232a40` | close file msg |
| `cfsobj` | `0x80232b00` | close fs obj msg |
| `cmust` | `0x80231e9c` | close must msg |
| `caudmsg` | `0x80231dc4` | close aud msg |
| `crcvy` | `0x80231e30` | close recovery msg |
| `chkro` | `0x802326e8` | check all ro |
| `chkbuf` | `0x80232060` | check if media buf be overwrited |
| `calcsec` | `0x80232640` | calc sec |
| `calclast` | `0x80232588` | calc last |
| `cutnow` | `0x8023254c` | CUT now |
| `delf` | `0x8023202c` | delete file testing |
| `disk2sec` | `0x80231fdc` | disk2sec |
| `dumpfdb` | `0x80231fa0` | dump filedb |
| `dumpmem` | `0x80231f74` | dump mem |
| `ext20` | `0x80231f44` | extend crash 20 sec |
| `ext` | `0x80232834` | extend crash |
| `fakeslow` | `0x80231f08` | fake slow |
| `gt` | `0x80232904` | get time |
| `nr` | `0x802324d4` | test NR |
| `lastr` | `0x80231ecc` | set now and last Readonly |
| `ocut` | `0x80232b90` | open cut msg |
| `omust` | `0x80231e6c` | open must msg |
| `odrop` | `0x80232ad0` | open drop msg |
| `ofsobj` | `0x80232b30` | open fs obj msg |
| `ofile` | `0x80232a70` | open file msg |
| `orcvy` | `0x80231df4` | open recovery msg |
| `oaudmsg` | `0x80231d94` | open aud msg |
| `proc` | `0x80231d24` | test proc end |
| `rawe` | `0x80231be8` | RAW enc |
| `rawll` | `0x80231c50` | raw encode all path |
| `savethm` | `0x80232510` | SAVE thumb and screen |
| `setend` | `0x80231b68` | set endchar to CD |
| `slowstop` | `0x80231b20` | set slowstop to test |
| `st %s` | `0x80232974` | set time |
| `showmdat` | `0x8023289c` | show mdat all |
| `setcr` | `0x802327cc` | set crash |
| `startw` | `0x80231938` | start to write bs |
| `update` | `0x80232738` | update setting |
| `write2` | `0x80232360` | write 2 new file |
| `ulaw` | `0x80231904` | show ulaw |
| `vtrigok` | `0x80231adc` | set vtrigok |
| `yloft960` | `0x80231978` | y lineoffset 960 |

### `vs` — vsmedia rec module

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `ocut` | `0x8025b2a4` | open cut msg |
| `ccut` | `0x8025b274` | close cut msg |
| `omust` | `0x8025a9b8` | open must msg |
| `cmust` | `0x8025a988` | close must msg |
| `ofsobj` | `0x8025b244` | open fs obj msg |
| `cfsobj` | `0x8025b214` | close fs obj msg |
| `ofile` | `0x8025b1e4` | open file msg |
| `cfile` | `0x8025b1b4` | close file msg |
| `st %s` | `0x8025b0e8` | set time |
| `gt` | `0x8025b078` | get time |
| `showmdat` | `0x8025b028` | show mdat all |
| `ext` | `0x8025afc0` | extend crash |
| `setcr` | `0x8025af4c` | set crash |
| `cal` | `0x8025aef4` | cal sec |
| `1920` | `0x8025ae84` | set to 1920 |
| `640` | `0x8025ae10` | set to 640 |
| `update` | `0x8025add4` | update setting |
| `chkro` | `0x8025ad84` | check all ro |
| `calcsec` | `0x8025acdc` | calc sec |
| `calclast` | `0x8025ac24` | calc last |
| `write2` | `0x8025a47c` | write 2 new file |
| `nr` | `0x8025ab20` | test NR |
| `cutnow` | `0x8025a924` | CUT now |
| `rawe` | `0x8025ab98` | RAW enc |
| `savethm` | `0x8025ab5c` | SAVE thumb and screen |
| `vtrigok` | `0x8025a8e8` | set vtrigok |
| `lastr` | `0x8025a8ac` | set now and last Readonly |
| `oamust` | `0x8025a87c` | open aud msg |
| `camust` | `0x8025a84c` | close aud msg |
| `delf` | `0x8025a818` | delete file testing |
| `ext20` | `0x8025a7e8` | extend crash 20 sec |

### `?` — 

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `rawll` | `0x8025a718` | raw encode all path |
| `stopfile` | `0x8025a6ac` | stop path 0 |
| `slowstop` | `0x8025a62c` | set slowstop to test |
| `disk2sec` | `0x8025a5dc` | disk2sec |
| `faketout` | `0x8025a5a0` | fake encode timeout |
| `fakeslow` | `0x8025a564` | fake slow |
| `dumpfdb` | `0x8025a528` | dump filedb |
| `cutnow` | `0x8025a924` | cut now |
| `emrend` | `0x8025a4b0` | emr end now! |

### `vst` — vidstrm rec module

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `sp0` | `0x802600f4` | stop path 0 |
| `rp0` | `0x802600b4` | resume path 0 |
| `sp1` | `0x80260074` | stop path 1 |
| `rp1` | `0x80260034` | resume path 1 |
| `sp2` | `0x8025fff4` | stop path 2 |
| `rp2` | `0x8025ffb4` | resume path 2 |
| `st %s` | `0x802609b4` | set time |
| `gt` | `0x80260944` | get time |
| `omust` | `0x80260914` | open must msg |
| `cmust` | `0x802608e4` | close must msg |
| `saud` | `0x802608a8` | suspend audio |
| `raud` | `0x8026086c` | resume audio |
| `720` | `0x80260620` | change path0 to 1280x720 |
| `gop60` | `0x8026080c` | change gop 60 |
| `gop15` | `0x802607ac` | change gop 15 |
| `rec` | `0x8026075c` | record |
| `stop` | `0x80260714` | stop |
| `show` | `0x802606cc` | show msg |
| `p0m` | `0x80260594` | path0 change to codec1 mjpg |
| `p0h` | `0x80260508` | path0 change to codec0 h264 |
| `p1m` | `0x8026047c` | path1 change to codec1 mjpg |
| `p1h` | `0x802603f0` | path1 change to codec0 h264 |
| `10fps` | `0x80260364` | path1 10 fps |
| `28fps` | `0x802602d8` | path0 28 fps |
| `5fps` | `0x8026024c` | path1 5fps |
| `dumpmem` | `0x802606a0` | dump memory info |
| `w1m` | `0x802601c0` | path1 tbr 1MB |
| `w2m` | `0x80260134` | path1 tbr 2MB |
| `a8k` | `0x8025ff3c` | audio SR 8kB |
| `a32k` | `0x8025fec4` | audio SR 32kB |
| `getcury` | `0x8025fe44` | get current yaddr |
| `afull` | `0x8025fdfc` | audio buff full test |

### `audio` — audio command

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dumpinfo` | `0x802622f0` | dump audio control info |

### `cwp` — CPU write protection

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `on %` | `0x8001977c` | Start protecting |
| `off` | `0x800194e4` | Stop protecting |
| `on2 %` | `0x800196d4` | Start protecting |
| `off2` | `0x80019480` | Stop protecting |
| `dump` | `0x8001933c` | Dump current status |

### `mwp` — DMA write protection

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `on` | `0x800199d4` | Start protecting |
| `off` | `0x8001995c` | Stop protecting |
| `user %` | `0x80019a50` | User configures protected address |
| `dump` | `0x80019928` | Dump current status |

### `usage` — CPU/DMA Usage

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dmacfg %` | `0x8001988c` | Configure interval time(ms) to measure DMA usage |
| `dmastart` | `0x80019858` | Start DMA measuring usage |
| `dmastop` | `0x80019824` | Stop DMA measuring usage |
| `cpucfg %` | `0x80019638` | Configure interval time(ms) to measure CPU usage |
| `cpustart` | `0x80019604` | Start CPU measuring usage |
| `cpustop` | `0x800195d0` | Stop CPU measuring usage |

### `gprof` — gProf

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `start` | `0x80019580` | start |
| `stop` | `0x80019544` | stop |
| `dump` | `0x80019ca4` | dump result |

### `ide` — ide command

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dumpinfo` | `0x800407b4` | dump ide info |

### `lvds` — lvds debug info

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `debug1` | `0x8004bc68` | dump lvds-1 control info |
| `debug2` | `0x8004d2e8` | dump lvds-2 control info |

### `nand` — nand test command

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `erase` | `0x80077148` | erase nand area except loader |
| `dumpspare` | `0x8007711c` | dump all nand spare area on UART |
| `dump` | `0x800770f0` | display nand information |
| `dumpbin` | `0x80077084` | dump all nand area |
| `rwchkFAT` | `0x80076f98` | read write test FAT area |
| `readchkall` | `0x80075998` | read check all NAND area |
| `supTabVer` | `0x80074690` | support table list version |
| `erasechkall` | `0x80075760` | erase write and read all nand area |
| `erasechkFAT` | `0x800756a0` | erase write and read FAT nand area |

### `sdio` — sdio command

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dumpinfo` | `0x80084c20` | dump sdio Misc info |

### `sdio3` — sdio3 command

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dumpinfo` | `0x80097478` | dump sdio3 Misc info |

### `drvdump` — Dump driver information

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `liveview` | `0x80026ccc` | Dump in liveview |
| `capture` | `0x80026a8c` | Dump in capture |
| `playback` | `0x80026c6c` | Dump in playback |
| `usb` | `0x80026c3c` | Dump in USB |
| `sleep` | `0x80026c0c` | Dump in sleep |
| `sd1_fast` | `0x80026bdc` | Dump in SD1 high speed |
| `sd1_slow` | `0x80026bac` | Dump in SD1 low speed |
| `sd2_fast` | `0x80026b7c` | Dump in SD2 high speed |
| `sd2_slow` | `0x80026b4c` | Dump in SD2 low speed |
| `all` | `0x80026b1c` | Dump current status in any status |

### `cpu` — CPU status

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `clk` | `0x800270e0` | Dump clock of CPU |

### `dma` — DMA status

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `clk` | `0x8002913c` | Dump clock of DMA |
| `eclk` | `0x80028fb4` | Dump engine's clock status |

### `sensor` — sensor module

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `chgmode %` | `0x80166070` | change sensor mode(sensor id, sensor mode) |
| `getmode %` | `0x80165ff4` | get current sensor mode status(sensor id) |
| `getstatus %` | `0x80165f7c` | get specified sensor mode status(sensor id, sensor mode) |
| `setexpt %` | `0x80165ebc` | set specified exposure time(sensor id, frame, line, pixel) |
| `setgain %` | `0x80165dfc` | set specified gain(snesor id, data1(H), data2(H), data3(H)) |
| `setreg %` | `0x80165d44` | set specified register(sensor id, reg(H), data1(H), data0(H), data length) |
| `getreg %` | `0x80165c94` | get specified register(sensor id, reg(H)) |
| `setvx1gpio %` | `0x80165bec` | set vx1 gpio (deviceId(0=THCV235, 1=THCV231), gpioId(0=TXGPIO3, 1=TXGPIO4), value) |
| `dumpvx1 %` | `0x80165c4c` | dump vx1 register |

### `ae` — auto exposure

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `lock %` | `0x80271040` | lock ae(ae id, flag(1:lock, 0:unlock) |
| `islock %` | `0x80271000` | get ae lock flag(ae id) |
| `start %` | `0x80270fbc` | start ae(ae id) |
| `pause %` | `0x80270f78` | pause ae(ae id) |
| `resume %` | `0x80270f38` | resume ae(ae id) |
| `set %` | `0x802711f4` | set ae(ae id, expo time, iso) |
| `uart %` | `0x80271114` | enable/disable ae uart msg(ae id, flag(1:enable, 0:disable)) |
| `osd %` | `0x80271184` | enable/disable ae osd msg(ae id, flag(1:enable, 0:disable)) |
| `miso %` | `0x8027108c` | manual iso(ae id, manual flag(1:enable, 0:disable), iso(25, 50, 100...) |

### `awb` — auto white balance

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `lock %` | `0x80285fb0` | lock awb(awb id, flag(1:lock, 0:unlock) |
| `islock %` | `0x80285f70` | get awb lock flag(awb id) |
| `start %` | `0x80285f2c` | start awb(awb id) |
| `pause %` | `0x80285ee8` | pause awb(awb id) |
| `resume %` | `0x80285ea8` | resume awb(awb id) |
| `set %` | `0x80285da8` | set awb gain(id, rgain, ggain, bgain) |
| `uart %` | `0x80285e38` | enable/disable awb uart msg(awb id, flag(1:enable, 0:disable)) |

### `dispsrv` — DispSrv

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dump` | `0x80183db0` | Dump status |
| `dumpdisp` | `0x80183ba8` | Dump current frame buffer |
| `dumpsrc` | `0x8018399c` | Dump all source buffer |
| `fps` | `0x80183920` | Measure frame rate |

### `fslinux` — File System Linux Version

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `format` | `0x80294224` | Format the disk |
| `benchmark` | `0x80294260` | Access speed test |
| `showinfo` | `0x8029414c` | Show disk info |

### `filesys` — File System

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `format` | `0x80110660` | Format the disk |
| `benchmark` | `0x801105b8` | Access speed test |
| `showinfo` | `0x8011048c` | Show disk info |
| `dumpfree` | `0x80110458` | Dump each free sections |
| `wrperf %` | `0x801103d4` | filesys wrperf [bEnable] [bDumpLog] |
| `w %` | `0x801101cc` | Write a word to SD card |

### `fwsrv` — FwSrv

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dumpuitron` | `0x800e42f4` | Dump uITRON from EMB |
| `dumpecos` | `0x800e3fbc` | Dump eCos from EMB |

### `gxkey` — GxKey

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dump` | `0x800d0608` | Dump key value |

### `gxpower` — GxPower

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `autooffen %` | `0x800d7a00` | enable auto power off, param value is 1 or 0 |
| `setofftime %` | `0x800d79b4` | set auto power off time, param is auto off time(s) |

### `?` — 

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `battchange %` | `0x800d78c0` | callback battery level changed event, param value is battery level |
| `chargecurrent %` | `0x800d7968` | set charge current, 0 is low, 1 is medium, 2 is high |
| `chargeen %` | `0x800d791c` | enable battery charge, param value is 1 or 0 |

### `sxt` — SxTimer

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dump` | `0x80025664` | dump all entries |

### `ver` — Library version

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dump` | `0x80025a3c` | Dump all used libs version |

### `gxvideo` — video device output control

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dump` | `0x80178bf8` | dump info |
| `bon` | `0x80178ad0` | backlight turn on |
| `blv %` | `0x80178ba0` | backlight set level |
| `boff` | `0x80178a98` | backlight turn off |

### `ecos` — eCos Utility

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `open` | `0x800d1538` | read A:\ECOS\FW96660T.bin to start |
| `close` | `0x800d150c` | stop and close eCos |
| `uart` | `0x800d1488` | init uart2 |
| `dump` | `0x800d1448` | dump info |
| `p %` | `0x800d1294` | printf from eCos |

### `lens` — lens command

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `lis` | `0x8029c00c` | zoom init |
| `lie` | `0x8029bfd4` | focus and iris init |
| `lretract` | `0x8029bc84` | lens retract |
| `rpi` | `0x8029b2bc` | check zpi and fpr |
| `gzs` | `0x8029b29c` | check current zoom position |

### `PStore` — PStore cmd

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `format %` | `0x802aae04` | fmt to default 64 sec |
| `showinfo` | `0x802aabc8` | show info |
| `dump` | `0x802aab5c` | dump section |

### `rsc` — rolling shutter

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `rscsdo %` | `0x802b2778` | rsc set debug option |
| `sensorinfor ` | `0x802b273c` | rsc StartLine and EndLine |
| `saveraw %` | `0x802b26e0` | save 2dlut raw(RSC Id , STATUS) |

### `ipl` — image pipeline module

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `setdzoom %` | `0x802d3094` | set digital zoom(ipl id, index) |
| `setdzoomin %` | `0x802d2fcc` | set digital zoom in(ipl id) |
| `setdzoomout %` | `0x802d2f04` | set digital zoom out(ipl id) |
| `setimepath %` | `0x802d2d58` | set ime path enable or not(ipl id, path id, path1 en, path2 en, path3 en) |
| `getimepath %` | `0x802d22d4` | get ime path status(ipl id) |
| `getcurmode %` | `0x802d2268` | get ipl current mode(ipl id) |
| `getcurbuf %` | `0x802d21f4` | get ipl current buffer(ipl id) |
| `dumpbuf %` | `0x802d317c` | dump ipl buffer allocation(ipl id) |
| `setdmapause %` | `0x802d2cf0` | set ipl dma pause |
| `setdmaresume %` | `0x802d2c88` | set ipl dma resume |
| `setsleep %` | `0x802d2c20` | enter sleep mode(ipl id) |
| `setwakeup %` | `0x802d2bb8` | exit sleep mode(ipl id) |
| `setimgratio %` | `0x802d2a04` | set crop ratio(ipl id, crop ratio) |
| `setdis %` | `0x802d29a8` | set dis on/off(ipl id, on/off) |
| `getcapmaxrawinfo %` | `0x802d2150` | get cap max raw status(ipl id) |
| `mtrig %` | `0x802d31bc` | manual trigger IPL |
| `saveraw %` | `0x802d27bc` | save sie output raw |
| `savemem %` | `0x802d26b0` | save memory (addr, width, height) |
| `saveca %` | `0x802d2518` | save ca data |
| `dumpDT` | `0x802d2124` | dump time mark, only valid at IPH_DUMP_TIME = ENABLE |
| `dumpT %` | `0x802d20ac` | dump vd & proc time(ipl id) |
| `dumptriginfo` | `0x802d2080` | dump trigger information |
| `dumpstatus %` | `0x802d2030` | dump ctrl status(ipl id, parameter idx) |
| `dumpflag` | `0x802d1fac` | dump ctrl flag |
| `dumpiplinfo` | `0x802d1f80` | dump ipl information |
| `setflip %d` | `0x802d310c` | set ipl flip(ipl id, 0:w/o flip 1:H flip 2:V flip 3:H&V flip |

### `iqs` — image qualiy module

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `ie %` | `0x80315820` | set image effect(ipl id, index) |
| `sat %` | `0x803156fc` | set image saturation(ipl id, value:0~100) |
| `sharp %` | `0x803155d8` | set image sharpness(ipl id, value:0~100) |
| `cont %` | `0x803154b4` | set image contrast(ipl id, value:0~100) |
| `Hue %` | `0x803153ac` | set image HUE(ipl id, value:0~360) |
| `ucset %` | `0x80315270` | user layer IQ adjustment(ipl id, ItemId, value) |
| `ucdump %` | `0x80315238` | dump IQUC |
| `dumpreg %` | `0x8031520c` | dump preview register |

### `af` — auto focus

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `lock %` | `0x8031cad8` | lock af(af id, flag(1:lock, 0:unlock) |
| `islock %` | `0x8031ca98` | get af lock flag(af id) |
| `start %` | `0x8031ca54` | start af(af id) |
| `pause %` | `0x8031ca10` | pause af(af id) |
| `resume %` | `0x8031c9d0` | resume af(af id) |

### `cap` — capture module

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dump buf` | `0x8036b250` | dump capture buffer |
| `getimgnor %` | `0x8036ad08` | snap shot(format(0:none, 1:raw, 2:jpg, 3:raw+jpg), width, height, sensor ID) |
| `getimghdr %` | `0x8036a990` | hdr shot(format(0:none, 1:raw, 2:jpg, 3:raw+jpg), width, height) |
| `getimghs %` | `0x8036a8d0` | hs shot(format(0:none, 1:raw, 2:jpg, 3:raw+jpg), width, height) |
| `getimgeburst %` | `0x8036a7e4` | encode burst shot(format(0:none, 1:raw, 2:jpg, 3:raw+jpg), width, height, sensor ID) |
| `getimglast %` | `0x8036b058` | last burst shot(0: start, 1:end) |
| `getimgmfhdr %` | `0x8036ac24` | multi frame hdr(format(0:none, 1:raw, 2:jpg, 3:raw+jpg), width, height) |
| `getimgmfas %` | `0x8036ab40` | multi frame anti-shake(format(0:none, 1:raw, 2:jpg, 3:raw+jpg), width, height) |
| `getimgsbs %` | `0x8036a5ac` | Dual SideBySide sensor(format(0:none, 1:raw, 2:jpg, 3:raw+jpg), width, height) |
| `showmsg %` | `0x8036a500` | show debug message 0/1(disable/enable) |

### `photo` — photo task

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dumpinfo` | `0x8036cf00` | dump photo task information |

### `ker` — OS

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dump` | `0x80010ab8` | Dump kernel all status |
| `dumpmem` | `0x80010a4c` | Dump code, stack and heap memory region |
| `dumptask` | `0x80010a8c` | Dump all task's status |
| `dumpstack %` | `0x800109e8` | Dump one task's stack |

### `mem` — Memory access

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `w %` | `0x800107f4` | Write a word into memory |
| `r %` | `0x80010938` | Read a region of memory |
| `fill %` | `0x80010888` | Fill a region of memory |
| `dump %` | `0x80010694` | Dump a region of memory to a file |
| `dumpcode` | `0x8001034c` | Dump firmware code region to a bin file |

### `hwclk` — check RTC clock function

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `get` | `0x8001510c` | get current time |
| `set %` | `0x80015170` | set current time |

### `shdr` — sensor HDR

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `dumpin` | `0x8037da7c` | dump RHE input 2 buffers |
| `chgmode %` | `0x8037d980` | change mode(0: dark mode, 1: bright mode, 2: blending mode) |
| `chgratio %` | `0x8037d940` | change AE ratio(0: 1x, 2: 4x, 4: 16x) |
| `chgbg %` | `0x8037d8f0` | change Band Gain |

### `?` — 

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `MsdcNvtCb_PhotoBegin` | `0x801a1d84` | MsdcNvtCb_GetDisplaySettings2 |
| `MsdcNvtCb_GetDisplayCurrentBufSel` | `0x801a1adc` | MsdcNvtCb_CaptureJpgWidthGetInfo |

### `?` — 

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `MsdcNvtCb_AdjGetNumOfItem` | `0x801a20e4` | MsdcNvtCb_AdjGetItemsDesc |
| `MsdcNvtCb_AdjSetItemsData` | `0x801a1f54` | MsdcNvtCb_AdjGetItemsData |

### `?` — 

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `MsdcNvtCb_UpdFwGetInfo` | `0x801a22a0` | MsdcNvtCb_UpdFwGetWorkMem |
| `MsdcNvtCb_UpdFwSetBlock` | `0x801a2758` | MsdcNvtCb_UpdFwAllInOne_Step1 |

### `?` — 

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `!(@` | `0x801b1b04` | (@ |

### `?` — 

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `MsdcNvtCb_DispCfgGet` | `0x8029ff68` | MsdcNvtCb_DispVdoBufGetCurrIdx |
| `MsdcNvtCb_DispEngineEnableSet` | `0x8029f9b4` | MsdcNvtCb_DispPaletteGet |
| `MsdcNvtCb_DispPaletteSet` | `0x8029fd54` | MsdcNvtCb_DispGammaEnableSet |
| `MsdcNvtCb_DispGammaTblGetSize` | `0x8029eaf4` | MsdcNvtCb_DispIcstGetInfo |
| `MsdcNvtCb_DispIcstSet` | `0x8029f8f8` | MsdcNvtCb_DispIcstGet |
| `MsdcNvtCb_DispSaturationGetInfo` | `0x8029f7a0` | MsdcNvtCb_DispSaturationSet |
| `MsdcNvtCb_DispContrastGetInfo` | `0x8029f644` | MsdcNvtCb_DispContrastSet |
| `MsdcNvtCb_DispBrightnessGetInfo` | `0x8029f4b4` | MsdcNvtCb_DispBrightnessSet |
| `MsdcNvtCb_DispGammaRTblSetTbl` | `0x8029f364` | MsdcNvtCb_DispGammaRTblGetTbl |
| `MsdcNvtCb_DispGammaGTblSetTbl` | `0x8029f214` | MsdcNvtCb_DispGammaGTblGetTbl |
| `MsdcNvtCb_DispGammaBTblSetTbl` | `0x8029f0c4` | MsdcNvtCb_DispGammaBTblGetTbl |
| `MsdcNvtCb_DispHsiTblGetSize` | `0x8029eab4` | MsdcNvtCb_DispHsiHTblSetTbl |
| `MsdcNvtCb_DispHsiHTblGetTbl` | `0x8029eecc` | MsdcNvtCb_DispHsiSTblSetTbl |
| `MsdcNvtCb_DispHsiSTblGetTbl` | `0x8029ed7c` | MsdcNvtCb_DispHsiITblSetTbl |
| `MsdcNvtCb_DispHsiITblGetTbl` | `0x8029ec2c` | MsdcNvtCb_DispSetActiveIde |

### `?` — 

| 명령 | 핸들러 | 설명 |
|---|---|---|
| `MsdcNvtCb_FileGetWorkingMemory` | `0x802a045c` | MsdcNvtCb_FileCopyPcToDevice |
| `MsdcNvtCb_FileCopyDeviceToPc` | `0x802a04e8` | MsdcNvtCb_FileDeleteDeviceFile |

## 이름이 확인된 함수 (3073개, 모듈별)

디버그 문자열로 추정한 이름입니다. 일부는 함수가 아니라 태스크·플래그 ID입니다.

<details><summary><code>AACD</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80375ee0` | `AACD_Init` |

</details>

<details><summary><code>adc</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80045d0c` | `adc_waitInterrupt` |

</details>

<details><summary><code>add</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801ca168` | `add_acl_table` |

</details>

<details><summary><code>AE</code> (19)</summary>

| 주소 | 이름 |
|---|---|
| `0x80270020` | `AE_GetCtrlObj` |
| `0x8027011c` | `AE_HDRNotifyEvent` |
| `0x802701a4` | `AE_Module_Lock` |
| `0x80270228` | `AE_Module_Unlock` |
| `0x80270294` | `AE_Pause` |
| `0x80270378` | `AE_Resume` |
| `0x80270440` | `AE_Start` |
| `0x80270510` | `AE_Flag_Lock` |
| `0x80270594` | `AE_Flag_Unlock` |
| `0x80270600` | `AE_IsLock` |
| `0x80270984` | `AE_Lock` |
| `0x80270aac` | `AE_IsPause` |
| `0x80270b64` | `AE_GetTaskObj` |
| `0x80270b64` | `AE_TrigEvent` |
| `0x80270c2c` | `AE_Close` |
| `0x80270d18` | `AE_Open` |
| `0x8031d9fc` | `AE_getPrvTab` |
| `0x8031e180` | `AE_getCapTab` |
| `0x8031fb18` | `AE_Process` |

</details>

<details><summary><code>AEAlg</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x8026f3a0` | `AEAlg_GetPrvSmoothRatio` |
| `0x8026f5b4` | `AEAlg_Allot` |
| `0x8026f7f0` | `AEAlg_Converge` |
| `0x80376040` | `AEAlg_GetCurveNode` |
| `0x803760c8` | `AEAlg_CalEV` |
| `0x803760c8` | `AEAlg_GenCurve` |

</details>

<details><summary><code>AF</code> (19)</summary>

| 주소 | 이름 |
|---|---|
| `0x80318f68` | `AF_SetAlgSearchMode` |
| `0x80319324` | `AF_Init_Alg1` |
| `0x803195cc` | `AF_Process` |
| `0x803195cc` | `AF_SingleWinProcess_Alg1` |
| `0x803195cc` | `AF_SingleWinProcess_Alg2` |
| `0x8031b58c` | `AF_Init_Alg2` |
| `0x8031bbbc` | `AF_GetCtrlObj` |
| `0x8031bc0c` | `AF_CAFProcess` |
| `0x8031bd0c` | `AF_Module_Unlock` |
| `0x8031beb4` | `AF_Module_Lock` |
| `0x8031bf28` | `AF_Pause` |
| `0x8031c014` | `AF_Resume` |
| `0x8031c0e8` | `AF_Start` |
| `0x8031c1b4` | `AF_IsLock` |
| `0x8031c258` | `AF_Lock` |
| `0x8031c330` | `AF_WaitIdle` |
| `0x8031c704` | `AF_Close` |
| `0x8031c7e0` | `AF_Open` |
| `0x8031c914` | `AF_TrigEvent` |

</details>

<details><summary><code>af</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8031be00` | `af_start` |

</details>

<details><summary><code>AFALG</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x803195cc` | `AFALG_MultiWinProcess` |
| `0x8031b92c` | `AFALG_SetParam` |

</details>

<details><summary><code>AppDisp</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8017d800` | `AppDisp_CalcImgSizebyRatio` |

</details>

<details><summary><code>AppMem</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801c771c` | `AppMem_Alloc` |

</details>

<details><summary><code>aud</code> (67)</summary>

| 주소 | 이름 |
|---|---|
| `0x80261910` | `aud_setGain` |
| `0x802619ec` | `aud_setVolume` |
| `0x80261ac4` | `aud_setTotalVolLevel` |
| `0x80261b44` | `aud_setParameter` |
| `0x80261cf0` | `aud_setOutput` |
| `0x80261dd0` | `aud_getTransceiveObject` |
| `0x8026231c` | `aud_setFeature` |
| `0x802625ec` | `aud_setExtCodec` |
| `0x80262780` | `aud_close` |
| `0x8026298c` | `aud_open` |
| `0x80262f88` | `aud_isChangeSampleRateAllow` |
| `0x802632f8` | `aud_switchCodec` |
| `0x8026359c` | `aud_init` |
| `0x8026359c` | `aud_initCodec` |
| `0x80265328` | `aud_setResampleInfoRx` |
| `0x80265364` | `aud_playbackRx` |
| `0x802653a0` | `aud_getCurrentBufferFromQueueRx` |
| `0x80265400` | `aud_getDoneBufferFromQueueRx` |
| `0x80265460` | `aud_isBufferQueueFullRx` |
| `0x802654c0` | `aud_addBufferToQueueRx` |
| `0x802655bc` | `aud_resetBufferQueueRx` |
| `0x80265618` | `aud_getConfigRx` |
| `0x80265720` | `aud_setConfigRx` |
| `0x802659f0` | `aud_setFeatureRx` |
| `0x80265b74` | `aud_setChannelRx` |
| `0x80265c14` | `aud_recordPresetRx` |
| `0x80265cfc` | `aud_openRx` |
| `0x80265db0` | `aud_setSamplingRateRx` |
| `0x80265e6c` | `aud_resumeRx` |
| `0x80265f14` | `aud_pauseRx` |
| `0x80266004` | `aud_stopRx` |
| `0x80266230` | `aud_recordRx` |
| `0x80266664` | `aud_addToQueue` |
| `0x80266780` | `aud_isQueueFull` |
| `0x80266808` | `aud_resetQueue` |
| `0x80266918` | `aud_getCurQueue` |
| `0x802669f4` | `aud_getDoneQueue` |
| `0x80266b98` | `aud_isLegalReample` |
| `0x80266c5c` | `aud_recordTx1` |
| `0x80266c98` | `aud_recordPresetTx1` |
| `0x80266cd4` | `aud_setResampleInfoTx1` |
| `0x80266ec8` | `aud_setSamplingRateTx1` |
| `0x80267054` | `aud_setConfigTx1` |
| `0x80267268` | `aud_playbackTx1` |
| `0x802676ac` | `aud_resumeTx1` |
| `0x8026780c` | `aud_addBufferToQueueTx1` |
| `0x80267e64` | `aud_getConfigTx1` |
| `0x80267fac` | `aud_pauseTx1` |
| `0x802680a4` | `aud_stopTx1` |
| `0x80268390` | `aud_setFeatureTx1` |
| `0x802684e4` | `aud_setChannelTx1` |
| `0x802685ac` | `aud_openTx1` |
| `0x80268774` | `aud_getConfigTx2` |
| `0x80268800` | `aud_recordTx2` |
| `0x8026883c` | `aud_recordPresetTx2` |
| `0x802688fc` | `aud_addBufferToQueueTx2` |
| `0x80268f54` | `aud_setConfigTx2` |
| `0x802691c0` | `aud_setFeatureTx2` |
| `0x802692b4` | `aud_setChannelTx2` |
| `0x8026937c` | `aud_setResampleInfoTx2` |
| `0x8026957c` | `aud_setSamplingRateTx2` |
| `0x80269708` | `aud_resumeTx2` |
| `0x80269770` | `aud_pauseTx2` |
| `0x80269838` | `aud_stopTx2` |
| `0x802699d0` | `aud_isLegalReample2` |
| `0x802699d0` | `aud_playbackTx2` |
| `0x80269ddc` | `aud_openTx2` |

</details>

<details><summary><code>audcodec</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x80263af0` | `audcodec_chkSamplingRate` |
| `0x80263bcc` | `audcodec_close` |
| `0x8026403c` | `audcodec_setParameter` |
| `0x80264cb4` | `audcodec_OcpHandler` |

</details>

<details><summary><code>AudFilt</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80286068` | `AudFilt_ApplyFiltering` |
| `0x8028623c` | `AudFilt_Open` |

</details>

<details><summary><code>AudFilter</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80286b34` | `AudFilter_Apply` |
| `0x80286bb8` | `AudFilter_Open` |

</details>

<details><summary><code>AudNoiseReduce</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80286990` | `AudNoiseReduce_Apply` |
| `0x80286a78` | `AudNoiseReduce_Open` |

</details>

<details><summary><code>AudNR</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x802863ac` | `AudNR_ApplyNoiseReduce` |
| `0x80286528` | `AudNR_SetConfig` |
| `0x80286754` | `AudNR_Init` |
| `0x802867fc` | `AudNR_Open` |

</details>

<details><summary><code>AWB</code> (19)</summary>

| 주소 | 이름 |
|---|---|
| `0x802851f4` | `AWB_GetCtrlObj` |
| `0x802852f0` | `AWB_Module_Lock` |
| `0x80285374` | `AWB_Module_Unlock` |
| `0x802853e0` | `AWB_Pause` |
| `0x802854c4` | `AWB_Resume` |
| `0x80285588` | `AWB_Start` |
| `0x80285648` | `AWB_Lock` |
| `0x8028570c` | `AWB_IsLock` |
| `0x802859d4` | `AWB_IsPause` |
| `0x80285a8c` | `AWB_GetTaskObj` |
| `0x80285a8c` | `AWB_TrigEvent` |
| `0x80285b54` | `AWB_Close` |
| `0x80285c30` | `AWB_Open` |
| `0x80321d48` | `AWB_Process` |
| `0x80321d48` | `AWB_getCA` |
| `0x8032258c` | `AWB_Init` |
| `0x8034977c` | `AWB_Adjust` |
| `0x8034ef04` | `AWB_CtrlInit` |
| `0x8039b654` | `AWB_AVG` |

</details>

<details><summary><code>AWBProc</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x802828b4` | `AWBProc_R2` |

</details>

<details><summary><code>AWBSim</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x802828b4` | `AWBSim_R2` |

</details>

<details><summary><code>Background</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x801d9c8c` | `Background_ProtectAll` |
| `0x801da22c` | `Background_DeleteAll` |
| `0x801da450` | `Background_CopyTo` |

</details>

<details><summary><code>BKG</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x800e884c` | `BKG_PostEvent` |
| `0x800e8938` | `BKG_DispatchMessage` |
| `0x800e8938` | `BKG_WaitEvent` |

</details>

<details><summary><code>caf</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80317e68` | `caf_Algorithm` |

</details>

<details><summary><code>Cal</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x801c18a4` | `Cal_DrawShowText` |
| `0x801c1c0c` | `Cal_GetDefaultInRoot` |
| `0x801c2340` | `Cal_IplUnInit` |
| `0x801c2574` | `Cal_IplInit` |
| `0x801c2868` | `Cal_IplOpen` |
| `0x801c2a34` | `Cal_SenDP_Bright` |

</details>

<details><summary><code>CAL</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80345c28` | `CAL_GetDebugLevel` |
| `0x80345c98` | `CAL_SetDebugLevel` |
| `0x8034650c` | `CAL_ReadDebugConfig_IMX206CQC_EVB_FF` |

</details>

<details><summary><code>CalibrationWnd</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801c174c` | `CalibrationWnd_OnOpen` |

</details>

<details><summary><code>CAP</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800063f4` | `CAP_FlgID` |

</details>

<details><summary><code>Cap</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80354e4c` | `Cap_EncodeSensorIDInfo` |
| `0x80354f48` | `Cap_ReadRawHeader` |
| `0x80354fec` | `Cap_WriteRawHeader` |

</details>

<details><summary><code>CARD</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801a4bf0` | `CARD_REMOVED` |

</details>

<details><summary><code>CarDV</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801cb974` | `CarDV_WiFi` |

</details>

<details><summary><code>cc</code> (10)</summary>

| 주소 | 이름 |
|---|---|
| `0x80099968` | `cc_getHwResGrant` |
| `0x800999fc` | `cc_hwUnlockResource` |
| `0x80099aec` | `cc_hwLockResource` |
| `0x80099ce8` | `cc_setConfig` |
| `0x8009a078` | `cc_startCore` |
| `0x8009a1dc` | `cc_sendCore2CMD` |
| `0x8009a350` | `cc_sendCore3CMD` |
| `0x8009a488` | `cc_close` |
| `0x8009a4f4` | `cc_open` |
| `0x8009a598` | `cc_isr` |

</details>

<details><summary><code>CCIR</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x802f73f4` | `CCIR_Proc` |

</details>

<details><summary><code>Check</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8016d558` | `Check_VideoSize_BufferLimit` |

</details>

<details><summary><code>ChgMode</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80167340` | `ChgMode_IMX206CQC` |

</details>

<details><summary><code>CHK</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80354ad4` | `CHK_ALIGN_VSIZE` |
| `0x80354b24` | `CHK_ALIGN_HSIZE` |

</details>

<details><summary><code>clk</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8009c0dc` | `clk_getDMAFreq` |
| `0x8009c174` | `clk_powerdown` |

</details>

<details><summary><code>cmd</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x800756a0` | `cmd_nand_erasechkFAT` |
| `0x80075760` | `cmd_nand_erasechkall` |
| `0x80075998` | `cmd_nand_readchkall` |
| `0x80076f98` | `cmd_nand_rwchkFAT` |
| `0x80077084` | `cmd_nand_dumpbin` |

</details>

<details><summary><code>Cmd</code> (27)</summary>

| 주소 | 이름 |
|---|---|
| `0x800ce8e8` | `Cmd_wifi_mode` |
| `0x801103d4` | `Cmd_filesys_wrperf` |
| `0x801105b8` | `Cmd_filesys_benchmark` |
| `0x80110660` | `Cmd_filesys_format` |
| `0x80231c50` | `Cmd_smrec_rawall` |
| `0x80232060` | `Cmd_smrec_checkgood` |
| `0x80232774` | `Cmd_smrec_cal` |
| `0x802327cc` | `Cmd_smrec_setcrash` |
| `0x80232834` | `Cmd_smrec_extcrash` |
| `0x8025a718` | `Cmd_vsmrec_rawall` |
| `0x8025aef4` | `Cmd_vsmrec_cal` |
| `0x8025af4c` | `Cmd_vsmrec_setcrash` |
| `0x8025afc0` | `Cmd_vsmrec_extcrash` |
| `0x80271114` | `Cmd_ae_uartmsg` |
| `0x80271184` | `Cmd_ae_osdmsg` |
| `0x802711f4` | `Cmd_ae_set` |
| `0x80285e38` | `Cmd_awb_uartmsg` |
| `0x802aab5c` | `Cmd_PStore_dump` |
| `0x802d2518` | `Cmd_ipl_saveCA` |
| `0x802d26b0` | `Cmd_ipl_savemem` |
| `0x802d27bc` | `Cmd_ipl_saveraw` |
| `0x80315270` | `Cmd_iquc_Set` |
| `0x803153ac` | `Cmd_iqs_Hue` |
| `0x803154b4` | `Cmd_iqs_Cont` |
| `0x803155d8` | `Cmd_iqs_Sharp` |
| `0x803156fc` | `Cmd_iqs_Sat` |
| `0x80315820` | `Cmd_iqs_IE` |

</details>

<details><summary><code>CoordTs</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x802891ac` | `CoordTs_Create` |

</details>

<details><summary><code>CoorTs</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8028912c` | `xCoorTs_CheckInit` |

</details>

<details><summary><code>cpu</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x8009aa84` | `cpu_cleanInvalidateDCacheAll` |
| `0x8009ab9c` | `cpu_lockDownDCache` |
| `0x8009acb0` | `cpu_invalidateICacheAll` |
| `0x8009b0ac` | `cpu_expCause` |

</details>

<details><summary><code>CSA1CSB1CSC1CSD1CSE1CSF1CSA2CSB2CSC2CSD2CSE2CSF2CSA3CSB3CSC3CSD3CSE3CSF3CSA4CSB4CSC4CSD4CSE4CSF4DP</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80345340` | `CSA1CSB1CSC1CSD1CSE1CSF1CSA2CSB2CSC2CSD2CSE2CSF2CSA3CSB3CSC3CSD3CSE3CSF3CSA4CSB4CSC4CSD4CSE4CSF4DP_Adjust_Dark` |

</details>

<details><summary><code>csi</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80046204` | `csi_getConfig` |
| `0x80046468` | `csi_isr` |

</details>

<details><summary><code>csi2</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x800466a8` | `csi2_getConfig` |
| `0x80046910` | `csi2_isr` |

</details>

<details><summary><code>dai</code> (8)</summary>

| 주소 | 이름 |
|---|---|
| `0x800305ac` | `dai_getI2sConfig` |
| `0x80030640` | `dai_setDebugMode` |
| `0x80030808` | `dai_setTxDMAPara` |
| `0x80030bdc` | `dai_setRxConfig` |
| `0x80030ce0` | `dai_setTxConfig` |
| `0x80030eb8` | `dai_setI2sConfig` |
| `0x80031020` | `dai_setConfig` |
| `0x800313a0` | `dai_lock` |

</details>

<details><summary><code>DataStamp</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80289288` | `DataStamp_SetInfor` |
| `0x8028930c` | `DataStamp_GetMaxWorkBufSize` |
| `0x80289384` | `DataStamp_Imprint` |

</details>

<details><summary><code>DbgSys</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x8029dea0` | `DbgSys_PropertyGet` |
| `0x8029df38` | `DbgSys_PropertySet` |
| `0x8029dfcc` | `DbgSys_CmdSend` |
| `0x8029e5c0` | `DbgSys_MsgReceive` |

</details>

<details><summary><code>DBGUT</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80003e1c` | `DBGUT_FLG_ID` |
| `0x80003e1c` | `DBGUT_SEM_ID` |

</details>

<details><summary><code>DbgUt</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800172bc` | `xDbgUt_Err` |

</details>

<details><summary><code>dce</code> (12)</summary>

| 주소 | 이름 |
|---|---|
| `0x801230fc` | `dce_checkStateMachine` |
| `0x8012326c` | `dce_setLoad` |
| `0x80123cec` | `dce_changeDistortCorrSel` |
| `0x80123d9c` | `dce_setOpMode` |
| `0x80123ed0` | `dce_changeFuncEn` |
| `0x80123fe8` | `dce_changeIntEn` |
| `0x801240e4` | `dce_isr` |
| `0x801243b8` | `dce_setMode` |
| `0x80124550` | `dce_getNormStripe_660` |
| `0x80125290` | `dce_close` |
| `0x80125350` | `dce_open` |
| `0x80125350` | `dce_setPllClock` |

</details>

<details><summary><code>DCE</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80316678` | `DCE_GetFovGain` |
| `0x80335e64` | `DCE_D2D_CB` |
| `0x8033a5a4` | `DCE_IQparam` |

</details>

<details><summary><code>DCED2D</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80310470` | `DCED2D_start` |

</details>

<details><summary><code>DCF</code> (18)</summary>

| 주소 | 이름 |
|---|---|
| `0x80116048` | `DCF_internalSetNextID` |
| `0x8011613c` | `DCF_GetDBInfoEx` |
| `0x801162d4` | `DCF_SetParm` |
| `0x80116494` | `DCF_SetDirFreeChars` |
| `0x801166b4` | `DCF_GetDirInfoEx` |
| `0x801167d4` | `DCF_SetFileFreeChars` |
| `0x801168f8` | `DCF_MakeObjPathEx` |
| `0x80116b34` | `DCF_MakeDirPathEx` |
| `0x80116eb0` | `DCF_GetDirPathEx` |
| `0x801174e8` | `DCF_GetIndexByIDEx` |
| `0x8011768c` | `DCF_GetObjPathByIDEx` |
| `0x801177e8` | `DCF_GetNextIDEx` |
| `0x80117b28` | `DCF_AddDBfileEx` |
| `0x80118254` | `DCF_internalSetCurIndex` |
| `0x80118434` | `DCF_GetObjPathEx` |
| `0x80118628` | `DCF_GetObjInfoEx` |
| `0x801187d4` | `DCF_SeekIndexEx` |
| `0x80119270` | `DCF_DelDBfileEx` |

</details>

<details><summary><code>Delay</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80013ca0` | `Delay_DelayUs` |
| `0x80013d88` | `Delay_DelayMs` |

</details>

<details><summary><code>DePackCb</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800e5db0` | `DePackCb_eCos` |

</details>

<details><summary><code>Dhcp</code> (13)</summary>

| 주소 | 이름 |
|---|---|
| `0x802897bc` | `xDhcp_GetCliIP` |
| `0x80289910` | `Dhcp_RegSrvCBCliAttach` |
| `0x80289a40` | `xDhcp_ConfigLeaseTbl` |
| `0x80289b88` | `xDhcp_SetSrvIntf` |
| `0x80289d34` | `Dhcp_UnInit_Network` |
| `0x80289ea0` | `Dhcp_Net_Ping` |
| `0x8028a0d0` | `Dhcp_Client_Stop` |
| `0x8028a42c` | `Dhcp_Srv_Start` |
| `0x8028a75c` | `Dhcp_Server_Stop` |
| `0x8028aa14` | `Dhcp_Client_Start` |
| `0x8028b290` | `xDhcp_Msg_SysCallReq` |
| `0x8028b328` | `Dhcp_IpcClose` |
| `0x8028b480` | `Dhcp_IpcOpen` |

</details>

<details><summary><code>DHCPIPC</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80004700` | `DHCPIPC_FLG_ID` |
| `0x80004700` | `DHCPIPC_SEM_ID` |

</details>

<details><summary><code>dis</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80125b78` | `dis_getClockRate` |

</details>

<details><summary><code>disFw</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x803777a4` | `disFw_setDisInfor` |

</details>

<details><summary><code>disHw</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80377814` | `disHw_setDisInfor` |

</details>

<details><summary><code>disp</code> (8)</summary>

| 주소 | 이름 |
|---|---|
| `0x8016f9fc` | `disp_closeDisp1` |
| `0x8016fa60` | `disp_setDisp1DeviceCtrl` |
| `0x80170fa0` | `disp_setDisp1LayerCtrl` |
| `0x80172fa4` | `disp_setDisp1Control` |
| `0x80174728` | `disp_closeDisp2` |
| `0x80174794` | `disp_setDisp2DeviceCtrl` |
| `0x80175778` | `disp_setDisp2LayerCtrl` |
| `0x80176970` | `disp_setDisp2Control` |

</details>

<details><summary><code>dispdev</code> (7)</summary>

| 주소 | 이름 |
|---|---|
| `0x8016e29c` | `dispdev_getLcdSize` |
| `0x8016e3a0` | `dispdev_readLcdReg` |
| `0x8016e4e0` | `dispdev_setDeviceRotate` |
| `0x8016e748` | `dispdev_openIF8Bits` |
| `0x8016ef34` | `dispdev_setDisplay` |
| `0x8026a2fc` | `dispdev_chgHdmiClkFreq` |
| `0x8026a5c4` | `dispdev_initHdmiVidFormat` |

</details>

<details><summary><code>dispdev1</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8017371c` | `dispdev1_ioctrl` |

</details>

<details><summary><code>dispdev2</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80176ce0` | `dispdev2_ioctrl` |

</details>

<details><summary><code>DISPSRV</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x800047cc` | `DISPSRV_FLG2_ID` |
| `0x800047cc` | `DISPSRV_FLG_ID` |
| `0x800047cc` | `DISPSRV_SEM_ID` |

</details>

<details><summary><code>DispSrv</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8017efa8` | `xDispSrv_Err` |

</details>

<details><summary><code>DispSrvCmd</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8017f83c` | `xDispSrvCmd_DecideFlipMethod` |
| `0x8017fb50` | `xDispSrvCmd_SetDisp` |

</details>

<details><summary><code>DispSrvFlip</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x800047cc` | `xDispSrvFlip_Tsk` |
| `0x80181240` | `xDispSrvFlip_ChkDualValid` |
| `0x80181240` | `xDispSrvFlip_UpdateDispObj` |
| `0x80181eb8` | `xDispSrvFlip_DirectFrmToTemp` |
| `0x80182b6c` | `xDispSrvFlip_SwitchDouble` |
| `0x801832d8` | `xDispSrvFlip_SwitchSource` |

</details>

<details><summary><code>dma</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x80044404` | `dma_setChannelPriority` |
| `0x80044520` | `dma_open` |
| `0x800447d0` | `dma_configWPFunc` |
| `0x800448d4` | `dma_clrWPStatus` |
| `0x80044a2c` | `dma_enableWPFunc` |
| `0x80044c44` | `dma_isr` |

</details>

<details><summary><code>DP</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8034a5e0` | `DP_Adjust_Bright` |

</details>

<details><summary><code>DPC</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8039b8b8` | `DPC_Bayer` |
| `0x8039b8b8` | `DPC_Bayer_Search` |

</details>

<details><summary><code>dre</code> (14)</summary>

| 주소 | 이름 |
|---|---|
| `0x801470b0` | `dre_chkNrParamValidity` |
| `0x80147110` | `dre_setFunctionEnable` |
| `0x80147254` | `dre_stateMachine` |
| `0x801473c8` | `dre_chkDMAOutParam` |
| `0x801473c8` | `dre_doDMAOutChkFlushSet` |
| `0x801473c8` | `dre_setOutAddr` |
| `0x801475dc` | `dre_chkSetDMAOutParam` |
| `0x80147aac` | `dre_chkDMAInAddr` |
| `0x80147aac` | `dre_doDMAInChkFlushSet` |
| `0x80147aac` | `dre_setInAddr` |
| `0x80147d1c` | `dre_chkSetDMAInParam` |
| `0x8014a8c0` | `dre_procNrDcm` |
| `0x8014ad24` | `dre_procHdrRcs` |
| `0x8014af8c` | `dre_procHdrDcm` |

</details>

<details><summary><code>DRE</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80335ac0` | `DRE_D2D_CB` |
| `0x8033cea8` | `DRE_IQparam` |

</details>

<details><summary><code>DRED2D</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8030d8c0` | `DRED2D_wait` |
| `0x8030e1e0` | `DRED2D_start` |

</details>

<details><summary><code>drv</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x8002ab94` | `drv_enableInt` |
| `0x8002ad04` | `drv_init` |
| `0x8005f3e8` | `drv_setIstEvent` |

</details>

<details><summary><code>DrvHDMI</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800c5e40` | `DrvHDMI_TurnOn` |

</details>

<details><summary><code>DrvKey</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800c6714` | `DrvKey_DetStatusKey` |

</details>

<details><summary><code>DrvSound</code> (10)</summary>

| 주소 | 이름 |
|---|---|
| `0x800c785c` | `DrvSound_SetCh` |
| `0x800c79a0` | `DrvSound_SetSR` |
| `0x800c7b14` | `DrvSound_SetSR_Resample` |
| `0x800c7db0` | `DrvSound_SetAudGain` |
| `0x800c7ec8` | `DrvSound_GetHDMIAudSR` |
| `0x800c7fdc` | `DrvSound_SetTotalVolLvl` |
| `0x800c8308` | `DrvSound_Init` |
| `0x800c8458` | `DrvSound_SetCodec` |
| `0x800c850c` | `DrvSound_SetOutDevConfig` |
| `0x800c87fc` | `DrvSound_Control` |

</details>

<details><summary><code>DrvTV</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800c4e84` | `DrvTV_TurnOn` |

</details>

<details><summary><code>Dx</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80025ff8` | `Dx_Getcaps` |

</details>

<details><summary><code>DxSys</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80029854` | `DxSys_Init` |

</details>

<details><summary><code>DxUSB</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800c63dc` | `DxUSB_UpdateConnectType` |

</details>

<details><summary><code>eac</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x80031b0c` | `eac_getDaConfig` |
| `0x80031d64` | `eac_setDaConfig` |
| `0x8003211c` | `eac_getAdConfig` |
| `0x800324fc` | `eac_setAdConfig` |

</details>

<details><summary><code>ECS</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80347fa0` | `ECS_Adjust` |

</details>

<details><summary><code>Edge</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x803172d4` | `Edge_Gamma` |

</details>

<details><summary><code>EDIT</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x802a4a44` | `EDIT_Crop` |
| `0x802a4c08` | `EDIT_Resize` |

</details>

<details><summary><code>efuse</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x8006052c` | `efuse_close` |
| `0x800605f0` | `efuse_read` |
| `0x800606e8` | `efuse_open` |
| `0x80060808` | `efuse_readData` |

</details>

<details><summary><code>Exif</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x80111f7c` | `xExif_InsertTag` |
| `0x80112110` | `xExif_WriteTag` |
| `0x80112900` | `xExif_WriteExif` |
| `0x80114b80` | `xExif_CheckInited` |
| `0x80114cdc` | `xExif_GetWorkingBuf` |

</details>

<details><summary><code>EXIF</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x8011245c` | `EXIF_UpdateInfo` |
| `0x80112700` | `EXIF_SetTag` |
| `0x80112900` | `EXIF_CreateExif` |
| `0x80113e38` | `EXIF_GetInfo` |
| `0x80114be4` | `EXIF_Init` |

</details>

<details><summary><code>ExifR</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x8011398c` | `ExifR_GetTagData` |
| `0x80113b2c` | `ExifR_GetExifTag` |
| `0x80113fcc` | `ExifR_ReadExif` |

</details>

<details><summary><code>FA</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x802f15a0` | `FA_IPC_IQ` |
| `0x802f1a58` | `FA_IPC_Flip` |
| `0x802f1a58` | `FA_IPC_IQ_ISR` |

</details>

<details><summary><code>fat</code> (21)</summary>

| 주소 | 이름 |
|---|---|
| `0x800ebcc0` | `fat_SetBitMapFreeCluster` |
| `0x800ebde4` | `fat_GetNewPageInfo` |
| `0x800ebeb4` | `fat_GetClusterValue16` |
| `0x800ebf94` | `fat_GetClusterValue12` |
| `0x800ec904` | `fat_WriteOneOldPage` |
| `0x800ec9a8` | `fat_SwapPage` |
| `0x800ecba8` | `fat_FindClusInCurPage` |
| `0x800ecd3c` | `fat_SetClusterValue32` |
| `0x800ece50` | `fat_GetClusterValue32` |
| `0x800ed234` | `fat_SetClusterValue16` |
| `0x800ed300` | `fat_SetClusterValue12` |
| `0x800ed460` | `fat_ClusterToSector` |
| `0x800ed4f4` | `fat_UninitFATCache` |
| `0x800ed580` | `fat_InitFATCache` |
| `0x800eea5c` | `fat_GetPreviousClus` |
| `0x800eeb68` | `fat_GetContinueClusterValue` |
| `0x800eed40` | `fat_GetBitMapFreeCluster` |
| `0x800eed40` | `fat_GetFreeCluster` |
| `0x800eef94` | `fat_ClearClusterLink` |
| `0x800ef0f4` | `fat_StorePage` |
| `0x800ef1e8` | `fat_StoreFAT` |

</details>

<details><summary><code>fatEx</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x800ec170` | `fatEx_SwapBitMapPage` |
| `0x800ec2f0` | `fatEx_SetBitMapFreeCluster` |
| `0x800ec6e0` | `fatEx_GetBitMapFreeCluster` |
| `0x800ecfb0` | `fatEx_SetClusterValue` |
| `0x800ed0a4` | `fatEx_GetClusterValue` |
| `0x800ed580` | `fatEx_GetTotalBitMapFreeCluster` |

</details>

<details><summary><code>FC</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x802fcec8` | `FC_IPC_Flip` |
| `0x802fd18c` | `FC_IPC_Chg_Crop` |
| `0x802fdb48` | `FC_IPC_IQ` |
| `0x802fdf68` | `FC_IPC_IQ_ISR` |

</details>

<details><summary><code>FD</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8030541c` | `FD_IPC_IQ` |
| `0x8030583c` | `FD_IPC_IQ_ISR` |

</details>

<details><summary><code>fdb</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800e7320` | `fdb_create` |

</details>

<details><summary><code>fde</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80126014` | `fde_getClockRate` |
| `0x801260e4` | `fde_isr` |

</details>

<details><summary><code>FileDB</code> (13)</summary>

| 주소 | 이름 |
|---|---|
| `0x8011b274` | `FileDB_internalSearhFile` |
| `0x8011b3f8` | `FileDB_ChooseSortMethod` |
| `0x8011b65c` | `FileDB_CurrFile` |
| `0x8011bccc` | `FileDB_SearhFile2` |
| `0x8011be04` | `FileDB_DumpInfo` |
| `0x8011c0fc` | `FileDB_DeleteFile` |
| `0x8011c41c` | `FileDB_InsertOneFile` |
| `0x8011c41c` | `FileDB_internalAddFile` |
| `0x8011d1b0` | `FileDB_Scan` |
| `0x8011f394` | `FileDB_Create` |
| `0x8011f7e8` | `FileDB_InsertSort` |
| `0x8011f7e8` | `FileDB_internalSortBy` |
| `0x8011fd10` | `FileDB_FileSysDirCB` |

</details>

<details><summary><code>FileSys</code> (36)</summary>

| 주소 | 이름 |
|---|---|
| `0x800ea1e4` | `FileSys_SearchFileClose` |
| `0x800ea23c` | `FileSys_SearchFile` |
| `0x800ea294` | `FileSys_SearchFileOpen` |
| `0x800ea2ec` | `FileSys_ChDir` |
| `0x800ea344` | `FileSys_GetCwd` |
| `0x800ea39c` | `FileSys_MakeDir` |
| `0x800ea3f0` | `FileSys_GetFileLen` |
| `0x800ea478` | `FileSys_LockDirFiles` |
| `0x800ea4d0` | `FileSys_DelDirFiles` |
| `0x800ea524` | `FileSys_GetParamEx` |
| `0x800ea590` | `FileSys_GetDiskInfoEx` |
| `0x800ea61c` | `FileSys_StatFile` |
| `0x800ea674` | `FileSys_FlushFile` |
| `0x800ea6c8` | `FileSys_TellFile` |
| `0x800ea750` | `FileSys_SeekFile` |
| `0x800ea7b0` | `FileSys_WriteFile` |
| `0x800ea810` | `FileSys_ReadFile` |
| `0x800ea870` | `FileSys_CloseFile` |
| `0x800ea8c8` | `FileSys_OpenFile` |
| `0x800ea920` | `FileSys_ScanDir` |
| `0x800ea978` | `FileSys_MoveFile` |
| `0x800ea9d0` | `FileSys_RenameFile` |
| `0x800eaa28` | `FileSys_CopyToByName` |
| `0x800eaa80` | `FileSys_SetDateTime` |
| `0x800eaad8` | `FileSys_GetDateTime` |
| `0x800eab30` | `FileSys_SetAttrib` |
| `0x800eab8c` | `FileSys_GetAttrib` |
| `0x800eabe4` | `FileSys_DeleteDir` |
| `0x800eac3c` | `FileSys_DeleteFile` |
| `0x800eac94` | `FileSys_ChangeDiskEx` |
| `0x800eacf0` | `FileSys_WaitFinishEx` |
| `0x800ead4c` | `FileSys_FormatAndLabel` |
| `0x800eada8` | `FileSys_GetStrgObjEx` |
| `0x800eae04` | `FileSys_CloseEx` |
| `0x800eae5c` | `FileSys_Init` |
| `0x800eaee0` | `FileSys_OpenEx` |

</details>

<details><summary><code>Filesys</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8010d7fc` | `Filesys_getFreeDriveHandle` |

</details>

<details><summary><code>FLG</code> (29)</summary>

| 주소 | 이름 |
|---|---|
| `0x800028f0` | `FLG_ID_MOVIESTAMP` |
| `0x800029bc` | `FLG_ID_ENGINEER` |
| `0x80002e30` | `FLG_ID_LVIEWNVT` |
| `0x80003130` | `FLG_ID_PB_DISP` |
| `0x80003130` | `FLG_ID_PLAYBACK` |
| `0x8000334c` | `FLG_ID_SMEDIAAUDDEC` |
| `0x8000334c` | `FLG_ID_SMEDIAPLAY` |
| `0x8000334c` | `FLG_ID_SMEDIAPRESENT` |
| `0x8000334c` | `FLG_ID_SMEDIAVIDDEC` |
| `0x8000351c` | `FLG_ID_SMRAWENC` |
| `0x8000351c` | `FLG_ID_SM_MDAT` |
| `0x8000351c` | `FLG_ID_SM_VTRIG` |
| `0x8000351c` | `FLG_ID_SRECMEDIA` |
| `0x8000351c` | `FLG_ID_SRECMEDIACMD` |
| `0x80003928` | `FLG_ID_VIDSTRM` |
| `0x80003928` | `FLG_ID_VSMRAWENC` |
| `0x80003928` | `FLG_ID_VSM_MDAT` |
| `0x80003928` | `FLG_ID_VSRECMEDIA` |
| `0x80003928` | `FLG_ID_VSRECMEDIACMD` |
| `0x80003ee8` | `FLG_ID_GPS` |
| `0x8000448c` | `FLG_ID_AUDFILTER` |
| `0x80004a0c` | `FLG_ID_FILEDB` |
| `0x80005218` | `FLG_ID_SOUND` |
| `0x800052b0` | `FLG_ID_MAIN` |
| `0x800052b0` | `FLG_ID_PRIMARY` |
| `0x800054c4` | `FLG_ID_PSTORE` |
| `0x80005618` | `FLG_ID_USBCLASS` |
| `0x800056f8` | `FLG_ID_UVAC` |
| `0x80005a84` | `FLG_ID_WIFICMD` |

</details>

<details><summary><code>FLGPTN</code> (22)</summary>

| 주소 | 이름 |
|---|---|
| `0x802d60b0` | `FLGPTN_IPC_D2D_DCE_E` |
| `0x802d60b0` | `FLGPTN_IPC_D2D_DRE_E` |
| `0x802d60b0` | `FLGPTN_IPC_D2D_IFE2_E` |
| `0x802d60b0` | `FLGPTN_IPC_D2D_IFE_E` |
| `0x802d60b0` | `FLGPTN_IPC_D2D_IME_E` |
| `0x802d60b0` | `FLGPTN_IPC_D2D_IPE_E` |
| `0x802d60b0` | `FLGPTN_IPC_D2D_ISE_E` |
| `0x802d60b0` | `FLGPTN_IPC_D2D_RDE_E` |
| `0x802d60b0` | `FLGPTN_IPC_D2D_RHE_E` |
| `0x802d60b0` | `FLGPTN_IPC_D2D_STRIPE_E` |
| `0x802d60b0` | `FLGPTN_IPC_RUNCHG_E1` |
| `0x802d60b0` | `FLGPTN_IPC_RUNCHG_E2` |
| `0x802d60b0` | `FLGPTN_IPC_RUNCHG_E3` |
| `0x802d60b0` | `FLGPTN_IPC_RUNCHG_E4` |
| `0x802d60b0` | `FLGPTN_IPC_RUNCHG_IQ_E1` |
| `0x802d60b0` | `FLGPTN_IPC_RUNCHG_IQ_E2` |
| `0x802d60b0` | `FLGPTN_IPC_RUNCHG_IQ_E3` |
| `0x802d60b0` | `FLGPTN_IPC_RUNCHG_IQ_E4` |
| `0x802d60b0` | `FLGPTN_SIE1` |
| `0x802d60b0` | `FLGPTN_SIE2` |
| `0x802d60b0` | `FLGPTN_SIE3` |
| `0x802d60b0` | `FLGPTN_SIE4` |

</details>

<details><summary><code>FlowMovie</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801bb184` | `FlowMovie_IconDrawMovieExe_Ontimer` |

</details>

<details><summary><code>FlowPB</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801bef74` | `FlowPB_UpdateIcons` |

</details>

<details><summary><code>FlowPhoto</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801b4e58` | `FlowPhoto_InitCfgSetting` |

</details>

<details><summary><code>fs</code> (72)</summary>

| 주소 | 이름 |
|---|---|
| `0x800eb604` | `fs_MB_TO_UCS2` |
| `0x800f00c0` | `fs_ParsingMBR` |
| `0x800f020c` | `fs_ParingDiskInfo` |
| `0x800f070c` | `fs_StrgTblClose` |
| `0x800f0828` | `fs_StrgTblOpen` |
| `0x800f0980` | `fs_StorageDrvInit` |
| `0x800f17d0` | `fs_ReleaseClusterSlidingWindow` |
| `0x800f1854` | `fs_InitClusterSlidingWindow` |
| `0x800f194c` | `fs_GetDataClusValue` |
| `0x800f1f8c` | `fs_GetWholeLongFilenameInRoot` |
| `0x800f2144` | `fs_StoreRecentDir` |
| `0x800f22bc` | `fs_FindFreeSearchHandle` |
| `0x800f243c` | `fs_ReleaseFileTable` |
| `0x800f24fc` | `fs_FindEmptyFileTable` |
| `0x800f2694` | `fs_CheckRecentDir` |
| `0x800f280c` | `fs_ReleaseSearchHandle` |
| `0x800f2890` | `fs_GetFirstFileInRoot` |
| `0x800f2bd8` | `fs_IsValidSearchHandle` |
| `0x800f2cec` | `fs_IsValidFileHandle` |
| `0x800f3238` | `fs_ReadOneClusForScan` |
| `0x800f3450` | `fs_ReadOneClusterData` |
| `0x800f3b9c` | `fs_GetNextFile` |
| `0x800f4184` | `fs_FindDirEntryInFolder` |
| `0x800f49ac` | `fs_GetFirstFileInNormal` |
| `0x800f4df4` | `fs_WriteSectors` |
| `0x800f4ef4` | `fs_FillWithBuf` |
| `0x800f5108` | `fs_SetFileSize` |
| `0x800f54a4` | `fs_WriteDirEntry` |
| `0x800f5628` | `fs_UpdateDirEntry` |
| `0x800f5a44` | `fs_CreateNormalEntry` |
| `0x800f5a44` | `fs_Rename_Shortname_ByNum` |
| `0x800f5a44` | `fs_SetFreeEntry00ToE5` |
| `0x800f6ad8` | `fs_CreateEntry` |
| `0x800f6ea8` | `fs_WriteOneClusterData` |
| `0x800f85b4` | `fs_checkSysInfoTag` |
| `0x800f868c` | `fs_getSysInfoByDriveName` |
| `0x800f88c0` | `fs_getSysInfoBySearchHandle` |
| `0x800f8960` | `fs_getSysInfoByFileHandle` |
| `0x800f8a00` | `fs_getSysInfoByPath` |
| `0x800f8b7c` | `fs_interfseek` |
| `0x800f8ce8` | `fs_interfopen` |
| `0x800f9544` | `fs_interfclose` |
| `0x800f96dc` | `fs_SetAttrib2` |
| `0x800f9854` | `fs_GetDateTime` |
| `0x800f99cc` | `fs_flush` |
| `0x800f9c10` | `fs_mkdir` |
| `0x800f9ce0` | `fs_fclose` |
| `0x800f9d60` | `fs_fseek` |
| `0x800f9f04` | `fs_SetDateTime` |
| `0x800fad3c` | `fs_faccess` |
| `0x800fb6b0` | `fs_fwrite` |
| `0x800fb82c` | `fs_fread` |
| `0x800fbb10` | `fs_FindFileCloseEx` |
| `0x800fbc70` | `fs_FindFileNextEx` |
| `0x800fc00c` | `fs_FindFileGetHandle` |
| `0x800fc170` | `fs_FindFileOpenEx` |
| `0x800fc2c8` | `fs_GetLabel` |
| `0x800fc4b4` | `fs_setLabel` |
| `0x800fc7c0` | `fs_remove` |
| `0x800fca30` | `fs_rmdir` |
| `0x800fcce0` | `fs_move` |
| `0x800fd028` | `fs_rename` |
| `0x800fd2e4` | `fs_ftruncate` |
| `0x800fd2e4` | `fs_interftruncate` |
| `0x800fdb0c` | `fs_perf_update_histogram` |
| `0x800fe10c` | `fs_perf_set_enable` |
| `0x800fe5f0` | `fs_test_bm_dualrec` |
| `0x800feb34` | `fs_test_bm_speed` |
| `0x800ff568` | `fs_FindValidEntryRetPoint` |
| `0x800ff6c8` | `fs_FindMatchLongNameRetPoint` |
| `0x80100960` | `fs_format` |
| `0x80100960` | `fs_formatExFAT` |

</details>

<details><summary><code>FsBackground</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80004d50` | `FsBackground_Task` |
| `0x80004d50` | `FsBackground_Task2` |

</details>

<details><summary><code>fsEx</code> (22)</summary>

| 주소 | 이름 |
|---|---|
| `0x800fa0b8` | `fsEx_faccess` |
| `0x80104c40` | `fsEx_GetEntrySize` |
| `0x80104ce0` | `fsEx_GetEntryFromPFile` |
| `0x80104d48` | `fsEx_GetNextClus` |
| `0x80104ec4` | `fsEx_FillEntryToFile` |
| `0x801050cc` | `fsEx_Read2SecOfNextClus` |
| `0x80105408` | `fsEx_FindDirEntryInFolder` |
| `0x8010589c` | `fsEx_GetLabelEntry` |
| `0x80105b74` | `fsEx_SetClusterEmpty` |
| `0x80105de0` | `fsEx_CreateLabelEntry` |
| `0x8010642c` | `fsEx_FillTarEntry` |
| `0x8010642c` | `fsEx_UpdateDirEntry` |
| `0x80106a1c` | `fsEx_CreateNormalEntry` |
| `0x8010742c` | `fsEx_CreateEntry` |
| `0x8010742c` | `fsEx_UpdateParentEntry` |
| `0x80107fe8` | `fsEx_FindData_GetNextClus` |
| `0x8010826c` | `fsEx_GetFirstValidFile` |
| `0x80108718` | `fsEx_GetNextFile` |
| `0x80108858` | `fsEx_CheckRecentDir` |
| `0x80108858` | `fsEx_StoreRecentDir` |
| `0x80108c04` | `fsEx_GetFirstFileInNormal` |
| `0x80108e18` | `fsEx_SetFileSize` |

</details>

<details><summary><code>fsEX</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8010826c` | `fsEX_ReadEntry` |

</details>

<details><summary><code>FSIPC</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80004b5c` | `FSIPC_FLG_ID` |
| `0x80004b5c` | `FSIPC_SEM_ID` |

</details>

<details><summary><code>FsIpc</code> (13)</summary>

| 주소 | 이름 |
|---|---|
| `0x8028c42c` | `FsIpc_Umount` |
| `0x8028c50c` | `FsIpc_Mount` |
| `0x8028c610` | `FsIpc_Close` |
| `0x8028c764` | `FsIpc_Open` |
| `0x8028c9f0` | `FsIpc_Msg_SysCallReq` |
| `0x8028ca88` | `FsIpc_Msg_AckCmd` |
| `0x8028caf4` | `FsIpc_Msg_WaitCmd` |
| `0x8028cb50` | `FsIpc_Msg_Uninit` |
| `0x8028cbb8` | `FsIpc_Msg_Init` |
| `0x8028cc64` | `FsIpc_Tsk_SetParam` |
| `0x8028cf40` | `FsIpc_CmdId_ReadDir` |
| `0x8028d438` | `FsIpc_Tsk_GetFsPath` |
| `0x8028d834` | `FsIpc_CmdId_Stat` |

</details>

<details><summary><code>FSLINUX</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80004c28` | `FSLINUX_COMMON_FLG_ID` |

</details>

<details><summary><code>FsLinux</code> (62)</summary>

| 주소 | 이름 |
|---|---|
| `0x8028de30` | `FsLinux_RegisterCB` |
| `0x8028de68` | `FsLinux_GetLongName` |
| `0x8028deb4` | `FsLinux_SetParam` |
| `0x8028def0` | `FsLinux_GetLabel` |
| `0x8028df2c` | `FsLinux_AllocFile` |
| `0x8028e0bc` | `FsLinux_GetParam` |
| `0x8028e1c8` | `FsLinux_ChangeDisk` |
| `0x8028e2b4` | `FsLinux_GetStrgObj` |
| `0x8028e3a4` | `FsLinux_WaitFinish` |
| `0x8028e444` | `FsLinux_ChDir` |
| `0x8028e5f4` | `FsLinux_FormatAndLabel` |
| `0x8028e824` | `FsLinux_GetDiskInfo` |
| `0x8028ec48` | `FsLinux_SearchFileRewind` |
| `0x8028edec` | `FsLinux_FlushFile` |
| `0x8028ef70` | `FsLinux_TruncFile` |
| `0x8028f114` | `FsLinux_TellFile` |
| `0x8028f2d4` | `FsLinux_SeekFile` |
| `0x8028f640` | `FsLinux_WriteFile` |
| `0x8028f8ec` | `FsLinux_DeleteFile` |
| `0x8028f9c4` | `FsLinux_CopyToByName` |
| `0x8028fc30` | `FsLinux_SetAttrib` |
| `0x8028fdd4` | `FsLinux_GetAttrib` |
| `0x8028ff94` | `FsLinux_MoveFile` |
| `0x802901c8` | `FsLinux_RenameFile` |
| `0x8029039c` | `FsLinux_RenameDir` |
| `0x80290570` | `FsLinux_DeleteDir` |
| `0x802906f4` | `FsLinux_MakeDir` |
| `0x80290878` | `FsLinux_GetFileLen` |
| `0x80290c88` | `FsLinux_OpenFile` |
| `0x80290e5c` | `FsLinux_CloseFile` |
| `0x8029142c` | `FsLinux_Benchmark` |
| `0x802919bc` | `FsLinux_ReadFile` |
| `0x80291b84` | `FsLinux_LockDirFiles` |
| `0x80291f2c` | `FsLinux_DelDirFiles` |
| `0x802922c8` | `FsLinux_ScanDir` |
| `0x8029253c` | `FsLinux_SearchFileClose` |
| `0x80292630` | `FsLinux_GetParentDir` |
| `0x802927bc` | `FsLinux_SearchFile` |
| `0x802929f0` | `FsLinux_SearchFileOpen` |
| `0x80292b98` | `FsLinux_SetDateTime` |
| `0x80292d9c` | `FsLinux_GetDateTime` |
| `0x80292fa0` | `FsLinux_StatFile` |
| `0x80293168` | `FsLinux_Close` |
| `0x80293350` | `FsLinux_Open` |
| `0x8029369c` | `FsLinux_Buf_GetTmpSize` |
| `0x802936ec` | `FsLinux_Buf_UnlockTmpBuf` |
| `0x80293750` | `FsLinux_Buf_UnlockArgBuf` |
| `0x802937b4` | `FsLinux_Buf_LocknGetTmpBuf` |
| `0x80293870` | `FsLinux_Buf_LocknGetArgBuf` |
| `0x8029392c` | `FsLinux_Buf_Uninit` |
| `0x802939cc` | `FsLinux_Buf_Init` |
| `0x80293d50` | `FsLinux_GetCtrlObjByDrive` |
| `0x80293e38` | `FsLinux_Ipc_SysCallReq` |
| `0x80293eb0` | `FsLinux_Ipc_SendMsgWaitAck` |
| `0x80293fd4` | `FsLinux_Ipc_WaitMsg` |
| `0x80294030` | `FsLinux_Ipc_Uninit` |
| `0x80294098` | `FsLinux_Ipc_Init` |
| `0x80294224` | `FsLinux_SxCmd_Format` |
| `0x80294260` | `FsLinux_SxCmd_Benchmark` |
| `0x802945a8` | `FsLinux_IsDefSync` |
| `0x80294624` | `FsLinux_FlushReadCache` |
| `0x802946d0` | `FsLinux_Conv2LinuxPath` |

</details>

<details><summary><code>fslnx</code> (15)</summary>

| 주소 | 이름 |
|---|---|
| `0x8028df68` | `fslnx_IsValidSearchHandle` |
| `0x8028e000` | `fslnx_IsValidFileHandle` |
| `0x8028e594` | `fslnx_SendPureCmd` |
| `0x8028eb1c` | `fslnx_searchfile` |
| `0x8028f480` | `fslnx_writefile` |
| `0x8028f80c` | `fslnx_deletefile` |
| `0x80290a70` | `fslnx_FindEmptyFileHandle` |
| `0x80290a70` | `fslnx_openfile` |
| `0x80290d70` | `fslnx_closefile` |
| `0x80290f3c` | `fslnx_FindEmptySearchHandle` |
| `0x80290f3c` | `fslnx_searchfileopen` |
| `0x8029117c` | `fslnx_searchfileclose` |
| `0x8029126c` | `fslnx_readfile` |
| `0x80291b84` | `fslnx_searchfilelock` |
| `0x80291f2c` | `fslnx_searchfiledel` |

</details>

<details><summary><code>FST</code> (20)</summary>

| 주소 | 이름 |
|---|---|
| `0x8010e374` | `FST_CMDGetFileLen` |
| `0x8010e44c` | `FST_CMDCloseFile` |
| `0x8010e534` | `FST_CMDAllocFile` |
| `0x8010e5c0` | `FST_CMDTruncFile` |
| `0x8010e650` | `FST_CMDFlushFile` |
| `0x8010e6bc` | `FST_CMDWriteFile` |
| `0x8010e7e0` | `FST_CMDTellFile` |
| `0x8010e858` | `FST_CMDSeekFile` |
| `0x8010e8f4` | `FST_CMDOpenFile` |
| `0x8010ea9c` | `FST_CMDRunBenchmark` |
| `0x8010ecb0` | `FST_CMDCopyToByName` |
| `0x8010f054` | `FST_CMDSetDiskLabel` |
| `0x8010f190` | `FST_CMDSysInit` |
| `0x8010f330` | `FST_CMDFormatStorage` |
| `0x8010f5a0` | `FST_CMDSetAttrib` |
| `0x8010f61c` | `FST_CMDGetLongName` |
| `0x8010f6b8` | `FST_CMDScanDir` |
| `0x8010f928` | `FST_CMDRename` |
| `0x80110d6c` | `FST_EntryAccessFolderFiles` |
| `0x80111c0c` | `FST_ChangeDisk` |

</details>

<details><summary><code>FsUitron</code> (34)</summary>

| 주소 | 이름 |
|---|---|
| `0x800f9b00` | `FsUitron_ChDir` |
| `0x800fba64` | `FsUitron_SearchFileRewind` |
| `0x800fbb94` | `FsUitron_SearchFileClose` |
| `0x800fbefc` | `FsUitron_SearchFile` |
| `0x800fc218` | `FsUitron_SearchFileOpen` |
| `0x8010a318` | `FsUitron_GetFileLen` |
| `0x8010a478` | `FsUitron_LockDirFiles` |
| `0x8010a5e4` | `FsUitron_DelDirFiles` |
| `0x8010a738` | `FsUitron_OpenFile` |
| `0x8010a890` | `FsUitron_ScanDir` |
| `0x8010aa00` | `FsUitron_MoveFile` |
| `0x8010ad84` | `FsUitron_CopyToByName` |
| `0x8010b048` | `FsUitron_SetAttrib` |
| `0x8010b190` | `FsUitron_GetLongName` |
| `0x8010b2d8` | `FsUitron_GetAttrib` |
| `0x8010b63c` | `FsUitron_GetParam` |
| `0x8010b73c` | `FsUitron_Benchmark` |
| `0x8010ba98` | `FsUitron_RegisterCB` |
| `0x8010bb00` | `FsUitron_FormatAndLabel` |
| `0x8010bdcc` | `FsUitron_GetLabel` |
| `0x8010bef8` | `FsUitron_SetParam` |
| `0x8010c144` | `FsUitron_GetDiskInfo` |
| `0x8010c2f4` | `FsUitron_AllocFile` |
| `0x8010c468` | `FsUitron_TruncFile` |
| `0x8010c5dc` | `FsUitron_StatFile` |
| `0x8010c758` | `FsUitron_FlushFile` |
| `0x8010c89c` | `FsUitron_TellFile` |
| `0x8010ca10` | `FsUitron_SeekFile` |
| `0x8010cbb4` | `FsUitron_CloseFile` |
| `0x8010ccf8` | `FsUitron_WriteFile` |
| `0x8010ced4` | `FsUitron_ReadFile` |
| `0x8010d088` | `FsUitron_SetDateTime` |
| `0x8010d21c` | `FsUitron_GetDateTime` |
| `0x8010d7fc` | `FsUitron_Open` |

</details>

<details><summary><code>FTYPEIPC</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800028f0` | `FTYPEIPC_SEM_ID` |

</details>

<details><summary><code>FtypeIpc</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8028b9c8` | `FtypeIpc_Msg_SendCmd` |
| `0x8028ba54` | `FtypeIpc_Msg_WaitCmd` |

</details>

<details><summary><code>FWSRV</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x800050f4` | `FWSRV_FLG_ID` |
| `0x800050f4` | `FWSRV_SEM_ID` |

</details>

<details><summary><code>FwSrv</code> (9)</summary>

| 주소 | 이름 |
|---|---|
| `0x800df600` | `xFwSrv_Wrn` |
| `0x800df654` | `xFwSrv_Err` |
| `0x800e01c4` | `xFwSrv_CmdLinuxWrite` |
| `0x800e11fc` | `xFwSrv_CmdBinUpdateAllInOne` |
| `0x800e26a4` | `xFwSrv_CmdDecompress` |
| `0x800e27c4` | `xFwSrv_CmdDspRead` |
| `0x800e2bc8` | `xFwSrv_CmdeCosReadEx` |
| `0x800e3000` | `xFwSrv_CmdeCosRead` |
| `0x800e34a4` | `xFwSrv_CmdBinDePack` |

</details>

<details><summary><code>FwSrvCmd</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800e218c` | `xFwSrvCmd_LinuxLoad` |

</details>

<details><summary><code>FwSrvSxCmd</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x800e3fbc` | `xFwSrvSxCmd_Dump_eCos` |
| `0x800e42f4` | `xFwSrvSxCmd_Dump_uITRON` |

</details>

<details><summary><code>g</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801a4bf0` | `g_bUIFlowWndPlayNoImgWndOpened` |

</details>

<details><summary><code>gDisplayCtrl</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80006258` | `gDisplayCtrl_FlgID` |

</details>

<details><summary><code>Get</code> (13)</summary>

| 주소 | 이름 |
|---|---|
| `0x801c4314` | `Get_AntishakeValue` |
| `0x801c4378` | `Get_WDRValue` |
| `0x801c43dc` | `Get_SharpnessValue` |
| `0x801c4460` | `Get_DatePrintValue` |
| `0x801c44c4` | `Get_AFWindowValue` |
| `0x801c4510` | `Get_SceneModeValue` |
| `0x801c459c` | `Get_ISOValue` |
| `0x801c4674` | `Get_ColorValue` |
| `0x801c4700` | `Get_WBValue` |
| `0x801c47c0` | `Get_QualityValue` |
| `0x801c4844` | `Get_EVValue` |
| `0x801c4904` | `Get_FlashValue` |
| `0x801c49ac` | `Get_MacroValue` |

</details>

<details><summary><code>GetExpoSetting</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80166b28` | `GetExpoSetting_IMX206CQC` |

</details>

<details><summary><code>GetGainSetting</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801669bc` | `GetGainSetting_IMX206CQC` |

</details>

<details><summary><code>GetModeInfo</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801686e4` | `GetModeInfo_IMX206CQC` |

</details>

<details><summary><code>GetStatus</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80166e6c` | `GetStatus_IMX206CQC` |

</details>

<details><summary><code>gICF</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80005cfc` | `gICF_FlgID` |
| `0x80005cfc` | `gICF_M_FlgID` |

</details>

<details><summary><code>gICF2</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80005cfc` | `gICF2_FlgID` |

</details>

<details><summary><code>gIPC</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80005cfc` | `gIPC_FlgID` |
| `0x80005cfc` | `gIPC_FlgID2` |
| `0x80005cfc` | `gIPC_FlgID3` |

</details>

<details><summary><code>GPSRec</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8026b8c0` | `GPSRec_Open` |

</details>

<details><summary><code>graph</code> (23)</summary>

| 주소 | 이름 |
|---|---|
| `0x800bab24` | `graph_handleImageList` |
| `0x800bb178` | `graph_setConfig` |
| `0x800bb2f8` | `graph_flushAopCache` |
| `0x800bbbc4` | `graph_requestGOP` |
| `0x800bc088` | `graph_requestAOP` |
| `0x800bc088` | `graph_requestAOP1DLUT` |
| `0x800bc088` | `graph_requestAOP2DLUT` |
| `0x800bc088` | `graph_requestAOPACC` |
| `0x800bc088` | `graph_requestAOPAbsMinusSHF` |
| `0x800bc088` | `graph_requestAOPAlphaPlane` |
| `0x800bc088` | `graph_requestAOPBlend` |
| `0x800bc088` | `graph_requestAOPColorFilter` |
| `0x800bc088` | `graph_requestAOPColorKey` |
| `0x800bc088` | `graph_requestAOPColorKeyGE` |
| `0x800bc088` | `graph_requestAOPMPSHF` |
| `0x800bc088` | `graph_requestAOPMult` |
| `0x800bc088` | `graph_requestAOPText` |
| `0x800bc088` | `graph_requestAOPTextMult` |
| `0x800bea14` | `graph_gop0Layer3` |
| `0x800bea14` | `graph_gop0Layer4` |
| `0x800bea14` | `graph_gop1Layer2` |
| `0x800bea14` | `graph_gop1Layer3` |
| `0x800bea14` | `graph_gop1Layer4` |

</details>

<details><summary><code>gRSC</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80005580` | `gRSC_FlgID` |

</details>

<details><summary><code>gStitchEst</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800062f0` | `gStitchEst_FlgID` |

</details>

<details><summary><code>gStitchImg</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800062f0` | `gStitchImg_FlgID` |

</details>

<details><summary><code>GxDisplay</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x80179754` | `GxDisplay_EndDraw` |
| `0x80179834` | `GxDisplay_BeginDraw` |
| `0x801799c4` | `GxDisplay_SetPalette` |
| `0x80179b3c` | `GxDisplay_InitLayer` |
| `0x8017a970` | `GxDisplay_Get` |
| `0x8017aa98` | `GxDisplay_Set` |

</details>

<details><summary><code>GxDSP</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800d2fe0` | `xGxDSP_ChkFwHeaderValid` |

</details>

<details><summary><code>GxeCos</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x800d0f60` | `GxeCos_Close` |
| `0x800d1044` | `GxeCos_Open` |

</details>

<details><summary><code>GxeCosCmd</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800d1538` | `xGxeCosCmd_Open` |

</details>

<details><summary><code>GxFlash</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80294cc0` | `GxFlash_SuspendCharge` |

</details>

<details><summary><code>GxGfx</code> (9)</summary>

| 주소 | 이름 |
|---|---|
| `0x801dd304` | `GxGfx_Copy` |
| `0x801dd5c0` | `GxGfx_Convert` |
| `0x801ddfdc` | `GxGfx_Clear` |
| `0x801e16a4` | `GxGfx_TextInRect` |
| `0x801e1e78` | `GxGfx_Text` |
| `0x801e3294` | `GxGfx_TextPrintInRect` |
| `0x801ee840` | `GxGfx_PushStack` |
| `0x801ee8f8` | `GxGfx_Init` |
| `0x801f03d8` | `GxGfx_Image` |

</details>

<details><summary><code>GxImg</code> (30)</summary>

| 주소 | 이름 |
|---|---|
| `0x8018d330` | `GxImg_CalcPlaneRect` |
| `0x8018d484` | `GxImg_MapToDispObjFmt` |
| `0x8018d84c` | `GxImg_MapToImeInFmt` |
| `0x8018d958` | `GxImg_MapToImeOutFmt` |
| `0x8018da34` | `GxImg_MapToImeOutFmtType` |
| `0x8018dbbc` | `GxImg_ScaleAdjustRect` |
| `0x8018e068` | `GxImg_ScaleByFW` |
| `0x8018e488` | `GxImg_SetParm` |
| `0x8018e540` | `GxImg_ChkGetCopyRect` |
| `0x8018e958` | `GxImg_GetBufAddr` |
| `0x8018eb98` | `GxImg_CalcRequireSize` |
| `0x8018ecf8` | `GxImg_InitBufEx` |
| `0x8018eebc` | `GxImg_InitBuf` |
| `0x8018f220` | `GxImg_SelfRotate` |
| `0x8018f220` | `GxImg_SelfRotatebyGrph` |
| `0x8018fd98` | `GxImg_RotMapToGrphId` |
| `0x8018fd98` | `GxImg_RotateDataByGrph` |
| `0x80190364` | `GxImg_CopyBlendingDataEx` |
| `0x801909ac` | `GxImg_CopyColorkeyData` |
| `0x80191124` | `GxImg_CopyDataEx` |
| `0x80191488` | `GxImg_CopyBlendingData` |
| `0x80191a88` | `GxImg_FillDataEx` |
| `0x80191fc8` | `GxImg_MapToIMEScaleMethod` |
| `0x80191fc8` | `GxImg_ScaleByIME` |
| `0x80192754` | `GxImg_ScaleDataFine` |
| `0x80192840` | `GxImg_RotateDataEx` |
| `0x80192b34` | `GxImg_MapToISEScaleMethod` |
| `0x80192b34` | `GxImg_ScaleByISE` |
| `0x80192b34` | `GxImg_ScaleData` |
| `0x801932a8` | `GxImg_DumpBuf` |

</details>

<details><summary><code>GxImgFile</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x80193e08` | `GxImgFile_Config` |
| `0x80193f3c` | `GxImgFile_CombineJPG` |
| `0x8019434c` | `GxImgFile_EncodeByBitrate` |
| `0x801945a4` | `GxImgFile_DecodeByDownsample` |
| `0x801947c8` | `GxImgFile_AllocDecBuf` |
| `0x80194a3c` | `GxImgFile_ParseHeader` |

</details>

<details><summary><code>GxLinux</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x800d1d78` | `GxLinux_ChkCoreInfo` |
| `0x800d2128` | `GxLinux_ChkValiduBoot` |
| `0x800d2328` | `GxLinux_UpdUBI` |

</details>

<details><summary><code>GxPower</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x800d7058` | `GxPower_SetControl` |
| `0x800d7268` | `GxPower_GetControl` |
| `0x800d73e4` | `GxPower_MapBattLvl` |

</details>

<details><summary><code>GxSound</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x80294dec` | `GxSound_GetSoundDataByID` |
| `0x80294e54` | `GxSound_SetSoundTable` |
| `0x80294ebc` | `GxSound_GetSoundSRByID` |
| `0x80294f3c` | `GxSound_Control` |
| `0x8029515c` | `GxSound_Open` |
| `0x80295810` | `GxSound_AudAction` |

</details>

<details><summary><code>GxStrg</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x800e952c` | `GxStrg_SetConfigEx` |
| `0x800e99b4` | `GxStrg_GetDevice` |
| `0x800e9a1c` | `GxStrg_CloseDevice` |
| `0x800e9b2c` | `GxStrg_OpenDevice` |
| `0x800e9d90` | `GxStrg_GetDeviceCtrl` |
| `0x800e9f3c` | `GxStrg_Det` |

</details>

<details><summary><code>GxTimer</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x801f1cfc` | `GxTimer_StartTimer` |
| `0x801f1ec4` | `GxTimer_CountTimer` |

</details>

<details><summary><code>GxUSB</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x800d8020` | `GxUSB_UpdateConnectType` |
| `0x800d80c8` | `GxUSB_GetIsUSBPlug` |

</details>

<details><summary><code>GxVideo</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x80178030` | `GxVideo_SetDeviceCtrl` |
| `0x801785d4` | `GxVideo_CloseDevice` |
| `0x801786dc` | `GxVideo_OpenDevice` |
| `0x801788f8` | `GxVideo_ExitDevice` |

</details>

<details><summary><code>GxVidFile</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80295b30` | `GxVidFile_ParseVideoInfo` |
| `0x80295fb4` | `GxVidFile_DecodeThumbFrame` |
| `0x802963e0` | `GxVidFile_Decode1stFrame` |

</details>

<details><summary><code>gyro</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x8026c9e4` | `gyro_setFreeRunParam` |
| `0x8026caa4` | `gyro_getFreeRunData` |
| `0x8026ce24` | `gyro_setMode` |
| `0x8026d0f0` | `gyro_HandleGyroEvent` |
| `0x8026d38c` | `gyro_open` |

</details>

<details><summary><code>h264</code> (7)</summary>

| 주소 | 이름 |
|---|---|
| `0x80372dcc` | `h264_isr` |
| `0x80372ef4` | `h264_close2` |
| `0x803730b4` | `h264_open2` |
| `0x80373280` | `h264_setDecInitReg` |
| `0x803734f8` | `h264_setEncInitReg` |
| `0x803735f8` | `h264_close` |
| `0x80373710` | `h264_open` |

</details>

<details><summary><code>h264Dec</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80377914` | `h264Dec_prepareOnePicture` |
| `0x80377d84` | `h264Dec_initDecoder` |
| `0x80377d84` | `h264Dec_initInternalMemory` |

</details>

<details><summary><code>h264Enc</code> (12)</summary>

| 주소 | 이름 |
|---|---|
| `0x8029691c` | `h264Enc_getH264Header` |
| `0x8029698c` | `h264Enc_getResult` |
| `0x80296aa0` | `h264Enc_encodeOnePicture` |
| `0x80296aa0` | `h264Enc_updateInternalMemory` |
| `0x80296e3c` | `h264Enc_initEncoder` |
| `0x80296e3c` | `h264Enc_initInternalMemory` |
| `0x802975c0` | `h264Enc_updateCfg` |
| `0x80297a94` | `h264Enc_initCfg` |
| `0x80297a94` | `h264Enc_setupProfile` |
| `0x80297e70` | `h264Enc_getRegSetResult` |
| `0x802993a4` | `h264Enc_RcInit` |
| `0x80299920` | `h264Enc_writeHeader` |

</details>

<details><summary><code>hdmitx</code> (13)</summary>

| 주소 | 이름 |
|---|---|
| `0x80033a94` | `hdmitx_checkVideoStable` |
| `0x80033b0c` | `hdmitx_configAudio` |
| `0x80033b0c` | `hdmitx_configVideo` |
| `0x80033b0c` | `hdmitx_setConfig` |
| `0x800343dc` | `hdmitx_close` |
| `0x800357fc` | `hdmitx_verifyVideoID` |
| `0x800359a8` | `hdmitx_ddcReadByte` |
| `0x80035d68` | `hdmitx_parseDTD` |
| `0x80036184` | `hdmitx_ddcReadByte2` |
| `0x80036344` | `hdmitx_ddcRead` |
| `0x800365c0` | `hdmitx_initDDC` |
| `0x800365c0` | `hdmitx_parseEDID` |
| `0x800365c0` | `hdmitx_parseExtBlock` |

</details>

<details><summary><code>HFSNVT</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80002c80` | `HFSNVT_FLG_ID` |
| `0x80002c80` | `HFSNVT_SEM_ID` |

</details>

<details><summary><code>HfsNvt</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80002c80` | `HfsNvt_MainTsk` |
| `0x801f2100` | `xHfsNvt_SendIPC` |
| `0x801f273c` | `HfsNvt_Open` |

</details>

<details><summary><code>hide</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8016c258` | `hide_logo` |

</details>

<details><summary><code>HwClock</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x800145a0` | `HwClock_SetTime` |
| `0x80014834` | `HwClock_GetTime` |

</details>

<details><summary><code>HwPower</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80014420` | `HwPower_GetPowerKey` |
| `0x80014520` | `HwPower_GetPowerOnState` |

</details>

<details><summary><code>i2c2</code> (8)</summary>

| 주소 | 이름 |
|---|---|
| `0x80047bbc` | `i2c2_getConfig` |
| `0x80047e34` | `i2c2_receive` |
| `0x8004818c` | `i2c2_setConfig` |
| `0x80048770` | `i2c2_unlock` |
| `0x80048894` | `i2c2_lock` |
| `0x80048da0` | `i2c2_close` |
| `0x80048e74` | `i2c2_open` |
| `0x80048f6c` | `i2c2_transmit` |

</details>

<details><summary><code>i2c3</code> (8)</summary>

| 주소 | 이름 |
|---|---|
| `0x80049630` | `i2c3_getConfig` |
| `0x800498a8` | `i2c3_receive` |
| `0x80049c00` | `i2c3_setConfig` |
| `0x8004a1e4` | `i2c3_unlock` |
| `0x8004a308` | `i2c3_lock` |
| `0x8004a7a8` | `i2c3_close` |
| `0x8004a87c` | `i2c3_open` |
| `0x8004a980` | `i2c3_transmit` |

</details>

<details><summary><code>ICF</code> (44)</summary>

| 주소 | 이름 |
|---|---|
| `0x802d685c` | `ICF_FLOW_A` |
| `0x802d685c` | `ICF_FLOW_C` |
| `0x802d7b20` | `ICF_M_SetCtrlType` |
| `0x802d7c10` | `ICF_M_TrigEvent` |
| `0x802d7c98` | `ICF_GetEngOPMode` |
| `0x802d7d58` | `ICF_WaitICFProcEnd` |
| `0x802d85fc` | `ICF_TrigEvent` |
| `0x802d8c88` | `ICF_UnlockFlag` |
| `0x802d8d60` | `ICF_GetFlag` |
| `0x802d8e18` | `ICF_LockFlag` |
| `0x802d8ef4` | `ICF_M_Tsk_Type13` |
| `0x802d90c0` | `ICF_M_Tsk_Type22` |
| `0x802d92e0` | `ICF_ClrMCmdEvent` |
| `0x802d9378` | `ICF_SetMCmdEvent` |
| `0x802d9424` | `ICF_GetMask` |
| `0x802d9a00` | `ICF_SetTimer` |
| `0x802d9ad0` | `ICF_CfgTimerParams` |
| `0x802f1234` | `ICF_FA_QUERY` |
| `0x802f1a58` | `ICF_FA_RUNTIMECHG` |
| `0x802f2350` | `ICF_FA_CLOSE` |
| `0x802f26f0` | `ICF_FA_PAUSE` |
| `0x802f295c` | `ICF_FA_START` |
| `0x802f3b10` | `ICF_FA_OPEN` |
| `0x802f600c` | `ICF_FC_QUERY` |
| `0x802f6494` | `ICF_FC_PAUSE` |
| `0x802f7f6c` | `ICF_FC_TimerTrigProc` |
| `0x802f8e44` | `ICF_FC_RawHeader_CtrlCB` |
| `0x802fb8d0` | `ICF_FC_START` |
| `0x802fdf68` | `ICF_FC_RUNTIMECHG` |
| `0x80301f1c` | `ICF_FC_CLOSE` |
| `0x80302808` | `ICF_FC_OPEN` |
| `0x80302d60` | `ICF_FC_GetSIExCh12BufAddr` |
| `0x80302d60` | `ICF_FC_SIEx_FLDEND_CCIR_ISR` |
| `0x80303a00` | `ICF_FC_SIE2_FLDEND_ISR` |
| `0x80303ed4` | `ICF_FC_SIE1_FLDEND_ISR` |
| `0x8030583c` | `ICF_FD_RUNTIMECHG` |
| `0x80305f5c` | `ICF_FD_QUERY` |
| `0x8030618c` | `ICF_FD_TimerTrigProc` |
| `0x803099d4` | `ICF_FD_SIE1_FLDEND_ISR` |
| `0x8030b21c` | `ICF_FD_START` |
| `0x8030bf64` | `ICF_FD_CLOSE` |
| `0x8030c468` | `ICF_FD_PAUSE` |
| `0x8030ca6c` | `ICF_FD_SIE2_FLDEND_ISR` |
| `0x8030ccd0` | `ICF_FD_OPEN` |

</details>

<details><summary><code>ICFFunc</code> (10)</summary>

| 주소 | 이름 |
|---|---|
| `0x802f0a10` | `ICFFunc_GetCtrlObj` |
| `0x802f0a94` | `ICFFunc_Module_Unlock` |
| `0x802f0b10` | `ICFFunc_Module_Lock` |
| `0x802f0b84` | `ICFFunc_Resume` |
| `0x802f0c2c` | `ICFFunc_Pause` |
| `0x802f0ebc` | `ICFFunc_GetTaskObj` |
| `0x802f0ebc` | `ICFFunc_TrigEvent` |
| `0x802f0f84` | `ICFFunc_IsPause` |
| `0x802f104c` | `ICFFunc_Close` |
| `0x802f10f0` | `ICFFunc_Open` |

</details>

<details><summary><code>ide</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8004098c` | `ide_isr` |

</details>

<details><summary><code>ide2</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800407ec` | `ide2_isr` |

</details>

<details><summary><code>idec</code> (31)</summary>

| 주소 | 이름 |
|---|---|
| `0x80037488` | `idec_getFDColor` |
| `0x800375b8` | `idec_getFDWinBord` |
| `0x800376f4` | `idec_getFDWinDim` |
| `0x8003781c` | `idec_getFDWinPos` |
| `0x80038700` | `idec_setFDColor` |
| `0x8003884c` | `idec_setFDWinBord` |
| `0x800389b0` | `idec_setFDWinDim` |
| `0x80038ae8` | `idec_setFDWinPos` |
| `0x80038c20` | `idec_setFDDis` |
| `0x80038ce8` | `idec_setFDEn` |
| `0x80039bac` | `idec_setOutComp` |
| `0x8003ae1c` | `idec_setEven` |
| `0x8003ae9c` | `idec_setOdd` |
| `0x8003afa8` | `idec_setDevice` |
| `0x8003b104` | `idec_setAlphaBlending` |
| `0x8003caa4` | `idec_setO1BurstLen` |
| `0x8003cb50` | `idec_setO2Fmt` |
| `0x8003cbe4` | `idec_setO1Fmt` |
| `0x8003d538` | `idec_setV1BurstLen` |
| `0x8003d5e4` | `idec_setVideoColorKeyOp` |
| `0x8003d768` | `idec_setV2Fmt` |
| `0x8003d980` | `idec_setV1Fmt` |
| `0x8003e820` | `idec_waitFrameEnd` |
| `0x8003e968` | `idec_setVideoBufferContent` |
| `0x8003eca8` | `idec_getShadowPaletteGroup` |
| `0x8003ee7c` | `idec_getPaletteGroupACrCbY` |
| `0x8003f08c` | `idec_getPaletteGroup` |
| `0x8003f230` | `idec_setPaletteGroupACrCbY` |
| `0x8003f41c` | `idec_setPaletteGroup` |
| `0x8003f5c0` | `idec_setOsdWinAttrEx` |
| `0x8003fdf4` | `idec_setVideoWinAttrEx` |

</details>

<details><summary><code>ife</code> (14)</summary>

| 주소 | 이름 |
|---|---|
| `0x80127000` | `ife_setDmaInAddr` |
| `0x80127098` | `ife_setOpMode` |
| `0x80127194` | `ife_checkOpMode` |
| `0x80127250` | `ife_chkStateMachine` |
| `0x80127504` | `ife_changeROI` |
| `0x801277c0` | `ife_setInSize` |
| `0x801278c4` | `ife_setRangeTh_A` |
| `0x80127bcc` | `ife_setRangeTh_B` |
| `0x80127ef8` | `ife_changeParam` |
| `0x80128304` | `ife_getClockRate` |
| `0x80128470` | `ife_changeAll` |
| `0x80128af8` | `ife_setMode` |
| `0x8012924c` | `ife_setClockRate` |
| `0x80129548` | `ife_isr` |

</details>

<details><summary><code>IFE</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x803168cc` | `IFE_GetVigSetting` |
| `0x80335d3c` | `IFE_D2D_CB` |
| `0x8033a750` | `IFE_IQparam` |

</details>

<details><summary><code>ife2</code> (15)</summary>

| 주소 | 이름 |
|---|---|
| `0x8012a420` | `ife2_checkDmaAddr` |
| `0x8012ac5c` | `ife2_setEngineControl` |
| `0x8012b76c` | `ife2_start` |
| `0x8012b83c` | `ife2_chgDstFmt` |
| `0x8012b964` | `ife2_chgSrcFmt` |
| `0x8012bb38` | `ife2_pause` |
| `0x8012be90` | `ife2_getClockRate` |
| `0x8012bf30` | `ife2_chgInSize` |
| `0x8012c070` | `ife2_chgFilterParam` |
| `0x8012c440` | `ife2_chgRefCenterParam` |
| `0x8012c7c0` | `ife2_chgDmaAddr` |
| `0x8012cb90` | `ife2_chgLineoffset` |
| `0x8012ce64` | `ife2_setMode` |
| `0x8012d260` | `ife2_close` |
| `0x8012d330` | `ife2_open` |

</details>

<details><summary><code>IFE2</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80336114` | `IFE2_CAP_D2D_CB` |
| `0x80336114` | `IFE2_D2D_CB` |
| `0x8033c588` | `IFE2_IQparam` |

</details>

<details><summary><code>IFE2D2D</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8030f710` | `IFE2D2D_start` |

</details>

<details><summary><code>IFED2D</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8030fc88` | `IFED2D_wait` |
| `0x8030ff3c` | `IFED2D_start` |

</details>

<details><summary><code>IFEIME</code> (8)</summary>

| 주소 | 이름 |
|---|---|
| `0x80335740` | `IFEIME_CAP_D2D_IMECB` |
| `0x80335740` | `IFEIME_D2D_IMECB` |
| `0x80335868` | `IFEIME_CAP_D2D_IPECB` |
| `0x80335868` | `IFEIME_D2D_IPECB` |
| `0x80335994` | `IFEIME_CAP_D2D_IFECB` |
| `0x80335994` | `IFEIME_D2D_IFECB` |
| `0x80335ee8` | `IFEIME_CAP_D2D_DCECB` |
| `0x80335ee8` | `IFEIME_D2D_DCECB` |

</details>

<details><summary><code>IFEIMED2D</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8030e52c` | `IFEIMED2D_start` |

</details>

<details><summary><code>ImageApp</code> (12)</summary>

| 주소 | 이름 |
|---|---|
| `0x801f3d18` | `ImageApp_CamMovie_Config` |
| `0x801f455c` | `ImageApp_CamPhoto_Config` |
| `0x801f47d8` | `ImageApp_IPCam_Config` |
| `0x801f4904` | `ImageApp_NetMovie_Config` |
| `0x801f4b1c` | `ImageApp_NetMovie_RecStop` |
| `0x801f4c94` | `ImageApp_NetMovie_RecStart` |
| `0x801f5938` | `ImageApp_NetPhoto_Config` |
| `0x801f59f4` | `ImageApp_NetPhoto_Open` |
| `0x801f602c` | `ImageApp_UsbMovie_Config` |
| `0x801f6460` | `xImageApp_UsbMovie_StopVideoCB` |
| `0x801f6d20` | `xImageApp_UsbMovie_GetH264HeaderCB` |
| `0x801f6f50` | `xImageApp_UsbMovie_StartVideoCB` |

</details>

<details><summary><code>ImageStream</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x801f841c` | `ImageStream_SetActive` |
| `0x801f84bc` | `ImageStream_UpdateSize` |
| `0x801f89a8` | `ImageStream_Close` |
| `0x801f8b8c` | `ImageStream_SetMode` |
| `0x801f9c18` | `ImageStream_Open` |

</details>

<details><summary><code>ImageUnit</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x801f80fc` | `ImageUnit_CfgOut` |
| `0x801f823c` | `ImageUnit_Out` |
| `0x801f82bc` | `ImageUnit_In` |
| `0x801f8738` | `ImageUnit_End` |
| `0x801f87d4` | `ImageUnit_Begin` |

</details>

<details><summary><code>ime</code> (98)</summary>

| 주소 | 이름 |
|---|---|
| `0x801319b8` | `ime_calScaleFilterCoef` |
| `0x80131a50` | `ime_setOutPath_ScaleFilter_P4` |
| `0x80131a98` | `ime_chkLineoffset` |
| `0x80131b44` | `ime_chkDmaAddr` |
| `0x80131c40` | `ime_calHVStripParam` |
| `0x801320b8` | `ime_setAdas_ROI` |
| `0x801322e0` | `ime_setAdas_Histogram` |
| `0x801323fc` | `ime_setAdas_EdgeKernel` |
| `0x80132560` | `ime_setDS_ColorLutInfo` |
| `0x8013266c` | `ime_setDS_P1Set3_IqInfo` |
| `0x80132794` | `ime_setDS_P1Set2_IqInfo` |
| `0x801328bc` | `ime_setDS_P1Set1_IqInfo` |
| `0x80132a10` | `ime_setDS_P1Set0_IqInfo` |
| `0x80132b38` | `ime_setGN_IqInfo` |
| `0x80132c3c` | `ime_setSSR_IqInfo` |
| `0x80132d64` | `ime_setDBCS_IqInfo` |
| `0x80132f44` | `ime_setILA_LumaSuppressInfo` |
| `0x801330b0` | `ime_setILA_ChromaAdaptInfo` |
| `0x801332c0` | `ime_setILA_ChromaAdjustInfo` |
| `0x80133424` | `ime_setILA_ScaleFactor` |
| `0x801336e0` | `ime_setOutPath_DmaAddr_P4` |
| `0x80133764` | `ime_setOutPath_Lineoffset_P4` |
| `0x801337e0` | `ime_setOutPath_OutputCropSize_P4` |
| `0x801338dc` | `ime_setOutPath_ScaleSize_P4` |
| `0x80133978` | `ime_setOutPath_ScaleFactor_P4` |
| `0x801339ec` | `ime_setOutPath_Enhance_P4` |
| `0x80133c68` | `ime_setOutPath_DmaAddr_P3` |
| `0x80133cec` | `ime_setOutPath_Lineoffset_P3` |
| `0x80133d68` | `ime_setOutPath_OutputCropSize_P3` |
| `0x80133e64` | `ime_setOutPath_ScaleSize_P3` |
| `0x80133f00` | `ime_setOutPath_ScaleFilter_P3` |
| `0x80133fb4` | `ime_setOutPath_ScaleFactor_P3` |
| `0x80134118` | `ime_setOutPath_Enhance_P3` |
| `0x801343a8` | `ime_setOutPath_DmaAddr_P2` |
| `0x8013442c` | `ime_setOutPath_Lineoffset_P2` |
| `0x801344d0` | `ime_setOutPath_OutputCropSize_P2` |
| `0x801345cc` | `ime_setOutPath_ScaleSize_P2` |
| `0x80134668` | `ime_setOutPath_ScaleFilter_P2` |
| `0x8013471c` | `ime_setOutPath_ScaleFactor_P2` |
| `0x80134880` | `ime_setOutPath_Enhance_P2` |
| `0x80134b10` | `ime_setOutPath_DmaAddr_P1` |
| `0x80134b94` | `ime_setOutPath_Lineoffset_P1` |
| `0x80134c38` | `ime_setOutPath_OutputCropSize_P1` |
| `0x80134d34` | `ime_setOutPath_ScaleSize_P1` |
| `0x80134dd0` | `ime_setOutPath_ScaleFilter_P1` |
| `0x80134e84` | `ime_setOutPath_ScaleFactor_P1` |
| `0x80134fe8` | `ime_setOutPath_Enhance_P1` |
| `0x80135304` | `ime_setInPath_ImageSize` |
| `0x801356a0` | `ime_setInPath_StripeInfo` |
| `0x801357e0` | `ime_chkInputPathStripe` |
| `0x80135d94` | `ime_setInPath` |
| `0x80135f58` | `ime_setDS_P1Set3_ImageInfo` |
| `0x801360b8` | `ime_setDS_P1Set2_ImageInfo` |
| `0x80136218` | `ime_setDS_P1Set1_ImageInfo` |
| `0x80136378` | `ime_setDS_P1Set0_ImageInfo` |
| `0x801364d0` | `ime_setILA_InputImageInfo` |
| `0x80136a38` | `ime_calImageScaleParam` |
| `0x80136f34` | `ime_setOutPath_P1` |
| `0x801373c0` | `ime_setOutPath_P2` |
| `0x80137844` | `ime_setOutPath_P3` |
| `0x80137cc8` | `ime_setOutPath_P4` |
| `0x80139300` | `ime_chgStitchingEnable` |
| `0x80139480` | `ime_chgStatisticEdgeROIParam` |
| `0x80139620` | `ime_chgStatisticHistogramParam` |
| `0x801397ac` | `ime_chgStatisticEdgeKerParam` |
| `0x801398dc` | `ime_chgStatisticalImageOutputType` |
| `0x801399c8` | `ime_chgStatisticFilterEnable` |
| `0x80139acc` | `ime_chgStatisticEnable` |
| `0x8013a3dc` | `ime_pause` |
| `0x8013a4d0` | `ime_setStart` |
| `0x8013a63c` | `ime_chgStripeParam` |
| `0x8013ae1c` | `ime_chgOutputPathParam` |
| `0x8013b158` | `ime_chgInputPathParam` |
| `0x8013b2f4` | `ime_close` |
| `0x8013b4b8` | `ime_chgDataStampColorLutParam` |
| `0x8013b598` | `ime_chgDataStampParam` |
| `0x8013b758` | `ime_chgDataStampImageParam` |
| `0x8013b918` | `ime_chgDataStampEnable` |
| `0x8013ba90` | `ime_chgProgressiveToInterlaceEnable` |
| `0x8013bb58` | `ime_chgFilmGrainNoiseParam` |
| `0x8013bc60` | `ime_chgFilmGrainNoiseEnable` |
| `0x8013bd28` | `ime_chgSingleSuperResParam` |
| `0x8013be30` | `ime_chgSingleSuperResEnable` |
| `0x8013bf74` | `ime_chgDrkBrtChromaSuppressParam` |
| `0x8013c07c` | `ime_chgDrkBrtChromaSuppressEnable` |
| `0x8013c144` | `ime_chgColorSpaceTransformEnable` |
| `0x8013c22c` | `ime_chgChromaAdaptLumaSuppressParam` |
| `0x8013c334` | `ime_chgChromaAdaptParam` |
| `0x8013c43c` | `ime_chgChromaAdaptChromaAdjustParam` |
| `0x8013c544` | `ime_chgChromaAdaptImageParam` |
| `0x8013c64c` | `ime_chgChromaAdaptEnable` |
| `0x8013c74c` | `ime_chgChromaMedianFilterEnable` |
| `0x8013c814` | `ime_chgOutputScalingFilterParam` |
| `0x8013c974` | `ime_chgOutputScalingEnhanceParam` |
| `0x8013cad4` | `ime_chgOutputPathDramOutEnable` |
| `0x8013cc1c` | `ime_chgOutputPathEnable` |
| `0x8013cd64` | `ime_setMode` |
| `0x8013d654` | `ime_open` |

</details>

<details><summary><code>IME</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80335c90` | `IME_D2D_CB` |
| `0x8033baa4` | `IME_IQparam` |

</details>

<details><summary><code>IMED2D</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8030f244` | `IMED2D_start` |

</details>

<details><summary><code>ImeOutAddr</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x802f4b68` | `ImeOutAddr_FA` |

</details>

<details><summary><code>ImeOutGetAddr</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x802f8608` | `ImeOutGetAddr_FC` |
| `0x80306a54` | `ImeOutGetAddr_FD` |

</details>

<details><summary><code>IMG</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x8035a1f0` | `IMG_CapNormalAssignBuf` |
| `0x8035df08` | `IMG_CapEBurstAssignBuf` |
| `0x80360b5c` | `IMG_CapHDRAssignBuf` |
| `0x80362f00` | `IMG_CapSimAssignBuf` |
| `0x80366358` | `IMG_CapMultInAssignBuf` |
| `0x8036963c` | `IMG_CapDualSBSAssignBuf` |

</details>

<details><summary><code>ImgBackground</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8036b828` | `ImgBackground_Close` |
| `0x8036b898` | `ImgBackground_Open` |

</details>

<details><summary><code>ImgCap</code> (55)</summary>

| 주소 | 이름 |
|---|---|
| `0x803536e0` | `ImgCap_EvtAssignBuf` |
| `0x803536e0` | `ImgCap_EvtEnter` |
| `0x803536e0` | `ImgCap_EvtExit` |
| `0x803536e0` | `ImgCap_EvtProc` |
| `0x80353a34` | `ImgCap_RawClose` |
| `0x80353a9c` | `ImgCap_RawOpen` |
| `0x803548a8` | `ImgCap_GetWriteFileEvent` |
| `0x8035490c` | `ImgCap_GetEncEvent` |
| `0x80354970` | `ImgCap_GetProc2Event` |
| `0x803549d4` | `ImgCap_GetProcEvent` |
| `0x80354a38` | `ImgCap_GetCapEvent` |
| `0x80354c50` | `ImgCap_SetUIInfo` |
| `0x80354d28` | `ImgCap_GetUIInfo` |
| `0x803550a0` | `ImgCap_AdjImgInfo` |
| `0x803552bc` | `ImgCap_YGenYCCImgInfo` |
| `0x80355584` | `ImgCap_AdjCtrlImgSize` |
| `0x80355870` | `ImgCap_DataStamp` |
| `0x80355a9c` | `ImgCap_EncBS` |
| `0x80355dbc` | `ImgCap_FormJpg` |
| `0x80356224` | `ImgCap_Ife2Filter` |
| `0x80356338` | `ImgCap_ImeScale` |
| `0x80356874` | `ImgCap_ife2Ime` |
| `0x80356e0c` | `ImgCap_RdeDECRawBS` |
| `0x80356fcc` | `ImgCap_DREFilter` |
| `0x80357214` | `ImgCap_ImeScaleWaitEnd` |
| `0x80357280` | `ImgCap_IseScaleWaitEnd` |
| `0x803572ec` | `ImgCap_IseScale` |
| `0x803574e8` | `ImgCap_Ife2ImeWaitEnd` |
| `0x8035759c` | `ImgCap_CBMsgProc` |
| `0x8035764c` | `ImgCap_NormalExit` |
| `0x803576c4` | `ImgCap_Normal` |
| `0x80357c94` | `ImgCap_NormalEnter` |
| `0x80357c94` | `ImgCap_NormalGetEventId` |
| `0x8035b03c` | `ImgCap_EBurstExit` |
| `0x8035b0b4` | `ImgCap_EBurst` |
| `0x8035b0b4` | `ImgCap_EBurstWriteHeader` |
| `0x8035b78c` | `ImgCap_EBurstEnter` |
| `0x8035ec1c` | `ImgCap_HDRExit` |
| `0x8035ec94` | `ImgCap_HDR` |
| `0x8035eedc` | `ImgCap_MFHDREnter` |
| `0x8035eff0` | `ImgCap_HDREnter` |
| `0x80361474` | `ImgCap_SimExit` |
| `0x803614c4` | `ImgCap_Sim` |
| `0x80361714` | `ImgCap_SimEnter` |
| `0x80363578` | `ImgCap_MultInExit` |
| `0x803635f0` | `ImgCap_MultIn` |
| `0x80363c80` | `ImgCap_MultInEnter` |
| `0x80363c80` | `ImgCap_MultInGetEventId` |
| `0x803671e0` | `ImgCap_DualSBSExit` |
| `0x80367258` | `ImgCap_DualSBS` |
| `0x8036751c` | `ImgCap_DualSBSEnter` |
| `0x8036a16c` | `ImgCap_WaitFinish` |
| `0x8036a200` | `ImgCap_StartCapture` |
| `0x8036bb7c` | `ImgCap_GetBuf` |
| `0x8036bc54` | `ImgCap_SetBuf` |

</details>

<details><summary><code>ImgEnc</code> (23)</summary>

| 주소 | 이름 |
|---|---|
| `0x803544f0` | `ImgEnc_EvtEnter` |
| `0x803544f0` | `ImgEnc_EvtExit` |
| `0x803544f0` | `ImgEnc_EvtProc` |
| `0x803547b4` | `ImgEnc_Close` |
| `0x8035481c` | `ImgEnc_Open` |
| `0x80359b10` | `ImgEnc_NormalExit` |
| `0x80359b60` | `ImgEnc_NormalEnter` |
| `0x80359bb0` | `ImgEnc_Normal` |
| `0x8035d81c` | `ImgEnc_EBurstEnter` |
| `0x8035d874` | `ImgEnc_EBurstExit` |
| `0x8035d8d4` | `ImgEnc_EBurst` |
| `0x80360840` | `ImgEnc_HDREnter` |
| `0x80360898` | `ImgEnc_HDRExit` |
| `0x803608f8` | `ImgEnc_HDR` |
| `0x80362bf8` | `ImgEnc_SimEnter` |
| `0x80362c3c` | `ImgEnc_SimExit` |
| `0x80362d0c` | `ImgEnc_Sim` |
| `0x80365c58` | `ImgEnc_MultInExit` |
| `0x80365ca8` | `ImgEnc_MultInEnter` |
| `0x80365cf8` | `ImgEnc_MultIn` |
| `0x80369320` | `ImgEnc_DualSBSEnter` |
| `0x80369378` | `ImgEnc_DualSBSExit` |
| `0x803693d8` | `ImgEnc_DualSBS` |

</details>

<details><summary><code>ImgProc</code> (21)</summary>

| 주소 | 이름 |
|---|---|
| `0x80353bf0` | `ImgProc_EvtEnter` |
| `0x80353bf0` | `ImgProc_EvtExit` |
| `0x80353bf0` | `ImgProc_EvtProc` |
| `0x80353eb4` | `ImgProc_Close` |
| `0x80353f1c` | `ImgProc_Open` |
| `0x80357f74` | `ImgProc_NormalEnter` |
| `0x80357fc4` | `ImgProc_NormalExit` |
| `0x803580d4` | `ImgProc_Normal` |
| `0x8035b974` | `ImgProc_EBurstEnter` |
| `0x8035b9c4` | `ImgProc_EBurstExit` |
| `0x8035bb20` | `ImgProc_EBurst` |
| `0x8035bb20` | `ImgProc_EBurstRawDec` |
| `0x8035f12c` | `ImgProc_HDREnter` |
| `0x8035f17c` | `ImgProc_HDRExit` |
| `0x80361860` | `ImgProc_SimExit` |
| `0x80364054` | `ImgProc_MultInEnter` |
| `0x803640a4` | `ImgProc_MultInExit` |
| `0x80364230` | `ImgProc_MultIn` |
| `0x8036768c` | `ImgProc_DualSBSEnter` |
| `0x803676dc` | `ImgProc_DualSBSExit` |
| `0x803677bc` | `ImgProc_DualSBS` |

</details>

<details><summary><code>ImgProc2</code> (20)</summary>

| 주소 | 이름 |
|---|---|
| `0x80354070` | `ImgProc2_EvtEnter` |
| `0x80354070` | `ImgProc2_EvtExit` |
| `0x80354070` | `ImgProc2_EvtProc` |
| `0x80354334` | `ImgProc2_Close` |
| `0x8035439c` | `ImgProc2_Open` |
| `0x80358d20` | `ImgProc2_NormalExit` |
| `0x80358d70` | `ImgProc2_NormalEnter` |
| `0x80358dc0` | `ImgProc2_Normal` |
| `0x8035c944` | `ImgProc2_EBurstExit` |
| `0x8035c994` | `ImgProc2_EBurstEnter` |
| `0x8035c9e4` | `ImgProc2_EBurst` |
| `0x8035fd2c` | `ImgProc2_HDRExit` |
| `0x8035fd7c` | `ImgProc2_HDREnter` |
| `0x803621b0` | `ImgProc2_SimExit` |
| `0x803621f4` | `ImgProc2_SimEnter` |
| `0x80364e28` | `ImgProc2_MultInExit` |
| `0x80364e78` | `ImgProc2_MultInEnter` |
| `0x80364ec8` | `ImgProc2_MultIn` |
| `0x80368504` | `ImgProc2_DualSBSExit` |
| `0x80368554` | `ImgProc2_DualSBSEnter` |

</details>

<details><summary><code>ImgStat</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8039efbc` | `ImgStat_CalBayerImg` |
| `0x8039efbc` | `ImgStat_SetCAOutAddr` |

</details>

<details><summary><code>ImgWriteFile</code> (20)</summary>

| 주소 | 이름 |
|---|---|
| `0x8035aaf8` | `ImgWriteFile_NormalEnter` |
| `0x8035ab48` | `ImgWriteFile_NormalExit` |
| `0x8035abbc` | `ImgWriteFile_Normal` |
| `0x8035e70c` | `ImgWriteFile_EBurstExit` |
| `0x8035e760` | `ImgWriteFile_EBurstEnter` |
| `0x8035e7b0` | `ImgWriteFile_EBurst` |
| `0x80361190` | `ImgWriteFile_HDREnter` |
| `0x803611e0` | `ImgWriteFile_HDRExit` |
| `0x80361254` | `ImgWriteFile_HDR` |
| `0x80366c9c` | `ImgWriteFile_MultInEnter` |
| `0x80366cec` | `ImgWriteFile_MultInExit` |
| `0x80366d60` | `ImgWriteFile_MultIn` |
| `0x80369cfc` | `ImgWriteFile_DualSBSEnter` |
| `0x80369d4c` | `ImgWriteFile_DualSBSExit` |
| `0x80369dc0` | `ImgWriteFile_DualSBS` |
| `0x8036b310` | `ImgWriteFile_EvtEnter` |
| `0x8036b310` | `ImgWriteFile_EvtExit` |
| `0x8036b310` | `ImgWriteFile_EvtProc` |
| `0x8036b5e0` | `ImgWriteFile_Close` |
| `0x8036b648` | `ImgWriteFile_Open` |

</details>

<details><summary><code>init</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x800e62a4` | `init_embmem` |
| `0x800e6ae8` | `init_fws` |
| `0x800e6d34` | `init_ps` |
| `0x800e73d0` | `init_fs` |

</details>

<details><summary><code>int</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8009b5f0` | `int_setConfig` |

</details>

<details><summary><code>IO</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800c192c` | `IO_InitADC` |

</details>

<details><summary><code>IPC</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x802da728` | `IPC_WaitVD2` |
| `0x802da990` | `IPC_D2D_Start` |
| `0x802db42c` | `IPC_D2D_End` |
| `0x802dba5c` | `IPC_WaitImeFMD2` |
| `0x8039a920` | `IPC_PAUSE` |
| `0x8039a9b8` | `IPC_RUN` |

</details>

<details><summary><code>ipe</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x8013e33c` | `ipe_stateMachine` |
| `0x8013e830` | `ipe_setLoad` |
| `0x8013e99c` | `ipe_changeOutYC` |
| `0x8013eca8` | `ipe_changeInput` |
| `0x8013eca8` | `ipe_setOpMode` |
| `0x801410dc` | `ipe_setClockRate` |

</details>

<details><summary><code>IPE</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x803172d4` | `IPE_Gamma` |
| `0x80335dec` | `IPE_D2D_CB` |
| `0x80338d6c` | `IPE_IQparam` |

</details>

<details><summary><code>IPED2D</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x803107a8` | `IPED2D_start` |

</details>

<details><summary><code>IPL</code> (164)</summary>

| 주소 | 이름 |
|---|---|
| `0x80005b40` | `IPL_FlgID` |
| `0x80006258` | `IPL_DisplayCtrl_Tsk` |
| `0x800062f0` | `IPL_StitchEst_Tsk` |
| `0x800062f0` | `IPL_StitchImg_Tsk` |
| `0x802cca04` | `IPL_SetCmdSETObj` |
| `0x802ccaa0` | `IPL_SetCmdGETObj` |
| `0x802ccb3c` | `IPL_GetCmd` |
| `0x802ccc10` | `IPL_SetCmd` |
| `0x802cd0f0` | `IPL_InitCmdGet` |
| `0x802cd0f0` | `IPL_InitCmdSet` |
| `0x802cd0f0` | `IPL_OpenTsk` |
| `0x802cd544` | `IPL_GetCurStatus` |
| `0x802cd5ac` | `IPL_GetCurMode` |
| `0x802cd624` | `IPL_ChkModeState` |
| `0x802cd7c8` | `IPL_GetRDECurRawInfo` |
| `0x802cd874` | `IPL_GetLASetInfo` |
| `0x802cd924` | `IPL_GetCASetInfo` |
| `0x802cd9d4` | `IPL_GetCapInfor` |
| `0x802cda80` | `IPL_GetCurCapCh3RawInfor` |
| `0x802cdb48` | `IPL_GetCurCapCh0RawInfor` |
| `0x802cdc10` | `IPL_GetDREWorkBufInfo` |
| `0x802cdcd0` | `IPL_DumpDataStatus` |
| `0x802ce148` | `IPL_GetCurCtrlFlow` |
| `0x802ce1c8` | `IPL_GetDCENorFactorInfo` |
| `0x802ce298` | `IPL_GetSIECurFrameInfo` |
| `0x802ce33c` | `IPL_GetCAInfo` |
| `0x802ce46c` | `IPL_GetDZoomInfo` |
| `0x802ce4f0` | `IPL_GetMaxCapRawInfor` |
| `0x802ce5ac` | `IPL_GetImeCurInfo` |
| `0x802ce968` | `IPL_GetCurIplInfo` |
| `0x802cea30` | `IPL_SetDZoom_WaitEnd` |
| `0x802cea90` | `IPL_SetVA` |
| `0x802ced48` | `IPL_SetImgRatio` |
| `0x802cf048` | `IPL_SetResumeDMA` |
| `0x802cf118` | `IPL_SetPauseDMA` |
| `0x802cf1e8` | `IPL_GetCapRaw` |
| `0x802cf2a0` | `IPL_SetWakeup` |
| `0x802cf3bc` | `IPL_SetSleep` |
| `0x802cf4d8` | `IPL_SetDZoom` |
| `0x802cf644` | `IPL_SetIme` |
| `0x802cf8ac` | `IPL_ChgMode` |
| `0x802cf8ac` | `IPL_SetModeInfo` |
| `0x802d0cdc` | `IPL_GetImeInfo` |
| `0x802d1b3c` | `IPL_GetVAInfo` |
| `0x802d1dc0` | `IPL_GetLAInfo` |
| `0x802d357c` | `IPL_UTI_CONV2_DS_FMT` |
| `0x802d3630` | `IPL_UTI_CONV2_IQS_ID` |
| `0x802d367c` | `IPL_UTI_CONV2_AWB_ID` |
| `0x802d36c8` | `IPL_UTI_CONV2_AE_ID` |
| `0x802d3714` | `IPL_UTI_CONV2_SEN_ID` |
| `0x802d37c0` | `IPL_UTI_CONV_SEN_STPIX` |
| `0x802d386c` | `IPL_UTI_CONV_SEN_RATIO` |
| `0x802d38f8` | `IPL_UTI_CONV_ALGINFO_RAW_BIT` |
| `0x802d39a4` | `IPL_YUV_SIZE` |
| `0x802d3a98` | `IPL_UTI_SET_CONT_BUFINFO` |
| `0x802d3bb8` | `IPL_UTI_Y_INFO_CONV2` |
| `0x802d3e80` | `IPL_GetBufItem` |
| `0x802d417c` | `IPL_BufGet` |
| `0x802d4248` | `IPL_BufSet` |
| `0x802d4854` | `IPL_CtrlGetInfor` |
| `0x802d48d8` | `IPL_CtrlSetInfor` |
| `0x802d4b1c` | `IPL_AlgSetUIInfo` |
| `0x802d4be8` | `IPL_AlgGetUIInfo` |
| `0x802d4c6c` | `IPL_AlgSetEventFP` |
| `0x802d5128` | `IPL_HeaderRawGetInfoByHeaderAddr_Int` |
| `0x802d51e4` | `IPL_HeaderRawGetCurInfo_Int` |
| `0x802d53d4` | `IPL_HeaderRawSetInfoISR_Int` |
| `0x802d55d8` | `IPL_HeaderRawResetBuffer_Int` |
| `0x802d5670` | `IPL_HeaderRawCreate` |
| `0x802d57ac` | `IPL_HeaderRawClose` |
| `0x802d5838` | `IPL_HeaderRawOpen` |
| `0x802d594c` | `IPL_HeaderRawUpdateLock_Int` |
| `0x802d59c0` | `IPL_HeaderRawLock` |
| `0x802d5a34` | `IPL_HeaderRawUpdateUnlock_Int` |
| `0x802d5b08` | `IPL_HeaderRawSetInfo_Int` |
| `0x802d5de4` | `IPL_HeaderRawUnlock` |
| `0x802d5e50` | `IPL_HeaderRawClrChkStatus` |
| `0x802d5f28` | `IPL_HeaderRawSetChkStatus` |
| `0x802d62bc` | `IPL_TRIG_H264` |
| `0x802d62bc` | `IPL_TRIG_NULL` |
| `0x802d62bc` | `IPL_TRIG_TIMER` |
| `0x802d62bc` | `IPL_TRIG_VD` |
| `0x802d685c` | `IPL_CF_2STRP` |
| `0x802d685c` | `IPL_CF_CCIR` |
| `0x802d685c` | `IPL_CF_NORMAL` |
| `0x802d685c` | `IPL_CF_RHEHDR` |
| `0x802d685c` | `IPL_M_CTRL_TYPE_13` |
| `0x802d685c` | `IPL_M_CTRL_TYPE_22` |
| `0x802d6d38` | `IPL_IMG_Y` |
| `0x802d6d38` | `IPL_IMG_YUV420` |
| `0x802d6d38` | `IPL_IMG_YUV422` |
| `0x802d6d38` | `IPL_IMG_YUV444` |
| `0x802d6d38` | `IPL_IMG_Y_PACK_UV420` |
| `0x802d6d38` | `IPL_IMG_Y_PACK_UV422` |
| `0x802d6d38` | `IPL_IMG_Y_PACK_UV444` |
| `0x802d7e7c` | `IPL_CTRL_CloseTsk` |
| `0x802d894c` | `IPL_CTRL_OpenTsk` |
| `0x802d9d30` | `IPL_DZoomGetInfo` |
| `0x802d9d30` | `IPL_DZoomSet` |
| `0x802daeb4` | `IPL_CTRL_Center` |
| `0x802daf40` | `IPL_CTRLQuery` |
| `0x802db1e8` | `IPL_CTRLManualTrig` |
| `0x802db780` | `IPL_CtrlModeChkStatus` |
| `0x802db9f4` | `IPL_CtrlSetSIEPPBNum` |
| `0x802dbcd0` | `IPL_CTRLModeProc` |
| `0x802dbcd0` | `IPL_IsRaw2YUVStopAll` |
| `0x802dbcd0` | `IPL_IsStopAllAfterCmd` |
| `0x802dc3fc` | `IPL_CTRLRunTimeChg_IQ` |
| `0x802dc5f4` | `IPL_CTRLRun` |
| `0x802dc5f4` | `IPL_CTRLRunProc` |
| `0x802dcc44` | `IPL_CTRLRunTimeChg` |
| `0x802dd258` | `IPL_CTRLRunTimeChg_IQ_ISR` |
| `0x802dd39c` | `IPL_HAL_Operation` |
| `0x803111e0` | `IPL_ISRInit` |
| `0x8032312c` | `IPL_SetTrigInfoFCB` |
| `0x80323ed8` | `IPL_GetIPLInfoFCB` |
| `0x80324088` | `IPL_GetImeInfoFCB` |
| `0x803241a8` | `IPL_GetImeCurInfoFCB` |
| `0x80324464` | `IPL_SetImgRatioFCB` |
| `0x80324968` | `IPL_SetImeFCB` |
| `0x803259a4` | `IPL_SetSensorMode` |
| `0x803265ec` | `IPL_MapCtrlFlow2ICF` |
| `0x803265ec` | `IPL_MapICF2BufMode` |
| `0x80326ac4` | `IPL_BufAssign` |
| `0x80326b7c` | `IPL_BufAssignFlowA` |
| `0x80328600` | `IPL_CtrlGetHalSetId` |
| `0x80328728` | `IPL_GetImePathInfo` |
| `0x80328a74` | `IPL_CtrlInitIpc_SIERawEnc_Cap` |
| `0x80328af4` | `IPL_CtrlInitIpc_SIEGamma_Cap` |
| `0x80328b78` | `IPL_CtrlInitIpc_SIEIn` |
| `0x80328d0c` | `IPL_CtrlInitIpc_SIEAct` |
| `0x80328ea0` | `IPL_CtrlPrvInit` |
| `0x803291b4` | `IPL_CtrlCapInit` |
| `0x803297ac` | `IPL_CtrlInitPrvBufInfo` |
| `0x803298d4` | `IPL_SetImePathInfo` |
| `0x80329d6c` | `IPL_ChkImePathInfo` |
| `0x8032a150` | `IPL_GetSensorStatus` |
| `0x8032aa44` | `IPL_CtrlInitIpc_SIEOB_Cap` |
| `0x8032ab9c` | `IPL_CtrlInitIpc_SIEIn_Cap` |
| `0x8032ad34` | `IPL_CtrlInitIpc_SIEAct_Cap` |
| `0x8032aedc` | `IPL_SIECCIR_FCB` |
| `0x8032b3f8` | `IPL_CtrlInitPrvIpcInfo` |
| `0x8032b8ac` | `IPL_CtrlInitIpc_SIECh1PPB` |
| `0x8032be50` | `IPL_CtrlInitIpc_IMEPxOutPPB_Stitch` |
| `0x8032c5b0` | `IPL_CtrlInitIpc_IMEPxOutPPB` |
| `0x8032c8bc` | `IPL_CtrlInitIpc_DispPxPPB` |
| `0x8032cd1c` | `IPL_CtrlInitIpc_DispPxPPB_Stitch` |
| `0x8032d744` | `IPL_CtrlInitCapIpcInfo` |
| `0x8032e228` | `IPL_CtrlPrvInitFlowA` |
| `0x8032ffa8` | `IPL_CtrlPrvInitFlowC` |
| `0x8033206c` | `IPL_SIEClkCBFlowC` |
| `0x803331d8` | `IPL_CtrlPrvInitFlowD` |
| `0x80334b44` | `IPL_SIEClkCBFlowD` |
| `0x803366c4` | `IPL_FCB_GetCapRaw` |
| `0x8033f924` | `IPL_Display_SetBufferNum` |
| `0x8033f9c0` | `IPL_GetSpecifiedIMEoutputAddr` |
| `0x8033fab8` | `IPL_CtrlPostImage` |
| `0x80340c18` | `IPL_ResetDisplayCtrlFlow` |
| `0x80340d14` | `IPL_MapToGxImgFmt` |
| `0x80342fec` | `IPL_Display_CloseTsk` |
| `0x803430a0` | `IPL_Display_OpenTsk` |
| `0x8034312c` | `IPL_FreezeDisplayImage` |
| `0x80343598` | `IPL_StitchImg_OpenTsk` |
| `0x80343624` | `IPL_StitchEst_OpenTsk` |

</details>

<details><summary><code>IPL2IME</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x802f5e04` | `IPL2IME_ISCompY` |
| `0x802f5f08` | `IPL2IME_ISCompX` |
| `0x802ff054` | `IPL2IME_TimerReload` |
| `0x8030085c` | `IPL2IME_VDReload` |

</details>

<details><summary><code>IPLCTRL</code> (8)</summary>

| 주소 | 이름 |
|---|---|
| `0x802d685c` | `IPLCTRL_INIT` |
| `0x802d685c` | `IPLCTRL_IPLPAUSE` |
| `0x802d685c` | `IPLCTRL_RUN` |
| `0x802d685c` | `IPLCTRL_SIEPAUSE1` |
| `0x802d685c` | `IPLCTRL_SIEPAUSE2` |
| `0x802d685c` | `IPLCTRL_STOP` |
| `0x802d685c` | `IPLCTRL_UNKNOW` |
| `0x802d685c` | `IPLCTRL_YCCSTOP` |

</details>

<details><summary><code>IQCB</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8033cea8` | `IQCB_SettingFlowFunc` |

</details>

<details><summary><code>IQS</code> (31)</summary>

| 주소 | 이름 |
|---|---|
| `0x80005ffc` | `IQS_DCESemiId` |
| `0x80005ffc` | `IQS_IFE2SemiId` |
| `0x80005ffc` | `IQS_IFESemiId` |
| `0x80005ffc` | `IQS_IMESemiId` |
| `0x80005ffc` | `IQS_IPESemiId` |
| `0x80005ffc` | `IQS_PRESemiId` |
| `0x80005ffc` | `IQS_SIE2SemiId` |
| `0x80005ffc` | `IQS_SIESemiId` |
| `0x801a2958` | `IQS_SetIQCtrl` |
| `0x801a2dd0` | `IQS_GetIQCtrl` |
| `0x803147dc` | `IQS_GetCtrlObj` |
| `0x80314904` | `IQS_Module_Lock` |
| `0x80314988` | `IQS_Module_Unlock` |
| `0x803149f4` | `IQS_Pause` |
| `0x80314ac4` | `IQS_Resume` |
| `0x80314b78` | `IQS_Start` |
| `0x80314e44` | `IQS_IsPause` |
| `0x80314ef0` | `IQS_GetTaskObj` |
| `0x80314ef0` | `IQS_TrigEvent` |
| `0x80314fb8` | `IQS_Close` |
| `0x80315094` | `IQS_Open` |
| `0x80337b90` | `IQS_GetISORange` |
| `0x80337eb4` | `IQS_AdjIQ` |
| `0x8033d3f0` | `IQS_SettingFlowFunc` |
| `0x8033daf4` | `IQS_GetInvGammaValue` |
| `0x8033dd48` | `IQS_GetGammaValue` |
| `0x8033deb0` | `IQS_GetRefImageInfo` |
| `0x8033df68` | `IQS_OBSubMode` |
| `0x8033e264` | `IQS_IsChromaAdaptEn` |
| `0x8033e314` | `IQS_GetChromaAdaptRatio` |
| `0x8039dda4` | `IQS_Ctrl_Process` |

</details>

<details><summary><code>iqs</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80314850` | `iqs_getCtrlObj` |

</details>

<details><summary><code>IQSim</code> (12)</summary>

| 주소 | 이름 |
|---|---|
| `0x801a3170` | `IQSim_SetConvertEnd` |
| `0x801a321c` | `IQSim_SetConvertProc` |
| `0x801a3320` | `IQSim_SetConvertInit` |
| `0x801a3478` | `IQSim_GetJpgOk` |
| `0x801a353c` | `IQSim_GetPRIFmt` |
| `0x801a35c0` | `IQSim_GetPRISize` |
| `0x801a3644` | `IQSim_GetPRIAddr` |
| `0x801a36c8` | `IQSim_GetQVFmt` |
| `0x801a374c` | `IQSim_GetQVSize` |
| `0x801a37d0` | `IQSim_GetQVAddr` |
| `0x801a3854` | `IQSim_GetJpgSize` |
| `0x801a38d4` | `IQSim_GetJpgAddr` |

</details>

<details><summary><code>IQUC</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x801a2b8c` | `IQUC_Trigger3DNROut` |
| `0x8035098c` | `IQUC_SetCtrlItem` |

</details>

<details><summary><code>ise</code> (11)</summary>

| 주소 | 이름 |
|---|---|
| `0x801422b0` | `ise_checkUserClockRate` |
| `0x80142330` | `ise_calScaleParam` |
| `0x80142ac0` | `ise_setDMAAddressInfo` |
| `0x80142bb4` | `ise_setScaleFilterParams` |
| `0x80142c6c` | `ise_setScaleFactors` |
| `0x80142de4` | `ise_setImageSizeInfo` |
| `0x80142f18` | `ise_setIOInfo` |
| `0x801437a4` | `ise_pause` |
| `0x801438ac` | `ise_close` |
| `0x801439c0` | `ise_setMode` |
| `0x80143f64` | `ise_open` |

</details>

<details><summary><code>ISED2D</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8030dba8` | `ISED2D_start` |

</details>

<details><summary><code>ISF</code> (48)</summary>

| 주소 | 이름 |
|---|---|
| `0x80002d94` | `ISF_SEM_CFG_ID` |
| `0x80002d94` | `ISF_SEM_ID` |
| `0x801fa4e4` | `ISF_CamDisp_GetParam` |
| `0x801fa584` | `ISF_CamDisp_SetParam` |
| `0x801fa708` | `ISF_CamDisp_BindInput` |
| `0x801fcdd4` | `ISF_Media_Close` |
| `0x801fd02c` | `ISF_Media_BindInput` |
| `0x801fd7b8` | `ISF_Media_GetParam` |
| `0x801fd81c` | `ISF_Media_SetParam` |
| `0x801fdd04` | `ISF_Media_Open` |
| `0x801fec98` | `ISF_Media_SetMode` |
| `0x801ff9e8` | `ISF_NetHTTP_SetParam` |
| `0x801ffff8` | `ISF_NetHTTP_SetMode` |
| `0x8020057c` | `ISF_NetRTSP_SetParam` |
| `0x80200694` | `ISF_NetRTSP_Req` |
| `0x8020076c` | `ISF_NetRTSP_GetVideoType` |
| `0x802007d4` | `ISF_NetRTSP_GetAudioType` |
| `0x802008c0` | `ISF_NetRTSP_InputPort3_PushImgBufToDest` |
| `0x80200ae8` | `ISF_NetRTSP_InputPort2_PushImgBufToDest` |
| `0x80200d0c` | `ISF_NetRTSP_InputPort1_PushImgBufToDest` |
| `0x80201394` | `ISF_UsbUVAC_InputPort2_PushImgBufToDest` |
| `0x80201448` | `ISF_UsbUVAC_InputPort1_PushImgBufToDest` |
| `0x802015a8` | `ISF_UsbUVAC_GetParam` |
| `0x8020160c` | `ISF_UsbUVAC_SetParam` |
| `0x80201930` | `ISF_UsbUVAC_Open` |
| `0x80202284` | `ISF_UserDraw_SetParam` |
| `0x8036fb6c` | `ISF_ImagePipe_GetParam` |
| `0x8036fcfc` | `ISF_ImagePipe_SetParam` |
| `0x80370598` | `ISF_ImagePipe1_OutputPort4_PullImgBufFromSrc` |
| `0x80370660` | `ISF_ImagePipe1_OutputPort3_PullImgBufFromSrc` |
| `0x80370728` | `ISF_ImagePipe1_OutputPort2_PullImgBufFromSrc` |
| `0x803707f0` | `ISF_ImagePipe1_OutputPort1_PullImgBufFromSrc` |
| `0x803708fc` | `ISF_ImagePipe1_GetParam` |
| `0x803709f4` | `ISF_ImagePipe1_SetParam` |
| `0x80370ec4` | `ISF_ImagePipe2_OutputPort4_PullImgBufFromSrc` |
| `0x80370f90` | `ISF_ImagePipe2_OutputPort3_PullImgBufFromSrc` |
| `0x8037105c` | `ISF_ImagePipe2_OutputPort2_PullImgBufFromSrc` |
| `0x80371128` | `ISF_ImagePipe2_OutputPort1_PullImgBufFromSrc` |
| `0x80371230` | `ISF_ImagePipe2_GetParam` |
| `0x803712c0` | `ISF_ImagePipe2_SetParam` |
| `0x803715cc` | `ISF_ImagePipe3_OutputPort1_PullImgBufFromSrc` |
| `0x803716d8` | `ISF_ImagePipe3_SetParam` |
| `0x80371964` | `ISF_ImagePipe4_OutputPort1_PullImgBufFromSrc` |
| `0x80371a70` | `ISF_ImagePipe4_SetParam` |
| `0x80371cb0` | `ISF_Photo_GetParam` |
| `0x80371d70` | `ISF_Photo_SetParam` |
| `0x8037226c` | `ISF_Cap_GetParam` |
| `0x80372300` | `ISF_Cap_SetParam` |

</details>

<details><summary><code>ISO</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80348bbc` | `ISO_Adjust` |

</details>

<details><summary><code>jpeg</code> (14)</summary>

| 주소 | 이름 |
|---|---|
| `0x800bfcd8` | `jpeg_setQTabHW` |
| `0x800bfe70` | `jpeg_setScaleRatio` |
| `0x800bfecc` | `jpeg_setCrop` |
| `0x800c00a4` | `jpeg_setDCOut` |
| `0x800c01e4` | `jpeg_setRestartInterval` |
| `0x800c0238` | `jpeg_setFileFormat` |
| `0x800c03b4` | `jpeg_setImgLineOffset` |
| `0x800c045c` | `jpeg_setEnableInt` |
| `0x800c04f4` | `jpeg_setConfig` |
| `0x800c0654` | `jpeg_setCmpStartAddr` |
| `0x800c07f8` | `jpeg_setStartDecode` |
| `0x800c0dcc` | `jpeg_close` |
| `0x800c0e64` | `jpeg_open` |
| `0x800c0fac` | `jpeg_getConfig` |

</details>

<details><summary><code>Jpg</code> (12)</summary>

| 주소 | 이름 |
|---|---|
| `0x80195a14` | `Jpg_ASyncDecWaitDone` |
| `0x80195cdc` | `Jpg_ASyncDecStart` |
| `0x801960e0` | `Jpg_ASyncDecOpen` |
| `0x8019650c` | `Jpg_EncSetData` |
| `0x8019659c` | `Jpg_ASyncEncClose` |
| `0x801965ec` | `Jpg_ASyncEncWaitDone` |
| `0x801967bc` | `Jpg_ASyncEncStart` |
| `0x8019683c` | `Jpg_ASyncEncSetHeader` |
| `0x80196d6c` | `Jpg_ASyncEncOpen` |
| `0x80196fdc` | `Jpg_SetBitRateCtrl` |
| `0x801971b8` | `Jpg_EncOneImg` |
| `0x8019765c` | `Jpg_ParseHeader` |

</details>

<details><summary><code>JpgBrc</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8029ae98` | `JpgBrc_PredictQuality` |

</details>

<details><summary><code>Lens</code> (15)</summary>

| 주소 | 이름 |
|---|---|
| `0x8029b338` | `Lens_Focus_SetCalData` |
| `0x8029b38c` | `Lens_Focus_GetTable` |
| `0x8029b3f4` | `Lens_Focus_GetDistTable` |
| `0x8029b45c` | `Lens_Focus_GetPosition` |
| `0x8029b4c4` | `Lens_Focus_SetFocalLength_um` |
| `0x8029b528` | `Lens_Focus_GetLength_um` |
| `0x8029b590` | `Lens_Focus_GetLength` |
| `0x8029b60c` | `Lens_Module_SetState` |
| `0x8029b69c` | `Lens_Shutter_Move` |
| `0x8029b79c` | `Lens_Aperture_Move` |
| `0x8029b9d4` | `Lens_Zoom_Stop` |
| `0x8029bafc` | `Lens_Zoom_Out` |
| `0x8029bb90` | `Lens_Zoom_In` |
| `0x8029bcb0` | `Lens_Init` |
| `0x8029c044` | `Lens_Module_Init` |

</details>

<details><summary><code>lensFF1</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8026c31c` | `lensFF1_Aperture_Go2Pos` |

</details>

<details><summary><code>LIVE555</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x8020fec0` | `LIVE555_FRM_REP` |
| `0x8020fec0` | `LIVE555_FRM_REQ` |
| `0x8020fec0` | `LIVE555_OPEN_SESSION_REP` |
| `0x8020fec0` | `LIVE555_SERVER_EVENT` |

</details>

<details><summary><code>lvds</code> (7)</summary>

| 주소 | 이름 |
|---|---|
| `0x8004b56c` | `lvds_getConfig` |
| `0x8004bef8` | `lvds_setConfig` |
| `0x8004c4cc` | `lvds_waitInterrupt` |
| `0x8004c678` | `lvds_chkRegister` |
| `0x8004c678` | `lvds_setEnable` |
| `0x8004c9a4` | `lvds_close` |
| `0x8004cbe8` | `lvds_isr` |

</details>

<details><summary><code>lvds2</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x8004d578` | `lvds2_setConfig` |
| `0x8004db50` | `lvds2_waitInterrupt` |
| `0x8004dcfc` | `lvds2_chkRegister` |
| `0x8004dcfc` | `lvds2_setEnable` |
| `0x8004e028` | `lvds2_close` |
| `0x8004e26c` | `lvds2_isr` |

</details>

<details><summary><code>Lview</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80203f40` | `xLview_SendIPC` |

</details>

<details><summary><code>LVIEWD</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80002e30` | `LVIEWD_FLG_ID` |
| `0x80002e30` | `LVIEWD_SEM_ID` |

</details>

<details><summary><code>Lviewd</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80002e30` | `Lviewd_MainTsk` |

</details>

<details><summary><code>LviewNvt</code> (12)</summary>

| 주소 | 이름 |
|---|---|
| `0x80202ae0` | `LviewNvt_TimeTrigOpen` |
| `0x80202ae0` | `LviewNvt_getCurEncJpgBuf` |
| `0x80203168` | `LviewNvt_Open` |
| `0x80203168` | `LviewNvt_SetQueueFrameNum` |
| `0x80203698` | `LviewNvt_SetEncData` |
| `0x802036f8` | `LviewNvt_GetEncData` |
| `0x80203910` | `LviewNvt_InitEncCodec` |
| `0x80203de4` | `LviewNvt_H264Close` |
| `0x80203e58` | `LviewNvt_H264ENC_SetInfo` |
| `0x80203eb0` | `LviewNvt_H264ENC_GetInfo` |
| `0x8020436c` | `LviewNvt_StopDaemon` |
| `0x8020445c` | `LviewNvt_StartDaemon` |

</details>

<details><summary><code>m</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80005ecc` | `m_IPH_FLGID` |
| `0x802d685c` | `m_CurFlow` |

</details>

<details><summary><code>Media</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x801fe5c4` | `Media_IPLGetReadyCB2` |
| `0x801fe700` | `Media_IPLGetReadyCB` |

</details>

<details><summary><code>MenuTV</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x801ac9ac` | `MenuTV_Menu_OnKeyDown` |
| `0x801aca08` | `MenuTV_Menu_OnKeyUp` |

</details>

<details><summary><code>MenuTV1</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x801accc8` | `MenuTV1_Menu_OnKeyDown` |
| `0x801acd24` | `MenuTV1_Menu_OnKeyUp` |
| `0x801ace7c` | `MenuTV1_OnOpen` |

</details>

<details><summary><code>mi</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80042780` | `mi_isr` |

</details>

<details><summary><code>ModeSleep</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x801a6780` | `ModeSleep_Close` |
| `0x801a68fc` | `ModeSleep_Open` |

</details>

<details><summary><code>motorFF1</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x8026c5ac` | `motorFF1_shutter_setNormalState` |
| `0x8026c67c` | `motorFF1_shutter_dummyLoadState` |
| `0x8026c67c` | `motorFF1_shutter_setState` |
| `0x8026c7a4` | `motorFF1_aperture_setNormalState` |
| `0x8026c7a4` | `motorFF1_aperture_setState` |

</details>

<details><summary><code>MOV</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x8027a814` | `MOV_SetIentry` |
| `0x802804a8` | `MOV_Read_stsz` |
| `0x80280750` | `MOV_Read_stsc` |
| `0x80280dd0` | `MOV_Read_stsd` |

</details>

<details><summary><code>Movie</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801d1004` | `Movie_RecordCB` |

</details>

<details><summary><code>MovieExe</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x801ce870` | `MovieExe_OnDualcam` |
| `0x801ce938` | `MovieExe_OnProtectManual` |
| `0x801ceae0` | `MovieExe_OnProtectAuto` |
| `0x801cf648` | `MovieExe_OnImageRatio` |
| `0x801d0208` | `MovieExe_OnMovieSize` |

</details>

<details><summary><code>MoviePlay</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801a600c` | `MoviePlay_DispSrv_Scalar2Display` |

</details>

<details><summary><code>MoviePlayExe</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x801d6cec` | `MoviePlayExe_OnAudPlayVolume` |
| `0x801d6eec` | `MoviePlayExe_OpenPlay` |

</details>

<details><summary><code>MovieStamp</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x8019f690` | `MovieStamp_CopyData` |
| `0x801a05b4` | `MovieStamp_UpdateData` |
| `0x801a1400` | `MovieStamp_SwTimerOpen` |

</details>

<details><summary><code>MOVMJPG</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8027af84` | `MOVMJPG_UpdateHeader` |

</details>

<details><summary><code>MOVRcvy</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x80279164` | `MOVRcvy_UpdateMdatHDR` |
| `0x802792dc` | `MOVRcvy_CheckNidx` |
| `0x80279670` | `MOVRcvy_SM_CheckNidx` |
| `0x80279b4c` | `MOVRcvy_GetNidxTbl` |

</details>

<details><summary><code>MOVRead</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x8027e1e0` | `MOVRead_SetMoovErrorReason` |
| `0x8027e228` | `MOVRead_ParseHeaderFirstVideo` |
| `0x8027e300` | `MOVRead_ParseHeader` |
| `0x80280304` | `MOVRead_ShowAllSize` |

</details>

<details><summary><code>MovRec</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80205a10` | `MovRec_Close` |
| `0x80205ad8` | `MovRec_Open` |

</details>

<details><summary><code>MP</code> (52)</summary>

| 주소 | 이름 |
|---|---|
| `0x802718d0` | `MP_AviWrite_Recvr_CheckNidx` |
| `0x80271ab0` | `MP_AviWrite_Recvr_GetNidxTbl` |
| `0x802724c4` | `MP_AviWrite_IndexTlb_Recovery` |
| `0x80273240` | `MP_AviWrite_MakeHeader` |
| `0x8027c9e0` | `MP_AVIUti_idx1VidRead` |
| `0x8027cb88` | `MP_AVIUti_idx1Read` |
| `0x8027cd8c` | `MP_AVIUti_moviParse` |
| `0x802872d0` | `MP_AACEnc_customizeFunc` |
| `0x80287394` | `MP_AACEnc_encodeOne` |
| `0x8028741c` | `MP_AACEnc_initAAC` |
| `0x80287718` | `MP_AACEnc_setInfo` |
| `0x80287914` | `MP_AACDec_setInfo` |
| `0x80287c68` | `MP_AACDec_waitDecodeDone` |
| `0x80287e98` | `MP_AACDec_initialize` |
| `0x802880ec` | `MP_PCMEnc_setInfo` |
| `0x80288260` | `MP_PCMEnc_getInfo` |
| `0x802883c0` | `MP_PCMDec_waitDecodeDone` |
| `0x80288578` | `MP_PCMDec_setInfo` |
| `0x802889b8` | `MP_PPCMEnc_setInfo` |
| `0x80288b2c` | `MP_PPCMEnc_getInfo` |
| `0x80288c9c` | `MP_aLawEnc_encodeOne` |
| `0x80288d1c` | `MP_aLawEnc_setInfo` |
| `0x80288f48` | `MP_uLawEnc_encodeOne` |
| `0x80288fc8` | `MP_uLawEnc_setInfo` |
| `0x802c074c` | `MP_H264Dec_malloc` |
| `0x802c07b8` | `MP_H264Dec_Stream_waitDecodeDone` |
| `0x802c13d0` | `MP_H264Dec_setInfo` |
| `0x802c16bc` | `MP_H264Dec_displayOneFrame` |
| `0x802c1b94` | `MP_H264Dec_Stream_initH264Decoder` |
| `0x802c1c24` | `MP_H264Dec_decodeThisVideo` |
| `0x802c2558` | `MP_H264Enc_TimerHdl` |
| `0x802c25b4` | `MP_H264Enc_TimerOpen` |
| `0x802c2840` | `MP_H264Enc_waitEncReady` |
| `0x802c29c0` | `MP_H264Enc_triggerEnc` |
| `0x802c2c54` | `MP_H264Enc_encodeOne` |
| `0x802c33b8` | `MP_H264Enc_initH264` |
| `0x802c33b8` | `MP_H264Enc_setInfo` |
| `0x802c47ec` | `MP_H264Dec_Reset_ImgQueue_Order` |
| `0x802c494c` | `MP_H264Dec_GetReOrderImg` |
| `0x802c49fc` | `MP_H264Dec_FreeImgFromQueue` |
| `0x802c4a6c` | `MP_H264Dec_AddImgToQueue` |
| `0x802c4b18` | `MP_H264Dec_ImgQueueInit` |
| `0x802c4cc8` | `MP_H264Enc_AddImgToQueue` |
| `0x802c4db0` | `MP_H264Enc_ImgQueueInit` |
| `0x802c50b8` | `MP_H264Enc_GetReOrderImg` |
| `0x802c51b0` | `MP_H264Enc_FreeImgFromQueue` |
| `0x802c5288` | `MP_H264Enc_Set3DNR` |
| `0x802c561c` | `MP_MjpgDec_decodeOne` |
| `0x802c579c` | `MP_MjpgDec_initialize` |
| `0x802c59e0` | `MP_MjpgDec_decodeThisVideo` |
| `0x802c5e4c` | `MP_MjpgEnc_encodeOne` |
| `0x802c6354` | `MP_MjpgEnc_setInfo` |

</details>

<details><summary><code>Msdc</code> (10)</summary>

| 주소 | 이름 |
|---|---|
| `0x80005618` | `Msdc_StrgTsk` |
| `0x802b48dc` | `Msdc_InitLUNs` |
| `0x802b48dc` | `Msdc_Open` |
| `0x802b5390` | `Msdc_Close` |
| `0x802b6a78` | `Msdc_SbcWRITE` |
| `0x802b7208` | `Msdc_SbcREAD` |
| `0x802b77f8` | `Msdc_PhaseErrorHandler` |
| `0x802b7934` | `Msdc_CommandHandler` |
| `0x802b88b0` | `Msdc_CBWHandler` |
| `0x802b8a08` | `Msdc_ClassRequestHandler` |

</details>

<details><summary><code>MSDCNVT</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x800053f8` | `MSDCNVT_FLG_ID` |
| `0x800053f8` | `MSDCNVT_SEM_ID` |

</details>

<details><summary><code>MsdcNvt</code> (19)</summary>

| 주소 | 이름 |
|---|---|
| `0x8029cd80` | `MsdcNvt_ChkParameters` |
| `0x8029cfb8` | `MsdcNvt_Init` |
| `0x8029d1d0` | `MsdcNvt_Vendor_Cb` |
| `0x8029d1d0` | `xMsdcNvt_Function` |
| `0x8029d3e4` | `MsdcNvt_Verify_Cb` |
| `0x8029d664` | `xMsdcNvt_Function_BiCall` |
| `0x8029d6f4` | `xMsdcNvt_BiCall_GetData` |
| `0x8029d780` | `xMsdcNvt_BiCall_Call` |
| `0x8029d7f4` | `xMsdcNvt_BiCall_GetProc_Step1` |
| `0x8029d8c0` | `xMsdcNvt_Function_SiCall` |
| `0x8029d94c` | `xMsdcNvt_SiCall_RunCmdSet` |
| `0x8029d9c0` | `xMsdcNvt_SiCall_RunCmdGet` |
| `0x8029db9c` | `xMsdcNvt_Bk_HostUnLock` |
| `0x8029dc34` | `xMsdcNvt_Bk_HostLock` |
| `0x8029dc9c` | `xMsdcNvt_Bk_RunCmd` |
| `0x8029ddec` | `xMsdcNvt_Function_DbgSys` |
| `0x8029e7e0` | `xMsdcNvt_Function_Misc` |
| `0x8029e870` | `xMsdcNvt_Misc_Set_UpdFw_SetBlock` |
| `0x8029e8a8` | `xMsdcNvt_Misc_Set_UpdFw_GetInfo` |

</details>

<details><summary><code>MsdcNvtCb</code> (12)</summary>

| 주소 | 이름 |
|---|---|
| `0x800e8f54` | `MsdcNvtCb_Attach` |
| `0x800e907c` | `MsdcNvtCb_Open` |
| `0x801a1e8c` | `MsdcNvtCb_AdjGetItemsData` |
| `0x801a1f54` | `MsdcNvtCb_AdjSetItemsData` |
| `0x801a20e4` | `MsdcNvtCb_AdjGetNumOfItem` |
| `0x801a2140` | `MsdcNvtCb_AdjGetItemsDesc` |
| `0x801a2368` | `MsdcNvtCb_UpdFwAllInOne_Step2` |
| `0x801a24f8` | `MsdcNvtCb_UpdFwAllInOne_Step1` |
| `0x8029fd54` | `MsdcNvtCb_DispPaletteSet` |
| `0x8029fe6c` | `MsdcNvtCb_DispPaletteGet` |
| `0x8029ff68` | `MsdcNvtCb_DispCfgGet` |
| `0x802a05c4` | `MsdcNvtCb_FileCopyPcToDevice` |

</details>

<details><summary><code>MsdcNvtCbDisp</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8029ff68` | `xMsdcNvtCbDisp_MapFormatIdeToMsdc` |

</details>

<details><summary><code>NameRuleDCFFull</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x802a2938` | `NameRuleDCFFull_customizeFunc` |
| `0x802a3080` | `NameRuleDCFFull_CalcNextID` |
| `0x802a3188` | `NameRuleDCFFull_GetPathBySeq` |
| `0x802a32cc` | `NameRuleDCFFull_DelPath` |
| `0x802a3368` | `NameRuleDCFFull_AddPath` |
| `0x802a3404` | `NameRuleDCFFull_CreateAndGetPath` |

</details>

<details><summary><code>NameRuleDCFFullUti</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x802a2788` | `NameRuleDCFFullUti_Set1stCrashID` |
| `0x802a2f60` | `NameRuleDCFFullUti_SetNextID` |

</details>

<details><summary><code>nand</code> (23)</summary>

| 주소 | 이름 |
|---|---|
| `0x8006a4a0` | `nand_dumpAllSpareAreaInfo` |
| `0x8006ae28` | `nand_dumpInfo` |
| `0x8006bcb0` | `nand_eraseAllPartitionBlockMapping` |
| `0x8006cb64` | `nand_cmdWaitCompletePolling` |
| `0x8006cbe0` | `nand_cmdWriteOperation_MULTI` |
| `0x8006cf74` | `nand_cmdEraseBlock` |
| `0x8006d22c` | `nand_cmdWriteOperation_SINGLE` |
| `0x8006d600` | `nand_cmdReadOperation` |
| `0x8006daf4` | `nand_cmdReadPageSpareDataTotal` |
| `0x8006deac` | `nand_cmdWaitComplete` |
| `0x8006df64` | `nand_cmdConditionEraseBlock` |
| `0x80075bd0` | `nand_setFeature` |
| `0x80075f38` | `nand_checkNandParamValid` |
| `0x80075f38` | `nand_getInfo` |
| `0x80076ae4` | `nand_identify` |
| `0x80076d6c` | `nand_attach` |
| `0x80077b08` | `nand_hostCheckReady` |
| `0x80077d30` | `nand_hostCorrectSecondaryEcc` |
| `0x800827ec` | `nand_markBadBlock` |
| `0x80082ff4` | `nand_readwriteCheck` |
| `0x80083538` | `nand_readCheck` |
| `0x800837f0` | `nand_eraseCheck` |
| `0x800837f0` | `nand_eraseCheckBadBlock` |

</details>

<details><summary><code>NetHTTP</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x801ffbec` | `NetHTTP_GetVideoBufCB` |
| `0x801ffd7c` | `NetHTTP_GetPipVideoBufCB` |
| `0x801ffff8` | `NetHTTP_StartEncoder` |

</details>

<details><summary><code>NH</code> (15)</summary>

| 주소 | 이름 |
|---|---|
| `0x802a08a8` | `NH_Custom_GetPathBySeq` |
| `0x802a097c` | `NH_Custom_DelPath` |
| `0x802a0a78` | `NH_Custom_AddPath` |
| `0x802a0c98` | `NH_Custom_SetFolderPath` |
| `0x802a1010` | `NH_Custom_SetWholeDirPath` |
| `0x802a1578` | `NH_Custom_customizeFunc` |
| `0x802a1804` | `NH_CustomUti_MakeObjPath` |
| `0x802a1e7c` | `NH_CustomUti_MakeDefaultPath` |
| `0x802a20a8` | `NH_Custom_BuildFullPath_GiveFileName` |
| `0x802a223c` | `NH_Custom_BuildFullPath_Auto` |
| `0x802a25a8` | `NH_CustomUti_MakePhotoPath` |
| `0x802a38a4` | `NH_FileDB_GetPathBySeq` |
| `0x802a3c24` | `NH_FileDB_AddPath` |
| `0x802a3e34` | `NH_FileDBUti_MakeObjPath` |
| `0x802a4508` | `NH_FileDB_customizeFunc` |

</details>

<details><summary><code>Non</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8008e2a4` | `Non_invert` |

</details>

<details><summary><code>nvt</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800e7cd0` | `nvt_rcv_msg` |

</details>

<details><summary><code>NVTBACK</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80003078` | `NVTBACK_FLG_ID` |
| `0x80003078` | `NVTBACK_MBX_ID` |

</details>

<details><summary><code>NVTIPC</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x80002a00` | `NVTIPC_FLG_ID` |
| `0x80002a00` | `NVTIPC_MSGQUEUE_FLG_ID` |
| `0x80002a00` | `NVTIPC_SEM_FLG_ID` |
| `0x80002a00` | `NVTIPC_SEM_ID` |
| `0x80002a00` | `NVTIPC_SEM_SYS_ACK_ID` |

</details>

<details><summary><code>NvtIPC</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x800d3918` | `NvtIPC_DumpDebugInfo` |
| `0x800d3bf0` | `NvtIPC_SemUnlock` |
| `0x800d3ddc` | `NvtIPC_SemLock` |
| `0x800d66a8` | `NvtIPC_MsgSnd` |
| `0x800d6bc4` | `NvtIPC_MsgPost` |
| `0x800d6d18` | `NvtIPC_Ftok` |

</details>

<details><summary><code>NvtIpc</code> (10)</summary>

| 주소 | 이름 |
|---|---|
| `0x800d3afc` | `NvtIpc_Cpu2Suspend_TimerCb` |
| `0x800d3b44` | `NvtIpc_Cpu2PowerOff_TimerCb` |
| `0x800d4018` | `NvtIpc_WaitCPU2PowerOnReady` |
| `0x800d4090` | `NvtIpc_WaitCPU2SuspendReady` |
| `0x800d417c` | `NvtIpc_WaitUartAck` |
| `0x800d426c` | `NvtIpc_WaitSysCallAck` |
| `0x800d435c` | `NvtIpc_SendLinuxAppPwroffAck` |
| `0x800d44a4` | `NvtIpc_WaitCPU2PowerOff` |
| `0x800d4788` | `NvtIpc_Open` |
| `0x800d4ab4` | `xNvtIpc_CoreHandleFunc` |

</details>

<details><summary><code>NvtIpcMsgQue</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x800d573c` | `NvtIpcMsgQue_DumpDebugInfo` |
| `0x800d596c` | `NvtIpcMsgQue_GetQuebyID` |
| `0x800d5a18` | `NvtIpcMsgQue_GetIDbyKey` |
| `0x800d5d10` | `NvtIpcMsgQue_Rel` |
| `0x800d5ee8` | `NvtIpcMsgQue_Get` |
| `0x800d6218` | `NvtIpcMsgQue_Ftok` |

</details>

<details><summary><code>NvtMem</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80015f24` | `NvtMem_GetNonCacheAddr` |

</details>

<details><summary><code>NVTUSER</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80002fe0` | `NVTUSER_MBX_ID` |

</details>

<details><summary><code>Nvtver</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80260ab0` | `Nvtver_DumpVerInfo` |

</details>

<details><summary><code>OS</code> (16)</summary>

| 주소 | 이름 |
|---|---|
| `0x8000c4c4` | `OS_AddMempool` |
| `0x8000c6dc` | `OS_AddMailbox` |
| `0x8000c8f8` | `OS_AddSemphore` |
| `0x8000cb04` | `OS_AddEventflag` |
| `0x8000cd24` | `OS_AddTask` |
| `0x8000e9ac` | `xOS_DumpFlgID` |
| `0x8000e9ac` | `xOS_DumpSemaID` |
| `0x80011144` | `OS_EndHeap` |
| `0x800111fc` | `OS_BeginHeap` |
| `0x800112bc` | `OS_EndStack` |
| `0x80011464` | `OS_EndCode` |
| `0x80011550` | `OS_BeginCode` |
| `0x8001160c` | `OS_ConfigCodeSection` |
| `0x800116c4` | `OS_ConfigZISection` |
| `0x80011770` | `OS_Init` |
| `0x80011928` | `OS_BeginStack` |

</details>

<details><summary><code>p2</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8019e2e8` | `p2_GetImageBuffer` |

</details>

<details><summary><code>PartLoad</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x800e49f4` | `xPartLoad_CalcBlockRange` |
| `0x800e49f4` | `xPartLoad_ReadNandToDRAM` |
| `0x800e49f4` | `xPartLoad_ReadNandToDRAM_Lz` |
| `0x800e51a4` | `PartLoad_Init` |

</details>

<details><summary><code>PB</code> (33)</summary>

| 주소 | 이름 |
|---|---|
| `0x80205cb0` | `PB_GetParam` |
| `0x80205fe4` | `PB_Open` |
| `0x802060f8` | `PB_SetParam` |
| `0x802064d4` | `PB_OpenSpecFileBySeq` |
| `0x8020710c` | `PB_DispSrv_SetDrawCb` |
| `0x80207d78` | `xPB_DispSrv_DrawSingleView` |
| `0x802083cc` | `PB_SysInit` |
| `0x8020867c` | `PB_AllocPBMemory` |
| `0x8020885c` | `PB_SetFinishFlag` |
| `0x80208d24` | `PB_Hdl_CaptureScreen` |
| `0x802090fc` | `PB_Hdl_EditImage` |
| `0x802092f4` | `xPB_DoUserEffect` |
| `0x802092f4` | `xPB_GetTmpBuff` |
| `0x80209648` | `PB_Hdl_Init` |
| `0x80209b44` | `PB_Hdl_PlaySpecFileHandle` |
| `0x8020a584` | `PB_ReResoultHandle` |
| `0x8020a584` | `PB_ScaleAndKeepImgRatio4ReSize` |
| `0x8020a91c` | `PB_RotateDisplayHandle` |
| `0x8020ab80` | `PB_SaveCurrRawBuf` |
| `0x8020b6a0` | `PB_DecodePrimaryHandler` |
| `0x8020b764` | `PB_SingleHandle` |
| `0x8020b764` | `xPB_SinglePrimaryHandle` |
| `0x8020bf6c` | `PB_UpdateEXIFHandle` |
| `0x8020c1c0` | `PB_ZoomHandle` |
| `0x8020c638` | `PB_WaitFileSystemInit` |
| `0x8020c728` | `PB_WriteFileByFileSys` |
| `0x8020d0f0` | `xPB_VdoReadCB` |
| `0x8020d184` | `PB_DecodeWhichFile` |
| `0x8020d9c0` | `PB_JpgBRCHandler` |
| `0x8020db48` | `PB_JPGScalarHandler` |
| `0x8020ef14` | `PB_CropSaveHandle` |
| `0x8020f284` | `PB_CopyImage2Display` |
| `0x8020f39c` | `PB_Thumb2Display` |

</details>

<details><summary><code>PBXFile</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x802a4e28` | `PBXFile_Access` |
| `0x802a4fa0` | `PBXFile_GetInfo` |

</details>

<details><summary><code>PBXFList</code> (10)</summary>

| 주소 | 이름 |
|---|---|
| `0x802a53c8` | `PBXFList_DCF_SeekIndex` |
| `0x802a54c4` | `PBXFList_DCF_SetInfo` |
| `0x802a5584` | `PBXFList_DCF_GetInfo` |
| `0x802a59d4` | `PBXFList_FDB_AddFile` |
| `0x802a5a3c` | `PBXFList_FDB_MakeFilePath` |
| `0x802a5a78` | `PBXFList_FDB_SetInfo` |
| `0x802a5b20` | `PBXFList_FDB_SeekIndex` |
| `0x802a5c40` | `PBXFList_FDB_Config` |
| `0x802a5dfc` | `PBXFList_FDB_GetInfo` |
| `0x802a60e4` | `PBXFList_FDB_Init` |

</details>

<details><summary><code>Perf</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80011c00` | `Perf_Close` |
| `0x80011d00` | `Perf_Open` |

</details>

<details><summary><code>Photo</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x801d5924` | `Photo_WriteDebugCB` |
| `0x8036bf18` | `Photo_WaitIdle` |
| `0x8036cb30` | `Photo_Open` |

</details>

<details><summary><code>PhotoDisplay2</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8019e470` | `PhotoDisplay2_Update` |

</details>

<details><summary><code>PhotoExe</code> (7)</summary>

| 주소 | 이름 |
|---|---|
| `0x801d24a4` | `PhotoExe_RatioSizeConvert` |
| `0x801d26c4` | `PhotoExe_OnCaptureSmile` |
| `0x801d3888` | `PhotoExe_OnImageRatio` |
| `0x801d3be8` | `PhotoExe_OnStopFunc` |
| `0x801d3ea4` | `PhotoExe_OnStartFunc` |
| `0x801d3fc0` | `PhotoExe_OnCaptureStart` |
| `0x801d49d8` | `PhotoExe_OnZoom` |

</details>

<details><summary><code>pinmux</code> (68)</summary>

| 주소 | 이름 |
|---|---|
| `0x800a6870` | `pinmux_checkMCLK` |
| `0x800a6870` | `pinmux_checkSDIO2` |
| `0x800a6870` | `pinmux_checkSDIO3` |
| `0x800a6a34` | `pinmux_selectMIDisplay` |
| `0x800a70e0` | `pinmux_configETH` |
| `0x800a7484` | `pinmux_configHDMI` |
| `0x800a7520` | `pinmux_configTV` |
| `0x800a7584` | `pinmux_configLCD2` |
| `0x800a75e0` | `pinmux_configLCD` |
| `0x800a763c` | `pinmux_configAUDIO` |
| `0x800a77fc` | `pinmux_configPWM` |
| `0x800a88fc` | `pinmux_configRemote` |
| `0x800a89fc` | `pinmux_configSPI` |
| `0x800a9414` | `pinmux_configUART` |
| `0x800a9b00` | `pinmux_configSIF` |
| `0x800a9e58` | `pinmux_configI2C` |
| `0x800aa030` | `pinmux_configMipiLvds` |
| `0x800aa318` | `pinmux_configSensor4` |
| `0x800aa7a0` | `pinmux_configSensor3` |
| `0x800aab90` | `pinmux_configSensor2` |
| `0x800aaeec` | `pinmux_configSensor` |
| `0x800ab718` | `pinmux_configNAND` |
| `0x800ab870` | `pinmux_configSDIO3` |
| `0x800ab97c` | `pinmux_configSDIO2` |
| `0x800aba28` | `pinmux_configSDIO` |
| `0x800abad4` | `pinmux_activePWM_1` |
| `0x800abbf4` | `pinmux_activePWM_2` |
| `0x800abd18` | `pinmux_activePWM_3` |
| `0x800abe3c` | `pinmux_activePWM_4` |
| `0x800abf58` | `pinmux_activePWM_5` |
| `0x800ac074` | `pinmux_activePWM_6` |
| `0x800ac190` | `pinmux_activePWM_7` |
| `0x800ac2ac` | `pinmux_activePWM_8` |
| `0x800ac410` | `pinmux_activePWM_9` |
| `0x800ac574` | `pinmux_activePWM_10` |
| `0x800ac6d8` | `pinmux_activePWM_11` |
| `0x800ac844` | `pinmux_activePWM_12` |
| `0x800ac964` | `pinmux_activePWM_13` |
| `0x800aca84` | `pinmux_activePWM_14` |
| `0x800acba4` | `pinmux_activePWM_15` |
| `0x800acccc` | `pinmux_activePWM_16` |
| `0x800ace30` | `pinmux_activePWM_17` |
| `0x800acf94` | `pinmux_activePWM_18` |
| `0x800ad0fc` | `pinmux_activePWM_19` |
| `0x800ad26c` | `pinmux_activeSIF_0` |
| `0x800ad3b8` | `pinmux_activeSIF_2` |
| `0x800ad510` | `pinmux_activeSIF_3` |
| `0x800ad6a4` | `pinmux_activeUART_2` |
| `0x800ad8f8` | `pinmux_activeUART_3` |
| `0x800adc2c` | `pinmux_activeUART_4` |
| `0x800ade3c` | `pinmux_activeI2S` |
| `0x800adfe4` | `pinmux_activeI2SMCLK` |
| `0x800ae100` | `pinmux_activeSPI2` |
| `0x800ae244` | `pinmux_activeSPI3` |
| `0x800ae3a4` | `pinmux_activeSPI4` |
| `0x800ae4e8` | `pinmux_activeSPI5` |
| `0x800ae62c` | `pinmux_activeBMC` |
| `0x800ae62c` | `pinmux_activeNAND` |
| `0x800ae62c` | `pinmux_activePWM_0` |
| `0x800ae62c` | `pinmux_activeSDIO` |
| `0x800ae62c` | `pinmux_activeSDIO2` |
| `0x800ae62c` | `pinmux_activeSDIO3` |
| `0x800ae62c` | `pinmux_activeSNMCLK` |
| `0x800ae62c` | `pinmux_activeSPI` |
| `0x800ae62c` | `pinmux_selectPrimaryLCD` |
| `0x800ae62c` | `pinmux_selectSecondaryLCD` |
| `0x800ae62c` | `pinmux_setPinmux` |
| `0x800aff40` | `pinmux_init` |

</details>

<details><summary><code>PipView</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801a5b00` | `PipView_OnDraw` |

</details>

<details><summary><code>Playback</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801a9df0` | `Playback_MenuCallback` |

</details>

<details><summary><code>PlayExe</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801d664c` | `PlayExe_OnOpen` |

</details>

<details><summary><code>pll</code> (14)</summary>

| 주소 | 이름 |
|---|---|
| `0x8009d9d4` | `pll_getClockMask` |
| `0x8009e334` | `pll_getPLLFreq` |
| `0x8009e4c0` | `pll_getClockFreq` |
| `0x8009e9a0` | `pll_getClkFreq` |
| `0x8009ea40` | `pll_setPLLEn` |
| `0x8009eaf0` | `pll_getPLLEn` |
| `0x8009f37c` | `pll_chkClkLimitation` |
| `0x8009f37c` | `pll_setClockRate` |
| `0x8009ffac` | `pll_selectClkSrc` |
| `0x800a01d0` | `pll_setClockFreq` |
| `0x800a08ec` | `pll_setClkFreq` |
| `0x800a098c` | `pll_checkPllUsage` |
| `0x800a098c` | `pll_setDrvPLL` |
| `0x800a0d58` | `pll_setPLL` |

</details>

<details><summary><code>POOL</code> (29)</summary>

| 주소 | 이름 |
|---|---|
| `0x80007134` | `POOL_ID_DATEIMPRINT` |
| `0x80007134` | `POOL_ID_EXIF` |
| `0x80007228` | `POOL_ID_CPU2` |
| `0x800072c0` | `POOL_ID_DHCPIPC` |
| `0x800072c0` | `POOL_ID_HFSIPC` |
| `0x800072c0` | `POOL_ID_USOCKIPC` |
| `0x800072c0` | `POOL_ID_WIFIIPC` |
| `0x80007450` | `POOL_ID_DCF_BUFFER` |
| `0x80007450` | `POOL_ID_FILEDB` |
| `0x80007450` | `POOL_ID_FSIPC` |
| `0x80007450` | `POOL_ID_FS_BUFFER` |
| `0x800075e4` | `POOL_ID_FWS_BUFFER` |
| `0x800075e4` | `POOL_ID_PS_BUFFER` |
| `0x800076d8` | `POOL_ID_NVTIPC` |
| `0x800076d8` | `POOL_ID_STORAGE_NAND` |
| `0x800076d8` | `POOL_ID_STORAGE_RAMDISK` |
| `0x800076d8` | `POOL_ID_STORAGE_SDIO` |
| `0x80007894` | `POOL_ID_DISP_VDO1` |
| `0x80007894` | `POOL_ID_DISP_VDO1TEMP` |
| `0x80007894` | `POOL_ID_DISP_VDO2` |
| `0x80007894` | `POOL_ID_DISP_VDO2TEMP` |
| `0x80007ad0` | `POOL_ID_DISP_OSD1` |
| `0x80007ad0` | `POOL_ID_DISP_OSD1TEMP` |
| `0x80007ad0` | `POOL_ID_DISP_OSD2` |
| `0x80007ad0` | `POOL_ID_DISP_OSD2TEMP` |
| `0x80007ad0` | `POOL_ID_GFX_IMAGE` |
| `0x80007ad0` | `POOL_ID_GFX_STRING` |
| `0x80007ad0` | `POOL_ID_GFX_TEMP` |
| `0x80007d94` | `POOL_ID_APP` |

</details>

<details><summary><code>Power</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8019bec0` | `Power_CB` |

</details>

<details><summary><code>ps</code> (23)</summary>

| 주소 | 이름 |
|---|---|
| `0x802a8740` | `ps_getStrgInfo` |
| `0x802a8848` | `ps_getBlockStartAdd` |
| `0x802a89b0` | `ps_releaseSpace` |
| `0x802a8b74` | `ps_getFreeLogicalBlock` |
| `0x802a8e8c` | `ps_uninitDrv` |
| `0x802a8f20` | `ps_initDrv` |
| `0x802a90d4` | `ps_writeBlockSeq` |
| `0x802a930c` | `ps_readBlockSeq` |
| `0x802a94bc` | `ps_addUsedLogicalBlock` |
| `0x802a94bc` | `ps_initBlockTable` |
| `0x802a9830` | `ps_writeBlockByBytes` |
| `0x802a999c` | `ps_setSecTable` |
| `0x802a9b48` | `ps_setHeadDesc` |
| `0x802a9bf4` | `ps_setSectionHead` |
| `0x802a9cfc` | `ps_writeByBytes` |
| `0x802a9fb4` | `ps_checkSingleSectionByHeader` |
| `0x802aa0ec` | `ps_checkSingleSection` |
| `0x802aa1d4` | `ps_readBlockByBytes` |
| `0x802aa2ec` | `ps_getHeadDesc` |
| `0x802aa3a0` | `ps_getSectionHead` |
| `0x802aa4b4` | `ps_getSecTable` |
| `0x802aa5a8` | `ps_dumpHeader` |
| `0x802aa894` | `ps_readByBytes` |

</details>

<details><summary><code>PStore</code> (16)</summary>

| 주소 | 이름 |
|---|---|
| `0x802a62b0` | `PStore_GetSectionIDByName` |
| `0x802a63a8` | `PStore_SetSectionDesc` |
| `0x802a6438` | `PStore_ReleaseAccessRight` |
| `0x802a65ac` | `PStore_DumpPStoreInfo` |
| `0x802a685c` | `PStore_InitDesc` |
| `0x802a6984` | `PStore_ReadSection` |
| `0x802a6b28` | `PStore_WriteSection` |
| `0x802a6f74` | `PStore_DeleteSection` |
| `0x802a7124` | `PStore_CloseSection` |
| `0x802a7270` | `PStore_GetSectionHandle` |
| `0x802a7270` | `PStore_OpenSection` |
| `0x802a77b8` | `PStore_Dump` |
| `0x802a7a98` | `PStore_Close` |
| `0x802a7bf0` | `PStore_InitialHeadBuffer` |
| `0x802a7d28` | `PStore_Open` |
| `0x802a818c` | `PStore_Format` |

</details>

<details><summary><code>pwm</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8004ebb8` | `pwm_dumpInfo` |

</details>

<details><summary><code>query</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801c7d98` | `query_devinfo` |

</details>

<details><summary><code>Quick</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801a95f4` | `Quick_Sets_MenuCallback` |

</details>

<details><summary><code>ramdsk</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x800de7ac` | `ramdsk_getParam` |
| `0x800de9d4` | `ramdsk_setParam` |

</details>

<details><summary><code>rde</code> (10)</summary>

| 주소 | 이름 |
|---|---|
| `0x80144b00` | `rde_isOpen` |
| `0x80144b48` | `rde_stateMachine` |
| `0x80145364` | `rde_chkDMAInInfo` |
| `0x801453d0` | `rde_setClockRate` |
| `0x80145780` | `rde_setCropStX` |
| `0x80145804` | `rde_setLineStrpDMAInInfo` |
| `0x801458a8` | `rde_chgCropParam` |
| `0x80145ac4` | `rde_chkDMAOutInfo` |
| `0x80145ac4` | `rde_setFunctionEnable` |
| `0x80145ac4` | `rde_setMode` |

</details>

<details><summary><code>RDE</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80335bb8` | `RDE_CAP_D2D_CB` |
| `0x80335bb8` | `RDE_D2D_CB` |

</details>

<details><summary><code>ReadReg</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80166f38` | `ReadReg_IMX206CQC` |

</details>

<details><summary><code>rhe</code> (13)</summary>

| 주소 | 이름 |
|---|---|
| `0x80162388` | `rhe_calcHdrRefLaScl` |
| `0x801624e8` | `rhe_calcRefDc` |
| `0x801625ac` | `rhe_calcHdrRefLaLpf` |
| `0x801626c4` | `rhe_calcHdrRefLaIn` |
| `0x8016278c` | `rhe_setRawSize` |
| `0x80162834` | `rhe_setLoad` |
| `0x80162d18` | `rhe_stateMachine` |
| `0x80162ee8` | `rhe_chgParam` |
| `0x8016315c` | `rhe_setMode` |
| `0x80163448` | `rhe_close` |
| `0x8016350c` | `rhe_open` |
| `0x8016350c` | `rhe_setClock` |
| `0x80163814` | `rhe_isr` |

</details>

<details><summary><code>RHED2D</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8030d940` | `RHED2D_start` |

</details>

<details><summary><code>rm</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801ca0dc` | `rm_acl_table` |

</details>

<details><summary><code>RSC</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80005580` | `RSC_Tsk` |
| `0x803503e4` | `RSC_FCB_RunTimeChg` |

</details>

<details><summary><code>rsc</code> (25)</summary>

| 주소 | 이름 |
|---|---|
| `0x802aafc0` | `rsc_stateMachine` |
| `0x802ab0fc` | `rsc_getInfo` |
| `0x802ab2ec` | `rsc_prcFrm` |
| `0x802ab420` | `rsc_prcSmp` |
| `0x802ab970` | `rsc_chgSet` |
| `0x802abc2c` | `rsc_open` |
| `0x802abfa8` | `rsc_Smp_int1_GD_DebugPrint` |
| `0x802ac06c` | `rsc_Smp_int1_GD_Process` |
| `0x802ac6ac` | `rsc_Smp_int2_AT_DebugPrint` |
| `0x802ac748` | `rsc_Smp_int2_AT_Process` |
| `0x802acfac` | `rsc_Frm_int1_AT_DebugPrint` |
| `0x802ad124` | `rsc_Frm_int1_AT_Prepare` |
| `0x802ad8d4` | `rsc_Frm_int2_AR_DebugPrint` |
| `0x802ad9f4` | `rsc_Frm_int2_AR_Process` |
| `0x802ae1c4` | `rsc_Frm_int3_MA_DebugPrint` |
| `0x802aeb1c` | `rsc_Frm_int3_MA_Process` |
| `0x802b0810` | `rsc_Frm_int4_MR_DebugPrint` |
| `0x802b08ec` | `rsc_Frm_int5_HI_DebugPrint` |
| `0x802b0944` | `rsc_Frm_int5_HI_Process` |
| `0x802b1100` | `rsc_Msc_CalcSine` |
| `0x802b1268` | `rsc_Msc_TransferDoubleToMS` |
| `0x802b13c0` | `rsc_Dbg_UpdateOption` |
| `0x802b161c` | `rsc_Dbg_PrintAllSet` |
| `0x802b22a4` | `rsc_Dbg_PrintAllIntX` |
| `0x80379834` | `rsc_setAction` |

</details>

<details><summary><code>rtc</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x800b1370` | `rtc_setAlarm` |
| `0x800b1474` | `rtc_setConfig` |
| `0x800b15d4` | `rtc_setPWRAlarm` |
| `0x800b17f4` | `rtc_setTime` |
| `0x800b1950` | `rtc_setDate` |
| `0x800b1c40` | `rtc_open` |

</details>

<details><summary><code>RTSPNVT</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x800031e8` | `RTSPNVT_FLG_ID` |
| `0x800031e8` | `RTSPNVT_SEM_ID` |

</details>

<details><summary><code>RtspNvt</code> (9)</summary>

| 주소 | 이름 |
|---|---|
| `0x8020f788` | `RtspNvt_SetParam` |
| `0x8020f9a8` | `RtspNvt_Close` |
| `0x8020fb3c` | `RtspNvt_Open` |
| `0x8020fec0` | `xRtspNvt_ICmd` |
| `0x8021029c` | `xRtspNvt_Wrn` |
| `0x802102e8` | `xRtspNvt_SendIPC` |
| `0x8021191c` | `xRtspNvt_OnUnLockStrmID` |
| `0x80211b98` | `xRtspNvt_OnGetAudio` |
| `0x802128d8` | `xRtspNvt_OnParseMediaSrcID` |

</details>

<details><summary><code>RtspNvtRec</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80211a24` | `xRtspNvtRec_FillAudInfo` |
| `0x8021202c` | `xRtspNvtRec_FillVdoInfo` |

</details>

<details><summary><code>SceneRenderWDR</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x80379e8c` | `SceneRenderWDR_SetA_chgCurveWeightMap` |
| `0x8037a268` | `SceneRenderWDR_SetA_Init` |
| `0x8037a71c` | `SceneRenderWDR_SetA_Proc` |
| `0x8037b9b8` | `SceneRenderWDR_SetB_chgCurveWeightMap` |
| `0x8037bd94` | `SceneRenderWDR_SetB_Init` |
| `0x8037c248` | `SceneRenderWDR_SetB_Proc` |

</details>

<details><summary><code>SD</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800c2340` | `SD_VOL` |

</details>

<details><summary><code>SD1</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80026bac` | `SD1_SLOW` |
| `0x80026bdc` | `SD1_FAST` |

</details>

<details><summary><code>SD2</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80026b4c` | `SD2_SLOW` |
| `0x80026b7c` | `SD2_FAST` |

</details>

<details><summary><code>sdio</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800852c8` | `sdio_getStorageObject` |

</details>

<details><summary><code>sdio2strg</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80096970` | `sdio2strg_SetParam` |

</details>

<details><summary><code>sdio3</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80097aac` | `sdio3_getStorageObject` |

</details>

<details><summary><code>sdio3strg</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80097548` | `sdio3strg_SetParam` |
| `0x80097760` | `sdio3strg_GetParam` |

</details>

<details><summary><code>sdioHost</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80088e5c` | `sdioHost_getBusClk` |
| `0x80088f58` | `sdioHost_setBusClk` |
| `0x8008a0ac` | `sdioHost_setDesTab` |

</details>

<details><summary><code>sdioPrtcl</code> (32)</summary>

| 주소 | 이름 |
|---|---|
| `0x8008e1c8` | `sdioPrtcl_getMiscInfo` |
| `0x8008e250` | `sdioPrtcl_setMemPool` |
| `0x8008eb84` | `sdioPrtcl_sendSDCmd` |
| `0x8008edf8` | `sdioPrtcl_bootreadSectors` |
| `0x8008edf8` | `sdioPrtcl_readBoot` |
| `0x8008f1e4` | `sdioPrtcl_bootclose` |
| `0x8008f3cc` | `sdioPrtcl_EmmcResetCmd` |
| `0x8008f548` | `sdioPrtcl_switchEmmcMode` |
| `0x8008f8b8` | `sdioPrtcl_bootopen` |
| `0x8008fd18` | `sdioPrtcl_switchSDMode` |
| `0x8008ffa0` | `sdioPrtcl_setSDSpeedMode` |
| `0x800900d0` | `sdioPrtcl_getSDSwFunStatus` |
| `0x80090198` | `sdioPrtcl_waitCardTransferState` |
| `0x8009037c` | `sdioPrtcl_getCardAppData` |
| `0x800907f0` | `sdioPrtcl_getSSRRegister` |
| `0x800908a4` | `sdioPrtcl_getSCRRegister` |
| `0x8009094c` | `sdioPrtcl_getExtCSD` |
| `0x80090b88` | `sdioPrtcl_getMMCExtCSD` |
| `0x80090c48` | `sdioPrtcl_writeCard` |
| `0x80090c48` | `sdioPrtcl_writeSectors` |
| `0x80091988` | `sdioPrtcl_getCardInfo` |
| `0x80091fdc` | `sdioPrtcl_sendCMD42` |
| `0x800921dc` | `sdioPrtcl_setCmd42` |
| `0x80092304` | `sdioPrtcl_setConfig` |
| `0x80092b48` | `sdioPrtcl_readCard` |
| `0x80092b48` | `sdioPrtcl_readSectors` |
| `0x800933d4` | `sdioPrtcl_open` |
| `0x80095144` | `sdioPrtcl_setCardStdbyState` |
| `0x80095350` | `sdioPrtcl_close` |
| `0x8009562c` | `sdioPrtcl_closeMemBus` |
| `0x80095818` | `sdioPrtcl_openMemBus` |
| `0x80095818` | `sdioPrtcl_setCardTransferState` |

</details>

<details><summary><code>sdiostrg</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80084cf0` | `sdiostrg_ExtIOCtrl` |
| `0x80084dc4` | `sdiostrg_SetParam` |
| `0x80084fd4` | `sdiostrg_GetParam` |

</details>

<details><summary><code>SectionRead</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80343e6c` | `SectionRead_Header` |

</details>

<details><summary><code>SectionWrite</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80343c68` | `SectionWrite_Header` |

</details>

<details><summary><code>SEMID</code> (23)</summary>

| 주소 | 이름 |
|---|---|
| `0x80002c28` | `SEMID_GXTIMER` |
| `0x80003fc4` | `SEMID_SPIFLASH` |
| `0x80003fc4` | `SEMID_SPI_FAT` |
| `0x80003fc4` | `SEMID_SPI_FAT2` |
| `0x80003fc4` | `SEMID_SPI_FAT3` |
| `0x80003fc4` | `SEMID_SPI_FW` |
| `0x80003fc4` | `SEMID_SPI_FW2` |
| `0x80003fc4` | `SEMID_SPI_FW3` |
| `0x80003fc4` | `SEMID_SPI_FW4` |
| `0x80003fc4` | `SEMID_SPI_FW5` |
| `0x80003fc4` | `SEMID_SPI_PS` |
| `0x80003fc4` | `SEMID_SPI_PS2` |
| `0x80003fc4` | `SEMID_SPI_PS3` |
| `0x80004524` | `SEMID_DCF_COMM` |
| `0x800046a8` | `SEMID_DPOF` |
| `0x80004a0c` | `SEMID_FILEDB_COMM` |
| `0x80004d50` | `SEMID_FILESYS_COMM` |
| `0x800051c0` | `SEMID_GXFLASH` |
| `0x800054c4` | `SEMID_PS_SEC1` |
| `0x800054c4` | `SEMID_PS_SEC2` |
| `0x800056f8` | `SEMID_UVC_PAL_BUF_1` |
| `0x800056f8` | `SEMID_UVC_PAL_BUF_2` |
| `0x80005960` | `SEMID_MP_H264` |

</details>

<details><summary><code>SEN</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80003f80` | `SEN_FlgID` |

</details>

<details><summary><code>Sensor</code> (20)</summary>

| 주소 | 이름 |
|---|---|
| `0x80163c7c` | `Sensor_Module_GetCurMode` |
| `0x80163e70` | `Sensor_Module_ChkCmdType` |
| `0x80163e70` | `Sensor_Module_ChkDataType` |
| `0x80163e70` | `Sensor_Module_Init` |
| `0x80163e70` | `Sensor_Module_Open` |
| `0x801641e8` | `Sensor_Module_ReadReg` |
| `0x80164300` | `Sensor_Module_Close` |
| `0x80164300` | `Sensor_Module_UnInit` |
| `0x801645d8` | `Sensor_Module_GetUserOption` |
| `0x801646e4` | `Sensor_Module_PresetMode` |
| `0x801647fc` | `Sensor_Module_PresetLock` |
| `0x80164968` | `Sensor_Module_WriteReg` |
| `0x80164a80` | `Sensor_Module_SetGain` |
| `0x80164bb0` | `Sensor_Module_SetExpTime` |
| `0x80164d1c` | `Sensor_Module_GetGainSetting` |
| `0x80164e30` | `Sensor_Module_SetAGC_ISOBase` |
| `0x80164f44` | `Sensor_Module_GetExpoSetting` |
| `0x80165070` | `Sensor_Module_ChgMode` |
| `0x80165070` | `Sensor_Module_ChkModeType` |
| `0x8016530c` | `Sensor_Module_GetStatus` |

</details>

<details><summary><code>SensorHDR</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x8037ddc4` | `SensorHDR_ModelA_SetEVGap` |
| `0x8037de40` | `SensorHDR_ModelA_GetEVGap` |
| `0x8037df3c` | `SensorHDR_ModelA_Init` |

</details>

<details><summary><code>SensorIF</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x8016613c` | `SensorIF_GetPllCtrlObj` |
| `0x80166198` | `SensorIF_GetTGECtrlObj` |
| `0x8016620c` | `SensorIF_GetSIECtrlObj` |
| `0x80166278` | `SensorIF_GetLVDSCtrlObj` |

</details>

<details><summary><code>Set2Preview</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80345d6c` | `Set2Preview_IMX206CQC_EVB_FF` |

</details>

<details><summary><code>SetGain</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8016703c` | `SetGain_IMX206CQC` |

</details>

<details><summary><code>SetLine</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80167134` | `SetLine_IMX206CQC` |

</details>

<details><summary><code>SetupExe</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x801d8d70` | `SetupExe_OnWifiStart` |
| `0x801d8f34` | `SetupExe_OnHDMIFormat` |
| `0x801d900c` | `SetupExe_OnTVFormat` |
| `0x801d9240` | `SetupExe_OnForceToLivedMode` |
| `0x801d935c` | `SetupExe_OnChangeDSCMode` |
| `0x801d96c8` | `SetupExe_OnFILEDB_FILEID_RESET` |

</details>

<details><summary><code>show</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8016dfa4` | `show_logo` |

</details>

<details><summary><code>SIE</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80316b90` | `SIE_GetVigSetting` |
| `0x803172d4` | `SIE_Gamma` |

</details>

<details><summary><code>sie1</code> (26)</summary>

| 주소 | 이름 |
|---|---|
| `0x8014f7f8` | `sie1_calcBSHScl` |
| `0x8014fad8` | `sie1_getHisto` |
| `0x8014fbd4` | `sie1_getOutAdd_Flip` |
| `0x8014ff70` | `sie1_getOutAdd` |
| `0x8015021c` | `sie1_calcCaLaSize` |
| `0x80150640` | `sie1_calcECSScl` |
| `0x8015079c` | `sie1_calcObPlnScl` |
| `0x801508a0` | `sie1_setVaWin` |
| `0x801509b4` | `sie1_setVaCrp` |
| `0x80150a74` | `sie1_setBccParam` |
| `0x80150c38` | `sie1_setCropWindow` |
| `0x80150cd0` | `sie1_setActiveWindow` |
| `0x80150d68` | `sie1_verifyFunction` |
| `0x80150ef0` | `sie1_setMainInput` |
| `0x80150ff4` | `sie1_calcVIG` |
| `0x80151b1c` | `sie1_stateMachine` |
| `0x80151ce0` | `sie1_chgBurstLengthByMode` |
| `0x80151d9c` | `sie1_measureFrameTime` |
| `0x801521e8` | `sie1_waitEvent` |
| `0x801522ac` | `sie1_chgParam` |
| `0x801526c8` | `sie1_chgFuncEn` |
| `0x801527f0` | `sie1_setMode` |
| `0x80152c4c` | `sie1_close` |
| `0x80152d24` | `sie1_open` |
| `0x80152d24` | `sie1_setClock` |
| `0x8015305c` | `sie1_isr` |

</details>

<details><summary><code>sie2</code> (22)</summary>

| 주소 | 이름 |
|---|---|
| `0x80156b54` | `sie2_calcBSHScl` |
| `0x80156e34` | `sie2_getHisto` |
| `0x80156f30` | `sie2_getOutAdd_Flip` |
| `0x801571f8` | `sie2_getOutAdd` |
| `0x801574a4` | `sie2_calcCaLaSize` |
| `0x801578c8` | `sie2_calcECSScl` |
| `0x80157a24` | `sie2_setVaWin` |
| `0x80157b38` | `sie2_setVaCrp` |
| `0x80157bf8` | `sie2_setBccParam` |
| `0x80157dbc` | `sie2_setCropWindow` |
| `0x80157e54` | `sie2_setActiveWindow` |
| `0x80157eec` | `sie2_verifyFunction` |
| `0x80158074` | `sie2_setMainInput` |
| `0x80158400` | `sie2_stateMachine` |
| `0x801587a8` | `sie2_waitEvent` |
| `0x80158844` | `sie2_chgParam` |
| `0x80158c60` | `sie2_chgFuncEn` |
| `0x80158d88` | `sie2_setMode` |
| `0x80159148` | `sie2_close` |
| `0x80159220` | `sie2_open` |
| `0x80159220` | `sie2_setClock` |
| `0x801595a0` | `sie2_isr` |

</details>

<details><summary><code>sie3</code> (13)</summary>

| 주소 | 이름 |
|---|---|
| `0x8015bebc` | `sie3_setVaWin` |
| `0x8015bfd0` | `sie3_setVaCrp` |
| `0x8015c090` | `sie3_setCropWindow` |
| `0x8015c128` | `sie3_setActiveWindow` |
| `0x8015c1c0` | `sie3_verifyFunction` |
| `0x8015c348` | `sie3_setMainInput` |
| `0x8015c4f4` | `sie3_stateMachine` |
| `0x8015c6ec` | `sie3_chgParam` |
| `0x8015cb08` | `sie3_chgFuncEn` |
| `0x8015ce44` | `sie3_close` |
| `0x8015cf14` | `sie3_open` |
| `0x8015cf14` | `sie3_setClock` |
| `0x8015d120` | `sie3_isr` |

</details>

<details><summary><code>sie4</code> (13)</summary>

| 주소 | 이름 |
|---|---|
| `0x8015f8fc` | `sie4_setVaWin` |
| `0x8015fa10` | `sie4_setVaCrp` |
| `0x8015fad0` | `sie4_setCropWindow` |
| `0x8015fb68` | `sie4_setActiveWindow` |
| `0x8015fc00` | `sie4_verifyFunction` |
| `0x8015fd88` | `sie4_setMainInput` |
| `0x8015ff34` | `sie4_stateMachine` |
| `0x8016012c` | `sie4_chgParam` |
| `0x80160548` | `sie4_chgFuncEn` |
| `0x80160884` | `sie4_close` |
| `0x80160954` | `sie4_open` |
| `0x80160954` | `sie4_setClock` |
| `0x80160b18` | `sie4_isr` |

</details>

<details><summary><code>SIED2D</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8030de1c` | `SIED2D_start` |

</details>

<details><summary><code>SIEx</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8033869c` | `SIEx_IQparam` |

</details>

<details><summary><code>sif</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x8004f6ac` | `sif_getConfig` |
| `0x8004fcc0` | `sif_waitTransferEnd` |
| `0x8004fd4c` | `sif_send` |
| `0x80050204` | `sif_setConfig` |
| `0x80050de0` | `sif_close` |
| `0x80050f9c` | `sif_open` |

</details>

<details><summary><code>SM</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x802320c8` | `SM_Media_SaveToSmallFile` |

</details>

<details><summary><code>SMedaiRecAud</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x802263bc` | `SMedaiRecAud_GetFsDiskInfo` |

</details>

<details><summary><code>SMediaAudioDec</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x802177bc` | `SMediaAudioDec_TskStart` |
| `0x80217848` | `SMediaAudioDec_AddBSDataToQueue` |
| `0x8021793c` | `SMediaAudioDec_ConfigureObj` |
| `0x8021793c` | `SMediaAudioDec_mallocRAW` |

</details>

<details><summary><code>SMediaBSQ</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80230780` | `SMediaBSQ_DoMdatAction` |
| `0x80231658` | `SMediaBSQ_CheckCardfull` |

</details>

<details><summary><code>SMediaPlay</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x80214150` | `SMediaPlay_WaitReady` |
| `0x80214c0c` | `SMediaPlay_PausePlay` |
| `0x80214ec4` | `SMediaPlay_StartPlay` |
| `0x80215410` | `SMediaPlay_Open` |
| `0x80215a88` | `SMediaPlay_StartVidDecTrigger` |

</details>

<details><summary><code>SMediaPlayFSUti</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80213740` | `SMediaPlayFSUti_ReadWriteConti` |

</details>

<details><summary><code>SMediaPresent</code> (9)</summary>

| 주소 | 이름 |
|---|---|
| `0x80218480` | `SMediaPresent_RefreshAudio` |
| `0x802184fc` | `SMediaPresent_AudStop` |
| `0x80218588` | `SMediaPresent_AudPause` |
| `0x802185f4` | `SMediaPresent_AudStart` |
| `0x80218698` | `SMediaPresent_AudClose` |
| `0x8021892c` | `SMediaPresent_TskStart` |
| `0x802189b8` | `SMediaPresent_AddAudioRawDataToQueue` |
| `0x80218bec` | `SMediaPresent_ConfigureObj` |
| `0x80218dcc` | `SMediaPresent_AddVideoRawDataToQueue` |

</details>

<details><summary><code>SMediaRec</code> (21)</summary>

| 주소 | 이름 |
|---|---|
| `0x80219c74` | `SMediaRec_CheckFiles` |
| `0x80219d00` | `SMediaRec_SetMaxStopFlashSec` |
| `0x80219e0c` | `SMediaRec_GetParam` |
| `0x8021a028` | `SMediaRec_CalcSecBySetting` |
| `0x8021a634` | `SMediaRec_SetUserData` |
| `0x8021ae20` | `SMediaRec_SetEmergencyRecording` |
| `0x8021b34c` | `SMediaRec_GetInfo` |
| `0x8021e94c` | `SMediaRec_ReAllocBuf2VA` |
| `0x8021fdd4` | `SMediaRec_ChangeParameter` |
| `0x80220724` | `SMediaRec_SetExtendCrash` |
| `0x80221ad4` | `SMediaRec_Disk2SecondWithType` |
| `0x80221f54` | `SMediaRec_Record` |
| `0x80222394` | `SMediaRec_Stop` |
| `0x802225f8` | `SMediaRec_Close` |
| `0x8022277c` | `SMediaRec_Open` |
| `0x802232e8` | `SMediaRec_GetReadyBufWithID` |
| `0x80223590` | `SMediaRec_PutReadyBufWithID` |
| `0x802237f8` | `SMediaRec_SetReadyBufWithID` |
| `0x80229458` | `SMediaRec_SetGPSData` |
| `0x8022a744` | `SMediaRec_Clean4Recording` |
| `0x8022faf4` | `SMediaRec_StopFlash` |

</details>

<details><summary><code>SMediaRecAud</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x802254b8` | `SMediaRecAud_EventISR` |
| `0x80225998` | `SMediaRecAud_EncodeAAC` |
| `0x80225de8` | `SMediaRecAud_SetEncParam` |
| `0x80226aec` | `SMediaRecAud_DeviceOpen` |
| `0x80226d14` | `SMediaRecAud_TriggerTimerSet` |
| `0x80227164` | `SMediaRecAud_ReadFixDataToBuf` |

</details>

<details><summary><code>SMediaRecFS</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80227848` | `SMediaRecFS_SetEndChar` |
| `0x80229fc4` | `SMediaRecFS_DeleteOld` |
| `0x80229fc4` | `SMediaRecFS_DeleteRO` |

</details>

<details><summary><code>SMediaRecFSUti</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x80227e48` | `SMediaRecFSUti_GetOverviewID_by_fstskID` |
| `0x802282c4` | `SMediaRecFSUti_ChangePathtoCrash` |
| `0x80228f50` | `SMediaRecFSUti_DeleteFileByPath` |
| `0x8022936c` | `SMediaRecFSUti_ReadWriteConti` |
| `0x80229c34` | `SMediaRecFSUti_CreateFile` |

</details>

<details><summary><code>SMediaRecMdat</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8022e33c` | `SMediaRecMdat_ConfigureObj` |

</details>

<details><summary><code>SMediaRecQ</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x8022b0b8` | `SMediaRecQ_GetSavefileQueue` |
| `0x8022b4d8` | `SMediaRecQ_AddSavefileQueue` |
| `0x8022b4d8` | `SMediaRecQ_GetUnWriteLastVideoAddr` |

</details>

<details><summary><code>SMediaRecUti</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x80219f70` | `SMediaRecUti_GetCustomDataMaxSize` |
| `0x8021a230` | `SMediaRecUti_CheckGood` |
| `0x8021ab24` | `SMediaRecUti_WaitEncThumbOK` |
| `0x8021b764` | `SMediaRecUti_GetBytePerSec` |
| `0x8021e4cc` | `SMediaRecUti_SetCtrlObj_Mem` |

</details>

<details><summary><code>SMediaRecVid</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x80222ef4` | `SMediaRecVid_SetTimeLapseTime` |
| `0x8022325c` | `SMediaRecVid_GetActAddr` |
| `0x802239ac` | `SMediaRecVid_SetEncodeParam` |
| `0x802241fc` | `SMediaRecVid_GetIpReadyFrameAddr` |
| `0x80224508` | `SMediaRecVid_EncTriggerTimerSet` |

</details>

<details><summary><code>SMediaRecVidTrig</code> (10)</summary>

| 주소 | 이름 |
|---|---|
| `0x80233384` | `SMediaRecVidTrig_PreEncode` |
| `0x80233884` | `SMediaRecVidTrig_GetYUVSrc` |
| `0x80233884` | `SMediaRecVidTrig_GetYuvFromQueue` |
| `0x80233af8` | `SMediaRecVidTrig_HowManyinQ` |
| `0x80233cc4` | `SMediaRecVidTrig_WaitAndTrig` |
| `0x80234500` | `SMediaRecVidTrig_TrigAndDoLastThenWait` |
| `0x80234ed8` | `SMediaRecVidTrig_TrigAndWait` |
| `0x80235c44` | `SMediaRecVidTrig_InitParam` |
| `0x80235e1c` | `SMediaRecVidTrig_CreatePluginObject` |
| `0x80236350` | `SMediaRecVidTrig_Start` |

</details>

<details><summary><code>SMediaVideoDec</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x80216ae0` | `SMediaVideoDec_TskStart` |
| `0x80216b6c` | `SMediaVideoDec_AddBSDataToQueue` |
| `0x80216c4c` | `SMediaVideoDec_ConfigureObj` |
| `0x80216c4c` | `SMediaVideoDec_mallocRAW` |

</details>

<details><summary><code>SMR</code> (12)</summary>

| 주소 | 이름 |
|---|---|
| `0x8022c1b4` | `SMR_FSObj_DoAction` |
| `0x8022c818` | `SMR_FSObj_SetInfo` |
| `0x8022cb20` | `SMR_FSObj_PadNidx2MdatbyFskID` |
| `0x8022ce1c` | `SMR_FSObj_MakeNidx2Mdat` |
| `0x8022d0ac` | `SMR_FSObj_MakeGPS2Mdat` |
| `0x8022d1b0` | `SMR_MakerObj_UpdateHeader` |
| `0x8022d22c` | `SMR_MakerObj_GetInfo` |
| `0x8022d2c0` | `SMR_MakerObj_SetInfo` |
| `0x8022d388` | `SMR_MakerObj_MakeHeader` |
| `0x8022d3ec` | `SMR_MakerObjUti_InitAvi` |
| `0x8022d3ec` | `SMR_MakerObjUti_InitMov` |
| `0x8022d3ec` | `SMR_MakerObj_Create` |

</details>

<details><summary><code>SMRawEnc</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x802369dc` | `SMRawEnc_CheckErrorBeforeEnc` |
| `0x80237130` | `SMRawEnc_ScaleRaw2JpgSize` |
| `0x80238860` | `SMRawEnc_Open` |

</details>

<details><summary><code>SMRawEncUti</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80236fd4` | `SMRawEncUti_GetReadyRaw` |
| `0x80237494` | `SMRawEncUti_ScaleRaw` |

</details>

<details><summary><code>SMRMultiVid</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x802241fc` | `SMRMultiVid_IPLGetReadyCB` |
| `0x80224a34` | `SMRMultiVid_SetYUVSrc` |

</details>

<details><summary><code>Sound</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8019b354` | `Sound_CB` |

</details>

<details><summary><code>spi</code> (19)</summary>

| 주소 | 이름 |
|---|---|
| `0x80053090` | `spi_getGyroQueueCount` |
| `0x8005310c` | `spi_setConfig` |
| `0x80053990` | `spi_getGyroData` |
| `0x80053f24` | `spi_addGyroQueue` |
| `0x80054254` | `spi_waitFlag` |
| `0x80054660` | `spi_setTransferLen` |
| `0x80054798` | `spi_waitClrFlag` |
| `0x80054ad8` | `spi_waitBitMatch` |
| `0x80054c3c` | `spi_stopGyro` |
| `0x80055128` | `spi_startGyro` |
| `0x80055e70` | `spi_writeReadSingle` |
| `0x80056044` | `spi_readSingle` |
| `0x80056624` | `spi_writeReadData` |
| `0x80056f98` | `spi_close` |
| `0x800572bc` | `spi_lock` |
| `0x800572bc` | `spi_open` |
| `0x80084530` | `spi_nand_cmdProgramSpare` |
| `0x8008467c` | `spi_nand_cmdEraseBlock` |
| `0x800847ec` | `spi_nand_cmdConditionEraseBlock` |

</details>

<details><summary><code>spiFAT</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x800db2c0` | `spiFAT_fwSetParam` |
| `0x800db374` | `spiFAT_fwReadSector` |
| `0x800db51c` | `spiFAT_fwWriteSector` |

</details>

<details><summary><code>spiFAT2</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x800db914` | `spiFAT2_fwSetParam` |
| `0x800db9c8` | `spiFAT2_fwReadSector` |
| `0x800dbb70` | `spiFAT2_fwWriteSector` |

</details>

<details><summary><code>spiFAT3</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x800dbf6c` | `spiFAT3_fwSetParam` |
| `0x800dc020` | `spiFAT3_fwReadSector` |
| `0x800dc1c8` | `spiFAT3_fwWriteSector` |

</details>

<details><summary><code>spiflash</code> (10)</summary>

| 주소 | 이름 |
|---|---|
| `0x800d901c` | `spiflash_dumpInfo` |
| `0x800d936c` | `spiflash_lock` |
| `0x800d93c4` | `spiflash_unlock` |
| `0x800d9418` | `spiflash_extIOCtrl` |
| `0x800d97bc` | `spiflash_enableQuadMode` |
| `0x800d97bc` | `spiflash_readByBytes` |
| `0x800d9d44` | `spiflash_eraseSector` |
| `0x800da038` | `spiflash_close` |
| `0x800da108` | `spiflash_programSector` |
| `0x800da4f0` | `spiflash_getDeviceInfo` |

</details>

<details><summary><code>spiNand</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x80058df0` | `spiNand_readPage` |
| `0x800591fc` | `spiNand_programPage` |
| `0x80059614` | `spiNand_readID` |
| `0x800599cc` | `spiNand_open` |

</details>

<details><summary><code>spiStrg</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x800dd840` | `spiStrg_fwErase` |
| `0x800dd9b4` | `spiStrg_fwReadSector` |
| `0x800ddab4` | `spiStrg_fwWriteSector` |
| `0x800de134` | `spiStrg_fwSetParam` |
| `0x800de404` | `spiStrg_unlock` |
| `0x800de48c` | `spiStrg_lock` |

</details>

<details><summary><code>Storage</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801dbccc` | `Storage_EmbMem5` |

</details>

<details><summary><code>Strg</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800e7804` | `Strg_CB` |

</details>

<details><summary><code>SwTimer</code> (8)</summary>

| 주소 | 이름 |
|---|---|
| `0x800165d0` | `SwTimer_Stop` |
| `0x80016694` | `SwTimer_Cfg` |
| `0x800168b8` | `SwTimer_WaitTimeup` |
| `0x80016a04` | `SwTimer_Start` |
| `0x80016b18` | `SwTimer_Close` |
| `0x80016c10` | `SwTimer_Open` |
| `0x80016d98` | `SwTimer_DelayMs` |
| `0x80016e70` | `SwTimer_Init` |

</details>

<details><summary><code>SXCMD</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80003c7c` | `SXCMD_SEM_ID` |

</details>

<details><summary><code>SxCmd</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x80013354` | `xSxCmd_IsChangeMode` |
| `0x80013560` | `SxCmd_Close` |
| `0x800135bc` | `SxCmd_Open` |
| `0x800139fc` | `SxCmd_AddTable` |

</details>

<details><summary><code>SxTimer</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80025690` | `SxTimer_GetData` |
| `0x800258e0` | `SxTimer_Close` |
| `0x80025940` | `SxTimer_Open` |

</details>

<details><summary><code>SysMan</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8019bb48` | `SysMan_GetKeySoundMask` |
| `0x8019bbf0` | `xSysMan_NormalKeyCB` |

</details>

<details><summary><code>SysStrg</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800e6610` | `xSysStrg_eCosRun` |

</details>

<details><summary><code>System</code> (27)</summary>

| 주소 | 이름 |
|---|---|
| `0x800cb464` | `System_OnShutdown` |
| `0x800cb948` | `System_OnBoot` |
| `0x800d7d08` | `System_OnPowerPreInit` |
| `0x800d84e0` | `System_OnUsbRemove` |
| `0x800e5b3c` | `System_OnStrgDetach` |
| `0x800e5b80` | `System_OnStrg_UploadFW` |
| `0x800e5f20` | `System_OnStrg_DownloadFW` |
| `0x800e62a4` | `System_OnStrgInit_EMBMEM` |
| `0x800e6aa4` | `System_OnStrgExit_FWS` |
| `0x800e6ae8` | `System_OnStrgInit_FWS` |
| `0x800e6d34` | `System_OnStrgInit_PS` |
| `0x800e6fac` | `System_OnStrgRemove` |
| `0x800e70b4` | `System_OnStrgInsert` |
| `0x800e73d0` | `System_OnStrgInit_FS` |
| `0x80121c14` | `System_OnSensorDisplay` |
| `0x80121cac` | `System_OnSensorRemove` |
| `0x80121da4` | `System_OnSensorInsert` |
| `0x8012209c` | `System_EnableSensor` |
| `0x8016cc0c` | `System_OnVideoRemove` |
| `0x8016cdb8` | `System_OnVideoInsert` |
| `0x8016d6f8` | `System_EnableDisp` |
| `0x8019a760` | `System_ModeSleepLeave` |
| `0x8019a840` | `System_ModeSleepEnter` |
| `0x8019a924` | `System_ModeClose` |
| `0x8019aa04` | `System_ModeOpen` |
| `0x8019ab44` | `System_AddMode` |
| `0x8019b234` | `System_OnAudioInit` |

</details>

<details><summary><code>tge</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x801610c4` | `tge_stateMachine` |
| `0x80161400` | `tge_close` |
| `0x801614c0` | `tge_open` |

</details>

<details><summary><code>timer</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x800b26ec` | `timer_isr` |
| `0x800b28bc` | `timer_openSysTimer` |

</details>

<details><summary><code>TM</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80012204` | `TM_Begin` |

</details>

<details><summary><code>uart</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x8005a4d4` | `uart_setBaudrate` |
| `0x8005a5b0` | `uart_setConfig` |
| `0x8005ab58` | `uart_isr` |

</details>

<details><summary><code>uart2</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x8005b540` | `uart2_setBaudrate` |
| `0x8005b61c` | `uart2_isr` |
| `0x8005bdfc` | `uart2_setConfig` |

</details>

<details><summary><code>uart3</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8005c4e0` | `uart3_isr` |

</details>

<details><summary><code>uart4</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8005cc40` | `uart4_isr` |

</details>

<details><summary><code>UI</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x8016c2e4` | `UI_ShowJPG` |
| `0x8019c61c` | `UI_Show` |
| `0x801a65c8` | `UI_Switch_DscMode` |

</details>

<details><summary><code>UICTRL</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x80002898` | `UICTRL_GFX_SEM_ID` |
| `0x8000386c` | `UICTRL_DRW_SEM_ID` |
| `0x8000386c` | `UICTRL_FLG_ID` |
| `0x8000386c` | `UICTRL_WND_SEM_ID` |

</details>

<details><summary><code>UIDisplay</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8019d480` | `UIDisplay_Init` |

</details>

<details><summary><code>UIFlowWndMovie</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x801b77f4` | `UIFlowWndMovie_OnKeyMode` |
| `0x801b7ba8` | `UIFlowWndMovie_SOS` |
| `0x801b8940` | `UIFlowWndMovie_OnEMRCompleted` |
| `0x801b89c4` | `UIFlowWndMovie_OnLoopRecFull` |

</details>

<details><summary><code>UIFlowWndWaitMoment</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801b290c` | `UIFlowWndWaitMoment_OnBackgroundDone` |

</details>

<details><summary><code>UIFlowWndWiFiMovie</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x801c06dc` | `UIFlowWndWiFiMovie_OnMovieWrError` |
| `0x801c08d4` | `UIFlowWndWiFiMovie_OnStorageSlow` |
| `0x801c093c` | `UIFlowWndWiFiMovie_OnMovieFull` |

</details>

<details><summary><code>UIMenuWndMSG</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801b27b4` | `UIMenuWndMSG_OnBackgroundDone` |

</details>

<details><summary><code>UIMenuWndWiFiMobileLinkOK</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x801b0e04` | `UIMenuWndWiFiMobileLinkOK_OnBackgroundDone` |
| `0x801b15ac` | `UIMenuWndWiFiMobileLinkOK_OnExeModeChange` |

</details>

<details><summary><code>UIMenuWndWiFiModuleLinkOK</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x801b0358` | `UIMenuWndWiFiModuleLinkOK_OnKeyShutter2_2` |
| `0x801b048c` | `UIMenuWndWiFiModuleLinkOK_OnKeyShutter2_1` |
| `0x801b0580` | `UIMenuWndWiFiModuleLinkOK_OnKeyShutter2` |

</details>

<details><summary><code>UIMenuWndWiFiWait</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801af4e4` | `UIMenuWndWiFiWait_OnBackgroundDone` |

</details>

<details><summary><code>UINet</code> (15)</summary>

| 주소 | 이름 |
|---|---|
| `0x801c7be4` | `UINet_FsIpc_Exit` |
| `0x801c7cb4` | `UINet_FsIpc_Init` |
| `0x801c8304` | `UINet_P2PConnect` |
| `0x801c83b8` | `UINet_P2PScan` |
| `0x801c8580` | `UINet_SiteSurvey` |
| `0x801c8e34` | `UINet_DumpAllSSID` |
| `0x801c8fcc` | `UINet_WifiSettings` |
| `0x801c9320` | `UINet_SetPASSPHRASE` |
| `0x801c93d8` | `UINet_SetSSID` |
| `0x801c95dc` | `UINet_DHCP_Start` |
| `0x801c9760` | `UINet_WifiInit` |
| `0x801c9e8c` | `UINet_StationStatus_CB` |
| `0x801ca168` | `UINet_AddACLTable` |
| `0x801ca3a8` | `UINet_AppIpc_UnInit` |
| `0x801ca474` | `UINet_AppIpc_Init` |

</details>

<details><summary><code>UIPlay</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x801d747c` | `xUIPlay_FList_DCF_DelAll` |
| `0x801d747c` | `xUIPlay_FList_FDB_DelFile` |
| `0x801d7a08` | `xUIPlay_FList_FDB_ProtectFile` |

</details>

<details><summary><code>UIStorageCheck</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801d614c` | `UIStorageCheck_DCIMWritable` |

</details>

<details><summary><code>usb</code> (19)</summary>

| 주소 | 이름 |
|---|---|
| `0x800b351c` | `usb_setConfig` |
| `0x800b3714` | `usb_close` |
| `0x800b3df0` | `usb_chkCharger` |
| `0x800b4198` | `usb_open` |
| `0x800b4198` | `usb_openInternal` |
| `0x800b63ac` | `usb_getEPByteCount` |
| `0x800b64c8` | `usb_unmaskEPINT` |
| `0x800b65fc` | `usb_maskEPINT` |
| `0x800b6730` | `usb_chkEPBusy` |
| `0x800b68fc` | `usb_clrEPFIFO` |
| `0x800b6ab0` | `usb_FIFO_EPxCfg` |
| `0x800b6ab0` | `usb_configUvcHeader` |
| `0x800b7b30` | `usb_setEpConfig` |
| `0x800b7f78` | `usb_abortDMA` |
| `0x800b82ac` | `usb_abortEndpoint` |
| `0x800b837c` | `usb_waitEPDone` |
| `0x800b8628` | `usb_setEPWrite` |
| `0x800b8b5c` | `usb_setEPRead` |
| `0x800b94cc` | `usb_ISR_OBSELETE` |

</details>

<details><summary><code>USB</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800b6ab0` | `USB_setFIFOCfg` |

</details>

<details><summary><code>usbhost</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800b9b64` | `usbhost_inthd` |

</details>

<details><summary><code>User</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800ce628` | `User_GetTempBuffer` |

</details>

<details><summary><code>USEREXIT</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x800024ec` | `USEREXIT_FLG_ID` |

</details>

<details><summary><code>USOCKIPC</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80005894` | `USOCKIPC_FLG_ID` |
| `0x80005894` | `USOCKIPC_SEM_ID` |

</details>

<details><summary><code>UsockIpc</code> (14)</summary>

| 주소 | 이름 |
|---|---|
| `0x802bf8d4` | `UsockIpc_CmdId_Udp_Receive` |
| `0x802bf968` | `UsockIpc_CmdId_Udp_Notify` |
| `0x802bf9f8` | `UsockIpc_getSndAddr` |
| `0x802bfa68` | `UsockIpc_CmdId_Receive` |
| `0x802bfafc` | `UsockIpc_CmdId_Notify` |
| `0x802bfc50` | `UsockIpc_Send` |
| `0x802bfe24` | `UsockIpc_Close` |
| `0x802bff0c` | `UsockIpc_Open` |
| `0x802c0260` | `UsockIpc_Msg_SendCmd` |
| `0x802c0318` | `UsockIpc_Msg_AckCmd` |
| `0x802c03b0` | `UsockIpc_Msg_SysCallReq` |
| `0x802c044c` | `UsockIpc_Msg_WaitCmd` |
| `0x802c04a8` | `UsockIpc_Msg_Uninit` |
| `0x802c0510` | `UsockIpc_Msg_Init` |

</details>

<details><summary><code>Uvac</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x801dad4c` | `xUvac_SetMFKRecParam` |
| `0x801db684` | `xUvac_ConfigMovieSizeCB` |
| `0x801db9b0` | `xUvac_Movie_RecordCB` |

</details>

<details><summary><code>UVAC</code> (16)</summary>

| 주소 | 이름 |
|---|---|
| `0x802b8d14` | `UVAC_SetEachStrmInfo` |
| `0x802b96a4` | `UVAC_Close` |
| `0x802b9814` | `UVAC_Stop` |
| `0x802b9b54` | `UVAC_Open` |
| `0x802ba5c8` | `UVAC_SetConfig` |
| `0x802ba854` | `UVAC_ConfigVidReso` |
| `0x802bba64` | `UVAC_MakeFrmDesc` |
| `0x802bbedc` | `UVAC_MakeStrmIntfDesc` |
| `0x802bbf8c` | `UVAC_MakeAudTypeFmtDesc` |
| `0x802bc12c` | `UVAC_MakeVidConfigDesc` |
| `0x802bc85c` | `UVAC_MakeClsSpecAudStrmIntfDesc` |
| `0x802bc85c` | `UVAC_MakeHSConfigDesc` |
| `0x802bc85c` | `UVAC_MakeStandIntrfDesc` |
| `0x802bd268` | `UVAC_GetTxfQueIdx` |
| `0x802bd97c` | `UVAC_AddIsoInTxfInfo` |
| `0x802bd97c` | `UVAC_GetFreeTxfInfo` |

</details>

<details><summary><code>UVACExe</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801db2d0` | `UVACExe_OnOpen` |

</details>

<details><summary><code>UVC</code> (13)</summary>

| 주소 | 이름 |
|---|---|
| `0x802b9080` | `UVC_TimeTrigSet` |
| `0x802b9548` | `UVC_TimeTrigClose` |
| `0x802bdf28` | `UVC_WinUSB_ClassReq` |
| `0x802be01c` | `UVC_TrigStilImg` |
| `0x802be254` | `UVC_AC_ProbeCommit_SetCur` |
| `0x802be37c` | `UVC_AC_CommitCtrl` |
| `0x802be37c` | `UVC_AC_ProbeCtrl` |
| `0x802be37c` | `UVC_SU_SelectCtrl` |
| `0x802be37c` | `UVC_VS_CommitCtrl` |
| `0x802be37c` | `UVC_VS_ProbeCtrl` |
| `0x802be37c` | `UVC_VS_Still_CommitCtrl` |
| `0x802be37c` | `UVC_VS_Still_ImgTrigCtrl` |
| `0x802be37c` | `UVC_VS_Still_ProbeCtrl` |

</details>

<details><summary><code>UVCIsoIn</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x802b8f6c` | `UVCIsoIn_ConcateH264Header` |
| `0x802b939c` | `UVCIsoIn_MakeIsoPayloadTxfData` |

</details>

<details><summary><code>Ux</code> (23)</summary>

| 주소 | 이름 |
|---|---|
| `0x800e8184` | `Ux_WaitEvent` |
| `0x800e82c0` | `Ux_PostEvent` |
| `0x80238bf8` | `Ux_GetFocusedWindowWithIndex` |
| `0x80238ce8` | `Ux_GetWindowByIndex` |
| `0x80238dd4` | `Ux_CloseWindowInternal` |
| `0x802390fc` | `Ux_CloseWindow` |
| `0x802392f0` | `Ux_OpenWindowInternal` |
| `0x802393fc` | `Ux_OpenWindow` |
| `0x80239d70` | `Ux_Redraw` |
| `0x8023a53c` | `Ux_WndDispatchMessage` |
| `0x8023a7e4` | `Ux_DrawShowEllipseProperty` |
| `0x8023a7e4` | `Ux_DrawShowImageProperty` |
| `0x8023a7e4` | `Ux_DrawShowLineProperty` |
| `0x8023a7e4` | `Ux_DrawShowRectProperty` |
| `0x8023a7e4` | `Ux_DrawShowRoundRectProperty` |
| `0x8023a7e4` | `Ux_DrawShowTextProperty` |
| `0x8023a7e4` | `Ux_SetShowObjProperty` |
| `0x8023a970` | `Ux_GetFontTable` |
| `0x8023b0c4` | `Ux_DrawShowObj` |
| `0x802408c8` | `Ux_GetBaseType` |
| `0x802409bc` | `Ux_DefaultEvent` |
| `0x80240b0c` | `Ux_SendEventInternal` |
| `0x80240c2c` | `Ux_SendEvent` |

</details>

<details><summary><code>UxButton</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8023b524` | `UxButton_GetItemData` |
| `0x8023b638` | `UxButton_SetItemData` |

</details>

<details><summary><code>UxList</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x8023bcf4` | `UxList_GetData` |
| `0x8023bddc` | `UxList_GetRange` |
| `0x8023c1c0` | `UxList_OnDraw` |

</details>

<details><summary><code>UxMenu</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x8023cc3c` | `UxMenu_GetData` |
| `0x8023cd10` | `UxMenu_GetItemData` |
| `0x8023ce48` | `UxMenu_GetRange` |
| `0x8023d280` | `UxMenu_SetData` |
| `0x8023d3a0` | `UxMenu_SetItemData` |
| `0x8023d7a0` | `UxMenu_OnDraw` |

</details>

<details><summary><code>UxProgressBar</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x8023dd8c` | `UxProgressBar_GetData` |
| `0x8023dff0` | `UxProgressBar_OnDraw` |
| `0x8023e460` | `UxProgressBar_SetData` |

</details>

<details><summary><code>UxScrollBar</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8023e658` | `UxScrollBar_GetData` |
| `0x8023ee9c` | `UxScrollBar_SetData` |

</details>

<details><summary><code>UxSlider</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x8023f194` | `UxSlider_GetData` |
| `0x8023f248` | `UxSlider_OnDraw` |
| `0x8023f648` | `UxSlider_SetData` |

</details>

<details><summary><code>UxState</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8023fd08` | `UxState_GetData` |
| `0x8023fde0` | `UxState_SetData` |

</details>

<details><summary><code>UxStateGraph</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8023f978` | `UxStateGraph_GetData` |
| `0x8023fa2c` | `UxStateGraph_SetData` |

</details>

<details><summary><code>UxStatic</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x802400d8` | `UxStatic_SetData` |

</details>

<details><summary><code>UxTab</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x802404c4` | `UxTab_GetData` |
| `0x8024059c` | `UxTab_SetData` |

</details>

<details><summary><code>version</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80260ab0` | `version_info_end` |

</details>

<details><summary><code>VidStrm</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x8025cf54` | `VidStrm_GetInfo` |
| `0x8025db34` | `VidStrm_SetReadyBufWithID` |
| `0x8025e488` | `VidStrm_Stop` |
| `0x8025e9b8` | `VidStrm_ChangeParam` |
| `0x8025f0ec` | `VidStrm_AddOne` |
| `0x8025f5dc` | `VidStrm_CloseALLForMedia` |

</details>

<details><summary><code>VidStrmEnc</code> (6)</summary>

| 주소 | 이름 |
|---|---|
| `0x80241368` | `VidStrmEnc_InitParam` |
| `0x8024174c` | `VidStrmEnc_GetYuvFromQueue` |
| `0x8024184c` | `VidStrmEnc_AddYuvToQueue` |
| `0x80241954` | `VidStrmEnc_HowManyinQ` |
| `0x80241cec` | `VidStrmEnc_Trig_IME` |
| `0x802422f8` | `VidStrmEnc_Trig_D2D` |

</details>

<details><summary><code>VidStrmMain</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x8025c82c` | `VidStrmMain_SetSetting` |
| `0x8025d540` | `VidStrmMain_SetCtrlObj_Mem` |
| `0x8025dd90` | `VidStrmMain_RecordStart` |

</details>

<details><summary><code>VidStrmMulti</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8025e5bc` | `VidStrmMulti_SetYUVSrc` |

</details>

<details><summary><code>VidStrmUti</code> (4)</summary>

| 주소 | 이름 |
|---|---|
| `0x8025bdc8` | `VidStrmUti_SetEncodeParam` |
| `0x8025c218` | `VidStrmUti_GetMAX_BytesPerSecond` |
| `0x8025cd18` | `VidStrmUti_EncTriggerTimerSet` |
| `0x8025dd04` | `VidStrmUti_GetActAddr` |

</details>

<details><summary><code>VSFakeMedia</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x8025bb44` | `VSFakeMedia_GetParam` |
| `0x8025d640` | `VSFakeMedia_ReAllocBuf2VA` |
| `0x8025f3c4` | `VSFakeMedia_Record` |
| `0x8025fb98` | `VSFakeMedia_Close` |
| `0x8025fc6c` | `VSFakeMedia_Open` |

</details>

<details><summary><code>VSMedaiRecAud</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80256b34` | `VSMedaiRecAud_GetFsDiskInfo` |

</details>

<details><summary><code>VSMediaBSQ</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x8024b660` | `VSMediaBSQ_DoMdatAction` |
| `0x8024cdb4` | `VSMediaBSQ_CheckCardfull` |

</details>

<details><summary><code>VSMediaRec</code> (20)</summary>

| 주소 | 이름 |
|---|---|
| `0x80247518` | `VSMediaRec_SetGPSData` |
| `0x80247d24` | `VSMediaRec_Clean4Recording` |
| `0x8024c568` | `VSMediaRec_StartWrite` |
| `0x8024c668` | `VSMediaRec_StopLoopEMR` |
| `0x8024c75c` | `VSMediaRec_StopFlash` |
| `0x8024e9a8` | `VSMediaRec_SetMaxStopFlashSec` |
| `0x8024ea0c` | `VSMediaRec_GetParam` |
| `0x8024ed80` | `VSMediaRec_SetUserData` |
| `0x8024ef30` | `VSMediaRec_SetEmergencyRecording` |
| `0x8024f460` | `VSMediaRec_CheckUnsavedFileBlocks` |
| `0x8024faa8` | `VSMediaRec_GetInfo` |
| `0x80252358` | `VSMediaRec_ReAllocBuf2VA` |
| `0x80252938` | `VSMediaRec_ChangeParameter` |
| `0x80253130` | `VSMediaRec_SetExtendCrash` |
| `0x80254708` | `VSMediaRec_Disk2SecondWithType` |
| `0x80254a70` | `VSMediaRec_AddOne` |
| `0x80254c6c` | `VSMediaRec_Record` |
| `0x80255448` | `VSMediaRec_Stop` |
| `0x802556f8` | `VSMediaRec_Close` |
| `0x80255854` | `VSMediaRec_Open` |

</details>

<details><summary><code>VSMediaRecAud</code> (7)</summary>

| 주소 | 이름 |
|---|---|
| `0x80255e9c` | `VSMediaRecAud_SetEncParam` |
| `0x80256398` | `VSMediaRecAud_GetBufSize` |
| `0x8025654c` | `VSMediaRecAud_EncodeAAC` |
| `0x80257378` | `VSMediaRecAud_TriggerTimerSet` |
| `0x802575c8` | `VSMediaRecAud_EventISR` |
| `0x80257938` | `VSMediaRecAud_DeviceOpen` |
| `0x80257f60` | `VSMediaRecAud_ReadFixDataToBuf` |

</details>

<details><summary><code>VSMediaRecFS</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x802476e0` | `VSMediaRecFS_DeleteOld` |
| `0x802476e0` | `VSMediaRecFS_DeleteRO` |

</details>

<details><summary><code>VSMediaRecFSUti</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80246098` | `VSMediaRecFSUti_ChangePathtoCrash` |

</details>

<details><summary><code>VSMediaRecMdat</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80249254` | `VSMediaRecMdat_ConfigureObj` |

</details>

<details><summary><code>VSMediaRecQ</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x802436e8` | `VSMediaRecQ_GetSavefileQueue` |
| `0x80243b70` | `VSMediaRecQ_AddSavefileQueue` |
| `0x80243b70` | `VSMediaRecQ_GetUnWriteLastVideoAddr` |

</details>

<details><summary><code>VSMediaRecUti</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8024fe1c` | `VSMediaRecUti_GetBytePerSec` |

</details>

<details><summary><code>VSMediaRecVid</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x8025c4dc` | `VSMediaRecVid_SetTimeLapseTime` |

</details>

<details><summary><code>VSMR</code> (8)</summary>

| 주소 | 이름 |
|---|---|
| `0x80244894` | `VSMR_FSObj_DoAction` |
| `0x80244ef8` | `VSMR_FSObj_SetInfo` |
| `0x802451fc` | `VSMR_FSObj_PadNidx2MdatbyFskID` |
| `0x802454f8` | `VSMR_FSObj_MakeNidx2Mdat` |
| `0x802457a0` | `VSMR_FSObj_MakeGPS2Mdat` |
| `0x8024d8b8` | `VSMR_MakerObj_GetInfo` |
| `0x8024d94c` | `VSMR_MakerObj_SetInfo` |
| `0x8024de84` | `VSMR_MakerObj_Create` |

</details>

<details><summary><code>VSMRawEnc</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x80258d88` | `VSMRawEnc_ScaleRaw2JpgSize` |
| `0x80259e04` | `VSMRawEnc_CheckErrorBeforeEnc` |
| `0x8025a0d0` | `VSMRawEnc_Open` |

</details>

<details><summary><code>VSMRawEncUti</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x80258c38` | `VSMRawEncUti_GetReadyRaw` |
| `0x802590ec` | `VSMRawEncUti_ScaleRaw` |

</details>

<details><summary><code>VSMRec</code> (8)</summary>

| 주소 | 이름 |
|---|---|
| `0x80245dd4` | `VSMRec_FSUti_DeleteFileByPath` |
| `0x802470e8` | `VSMRec_FSUti_CreateFile` |
| `0x80247404` | `VSMRec_FSUti_ReadWriteConti` |
| `0x8024d5b4` | `VSMRec_OverUti_SetInfo` |
| `0x8024d650` | `VSMRec_OverUti_GetInfo` |
| `0x8024d7a4` | `VSMRec_MakerObj_UpdateHeader` |
| `0x8024da3c` | `VSMRec_MakerObj_MakeHeader` |
| `0x8024de84` | `VSMRec_MakerObjUti_InitMov` |

</details>

<details><summary><code>VSWA</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80257210` | `VSWA_TriggerTimerSet4AudFilter` |

</details>

<details><summary><code>vx1</code> (14)</summary>

| 주소 | 이름 |
|---|---|
| `0x8005d6c8` | `vx1_writeSblM` |
| `0x8005d820` | `vx1_writeSblS` |
| `0x8005d914` | `vx1_writeML` |
| `0x8005da40` | `vx1_readSblM` |
| `0x8005dc00` | `vx1_readSblS` |
| `0x8005df3c` | `vx1_dumpSublinkSlave` |
| `0x8005e098` | `vx1_dumpSublinkMaster` |
| `0x8005e3c0` | `vx1_readML` |
| `0x8005e550` | `vx1_dumpMainlink` |
| `0x8005e6e0` | `vx1_getConfig` |
| `0x8005e890` | `vx1_setConfig` |
| `0x8005eb54` | `vx1_openSublink` |
| `0x8005eca4` | `vx1_powerdown` |
| `0x8005ede4` | `vx1_open` |

</details>

<details><summary><code>wait</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801b9784` | `wait_finish` |

</details>

<details><summary><code>wdt</code> (3)</summary>

| 주소 | 이름 |
|---|---|
| `0x800b2b28` | `wdt_disable` |
| `0x800b2bb0` | `wdt_enable` |
| `0x800b2c3c` | `wdt_setConfig` |

</details>

<details><summary><code>WifiApp</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x801cdf40` | `WifiApp_SendCmd` |

</details>

<details><summary><code>WIFICMD</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80005a84` | `WIFICMD_SEM_ID` |

</details>

<details><summary><code>WifiCmd</code> (5)</summary>

| 주소 | 이름 |
|---|---|
| `0x801cb974` | `WifiCmd_getQueryData` |
| `0x802c8594` | `WifiCmd_ReceiveCmd` |
| `0x802c8718` | `WifiCmd_DispatchCmd` |
| `0x802c894c` | `WifiCmd_PutData` |
| `0x802c8bd8` | `WifiCmd_GetData` |

</details>

<details><summary><code>WIFIIPC</code> (2)</summary>

| 주소 | 이름 |
|---|---|
| `0x800059b8` | `WIFIIPC_FLG_ID` |
| `0x800059b8` | `WIFIIPC_SEM_ID` |

</details>

<details><summary><code>WiFiIpc</code> (16)</summary>

| 주소 | 이름 |
|---|---|
| `0x802c69fc` | `WiFiIpc_getSndAddr` |
| `0x802c6a68` | `WiFiIpc_getRcvAddr` |
| `0x802c6ad4` | `WiFiIpc_CmdId_P2PCB` |
| `0x802c6b34` | `WiFiIpc_CmdId_WSC_FlashCB` |
| `0x802c6b90` | `WiFiIpc_CmdId_WSCCB` |
| `0x802c6bf0` | `WiFiIpc_CmdId_LinkCB` |
| `0x802c6c50` | `WiFiIpc_CmdId_StaCB` |
| `0x802c7a44` | `WiFiIpc_RunSystemCmd` |
| `0x802c7bd8` | `WiFiIpc_Close` |
| `0x802c7cc0` | `WiFiIpc_Open` |
| `0x802c7fe0` | `WiFiIpc_Msg_SendCmd` |
| `0x802c8098` | `WiFiIpc_Msg_AckCmd` |
| `0x802c8108` | `WiFiIpc_Msg_SysCallReq` |
| `0x802c81a4` | `WiFiIpc_Msg_WaitCmd` |
| `0x802c8200` | `WiFiIpc_Msg_Uninit` |
| `0x802c8268` | `WiFiIpc_Msg_Init` |

</details>

<details><summary><code>WIFISTR</code> (1)</summary>

| 주소 | 이름 |
|---|---|
| `0x80005a84` | `WIFISTR_SEM_ID` |

</details>

<details><summary><code>XML</code> (17)</summary>

| 주소 | 이름 |
|---|---|
| `0x801ca930` | `XML_GetHW_check_2` |
| `0x801cab1c` | `XML_QueryCmd_CurSts` |
| `0x801cafb0` | `XML_VdoReadCB` |
| `0x801cb0a0` | `XML_UploadFile` |
| `0x801cb478` | `XML_MakeJpgFromIFrame` |
| `0x801cba7c` | `XML_ValueResult` |
| `0x801cbdf4` | `XML_GetDiskFreeSpace` |
| `0x801cc134` | `XML_StringResult_2` |
| `0x801cc264` | `XML_GetVersion` |
| `0x801cc384` | `XML_StringResult` |
| `0x801cc5bc` | `XML_DefaultFormat` |
| `0x801cc6bc` | `XML_DeleteAllPicture` |
| `0x801cc8ac` | `XML_DeleteOnePicture` |
| `0x801ccd20` | `XML_GetScreen` |
| `0x801cd2fc` | `XML_GetThumbnail` |
| `0x801cd960` | `XML_FileList` |
| `0x801cdc34` | `XML_QueryCmd` |

</details>

