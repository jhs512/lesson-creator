# DNS 개념 자료와 그림의 범위

확인일: 2026-09-06. 교안의 설명과 그림은 독자 수준에 맞게 새로 작성했다. 아래 외부 이미지를 교안의 원본으로 복제하지 않았다.

| 자료 | 참고한 범위 |
| --- | --- |
| [Cloudflare: DNS](https://www.cloudflare.com/learning/dns/what-is-dns/) | 이름 조회 역할과 질의·응답 흐름, 개념 그림의 표현 참고 |
| [Cloudflare: DNS 서버 종류](https://www.cloudflare.com/learning/dns/dns-server-types/) | 재귀 리졸버·루트·TLD·권한 서버의 역할 구분 |
| [Cisco: 네트워크 토폴로지 아이콘](https://www.cisco.com/c/en/us/about/brand-center/network-topology-icons.html) | 장비를 구분하는 시각 표현 참고. 이번 그림의 아이콘은 직접 그린 도형 |
| [RFC 1034](https://www.rfc-editor.org/info/rfc1034/) | 이름 계층, 분산 관리, 위임, 재귀·반복 질의 |
| [RFC 1035](https://www.rfc-editor.org/rfc/rfc1035.html) | 레코드 형식, 질문·응답 및 응답 코드 |
| [RFC 2308](https://www.rfc-editor.org/rfc/rfc2308.html) | 부정 응답의 캐시와 유효 시간 |
| [RFC 7505](https://www.rfc-editor.org/rfc/rfc7505.html) | Null MX와 메일 수신 의사 구분 |
| [RFC 4033](https://www.rfc-editor.org/rfc/rfc4033.html) | DNSSEC의 출처·무결성 검증과 적용 범위 |
| [RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html) | HTTP/3과 QUIC을 TCP 예시의 별도 보충으로 구분 |

`naver.com`은 접속 흐름을 설명하는 실제 이름의 예다. 그림은 네이버의 현재 IP, 실제 장비, 실제 측정 경로를 나타내지 않는다. `example.test` 및 192.0.2.0/24 등 예시용 이름과 주소는 수업의 관계를 설명하는 값이다. `portal.a-company.test`와 192.168.20.0/24는 별도로 구성하는 내부 실습 모델이다.

그림의 인터넷 구름은 여러 망과 중간 라우터의 생략 표시다. 번개·지그재그는 중간 연결을 줄인 기호이며 패킷이 특정 모양의 케이블을 따라 이동한다는 뜻이 아니다. DNS 조회는 이름 관리 계층의 서버에 질문하는 과정이고 웹 통신은 응답으로 받은 IP를 이용하는 별도 과정이다. 라우팅 그림에서는 주소 변환·터널 등 추가 처리를 생략했다.

개념 PNG 8개는 Nanum Gothic 글꼴로 렌더하고 검토했다. 글꼴 원본은 [Google Fonts의 Nanum Gothic](https://github.com/google/fonts/tree/main/ofl/nanumgothic)이다. 글꼴 자체는 저장소에 포함하지 않는다.
