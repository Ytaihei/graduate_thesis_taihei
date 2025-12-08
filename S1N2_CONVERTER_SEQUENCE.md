# S1N2 Converter プロトコル変換シーケンス

## 概要

S1N2 Converter は、4G LTE eNB (S1AP) と 5G Core (NGAP) 間のプロトコル変換を行うゲートウェイです。sXGP (1.9GHz 帯 LTE) の eNB を 5G SA コアネットワーク (Open5GS) に接続することを可能にします。

### ネットワーク構成

```
┌─────────────┐     S1AP/SCTP      ┌──────────────┐     NGAP/SCTP      ┌─────────────┐
│   eNB       │◄──────────────────►│ S1N2         │◄──────────────────►│   AMF       │
│172.24.0.111 │     Port 36412     │ Converter    │     Port 38412     │172.24.0.12  │
│             │                    │ 172.24.0.30  │                    │             │
└─────────────┘                    └──────────────┘                    └─────────────┘
       │                                  │                                   │
       │         GTP-U/UDP               │          GTP-U/UDP               │
       │         Port 2152               │          Port 2152               │
       ▼                                  ▼                                   ▼
┌─────────────┐                    ┌──────────────┐                    ┌─────────────┐
│   eNB       │◄──────────────────►│ S1N2         │◄──────────────────►│   UPF       │
│(S1-U側)     │                    │ (GTP Proxy)  │                    │172.24.0.21  │
└─────────────┘                    └──────────────┘                    └─────────────┘
```

## 1. eNB 接続シーケンス (S1 Setup)

### フロー

```
eNB                      S1N2 Converter                    AMF
 │                              │                            │
 │  S1SetupRequest (S1AP)       │                            │
 │ ─────────────────────────────►                            │
 │  proc=17, Global-ENB-ID,     │                            │
 │  SupportedTAs, ENBname       │                            │
 │                              │                            │
 │                              │  NGSetupRequest (NGAP)     │
 │                              │ ───────────────────────────►
 │                              │  proc=21, Global-gNB-ID,   │
 │                              │  SupportedTAList, RANname  │
 │                              │                            │
 │                              │  NGSetupResponse (NGAP)    │
 │                              │ ◄───────────────────────────
 │                              │  AMF Name, Served GUAMIs,  │
 │                              │  PLMN Support List         │
 │                              │                            │
 │  S1SetupResponse (S1AP)      │                            │
 │ ◄─────────────────────────────                            │
 │  MME Name, ServedGUMMEIs,    │                            │
 │  RelativeMMECapacity         │                            │
```

### 変換内容

| S1AP パラメータ | NGAP パラメータ | 変換ロジック |
|----------------|----------------|--------------|
| Global-ENB-ID | Global-gNB-ID (NR-CGI) | PLMN保持、eNB-ID → NR Cell ID |
| SupportedTAs | SupportedTAList | TAC保持、Broadcast PLMNs追加 |
| ENBname | RANNodeName | 文字列コピー |
| PagingDRX | DefaultPagingDRX | 値マッピング |

## 2. UE アタッチシーケンス (Registration)

### フロー

```
UE        eNB                S1N2 Converter                AMF
 │         │                        │                        │
 │ RRC     │                        │                        │
 │ ────────►                        │                        │
 │         │                        │                        │
 │         │ InitialUEMessage(S1AP) │                        │
 │         │ ────────────────────────►                        │
 │         │ proc=12                │                        │
 │         │ NAS: Attach Request    │                        │
 │         │ (EPS Mobile Identity,  │                        │
 │         │  PDN Connectivity Req) │                        │
 │         │                        │                        │
 │         │                        │ InitialUEMessage(NGAP) │
 │         │                        │ ────────────────────────►
 │         │                        │ proc=15                │
 │         │                        │ NAS: Registration Req  │
 │         │                        │ (5G-GUTI/SUCI,         │
 │         │                        │  UE Security Cap)      │
 │         │                        │                        │
```

### NAS メッセージ変換 (4G → 5G)

| 4G EPS NAS | 5G NAS | 変換ロジック |
|------------|--------|--------------|
| Attach Request (0x41) | Registration Request (0x41) | メッセージタイプ保持 |
| IMSI (EPS Mobile Identity) | SUCI | IMSI → SUCI (NULL scheme) 変換 |
| UE Network Capability | UE Security Capability | IA/EA アルゴリズムマッピング |
| PDN Connectivity Request | UL NAS Transport (PDU Session Est. Req) | 別メッセージとして分離 |
| EPS Attach Type | 5GS Registration Type | Initial → Initial Registration |

## 3. 認証シーケンス

### フロー

