import sys,json
from pathlib import Path
import pytest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source/icl_core'))
from icl.api import run_source,compile_source,loads_ocir,dumps_ocir
from icl.runtime import ICLError
SOURCES=[
 ('type State = Record{value:Int64}; fn f(x:State)->State{return {value:x.value+1};} fn main()->Int64{return f({value:4}).value;}',5),
 ('fn main()->List[Int64]{return [];}',[]),
 ('fn f(x:List[Int64])->Int64{return len(x);} fn main()->Int64{return f([]);}',0),
 ('type A=List[Int64]; type B=Record{data:A,n:Int64}; fn main()->Int64{let a:A=[];let b:B={data:a,n:2};return b.n+len(b.data);}',2),
 ('fn main()->Int64{var a:List[Int64]=[];a=[1,2];return len(a);}',2),
 ('type B=Record{p:Record{x:Int64,y:Int64},z:Int64};fn main()->Int64{let b:B={p:{x:2,y:3},z:4};return b.p.y;}',3),
]
@pytest.mark.parametrize('source,expected',SOURCES)
@pytest.mark.parametrize('engine',['tree','vm'])
def test_positive(source,expected,engine):assert run_source('module ext;'+source,engine=engine)['value']==expected
@pytest.mark.parametrize('source,expected',SOURCES)
def test_roundtrip(source,expected):
 o=compile_source('module ext;'+source);assert loads_ocir(dumps_ocir(o))==o
@pytest.mark.parametrize('bad',[
 'type X=Record{a:Int64,a:Bool};fn main()->Int64{return 0;}',
 'type X=X;fn main()->Int64{return 0;}',
 'type X=Y;type Y=Int64;fn main()->Int64{return 0;}',
 'type Int64=Bool;fn main()->Int64{return 0;}',
 'type X=Int64;type X=Bool;fn main()->Int64{return 0;}',
 'fn main()->List[Int64]{return [true];}',
 'fn main()->Int64{let xs=[];return len(xs);}',
 'type X=Record{a:Int64};fn main()->X{return {a:true};}',
 'type X=Record{a:Int64};fn main()->X{return {a:1,b:2};}',
 'type X=Record{a:Int64};fn main()->X{return {};}',
])
def test_negative(bad):
 with pytest.raises(ICLError):compile_source('module bad;'+bad)
def test_cross_module():
 lib='module lib;type S=Record{a:Int64};fn inc(s:S)->S{return {a:s.a+1};}'
 src='module main;import lib;fn main()->Int64{return lib.inc({a:3}).a;}'
 assert run_source(src,module_map={'lib':lib})['value']==4
@pytest.mark.parametrize('engine',['tree','vm'])
def test_frame_inverse(engine):
 lib=(R/'source/stdlib/frames.icl').read_text()
 s='module main; import frames; fn main()->Bool{let p={x:2.5,y:-7.0};return frames.rotate270(frames.rotate90(p))==p;}'
 assert run_source(s,engine=engine,module_map={'frames':lib})['value'] is True
