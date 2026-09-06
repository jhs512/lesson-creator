"""Regression tests for concept/practice roles and native numbered explanations."""
import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lesson_schema import validate
from lesson_render import render
from lesson_term_flow import check_page

def sample(role='concept'):
 return {'type':'lesson','lesson_role':role,'title':'1교시. 이름과 주소','lead':'이름이 필요한 이유를 알아보자.',
 'toc':['질문','동작','정리'],'sections':[{'heading':h,'body':[{'kind':'paragraph','text':'이름을 보고 주소를 찾는다.'}]} for h in ['질문','동작','정리']], 'review':['왜 이름을 쓸까?','어떻게 찾을까?','어디로 보낼까?']}
def challenge():
 return {'kind':'task','task_type':'challenge','instruction':'관찰하고 복구한다.','requirements':['결과를 남긴다.'],'goal_output':'정상 복구', 'answer':{'element':{'kind':'paragraph','text':'새 조회와 접속으로 확인한다.'}}}

class RoleTests(unittest.TestCase):
 def test_concept_does_not_require_coding_tasks_or_extras(self):
  p=sample();self.assertEqual(validate(p),[]);self.assertNotIn('추가 과제',render(p))
 def test_concept_rejects_required_execution(self):
  p=sample();p['sections'][0]['body'].append({'kind':'task','task_type':'action','instruction':'구성한다.'})
  self.assertTrue(any('개념 교시' in e for e in validate(p)))
 def test_requested_concept_challenge_cannot_be_replaced_by_review_questions(self):
  p=sample();p['require_final_challenge']=True
  self.assertTrue(any('요청된 마지막 도전문제' in e for e in validate(p)))
  c=challenge();c['instruction']='주어진 사례의 통신 경로를 설명한다.'
  c['requirements']=['주소와 역할을 연결한다.'];c['goal_output']='경로 설명과 근거'
  c['answer']={'element':{'kind':'paragraph','text':'주소를 받은 뒤 웹 서버로 새 요청을 보낸다.'}}
  p['sections'][-1]['body'].append(c);self.assertEqual(validate(p),[])
  p['sections'][-1]['body'].append({'kind':'task','task_type':'predict','instruction':'또 다른 질문','answer':{'element':{'kind':'paragraph','text':'답'}}})
  self.assertTrue(any('도전이 마지막' in e for e in validate(p)))
 def test_final_challenge_requirement_must_be_boolean(self):
  p=sample();p['require_final_challenge']='false'
  self.assertTrue(any('true 또는 false' in e for e in validate(p)))
 def test_legacy_coding_gate_remains(self):
  p=sample();del p['lesson_role'];self.assertTrue(any('4~7' in e for e in validate(p)))
 def test_integrated_project_needs_one_coherent_challenge(self):
  p=sample('integrated_practice');self.assertTrue(any('종합실습' in e for e in validate(p)))
  p['sections'][-1]['body'].append(challenge());self.assertEqual(validate(p),[])
  self.assertNotIn('정답 코드',render(p));self.assertNotIn('다시 써 보자',render(p))
 def test_guided_practice_needs_actual_task(self):
  p=sample('guided_practice');self.assertTrue(any('실제 수행' in e for e in validate(p)))
 def test_native_numbered_list_preserves_first_use_validation(self):
  p=sample();p['sections'][0]['body']=[{'kind':'numbered_list','items':['캐시는 받은 답을 저장한 사본이다.','캐시에서 주소를 찾는다.']}]
  p['learning_terms']=[{'term':'캐시','introduced_by':'받은 답을 저장한 사본이다.'}]
  self.assertEqual(check_page(p)[1],[]);self.assertIn('1. 캐시는',render(p));self.assertIn('2. 캐시에서',render(p))
  p['sections'][0]['body'][0]['items'].reverse();self.assertTrue(check_page(p)[1])
 def test_screenshot_requires_capture_evidence(self):
  p=sample();e={'kind':'image','src':'sample.png','image_kind':'screenshot','text_content':'정상 화면'};p['sections'][0]['body'].append(e)
  self.assertTrue(any('capture' in x for x in validate(p)))
  e['capture']={'application':'Packet Tracer','version':'observed version','scenario':'정상 조회','evidence':'captures/original.png'}
  self.assertEqual(validate(p),[])
 def test_concept_lint_skips_coding_density_but_keeps_format_gate(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'lesson.md';path.write_text(render(sample()))
   cmd=[sys.executable,str(Path(__file__).resolve().parents[1]/'lesson_lint.py'),str(path),'--role','concept']
   result=subprocess.run(cmd,capture_output=True,text=True)
   self.assertEqual(result.returncode,0);self.assertNotIn('손 과제 총량',result.stdout)
   path.write_text(path.read_text()+'\n```\nbad\n```\n')
   result=subprocess.run(cmd,capture_output=True,text=True)
   self.assertEqual(result.returncode,1);self.assertIn('언어 지정 없음',result.stdout)
if __name__=='__main__':unittest.main()

class CheckpointTests(unittest.TestCase):
 def page(self):
  p=sample();p['review']=[];p['checkpoint_count']=10
  p['sections'][-1]['body']=[{'kind':'checkpoint_question','number':i,'question':'이름의 역할은?', 'correct':'B','options':[{'text':str(j),'feedback':'판단 근거 '+str(j)} for j in range(4)]} for i in range(1,11)]
  return p
 def test_count_and_number_gate(self):
  p=self.page();self.assertEqual(validate(p),[])
  p['sections'][-1]['body'].pop();self.assertTrue(any('문항 수' in e for e in validate(p)))
 def test_options_answer_and_feedback_gate(self):
  for key,value in [('correct','E'),('options',[{'text':'같음','feedback':'근거'}]*4)]:
   p=self.page();p['sections'][-1]['body'][0][key]=value;self.assertTrue(validate(p))
  p=self.page();del p['sections'][-1]['body'][0]['options'][0]['feedback'];self.assertTrue(validate(p))
 def test_answer_toggle_nested_under_question(self):
  from html.parser import HTMLParser
  class Details(HTMLParser):
   def __init__(self):super().__init__();self.depth=0;self.answers=0
   def handle_starttag(self,tag,attrs):
    if tag=='details':self.depth+=1
   def handle_endtag(self,tag):
    if tag=='details':self.depth-=1
   def handle_data(self,data):
    if '정답·해설 보기' in data:
     assert self.depth==2;self.answers+=1
  md=render(self.page());parser=Details();parser.feed(md)
  self.assertEqual(parser.answers,10);self.assertEqual(parser.depth,0);self.assertNotIn('되새김 문제',md)
 def test_choices_cannot_introduce_required_terms(self):
  p=self.page();p['learning_terms']=[{'term':'새용어','introduced_by':'새용어 설명'}]
  p['sections'][-1]['body'][0]['options'][0]['text']='새용어'
  self.assertTrue(check_page(p)[1])

class TwoFlowTests(unittest.TestCase):
 def page(self):
  p=CheckpointTests().page();p['lesson_format']='two_flow_50';p['session_minutes']=50
  quiz=p['sections'][-1]
  p['sections']=[{'heading':str(i),'body':[{'kind':'paragraph','text':'사례를 읽는다.'}],'phase':phase,'flow':flow,'minutes':10} for i,(phase,flow) in enumerate([('explain',1),('read',1),('explain',2),('read',2)])]+[dict(quiz,phase='quiz',flow=0,minutes=10)]
  return p
 def test_order_and_time_are_required(self):
  p=self.page();self.assertEqual(validate(p),[])
  p['sections'][1]['phase']='explain';self.assertTrue(validate(p))
  p=self.page();p['sections'][1]['minutes']=20;self.assertTrue(validate(p))
 def test_public_address_gate_includes_quiz_and_image_labels(self):
  for where in ('question','image'):
   p=self.page();p['public_ip_examples']=True
   if where=='question':p['sections'][-1]['body'][0]['question']='192.168.0.10으로 보낸다.'
   else:p['sections'][0]['body'].append({'kind':'image','src':'local.png','text_content':'192.0.2.10'})
   self.assertTrue(any('공인 IP' in e for e in validate(p)))
  p=self.page();p['public_ip_examples']=True;p['sections'][0]['body'][0]['text']='8.8.8.8에 질문한다.';self.assertEqual(validate(p),[])