```
UE        eNB                S1N2 Converter                AMF
 │         │                        │                        │
 │         │                        │ DL NASTransport(NGAP)  │
 │         │                        │ ◄────────────────────────
 │         │                        │ NAS: Auth Request      │
 │         │                        │ (RAND, AUTN, ngKSI)    │
 │         │                        │                        │
 │         │ DL NASTransport(S1AP)  │                        │
 │         │ ◄────────────────────────                        │
 │         │ proc=11                │                        │
 │         │ NAS: Auth Request      │                        │
 │         │ (RAND, AUTN, eKSI)     │                        │
 │         │                        │                        │
 │ Auth    │                        │                        │
 │ ◄────────                        │                        │
 │         │                        │                        │
 │ RES     │                        │                        │
 │ ────────►                        │                        │
 │         │                        │                        │
 │         │ UL NASTransport(S1AP)  │                        │
 │         │ ────────────────────────►                        │
 │         │ proc=13                │                        │
 │         │ NAS: Auth Response     │                        │
 │         │ (RES)                  │                        │
 │         │                        │                        │
 │         │                        │ UL NASTransport(NGAP)  │
 │         │                        │ ────────────────────────►
 │         │                        │ proc=46                │
 │         │                        │ NAS: Auth Response     │
 │         │                        │ (RES*)                 │
```

### 認証パラメータ変換

| 4G パラメータ | 5G パラメータ | 変換ロジック |
|--------------|--------------|--------------|
| RAND (16 bytes) | RAND (16 bytes) | そのままコピー |
| AUTN (16 bytes) | AUTN (16 bytes) | そのままコピー |
| eKSI (3 bits) | ngKSI (4 bits) | TSC=0 追加 |
| RES (4-16 bytes) | RES* (16 bytes) | HRES* 計算して拡張 |

## 4. セキュリティモードシーケンス

### フロー

```
UE        eNB                S1N2 Converter                AMF
 │         │                        │                        │
 │         │                        │ DL NASTransport(NGAP)  │
 │         │                        │ ◄────────────────────────
 │         │                        │ NAS: Security Mode Cmd │
 │         │                        │ (Selected NAS Security │
 │         │                        │  Algorithm, ngKSI)     │
 │         │                        │                        │
 │         │ DL NASTransport(S1AP)  │                        │
 │         │ ◄────────────────────────                        │
 │         │ NAS: Security Mode Cmd │                        │
 │         │ (Selected NAS Security │                        │
 │         │  Algorithm, eKSI)      │                        │
 │         │                        │                        │
 │ SMC     │                        │                        │
 │ ◄────────                        │                        │
 │         │                        │                        │
 │ SMC Cmp │                        │                        │
 │ ────────►                        │                        │
 │         │                        │                        │
 │         │ UL NASTransport(S1AP)  │                        │
 │         │ ────────────────────────►                        │
 │         │ NAS: Security Mode Cmp │                        │
 │         │ (IMEISV, NAS MAC)      │                        │
 │         │                        │                        │
 │         │                        │ UL NASTransport(NGAP)  │
 │         │                        │ ────────────────────────►
 │         │                        │ NAS: Security Mode Cmp │
 │         │                        │ (IMEISV)               │
```

### セキュリティアルゴリズムマッピング

| 4G アルゴリズム | 5G アルゴリズム |
|----------------|----------------|
| EEA0 (NULL) | NEA0 (NULL) |
| EEA1 (SNOW3G) | NEA1 (SNOW3G) |
| EEA2 (AES) | NEA2 (AES) |
| EIA0 (NULL) | NIA0 (NULL) |
| EIA1 (SNOW3G) | NIA1 (SNOW3G) |
| EIA2 (AES) | NIA2 (AES) |

## 5. Initial Context Setup シーケンス (PDU Session Establishment)

S1N2 Converter は、4G の Attach 手順と 5G の PDU Session Establishment 手順のタイミングの違いを吸収するため、独自のシーケンスを採用しています。

### 独自シーケンスの特徴
1. **Registration Accept のインターセプト**: AMF からの Registration Accept を受信した時点で、PDU セッション確立を待たずに eNB へ `InitialContextSetupRequest` (Attach Accept 相当) を送信します。
2. **Early S1AP Setup**: この際、S1N2 は自身の GTP Proxy TEID を eNB に通知し、S1-U ベアラを先行して確立させます。
3. **遅延 PDU Session Establishment**: Registration Complete 送信後に、キャッシュしておいた PDN Connectivity Request を元に `PDU Session Establishment Request` を AMF へ送信します。
4. **TEID 更新**: その後 AMF から PDU Session Resource Setup を受信したタイミングで、UPF の TEID を学習し、GTP Proxy のマッピングを更新します。

### フロー詳細

