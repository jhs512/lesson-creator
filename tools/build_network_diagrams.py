"""Render the Day 3 DNS example as 19 PNG/SVG network textbook diagrams.

Canvas contains reusable equipment primitives; the scenes are a fixed lesson
example, not a natural-language or general-purpose topology generator.
"""
import argparse
from pathlib import Path
from html import escape
import math
import os
from PIL import Image, ImageDraw, ImageFont

# Defaults do not create directories or render files when the module is imported.
OUT=Path('network-diagrams')
FONT=None
FONT_FAMILY=None
FIGURE_SLUGS=(
    'overview', 'l1_lookup_web', 'l1_reply', 'l1_connect', 'l1_nslookup',
    'l2_hierarchy', 'l2_sequence', 'l3_records', 'l3_ttl', 'l3_cache_poison',
    'l4_route', 'l4_settings', 'l4_topology', 'l5_topology', 'l5_events',
    'l5_normal', 'l5_compare', 'l6_diagnose', 'l6_evidence',
)


def font_candidates():
    """Common locally installed Korean fonts; no download is performed."""
    windows=Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'
    return (
        Path('/System/Library/Fonts/AppleSDGothicNeo.ttc'),
        windows/'malgun.ttf',
        Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),
        Path('/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf'),
        Path('/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf'),
        Path('/Library/Fonts/NotoSansKR-Regular.ttf'),
        Path.home()/'.local/share/fonts/NotoSansKR-Regular.ttf',
    )


def resolve_font(requested=None):
    """Return a usable font path and its embedded family name."""
    candidates=(Path(requested).expanduser(),) if requested else font_candidates()
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            face=ImageFont.truetype(str(candidate), 24)
        except OSError:
            continue
        return candidate, face.getname()[0]
    if requested:
        raise ValueError(f'Cannot read font: {requested}. Supply a Korean TTF/OTF/TTC file with --font.')
    raise ValueError('No supported local Korean font was found. Install a Korean font such as Noto Sans KR and pass its file path with --font.')


