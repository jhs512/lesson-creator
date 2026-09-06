# 4–5교시 Packet Tracer 실측 촬영 계획

상태: 사용자 요청으로 PC 사용 가능 시점까지 보류. 개념 그림·전체 교안 작성 다음 단계에서 촬영한다. 현재 본문 그림은 설정과 동작을 설명하는 구성도이며 실제 캡처가 아니다.

실행 환경의 Packet Tracer 버전과 시작 파일을 먼저 기록한다. 실제 화면을 캡처하고, 각 관찰의 파일·조건·값을 함께 남긴다. UI 이름이나 동작이 교안과 다르면 실제 실행 결과에 맞춰 교안을 수정한다.

| 교시·삽입 위치 | 촬영 화면 | 함께 확인할 값 |
| --- | --- | --- |
| 4 · 장비 연결 직후 | 전체 Logical 토폴로지 | PC 네 대, Switch0 한 대, Router0 한 대, DNS·웹 서버 및 포트 연결 |
| 4 · VLAN·라우터 설정 직후 | Switch0·Router0 CLI | VLAN 10/20 포트 배정, G0/0·G0/1 주소와 up/up |
| 4 · DNS 설정 직후 | PC0 IP Configuration / DNSServer DNS | 질문할 DNS .53, A 값 .100, 게이트웨이 .1 구분 |
| 4 · 정상 확인 | nslookup / Web Browser | 응답 .100, 정상 포털 문구 |
| 5 · 정상 관찰 | DNS 응답 PDU / 후속 HTTP PDU | 응답 패킷 목적지는 PC0, 응답 속 A와 HTTP 목적지는 .100 |
| 5 · 변경 관찰 | A 레코드 설정 / 새 DNS·HTTP PDU / 브라우저 | .200으로 바뀐 A 값과 후속 목적지, 예상 밖 서버 문구 |
| 5 · 복구 확인 | 새 nslookup / 정상 브라우저 | A 복구 .100, 새 조회 .100, 정상 문구 |

정상 파일은 `day03_dns_normal.pkt`, 비교 결과는 정상으로 복구한 `day03_dns_response_comparison.pkt`로 보관한다. 이벤트 목록 초기화와 PC DNS 캐시 초기화를 구분하고, Simulation에서 Capture/Forward로 응답이 도착할 때까지 진행한다. `ipconfig /flushdns` 지원 여부와 대체 초기화 절차도 실제 버전에서 확인한다.

실측 이미지마다 `image_kind: screenshot`과 `capture.application`, `version`, `scenario`, `evidence`를 남긴다. PNG 원본과 해당 `.pkt` 상태를 대응시키고 본문 삽입 후 다시 확인한다. 관리 화면의 A 변경을 실제 DNS 스푸핑·캐시 포이즈닝 재현으로 표현하지 않는다.
