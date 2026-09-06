"""Draw public-network DNS concepts, separate from Packet Tracer lab diagrams.

Uses original equipment primitives in build_network_diagrams. The pictures
are explanatory models, never captured packets or a specific site's topology.
"""
import argparse
from pathlib import Path
from build_network_diagrams import Canvas, BLUE, GREEN, RED, PURPLE, GREY, INK


def internet(d, x, y, w=420, h=240):
    curves=[((.18,.9),(-.03,.9),(-.06,.50),(.14,.45)),
            ((.14,.45),(.08,.22),(.28,.04),(.45,.20)),
            ((.45,.20),(.58,-.04),(.88,.10),(.86,.35)),
            ((.86,.35),(1.06,.35),(1.07,.77),(.88,.84)),
            ((.88,.84),(.77,.96),(.45,.90),(.18,.9))]
    points=[]
    for a,b,c,e in curves:
        for i in range(17):
            t=i/16
            points.append((x+w*((1-t)**3*a[0]+3*(1-t)**2*t*b[0]+3*(1-t)*t*t*c[0]+t**3*e[0]),
                           y+h*((1-t)**3*a[1]+3*(1-t)**2*t*b[1]+3*(1-t)*t*t*c[1]+t**3*e[1])))
    d.poly(points,'#e6f5fc','#8cbed1',2)
    d.text(x+w*.51,y+h*.52,'인터넷',31,BLUE,True)
    d.poly([(x+w*.50,y+h*.16),(x+w*.45,y+h*.31),(x+w*.52,y+h*.31),
            (x+w*.48,y+h*.41),(x+w*.59,y+h*.24),(x+w*.52,y+h*.24)], '#efb640', '#cf9a27', 1)


def arrow(d, points, label, x, y, color=BLUE, dash=False):
    d.line(points, color, 5, dash, True)
    d.label(x,y,label,color,27)


def network(d, y, right='DNS 서버', address='조회할 서버의 IP'):
    d.pc(175,y,'내 PC',s=1.0)
    d.router(470,y,'집·회사 라우터',.78)
    internet(d,730,y-130)
    d.server(1460,y,right,address,1.15)
    d.line([(260,y),(390,y)],GREY,3)
    d.line([(550,y),(620,y-27),(660,y+25),(715,y)],GREY,3)
    d.line([(1145,y),(1220,y-25),(1270,y+20),(1395,y)],GREY,3)


