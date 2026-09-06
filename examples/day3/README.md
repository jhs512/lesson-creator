# DNS 교안 예제

원본 Notion의 인증 정보·페이지 ID·업로드 ID를 제거하고 로컬 그림을 참조하는 예제다. [Day3 개요](overview.md)에서 교시 순서를 확인한다.

| 파일 | 수업 역할 | 주제 |
| --- | --- | --- |
| `lesson1.json` | 개념 설명 | 이름·IP·DNS, 주소창에서 웹 서버까지의 통신과 라우터 경유 |
| `lesson2.json` | 개념 설명 | 네임서버의 역할·이름 계층·위임·조회 주체 |
| `lesson3.json` | 개념 설명 | 레코드·캐시·TTL·응답과 로그 판단 |
| `lesson4.json` | 따라 하는 실습 | 정상 내부망의 DNS·웹 통신 구성 |
| `lesson5.json` | 따라 하는 실습 | 응답 주소 변경·후속 접속 추적·복구 |
| `lesson6.json` | 종합실습 | 정상 기준·두 장애 조건·실제 관찰·복구 보고서 |

1–3교시는 특정 실습 장비의 예고보다 일반 네트워크 개념을 자세히 설명한다. 새 개념 그림 8개는 인터넷 구름·라우터·서버 기호로 원리를 보여 준다. 4–5교시의 기존 그림은 설명용 구성도다. 실제 Packet Tracer 캡처는 사용자 요청에 따라 PC 사용 가능 시점까지 보류했고 [촬영 계획](../../docs/packet-tracer-capture-plan.md)에 위치와 확인값을 남겼다.

본문에 표시하는 그림은 15개다. `assets/`에는 새 개념 그림 8쌍과 이전 원본 19쌍, 총 PNG·SVG 27쌍이 있다. 이전 그림은 보관하지만 개념 교시의 본문에서는 새 그림을 사용한다.

저장소 루트에서 `python tools/check_examples.py`를 실행하면 `build/day3/`에 Markdown·HTML 미리보기가 생긴다. 생성 명령은 [그림 안내](../../docs/diagrams.md), 검수 범위는 [검수 기록](../../docs/validation.md)에 있다.

Packet Tracer 프로그램과 `.pkt` 파일은 포함하지 않는다. 학생이 정상 구성을 `day03_dns_normal.pkt`, 비교 후 정상 복구 상태를 `day03_dns_response_comparison.pkt`로 저장한다. 종합실습 결과는 `day03_dns_integrated.pkt`와 `day03_dns_report.md`, 직접 캡처한 근거 이미지다. 시작 파일이 없으면 현재 교안의 선택 준비 절차에서 정상망과 비교 서버를 모두 만들 수 있다.