```
UE        eNB                S1N2 Converter                AMF/SMF/UPF
 │         │                        │                        │
 │         │                        │ DL NASTransport(NGAP)  │
 │         │                        │ ◄────────────────────────
 │         │                        │ NAS: Registration Acc  │
 │         │                        │                        │
 │         │ InitialContextSetup    │                        │
 │         │ Request (S1AP)         │                        │
 │         │ ◄────────────────────────                        │
 │         │ proc=9                 │                        │
 │         │ NAS: Attach Accept     │                        │
 │         │ E-RAB ToBeSetup List   │                        │
 │         │ (S1N2 Proxy TEID)      │                        │
 │         │                        │                        │
 │ Bearer  │                        │                        │
 │ Setup   │                        │                        │
 │ ◄────────                        │                        │
 │         │                        │                        │
 │         │ InitialContextSetup    │                        │
 │         │ Response (S1AP)        │                        │
 │         │ ────────────────────────►                        │
 │         │ proc=9                 │                        │
 │         │ E-RAB Setup List       │                        │
 │         │ (eNB TEID, IP)         │                        │
 │         │                        │                        │
 │         │ UplinkNASTransport     │                        │
 │         │ (S1AP)                 │                        │
 │         │ ────────────────────────►                        │
 │         │ NAS: Attach Complete   │                        │
 │         │                        │                        │
 │         │                        │ UplinkNASTransport     │
 │         │                        │ (NGAP)                 │
 │         │                        │ ────────────────────────►
 │         │                        │ NAS: Registration Cmp  │
 │         │                        │                        │
 │         │                        │ UplinkNASTransport     │
 │         │                        │ (NGAP)                 │
 │         │                        │ ────────────────────────►
 │         │                        │ NAS: PDU Session Est   │
 │         │                        │ Request                │
 │         │                        │                        │
 │         │                        │ InitialContextSetup    │
 │         │                        │ Request (NGAP)         │
 │         │                        │ ◄────────────────────────
 │         │                        │ proc=14                │
 │         │                        │ PDU Session Resource   │
 │         │                        │ Setup Request          │
 │         │                        │ (UPF TEID)             │
 │         │                        │                        │
 │         │                        │ InitialContextSetup    │
 │         │                        │ Response (NGAP)        │
 │         │                        │ ────────────────────────►
 │         │                        │ proc=14                │
 │         │                        │ PDU Session Resource   │
 │         │                        │ Setup Response List    │
```

### ベアラ/PDU セッション変換

| S1AP (E-RAB) | NGAP (PDU Session) | 変換ロジック |
|--------------|-------------------|--------------|
| E-RAB ID | PDU Session ID | ID マッピング (通常 5) |
| QCI | 5QI | QCI → 5QI マッピング |
| ARP | ARP | Priority Level 保持 |
| S1-U GTP TEID | N3 GTP TEID | **S1N2 Proxy TEID** (初期) → **UPF TEID** (更新) |
| S1-U Transport Layer Address | N3 Transport Layer Address | IP アドレス変換 |

## 6. GTP-U データプレーン

### TEID マッピング

```
eNB                    S1N2 Converter                    UPF
 │                            │                            │
 │  GTP-U (S1-U TEID)         │                            │
 │ ───────────────────────────►                            │
 │  Inner: UE IP packet       │                            │
 │                            │  GTP-U (N3 TEID)           │
 │                            │ ───────────────────────────►
 │                            │  Inner: UE IP packet       │
 │                            │                            │
 │                            │  GTP-U (N3 TEID)           │
 │                            │ ◄───────────────────────────
 │                            │  Inner: UE IP packet       │
 │  GTP-U (S1-U TEID)         │                            │
 │ ◄───────────────────────────                            │
 │  Inner: UE IP packet       │                            │
```

### TEID 管理

- **S1-U TEID**: eNB が生成し、S1AP InitialContextSetupResponse で通知
- **N3 TEID**: UPF が生成し、NGAP InitialContextSetupRequest の PDU Session Resource で通知
- **S1N2 Converter**: S1-U TEID ↔ N3 TEID のマッピングテーブルを管理

## 7. UE ID マッピング

### ID 対応関係

| S1AP ID | NGAP ID | 管理方法 |
|---------|---------|----------|
| ENB-UE-S1AP-ID | RAN-UE-NGAP-ID | 同一値を使用 |
| MME-UE-S1AP-ID | AMF-UE-NGAP-ID | Converter がマッピング管理 |
| IMSI | SUCI | NAS 変換時に変換 |
| GUTI | 5G-GUTI | NAS 変換時に変換 |

## 8. エラーハンドリング

### Security Mode Reject