def create(out, font):
    def canvas(slug,title,sub,h=1020):
        return Canvas(slug,title,sub,h=h,out=out,font=font)

    d=canvas('concept_l1_dns','이름을 묻는 통신: DNS 질문과 응답','naver.com 접속의 개념도 · 주소를 아직 모르는 상황')
    network(d,370,'조회할 DNS 서버','주소 찾기를 부탁받는 곳')
    arrow(d,[(180,610),(1455,610)],'질문: naver.com에 연결할 IP 주소는?',510,556)
    d.envelope(440,590,BLUE,1.1)
    arrow(d,[(1455,745),(180,745)],'응답: 이름에 대응하는 IP 주소',540,690,GREEN)
    d.envelope(1200,725,GREEN,1.1)
    d.text(150,842,'질문 패킷의 목적지 = DNS 서버',30,BLUE)
    d.text(990,842,'응답 패킷의 목적지 = 내 PC',30,GREEN)
    d.footer('DNS로 주소를 알아낸 다음, 그 주소로 웹 통신을 시작한다.')
    d.save()

    d=canvas('concept_l1_web','주소를 받은 뒤: 웹 서버로 보내는 새 통신','DNS가 알려준 IP를 목적지로 사용한다 · HTTPS의 기본 예')
    network(d,365,'웹 서버','DNS에서 받은 IP 주소')
    d.rect(650,570,520,85,'#eff9f3',GREEN,14,2)
    d.text(910,593,'내 PC가 받은 주소로 목적지를 정한다',28,GREEN,True)
    arrow(d,[(180,725),(1455,725)],'연결·암호화 준비 뒤 HTTPS 요청',515,672,BLUE)
    arrow(d,[(1455,825),(180,825)],'웹페이지 응답',705,778,GREEN)
    d.footer('DNS 응답 안의 주소와 다음 웹 통신의 목적지를 연결하자. DNS 서버가 웹 내용을 중계하지 않는다.')
    d.save()

    d=canvas('concept_l1_route','라우터는 다음으로 전달할 곳을 고른다','멀리 있는 웹 서버의 IP와 바로 건넬 장비를 구분한다 · 경로 개념도')
    d.pc(160,350,'내 PC','출발지')
    d.router(565,350,'가까운 라우터',.85)
    d.router(1030,350,'중간 라우터',.85)
    d.server(1540,350,'웹 서버','최종 목적지',1.05)
    for a,b in [(260,450),(680,915),(1140,1435)]:
        arrow(d,[(a,350),(b,350)],'전달',a+35,298)
    d.text(565,525,'목적지 IP를 보고\n다음 연결을 선택',30,BLUE,True)
    d.text(1030,525,'자신의 경로 정보로\n다음 연결을 선택',30,BLUE,True)
    for x in (270,735,1240):
        d.rect(x,700,300,125,'#f0f7fd',BLUE,10,2)
        d.text(x+150,726,'IP 목적지',28,BLUE,True)
        d.text(x+150,770,'웹 서버 주소',29,INK,True)
    d.text(900,875,'이름은 DNS로 조회하고, 패킷 전달은 목적지 IP를 기준으로 진행한다.',31,INK,True)
    d.footer('중간 망은 생략했다. 주소 변환·터널 같은 추가 처리를 제외한 기본 라우팅 원리다.')
    d.save()

    d=canvas('concept_l2_tree','이름을 나누어 관리하는 계층','도메인 이름의 오른쪽에서 왼쪽으로 담당 범위를 좁힌다')
    d.server(880,250,'루트 .','이름 공간의 시작',.8)
    for x,name in [(380,'.com'),(1370,'.kr')]:
        d.line([(880,375),(880,410),(x,410),(x,460)],BLUE,3)
        d.server(x,525,name,'최상위 도메인',.85)
    for x,name in [(230,'naver.com'),(655,'example.com')]:
        d.line([(380,650),(380,690),(x,690),(x,735)],GREEN,3)
        d.server(x,800,name,'도메인',.8)
    d.text(1360,745,'관리 관계를 보여 주는 선이다.\n실제 패킷이 이 선을 따라\n차례로 전달된다는 뜻은 아니다.',31,GREY,True)
    d.footer('루트와 .com의 담당 서버는 다음 담당 서버를 안내한다. 웹 서버의 위치와는 다른 관리 구조다.')
    d.save()

    d=canvas('concept_l2_lookup','부탁받은 DNS 서버가 주소를 찾아온다','아직 저장된 주소나 담당자 안내가 없는 경우',h=1180)
    d.pc(170,580,'내 PC','naver.com 조회',.95)
    d.server(615,580,s=1.1)
    d.text(585,780,'부탁받은 DNS 서버',29,INK,True)
    d.text(585,825,'내 PC 대신 주소를 찾는다',26,GREY,True)
    for y,name,info in [(240,'루트 서버','.com 담당 서버 안내'),(580,'.com TLD 서버','naver.com 담당 서버 안내'),(930,'권한 네임서버','담당 이름의 원본 답')]:
        d.server(1500,y,name,info,.95)
    arrow(d,[(280,540),(550,540)],'1 질문',335,490)
    arrow(d,[(550,640),(280,640)],'8 최종 답',315,664,GREEN)
    for y,left,q,a in [(220,755,'2 naver.com 조회','3 .com 담당 서버 안내'),(560,800,'4 naver.com 조회','5 naver.com 담당 안내'),(900,755,'6 naver.com 조회','7 주소 응답')]:
        source_y=480 if y<500 else 580 if y<700 else 680
        arrow(d,[(700,source_y),(left,source_y),(left,y),(1405,y)],q,905,y-44,BLUE)
        arrow(d,[(1405,y+80),(left+45,y+80),(left+45,source_y+30),(700,source_y+30)],a,905,y+88,GREEN,True)
    d.footer('부탁받은 DNS 서버가 안내를 따라 다음 담당자에게 질문하고, 구한 주소를 내 PC에 돌려준다.')
    d.save()

    d=canvas('concept_l3_records','레코드는 이름에 붙여 둔 정보다','질문할 정보의 종류에 따라 답의 의미가 달라진다')
    d.server(880,440,'권한 네임서버','담당 이름의 레코드 보관',1.25)
    d.pc(270,295,'A · AAAA','IPv4 · IPv6 주소',.9)
    d.server(1470,295,'MX','메일 수신 서버 이름',.9)
    d.server(1470,785,'NS','담당 네임서버 이름',.9)
    d.rect(110,715,440,105,'#f0f7fd',BLUE,14,2)
    d.text(330,735,'CNAME',31,BLUE,True)
    d.text(330,780,'별명 → 다른 이름',29,INK,True)
    for points in [[(795,405),(425,295)],[(980,405),(1365,295)],[(980,515),(1365,755)],[(795,515),(550,755)]]:
        d.line(points,BLUE,4,arrow=True)
    d.footer('선은 레코드 값이 가리키는 대상을 나타낸다. DNS 서버가 웹·메일 내용을 가져오는 경로가 아니다.')
    d.save()

    d=canvas('concept_l3_cache','원본을 바꿔도 저장된 답은 잠시 남는다','10:00에 받은 답의 TTL은 300초 · 공인 주소를 사용한 가정 사례',h=1210)
    for y,t,cache,original in [(280,'10:00','104.16.132.229 · TTL 300','104.16.132.229'),(620,'10:02','104.16.132.229 · TTL 180','104.16.133.229'),(960,'10:05 이후 새 질문','104.16.133.229 · 새 TTL','104.16.133.229')]:
        d.text(70,y-70,t,30,BLUE)
        d.pc(280,y,'PC',s=.63)
        d.server(835,y,'재귀 리졸버','저장된 A: '+cache.replace(' · ', '\n'),.75)
        d.server(1480,y,'권한 서버','원본 A: '+original,.75)
        d.line([(385,y-20),(745,y-20)],BLUE,4,arrow=True)
        d.line([(745,y+45),(385,y+45)],GREEN,4,arrow=True)
        if y==620:
            d.line([(940,y),(1380,y)],GREY,3,True)
            d.label(1050,y-45,'원본 재조회 없음',GREY,27)
        else:
            d.line([(940,y-20),(1380,y-20)],BLUE,4,arrow=True)
            d.line([(1380,y+45),(940,y+45)],GREEN,4,arrow=True)
        if y<960:d.line([(65,y+190),(1725,y+190)],'#dce4eb',1)
    d.footer('TTL 만료는 다음 조회에서 새 답을 구할 계기다. 모든 PC에 새 주소를 동시에 보내는 기능은 아니다.')
    d.save()

    d=canvas('concept_l3_changed','답이 달라지면 다음 접속 대상도 달라질 수 있다','공인 주소를 사용한 가정 사례 · 변경이 정상인지 공격인지는 추가 근거로 판단한다',h=1060)
    for y,title,ip,color,server in [(340,'정상 기준','104.16.132.229',GREEN,'원래 웹 서버'),(740,'예상과 다른 응답','104.16.133.229',RED,'다른 웹 서버')]:
        d.text(65,y-155,title,33,color)
        d.pc(205,y,'PC',s=.78)
        internet(d,605,y-115,400,210)
        d.server(1490,y,server,ip,.95)
        arrow(d,[(315,y),(570,y)],'받은 주소로 접속',330,y-58,color)
        arrow(d,[(1020,y),(1395,y)],ip,1070,y-58,color)
    d.footer('정상 이전 · 원본 설정 오류 · 오래된 캐시 · 거짓 응답을 구분한다. 주소 변화만으로 공격을 확정하지 않는다.')
    d.save()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=Path('examples/day3/assets'))
    p.add_argument('--font',type=Path,required=True)
    a=p.parse_args();create(a.out,a.font)


if __name__=='__main__':main()
