# 네트워크 그림 만들기

`tools/build_network_diagrams.py`는 Day 3 DNS 교안의 구성도와 동작 흐름 19개를 만든다. PC·스위치·라우터·서버·연결선·패킷 봉투를 Python 도형으로 그리며, PNG와 편집 가능한 SVG를 함께 저장한다. AI 이미지 API나 Notion 계정이 필요하지 않다.

## 실행

저장소 루트에서 의존성을 설치한 뒤 실행한다.

```sh
python -m pip install -r requirements.txt
python tools/build_network_diagrams.py --out ./network-diagrams
```

각 그림의 `.png`와 `.svg` 19쌍, 그리고 전체 미리보기 `contact_sheet.png`가 지정한 폴더에 생긴다. 같은 폴더에 다시 실행하면 같은 이름의 결과를 갱신한다. 다른 파일은 삭제하지 않으며, 미리보기에는 이 예제의 19개 그림만 포함한다.

## 한글 폰트

macOS의 Apple SD Gothic Neo, Windows의 맑은 고딕, Linux의 일반적인 Noto CJK 설치 위치를 순서대로 확인한다. 설치 위치가 다르거나 다른 폰트를 쓰려면 한글을 지원하는 파일을 지정한다.

```sh
python tools/build_network_diagrams.py --out ./network-diagrams --font /path/to/NotoSansKR-Regular.ttf
```

폰트는 저장소에 포함하거나 자동으로 내려받지 않는다. 공유 가능한 한글 폰트를 따로 설치하고 해당 폰트의 사용 조건을 따른다. 폰트를 찾지 못하면 설치 파일 경로를 지정하라는 안내와 함께 중단한다.

SVG의 글꼴 이름은 실제로 불러온 폰트에서 읽는다. 필요한 경우 `--font-family "Noto Sans KR"`로 SVG 글꼴 이름만 지정할 수 있다. 이 옵션은 PNG에 쓰는 폰트를 바꾸지 않으므로 `--font`와 맞는 이름을 사용한다. SVG 글자는 윤곽선으로 변환하지 않기 때문에 열어 보는 컴퓨터에도 같은 폰트가 있어야 동일하게 보인다. PNG는 받는 사람에게 폰트가 없어도 동일하게 보인다.

기준 그림은 Apple SD Gothic Neo로 확인했다. 다른 폰트는 글자 폭과 높이가 달라질 수 있으므로 `contact_sheet.png`와 본 그림의 겹침·잘림·한글 표시를 확인한다. 가로 폭을 넘는 일부 문구는 생성 중 오류로 알리지만, 이것만으로 모든 배치를 검증하지는 않는다. 필요하면 해당 장면의 글자 크기나 좌표를 조정한다.

## 다른 교안에 응용하기

이 코드는 문장을 넣으면 임의의 그림을 만드는 범용 생성기가 아니다. 장비 이름·IP·포트·주소·설명은 Day 3 실습에 맞춰 정해져 있다. 다른 교안에는 장면 함수와 `topology()`의 값을 수정해 사용한다. `Canvas`의 `pc()`, `switch()`, `router()`, `server()`, `line()`, `envelope()`는 다른 구성도를 만들 때 재사용할 수 있다.

```python
from tools.build_network_diagrams import Canvas

diagram = Canvas(
    "simple-example", "PC와 서버", "논리적인 통신 관계를 보여 주는 예시",
    out="./network-diagrams", font="/path/to/NotoSansKR-Regular.ttf",
)
diagram.pc(350, 450, "PC0")
diagram.server(1350, 450, "WebServer")
diagram.line([(440, 430), (1270, 430)], arrow=True)
diagram.save()
```

모듈을 가져오는 것만으로 파일이나 폴더를 생성하지 않는다. `save()` 또는 실행 명령이 실제 결과를 저장한다. 생성 기능과 Notion에 이미지를 올리는 기능은 별개다.

## DNS 개념 그림

`tools/build_dns_concepts.py`는 1–3교시의 개념 그림 8개를 만든다. 인터넷 구름, 중간 연결, 라우터와 서버를 사용해 주소 조회·웹 통신·다음 전달 대상·이름 계층·조회 주체·레코드·캐시·응답 변화의 관계를 설명한다. 실제 서비스나 Packet Tracer의 측정 화면이 아니다.

```bash
python tools/build_dns_concepts.py --out examples/day3/assets --font /path/to/NanumGothic-Regular.ttf
```

이번 PNG는 Nanum Gothic으로 렌더했다. SVG를 다른 환경에서 같은 모양으로 보려면 같은 글꼴이 필요하다. 출처와 그림 범위는 [개념 자료 출처](concept-sources.md), 별도 실측의 준비 사항은 [촬영 계획](packet-tracer-capture-plan.md)을 참고한다.