UE が Security Mode Command を拒否した場合：
1. UE → eNB: Security Mode Reject (4G NAS)
2. eNB → S1N2: UplinkNASTransport (S1AP)
3. S1N2 → AMF: UplinkNASTransport (NGAP) + NAS: Security Mode Reject
4. AMF: 認証手順を再試行または UE コンテキスト解放

### UE Context Release

UE が切断された場合：
1. eNB → S1N2: UEContextReleaseRequest (S1AP)
2. S1N2 → AMF: UEContextReleaseRequest (NGAP)
3. AMF → S1N2: UEContextReleaseCommand (NGAP)
4. S1N2 → eNB: UEContextReleaseCommand (S1AP)
5. S1N2: TEID マッピングと UE コンテキストをクリーンアップ

## 9. pcap サンプル解析 (20251203_9.pcap)

### 成功シーケンス (Frame 3383-3726)

| Time (s) | Direction | Protocol | Message |
|----------|-----------|----------|---------|
| 86.927 | eNB→S1N2 | S1AP | InitialUEMessage (Attach Request) |
| 86.927 | S1N2→AMF | NGAP | InitialUEMessage (Registration Request) |
| 86.934 | AMF→S1N2 | NGAP | DownlinkNASTransport (Auth Request) |
| 86.934 | S1N2→eNB | S1AP | DownlinkNASTransport (Auth Request) |
| 87.012 | eNB→S1N2 | S1AP | UplinkNASTransport (Auth Response) |
| 87.012 | S1N2→AMF | NGAP | UplinkNASTransport (Auth Response) |
| 87.020 | AMF→S1N2 | NGAP | DownlinkNASTransport (Security Mode Cmd) |
| 87.020 | S1N2→eNB | S1AP | DownlinkNASTransport (Security Mode Cmd) |
| 87.052 | eNB→S1N2 | S1AP | UplinkNASTransport (Security Mode Complete) |
| 87.052 | S1N2→AMF | NGAP | UplinkNASTransport (Security Mode Complete + Reg Request) |
| 87.078 | AMF→S1N2 | NGAP | InitialContextSetupRequest |
| 87.078 | S1N2→eNB | S1AP | InitialContextSetupRequest |
| 87.372 | eNB→S1N2 | S1AP | InitialContextSetupResponse |
| 87.373 | eNB→S1N2 | S1AP | UplinkNASTransport (Attach Complete) |
| 87.373 | S1N2→AMF | NGAP | UplinkNASTransport (Registration Complete) |
| 87.396 | S1N2→AMF | NGAP | InitialContextSetupResponse |

### データ通信 (Frame 3860-)

| Time (s) | Direction | Protocol | Message |
|----------|-----------|----------|---------|
| 90.592 | eNB→S1N2 | GTP-U | Echo Request (ICMP to 8.8.8.8) |
| 90.592 | S1N2→UPF | GTP-U | Echo Request (TEID変換済み) |
| 90.597 | UPF→S1N2 | GTP-U | Echo Reply |
| 90.597 | S1N2→eNB | GTP-U | Echo Reply (TEID変換済み) |

## 10. 関連ソースコード

| ファイル | 機能 |
|---------|------|
| `src/s1n2_converter.c` | メイン変換ロジック |
| `src/s1n2_nas_converter.c` | NAS メッセージ変換 (4G↔5G) |
| `src/s1n2_gtp.c` | GTP-U プロキシ、TEID 管理 |
| `src/s1n2_auth.c` | 認証パラメータ変換 |
| `src/s1n2_security.c` | セキュリティコンテキスト管理 |
| `include/s1n2_converter.h` | 公開 API 定義 |

## 11. 主要な変換関数

```c
// S1AP → NGAP 変換
int s1n2_convert_s1setup_to_ngsetup(...)      // S1SetupRequest → NGSetupRequest
int s1n2_convert_initial_ue_message(...)      // InitialUEMessage 変換
int s1n2_convert_uplink_nas_transport(...)    // UplinkNASTransport 変換
int s1n2_convert_initial_context_setup_response(...)  // ICS Response 変換

// NGAP → S1AP 変換
int s1n2_convert_ngsetup_to_s1setup(...)      // NGSetupResponse → S1SetupResponse
int s1n2_convert_ngap_downlink_nas_transport(...)  // DownlinkNASTransport 変換

// NAS 変換
int convert_4g_nas_to_5g(...)                 // 4G EPS NAS → 5G NAS
int convert_5g_nas_to_4g(...)                 // 5G NAS → 4G EPS NAS

// メッセージハンドラ
int s1n2_handle_s1c_message(...)              // S1AP メッセージ受信処理
int s1n2_handle_n2_message(...)               // NGAP メッセージ受信処理
```

---

*Document generated: 2025-12-04*
*Based on pcap analysis: 20251203_9.pcap*