INK='#1a2834';GREY='#697885';BLUE='#1573bb';GREEN='#008461';RED='#c63c39';PURPLE='#80569d';WIRE='#43515b'
class Canvas:
    def __init__(self,slug,title,subtitle='',h=1100,w=1800,*,out=None,font=None,font_family=None):
        self.slug,self.w,self.h=slug,w,h
        self.out=Path(out) if out is not None else OUT
        self.font,detected_family=resolve_font(font if font is not None else FONT)
        self.font_family=font_family or FONT_FAMILY or detected_family
        self.im=Image.new('RGB',(w*2,h*2),'white');self.d=ImageDraw.Draw(self.im)
        self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">','<rect width="100%" height="100%" fill="white"/>']
        self.text(50,28,title,40)
        if subtitle:self.text(52,83,subtitle,24,GREY)
        self.line([(50,129),(w-50,129)],'#b8c5cd',1)
    def text(self,x,y,s,size=27,color=INK,center=False):
        font=ImageFont.truetype(str(self.font),round(size*2))
        for i,line in enumerate(s.split('\n')):
            xx=x*2;yy=(y+i*size*1.36)*2;tw=self.d.textlength(line,font=font)
            if center:xx-=tw/2
            if xx<0 or xx+tw>self.w*2:
                raise ValueError(f'{self.slug}: text exceeds canvas width with this font: {line!r}. Adjust the layout or font size.')
            self.d.text((xx,yy),line,font=font,fill=color)
            self.svg.append(f'<text x="{xx/2:.2f}" y="{yy/2+size*.92:.2f}" font-family="{escape(self.font_family, quote=True)}, sans-serif" font-size="{size}" fill="{color}">{escape(line)}</text>')
    def rect(self,x,y,w,h,fill='white',stroke=INK,r=0,width=2,dash=False):
        if not dash:self.d.rounded_rectangle((x*2,y*2,(x+w)*2,(y+h)*2),radius=r*2,fill=fill,outline=stroke,width=width*2)
        else:
            self.d.rectangle((x*2,y*2,(x+w)*2,(y+h)*2),fill=fill)
            self.line([(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)],stroke,width,True)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"'+(' stroke-dasharray="10 7"' if dash else '')+'/>')
    def ellipse(self,x,y,w,h,fill,stroke=INK,width=2):
        self.d.ellipse((x*2,y*2,(x+w)*2,(y+h)*2),fill=fill,outline=stroke,width=width*2)
        self.svg.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    def poly(self,pts,fill,stroke=INK,width=2):
        self.d.polygon([(round(x*2),round(y*2)) for x,y in pts],fill=fill)
        self.d.line([(round(x*2),round(y*2)) for x,y in pts+[pts[0]]],fill=stroke,width=width*2,joint='curve')
        self.svg.append(f'<polygon points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    def line(self,pts,color=WIRE,width=3,dash=False,arrow=False):
        if dash:
            for a,b in zip(pts,pts[1:]):
                length=math.dist(a,b)
                if not length:continue
                for t in range(0,int(length),20):
                    e=min(t+12,length)
                    self.d.line([(2*(a[0]+(b[0]-a[0])*v/length),2*(a[1]+(b[1]-a[1])*v/length)) for v in [t,e]],fill=color,width=width*2)
        else:self.d.line([(x*2,y*2) for x,y in pts],fill=color,width=width*2,joint='curve')
        self.svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"'+(' stroke-dasharray="12 8"' if dash else '')+'/>')
        if arrow:
            a,b=pts[-2:];angle=math.atan2(b[1]-a[1],b[0]-a[0]);n=17
            self.poly([b,(b[0]-n*math.cos(angle-.5),b[1]-n*math.sin(angle-.5)),(b[0]-n*math.cos(angle+.5),b[1]-n*math.sin(angle+.5))],color,color,1)
    def dot(self,x,y,color='#39b657'):self.ellipse(x-5,y-5,10,10,color,color,1)
    def label(self,x,y,text,color=INK,size=23):
        font=ImageFont.truetype(str(self.font),size*2);w=self.d.textlength(text,font=font)/2
        self.rect(x-5,y-3,w+10,size+10,'white','white',2,1);self.text(x,y,text,size,color)
    def envelope(self,x,y,color=BLUE,scale=1):
        w,h=53*scale,34*scale
        self.rect(x,y,w,h,'#fffef8',color,2,2)
        self.line([(x,y),(x+w/2,y+h*.56),(x+w,y)],color,2)
        self.line([(x,y+h),(x+w*.35,y+h*.45)],color,1)
        self.line([(x+w,y+h),(x+w*.65,y+h*.45)],color,1)
    def pc(self,x,y,name='',ip='',s=1):
        def p(a,b):return(x+a*s,y+b*s)
        self.poly([p(-62,-55),p(38,-55),p(53,-42),p(53,28),p(-62,28)],'#b9c3c8','#54646f')
        self.poly([p(38,-55),p(53,-42),p(53,28),p(38,18)],'#81929c','#54646f')
        self.rect(x-53*s,y-46*s,81*s,58*s,'#c6e6f7','#657e90',2)
        self.poly([p(-50,-42),p(22,-42),p(-50,8)],'#edf9fe','#edf9fe',1)
        self.rect(x-16*s,y+28*s,22*s,19*s,'#87959d','#54646f')
        self.poly([p(-47,49),p(42,49),p(67,68),p(-64,68)],'#d4dadd','#627380')
        for dy in [55,61]:self.line([p(-39,dy),p(36,dy)],'#91a1ab',1)
        self.rect(x+61*s,y-26*s,27*s,77*s,'#d7d9d1','#657580',3)
        self.line([p(66,-11),p(83,-11)],'#7c8b94',2);self.dot(x+75*s,y+31*s)
        if name:self.text(x,y+82*s,name,27,INK,True)
        if ip:self.text(x,y+120*s,ip,23,GREY,True)
    def server(self,x,y,name='',ip='',s=1,color='#ded9c8'):
        def p(a,b):return(x+a*s,y+b*s)
        self.poly([p(-47,-65),p(19,-65),p(46,-43),p(-20,-43)],'#f3efe1','#726f65')
        self.poly([p(19,-65),p(46,-43),p(46,59),p(19,39)],'#b4ad9b','#726f65')
        self.poly([p(-47,-65),p(19,-65),p(19,39),p(-47,39)],color,'#726f65')
        for dy in [-46,-28,-10]:self.rect(x-38*s,y+dy*s,45*s,10*s,'#8899a1','#637582',2,1)
        self.ellipse(x-35*s,y+12*s,9*s,9*s,'#46b758','#278c3f',1)
        for dx in [-32,-23,-14,-5]:self.line([p(dx,28),p(dx,33)],'#8c887e',1)
        if name:self.text(x,y+75*s,name,27,INK,True)
        if ip:self.text(x,y+113*s,ip,23,GREY,True)
    def switch(self,x,y,name='Switch0',s=1,ports=False):
        def p(a,b):return(x+a*s,y+b*s)
        self.poly([p(-140,-38),p(96,-38),p(140,-71),p(-96,-71)],'#45bcde','#147d9b')
        self.poly([p(-140,-38),p(96,-38),p(96,28),p(-140,28)],'#087faf','#08627e')
        self.poly([p(96,-38),p(140,-71),p(140,-3),p(96,28)],'#046588','#07506c')
        for a,b in [((-85,-54),(-28,-54)),((14,-48),(64,-48))]:self.line([p(*a),p(*b)],'white',4,arrow=True)
        for i in range(9):
            xx=-127+i*23
            self.rect(x+xx*s,y-21*s,17*s,20*s,'#173b4b','#b1e4e9',1,1)
            if ports:self.text(x+(xx+8)*s,y+3*s,str(i+1),14,'white',True)
        if name:self.text(x,y+50*s,name,31,INK,True)
    def router(self,x,y,name='Router0',s=1):
        self.rect(x-90*s,y-19*s,180*s,57*s,'#048ab5','#067393',0,2)
        self.ellipse(x-90*s,y+8*s,180*s,58*s,'#067c9e','#067393')
        self.rect(x-88*s,y-16*s,176*s,51*s,'#048ab5','#048ab5',0,1)
        self.ellipse(x-90*s,y-47*s,180*s,69*s,'#35b8d7','#067393')
        for a,b in [((-53,-10),(42,-27)),((45,-8),(-45,-27))]:self.line([(x+a[0]*s,y+a[1]*s),(x+b[0]*s,y+b[1]*s)],'white',5,arrow=True)
        if name:self.text(x,y-98*s,name,31,INK,True)
    def cloud(self,x,y,w=380,h=145,label='Internet'):
        for dx,dy,rw,rh in [(0,45,w*.45,h*.63),(w*.16,8,w*.42,h*.9),(w*.42,0,w*.42,h*.9),(w*.67,44,w*.33,h*.61)]:self.ellipse(x+dx,y+dy,rw,rh,'#d9f1fa','#9ecadb',2)
        self.rect(x+w*.2,y+h*.47,w*.61,h*.48,'#d9f1fa','#d9f1fa',0,1)
        self.text(x+w/2,y+h*.43,label,29,BLUE,True)
    def footer(self,text):self.text(50,self.h-53,text,24,GREY)
    def save(self):
        self.out.mkdir(parents=True,exist_ok=True)
        self.im.resize((self.w,self.h),Image.Resampling.LANCZOS).save(self.out/f'{self.slug}.png')
        (self.out/f'{self.slug}.svg').write_text('\n'.join(self.svg+['</svg>']),encoding='utf-8')

# Shared physical scene. Port mapping exactly follows the Day 3 Packet Tracer exercise.
def topology(d,expanded=False,active=None,full=False):
    d.rect(50,365,440,660,'#f7f1fa',PURPLE,24,2,True)
    d.text(79,384,'VLAN 10 · DEV',29,PURPLE)
    d.text(79,425,'192.168.10.0/24',24,PURPLE)
    d.rect(1110,167,640,858,'#f0f9f5',GREEN,24,2,True)
    d.text(1140,185,'VLAN 20 · SEC    192.168.20.0/24',28,GREEN)
    wires={
        'pc0':[(320,530),(515,530),(515,580),(710,580)],
        'pc1':[(320,818),(565,818),(565,610),(710,610)],
        'g0':[(775,540),(680,445),(680,285),(790,285)],
        'g1':[(925,540),(1020,445),(1020,285),(910,285)],
        'dns':[(985,580),(1135,580),(1135,330),(1225,330)],
        'web':[(985,592),(1190,592),(1190,490),(1710,490),(1710,340),(1609,340)],
        'pc2':[(945,628),(1070,697),(1070,795),(1210,795),(1210,850),(1233,850)],
        'pc3':[(965,613),(1088,700),(1088,1010),(1700,1010),(1700,865),(1660,865)],
        'unexpected':[(985,600),(1460,600),(1460,640),(1510,640)]}
    used=['pc0','g0','g1','dns','web']
    if full:used+=['pc1','pc2','pc3']
    if expanded:used+=['unexpected']
    for k in used:d.line(wires[k],WIRE,3)
    d.pc(240,530,'PC0','192.168.10.10 /24',1.03)
    if full:
        d.pc(240,818,'PC1','192.168.10.20 /24',.9)
        d.pc(1280,850,'PC2','192.168.20.10 /24',.76)
        d.pc(1590,850,'PC3','192.168.20.20 /24',.76)
    d.switch(850,600,'Switch0 · 2960',1,True)
    d.router(850,263,'Router0 · 2911',1)
    d.server(1280,330,'DNSServer','192.168.20.53',1.05)
    d.server(1560,330,'IntranetServer','192.168.20.100',1.05)
    if expanded:d.server(1560,640,'UnexpectedServer','192.168.20.200',.93,color='#f1c9ba')
    for x,y,t,c in [(524,493,'Fa0/1 · VLAN 10',PURPLE),(493,759,'Fa0/2',PURPLE),(505,351,'G0/0 · 192.168.10.1',PURPLE),(943,351,'G0/1 · 192.168.20.1',GREEN),(609,462,'Fa0/5',PURPLE),(970,464,'Fa0/6',GREEN),(1086,528,'Fa0/7',GREEN),(1210,503,'Fa0/8',GREEN)]:
        if t=='Fa0/2' and not full:continue
        d.label(x,y,t,c,22)
    if full:
        d.label(1068,750,'Fa0/3',GREEN,22);d.label(1230,983,'Fa0/4',GREEN,22)
    if expanded:d.label(1340,563,'Fa0/9',GREEN,22)
    d.text(640,699,'1–2, 5번 포트: VLAN 10',24,PURPLE)
    d.text(640,737,'3–4, 6–'+('9' if expanded else '8')+'번 포트: VLAN 20',24,GREEN)
    d.text(633,779,'같은 스위치 안에서 포트를 나눈다.',23,GREY)
    if active:
        color=BLUE if active in ('query','response') else (RED if active=='unexpected' else GREEN)
        forward=active!='response';dest='dns' if active in ('query','response') else ('unexpected' if active=='unexpected' else 'web')
        paths=[wires['pc0'],wires['g0'],list(reversed(wires['g1'])),wires[dest]]
        if not forward:paths=[list(reversed(p)) for p in reversed(paths)]
        for p in paths:d.line(p,color,7,arrow=True)
        d.envelope(548,513,color)
        d.envelope(690,304,color)
        d.envelope(992,397,color)
        if dest=='dns':d.envelope(1110,425,color)
        elif dest=='web':d.envelope(1335,473,color)
        else:d.envelope(1335,583,color)
        label={'query':'DNS 질문: portal.a-company.test의 A?','response':'DNS 응답: A = 192.168.20.100','web':'TCP 연결 후 HTTP 요청 → .100','unexpected':'TCP 연결 후 HTTP 요청 → .200'}[active]
        d.label(520,957,label,color,27)
        d.label(505,351,'G0/0 · 192.168.10.1',PURPLE,22)
        d.label(943,351,'G0/1 · 192.168.20.1',GREEN,22)
        d.label(970,464,'Fa0/6',GREEN,22)
    return wires

def physical_figures():
    items=[('overview','Day 3 · 이름을 물어보고, 응답 주소로 접속하기',True,None,False),
           ('l4_topology','정상 DNS 실습 구성 · 장비와 포트 배치',False,None,True),
           ('l5_topology','응답 변화 실습 구성 · 예상 밖 서버 한 대 추가',True,None,True),
           ('l4_route','DNS 질의가 VLAN 10에서 VLAN 20으로 건너간다',False,'query',False),
           ('l1_lookup_web','1 · PC0이 설정된 DNS 서버에 이름을 묻는다',False,'query',False),
           ('l1_reply','2 · DNS 서버가 포털 주소를 PC0에 돌려준다',False,'response',False),
           ('l1_connect','3 · PC0이 받은 주소로 새 웹 연결을 시작한다',False,'web',False),
           ('l5_normal','변경 전 · 같은 구성에서 정상 포털 .100에 접속한다',True,'web',False),
           ('l5_compare','변경 후 · 같은 이름으로 .200 서버에 도착한다',True,'unexpected',False)]
    for slug,title,expanded,active,full in items:
        subtitle='실습 구성도 · 검은 선 = 연결   /   점선 경계 = VLAN'
        if active:subtitle+='   /   봉투 = 현재 패킷   /   나머지 PC 생략'
        d=Canvas(slug,title,subtitle,1120)
        topology(d,expanded,active,full)
        if slug=='overview':
            d.label(520,957,'DNS .53 조회 → 응답 .100 또는 .200 → 웹 접속',BLUE,26)
        d.footer('모든 장비의 마스크는 255.255.255.0이다. Router0의 두 선은 각 VLAN의 access 포트에 연결한다.')
        d.save()

def nslookup():
    d=Canvas('l1_nslookup','nslookup 출력의 두 주소를 실제 서버와 연결하기','출력은 내부 DNS를 지정한 예시다. 위쪽은 질문 대상, 아래쪽은 DNS가 알려준 웹 서버다.',900)
    d.pc(210,430,'PC0','192.168.10.10',1.4)
    d.rect(430,206,875,380,'#f9fbfc','#83929e',4,2)
    d.text(458,225,'Command Prompt · 출력 예시',24,GREY)
    d.text(458,279,'> nslookup portal.a-company.test 192.168.20.53',27)
    d.text(458,349,'Server:  dns.a-company.test\nAddress: 192.168.20.53',30,BLUE)
    d.text(458,462,'Name:    portal.a-company.test\nAddress: 192.168.20.100',30,GREEN)
    d.server(1540,312,'DNSServer','192.168.20.53',1.15)
    d.server(1540,625,'IntranetServer','192.168.20.100',1.15)
    d.line([(830,409),(1370,409),(1370,314),(1475,314)],BLUE,4,arrow=True)
    d.line([(850,519),(1370,519),(1370,625),(1475,625)],GREEN,4,arrow=True)
    d.envelope(1390,301,BLUE);d.envelope(1390,611,GREEN)
    d.text(456,653,'Server / 첫 Address → 질문을 받은 DNS 서버',29,BLUE)
    d.text(456,713,'Name / 마지막 Address → 조회한 이름과 그 주소',29,GREEN)
    d.footer('선은 출력 값과 장비의 대응 관계다. 실제 패킷은 Switch0과 Router0을 거친다.');d.save()

def hierarchy():
    d=Canvas('l2_hierarchy','Root · TLD · 권한 서버는 서로 다른 관리 범위를 맡는다','공개 DNS의 관리 계층을 장비와 구역으로 표현한 개념도다. 물리 케이블 배선도는 아니다.',1120)
    d.cloud(670,163,430,136,'DNS 이름 공간')
    d.server(885,352,'Root · 루트 .','최상위 도메인 서버 안내',.82)
    d.line([(885,413),(885,490)],WIRE,3)
    d.line([(365,490),(1450,490)],WIRE,3)
    for x,title,col in [(365,'.kr',GREY),(885,'.com',BLUE),(1450,'.net',GREY)]:
        d.line([(x,490),(x,544)],col,3);d.server(x,600,'TLD '+title,'권한 서버 위치 안내',.78)
    d.line([(885,665),(885,731)],BLUE,5,arrow=True)
    d.rect(540,745,680,298,'#f2f8fc',BLUE,20,2,True)
    d.text(570,762,'example.com 관리 구역',30,BLUE)
    d.server(715,884,'권한 DNS 서버','원본 레코드 보관',.78)
    d.server(1040,884,'www 웹 서버','192.0.2.100',.78)
    d.line([(755,885),(985,885)],GREEN,4,arrow=True);d.label(810,838,'A 레코드',GREEN,24)
    d.footer('www.example.com과 192.0.2.100은 설명용이다. 내부 a-company.test는 실습 DNS에 직접 설정한다.');d.save()

def recursive():
    d=Canvas('l2_sequence','재귀 리졸버가 다음 DNS 서버에 직접 다시 묻는다','캐시가 없는 공개 DNS 조회 모델 · 파랑 = 질문   /   주황 = 다음 담당자 안내   /   초록 = 최종 답',1140)
    d.pc(180,610,'PC','최종 답을 요청',1.18)
    d.server(670,610,'재귀 리졸버','외부 조회를 계속 수행',1.2)
    d.rect(1110,165,635,835,'#f5fafc','#8fb3c3',20,2,True)
    d.text(1145,184,'인터넷의 DNS 서버들',29,BLUE)
    for y,t,ip in [(350,'Root','루트 이름 서버'),(630,'.com TLD','최상위 도메인 서버'),(900,'권한 서버','example.com 구역')]:d.server(1510,y,t,ip,.86)
    d.line([(285,586),(600,586)],BLUE,5,arrow=True);d.label(318,535,'1  최종 답 요청',BLUE,26)
    d.line([(600,659),(285,659)],GREEN,5,arrow=True);d.label(321,692,'8  최종 답 반환',GREEN,26)
    flows=[([(725,555),(925,320),(1430,320)],BLUE,'2  Root에 질문',960,271), ([(1430,380),(995,380),(725,580)],'#a06c16','3  .com 서버 안내',960,396), ([(735,610),(1420,610)],BLUE,'4  .com에 질문',985,558), ([(1420,670),(735,670)],'#a06c16','5  권한 서버 안내',964,691), ([(730,705),(942,867),(1430,867)],BLUE,'6  A 레코드 질문',976,811), ([(1430,921),(935,921),(690,720)],GREEN,'7  최종 A 값 응답',980,944)]
    for pts,c,t,x,y in flows:d.line(pts,c,4,arrow=True);d.label(x,y,t,c,25)
    d.envelope(810,441,BLUE);d.envelope(1165,594,BLUE);d.envelope(1130,905,GREEN)
    d.footer('PC의 재귀 요청을 받은 리졸버가 Root · TLD · 권한 서버에 반복 질의한다. 실제로는 캐시가 단계를 줄일 수 있다.');d.save()

def records():
    d=Canvas('l3_records','레코드가 가리키는 장비와 이름을 나누어 읽기','A · AAAA는 주소를, CNAME · MX · NS는 다른 이름을 값으로 가진다.',1080)
    d.server(295,480,'DNS 서버','레코드를 찾아 응답',1.4)
    d.rect(75,718,670,205,'#fbfbf8','#a6a6a0',4)
    d.text(100,742,'www.a-company.test',29,BLUE)
    d.text(100,790,'CNAME → portal.a-company.test',29,BLUE)
    d.text(100,838,'A 조회 → 192.168.20.100',29,GREEN)
    items=[(1240,276,'포털 웹 서버','portal.a-company.test','A → 192.168.20.100',GREEN),(1240,590,'메일 수신 서버','mail.a-company.test','MX → 메일 서버 이름',BLUE),(1240,893,'권한 DNS 서버','ns1.a-company.test','NS → 담당 DNS 이름',PURPLE)]
    for x,y,title,name,label,col in items:
        d.server(x,y,title,name,.94)
        d.line([(365,460),(705,y),(1165,y)],col,4,arrow=True)
        d.label(725,y-60,label,col,29);d.envelope(1038,y-17,col)
    d.text(1370,240,'AAAA\nIPv6 주소\n2001:db8::100',25,GREY)
    d.footer('화살표는 레코드 값과 대상의 대응이다. DNS 서버가 이 웹·메일 서버에 질문을 보낸다는 뜻은 아니다.');d.save()

def cache():
    d=Canvas('l3_ttl','원본과 캐시는 서로 다른 장비에 남는다','같은 배치에서 시간을 바꾸어 보자. 원본 A를 수정해도 이미 받은 캐시가 바로 사라지지는 않는다.',1240)
    for y,t,ttl,old,new in [(285,'10:00',300,'.100','.100'),(610,'10:02',180,'.100','.200'),(935,'10:05',0,'.200','.200')]:
        d.text(58,y-91,t,39,BLUE)
        if y>285:d.line([(50,y-145),(1740,y-145)],'#ced6dc',2)
        d.pc(365,y,'PC','질문',.8)
        d.server(840,y,'재귀 리졸버','캐시의 사본',.87)
        d.server(1470,y,'권한 DNS 서버','원본 A 레코드',.87)
        d.line([(453,y-12),(761,y-12)],BLUE,4,arrow=True);d.envelope(567,y-31,BLUE,.86)
        d.line([(761,y+46),(453,y+46)],GREEN,4,arrow=True)
        d.label(514,y+66,f'PC에 {old} 응답',GREEN,24)
        if ttl==180:
            d.line([(913,y-12),(1391,y-12)],'#b8c3cb',3,True)
            d.label(1055,y-70,'원본 재조회 없음',GREY,27)
        else:
            d.line([(913,y-12),(1391,y-12)],BLUE,4,arrow=True);d.envelope(1120,y-31,BLUE,.86)
            d.line([(1391,y+46),(913,y+46)],GREEN,4,arrow=True)
            d.label(1022,y-74,'첫 조회' if ttl==300 else '만료 후 다시 조회',BLUE,27)
        d.label(684,y+151,f'사본 {old} / 남은 TTL '+str(ttl) if ttl else 'TTL 0 확인 → 새 답 .200 수신',BLUE,25)
        d.label(1367,y+151,f'원본 {new}',GREEN,27)
        if ttl==180:d.label(1250,y-95,'서버 이전으로 원본 변경',GREEN,26)
    d.footer('마지막 줄은 TTL 0으로 만료된 뒤 질문이 들어온 경우다. 새 응답을 받으면 새 TTL로 캐시를 저장한다.');d.save()

def poison():
    d=Canvas('l3_cache_poison','거짓 응답이 캐시에 남으면 다음 PC도 같은 답을 받는다','왼쪽: 한 질문에 대한 거짓 답   /   오른쪽: 저장된 거짓 정보의 재사용',1030)
    d.line([(875,171),(875,935)],'#aebbc4',2,True)
    d.text(65,173,'DNS 스푸핑 · 거짓 응답을 신뢰',32,RED)
    d.text(940,173,'캐시 포이즈닝 · 거짓 정보를 재사용',32,RED)
    d.server(195,360,'거짓 응답의 출처','개념 표현',.9,color='#f1c5b9')
    d.pc(640,630,'질문한 PC','잘못된 .200 수신',1)
    d.line([(255,397),(581,590)],RED,6,arrow=True);d.envelope(385,475,RED)
    d.label(259,542,'거짓 DNS 답: .200',RED,28)
    d.server(1065,400,'오염된 캐시','거짓 A = .200 저장',1.1,color='#f1c5b9')
    for x,y,name in [(1470,355,'PC A'),(1470,666,'PC B')]:
        d.pc(x,y,name,'이후 질문에도 .200',.89)
        d.line([(1142,433),(1350,y),(1390,y)],RED,5,arrow=True);d.envelope(1230,y+9,RED,.9)
    d.text(958,826,'저장된 답을 여러 사용자에게 다시 전달',29,RED)
    d.footer('이 그림은 영향의 개념도다. Day 3 실습은 관리 화면에서 원본 A를 바꿔 접속 변화만 관찰한다.');d.save()

def settings():
    d=Canvas('l4_settings','설정 칸을 입력하기 전에, 어느 장비의 주소인지 짚어 보자','실제 화면을 단순화한 안내도 · IP와 포트는 Day 3 실습 구성 기준',1030)
    d.pc(235,329,'PC0','192.168.10.10 /24',1.15)
    d.router(880,355,'Router0',1)
    d.server(1410,330,'DNSServer','192.168.20.53',1.1)
    d.server(1410,745,'IntranetServer','192.168.20.100',1.1)
    d.rect(55,540,720,340,'#fbfcfd','#9ca9b1',4)
    d.text(79,555,'PC0 · IP Configuration',29)
    d.text(79,610,'IP Address      192.168.10.10\nSubnet Mask   255.255.255.0\nGateway         192.168.10.1\nDNS Server     192.168.20.53',28)
    d.line([(617,710),(867,710),(867,438)],PURPLE,4,arrow=True);d.label(806,645,'다른 망으로 건널 곳',PURPLE,23)
    d.line([(617,750),(1050,750),(1050,353),(1335,353)],BLUE,4,arrow=True)
    d.label(1060,514,'이름을 물어볼 곳',BLUE,23)
    d.line([(1410,475),(1410,656)],GREEN,5,arrow=True)
    d.label(1150,549,'A: portal.a-company.test → .100',GREEN,25)
    d.footer('값과 장비의 대응을 보여 주는 선이다. 실제 배선은 공통 구성도의 Switch0을 거친다.');d.save()

def events():
    d=Canvas('l5_events','PDU를 열어 DNS 메시지의 A 값과 다음 목적지를 연결하기','Packet Tracer 관찰 안내도 · DNS 응답 패킷의 목적지와 메시지 안의 웹 서버 주소를 구분한다.',1050)
    d.server(215,328,'DNSServer','192.168.20.53',1.12)
    d.pc(878,328,'PC0','192.168.10.10',1.12)
    d.server(1510,328,'IntranetServer','192.168.20.100',1.12)
    d.line([(280,300),(790,300)],BLUE,6,arrow=True);d.envelope(470,282,BLUE)
    d.label(435,230,'DNS 응답',BLUE,29)
    d.line([(985,300),(1428,300)],GREEN,6,arrow=True);d.envelope(1120,282,GREEN)
    d.label(1055,230,'새 TCP 연결 → HTTP',GREEN,28)
    for x,title,lines,col in [(70,'DNS 응답 패킷',['IP 출발지: 192.168.20.53','IP 목적지: 192.168.10.10','DNS 안의 A 값: 192.168.20.100'],BLUE),(970,'다음 TCP / HTTP 패킷',['IP 출발지: 192.168.10.10','IP 목적지: 192.168.20.100','DNS에서 받은 주소를 사용'],GREEN)]:
        d.rect(x,563,750,290,'#f9fcfe',col,4)
        d.text(x+22,585,title,32,col)
        d.text(x+22,646,'\n'.join(lines),28)
    d.line([(655,799),(891,902),(1354,854)],GREEN,4,arrow=True)
    d.label(683,916,'응답 안의 A 값 → 새 연결의 목적지',GREEN,28)
    d.footer('장비 사이의 선은 논리 통신이다. 실제 VLAN 경로는 공통 구성도에서 봉투를 따라 확인한다.');d.save()

def diagnose():
    d=Canvas('l6_diagnose','장애가 의심되는 위치를 공통 구성도 위에서 좁힌다','앞에서 사용한 장비 배치를 유지하고, 다음으로 확인할 지점을 번호로 표시했다.',1370)
    topology(d,False,None,False)
    for x,y,n,col in [(515,530,'1',RED),(1135,385,'2',BLUE),(1710,416,'3',GREEN)]:
        d.ellipse(x-23,y-23,46,46,'white',col,4);d.text(x,y-20,n,30,col,True)
    for x,title,body,col in [(60,'1  시간 초과','PC DNS 주소 · 경로\nDNS 서비스 응답 확인',RED),(635,'2  DNS 응답 내용','NXDOMAIN: 이름 확인\n예상 밖 A: 원본 · 캐시 확인',BLUE),(1200,'3  정상 A인데 웹 실패','TCP 포트 · 방화벽\nHTTP 서비스 확인',GREEN)]:
        d.text(x,1100,title,29,col);d.text(x,1155,body,26)
    d.footer('번호는 원인을 확정하는 표시가 아니다. 관찰 결과에 따라 다음으로 확인할 장비와 설정을 고르는 기준이다.');d.save()

def evidence():
    d=Canvas('l6_evidence','DNS 서버 · 캐시 · PC 기록을 모아 판단한다','관찰한 값이 어디서 나왔는지 먼저 표시한 뒤, 가능한 원인과 다음 확인을 연결한다.',1040)
    d.server(290,312,'권한 DNS 서버','원본 A · 변경 이력',1.08)
    d.server(890,312,'재귀 리졸버','캐시 A · 남은 TTL',1.08)
    d.pc(1510,312,'질의한 PC','질의 시간 · 출발지',1.05)
    for x,col in [(290,GREEN),(890,BLUE),(1510,PURPLE)]:d.line([(x,481),(x,540),(890,625)],col,3,arrow=True)
    d.rect(456,640,870,322,'#fffefa','#888e92',3)
    d.text(485,665,'day03_dns_analysis.md',32)
    d.line([(484,716),(1294,716)],'#c6c9ca',2)
    d.text(484,740,'관찰: A .100 → .200 / TTL 300 → 86400',28)
    d.text(484,792,'해석: 서버 이전 · 비인가 변경 등 가능성',28)
    d.text(484,844,'다음 확인: 원본 · 캐시 상태 · 승인 기록 · 질의 출발지',26)
    d.footer('NXDOMAIN 3건은 관찰한 반복 기록이다. 평소 질의량과 비교해야 급증 여부를 판단할 수 있다.');d.save()

def make_contact_sheet(output):
    # Use only the current 19 scenes, never an old sheet or unrelated PNG files.
    files=[Path(output)/f'{slug}.png' for slug in sorted(FIGURE_SLUGS)]
    sheet=Image.new('RGB',(1400,((len(files)+1)//2)*490),'#f3f4f5');draw=ImageDraw.Draw(sheet)
    for i,p in enumerate(files):
        with Image.open(p) as source:
            im=source.copy()
        im.thumbnail((690,452));x=(i%2)*700;y=(i//2)*490
        sheet.paste(im,(x,y+28));draw.text((x+12,y+5),p.stem,fill='black')
    sheet.save(Path(output)/'contact_sheet.png')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path('network-diagrams'),help='Output directory (default: ./network-diagrams).')
    parser.add_argument('--font',type=Path,help='Path to a Korean TTF/OTF/TTC font. Otherwise detect a common installed font.')
    parser.add_argument('--font-family',help='Optional SVG family name override; default is the loaded font\'s actual family.')
    args=parser.parse_args(argv)
    global OUT,FONT,FONT_FAMILY
    try:
        FONT,detected_family=resolve_font(args.font)
    except ValueError as error:
        parser.error(str(error))
    OUT=args.out.expanduser().resolve()
    FONT_FAMILY=args.font_family or detected_family
    physical_figures();nslookup();hierarchy();recursive();records();cache();poison();settings();events();diagnose();evidence()
    make_contact_sheet(OUT)
    print(f'{len(FIGURE_SLUGS)} network figures rendered to PNG and SVG: {OUT}')
    print(f'Font: {FONT} (SVG family: {FONT_FAMILY})')
    return 0

if __name__=='__main__':raise SystemExit(main())
