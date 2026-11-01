"""Regression tests for the real boost-list update, including accumulated reserves."""
from game_code import *
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64,UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.x86_const import *
import itertools,json,math

STOP=0x4000000;MEM=0x5000000;STACK=0x6000000
OLD_PATCH=0xe2f30a;NEW_PATCH=0xe2f213
assert data(NEW_PATCH,2)==bytes.fromhex('740a')

class Harness:
    def __init__(self,version,brake=True,cancel=True,damage=-1,bypass_a=False,
                 bypass_b=False,grounded=True,durations=(20.0,),age=2.0):
        self.uc=u=Uc(UC_ARCH_X86,UC_MODE_64);self.version=version
        self.mapped=set();self.trace=[];self.frame_calls=[]
        self.map(0xe2f000,0x2000);u.mem_write(0xe2f000,data(0xe2f000,0x2000))
        self.map(0xe75000,0x1000);u.mem_write(0xe75000,data(0xe75000,0x1000))
        if version==1:u.mem_write(OLD_PATCH,b'\xeb')
        if version==2:u.mem_write(NEW_PATCH,b'\xeb')
        self.map(STOP,0x1000);self.map(MEM,0x20000);self.map(STACK,0x10000)
        # Only memory management and derived speed/intensity are stubbed. The
        # boost predicate, real duration helper, age advance and removal loop run.
        self.stubs=(0x149d250,0x1be9bf8,0xe758a0,0xe75ae0)
        for addr in self.stubs:
            page=addr&~0xfff
            if page not in self.mapped:self.map(page,0x1000)
            u.mem_write(addr,b'\xc3')
        self.comp=MEM;self.boost=MEM+0x1000;handle=MEM+0x2000;vehicle=MEM+0x3000
        damage_handle=MEM+0x4000;damage_obj=MEM+0x5000
        self.active=MEM+0x8000;self.items=MEM+0x9000;pending=MEM+0xa000
        self.vehicle=vehicle
        self.q(self.comp+0x60,handle);self.q(handle+0x28,vehicle)
        self.q(self.comp+0x68,damage_handle);self.q(damage_handle+0x28,damage_obj)
        u.mem_write(damage_obj+0x40,struct.pack('<i',damage))
        self.b(vehicle+0x214,grounded);self.b(vehicle+0x35,brake)
        self.b(vehicle+0x34,bypass_a);self.b(vehicle+0x36,bypass_b)
        self.b(self.boost+0x3a,cancel)
        self.f(self.boost+0x1c,0.2);self.f(self.boost+0x20,0.8);self.f(self.boost+0x24,0.2)
        self.q(self.comp+0x28,self.active);self.q(self.comp+0x30,pending)
        u.mem_write(self.active+0xc,struct.pack('<i',len(durations)))
        self.q(self.active+0x20,self.items)
        self.instances=[]
        for index,duration in enumerate(durations):
            inst=MEM+0x6000+index*0x100;self.instances.append(inst)
            self.q(self.items+index*8,inst);self.q(inst+0x10,self.boost)
            self.f(inst+0x18,age);self.f(inst+0x28,duration)
            u.mem_write(inst+0x34,struct.pack('<i',-1))
        self.initial={UC_X86_REG_RBX:0x1234,UC_X86_REG_R12:0x5678,
                      UC_X86_REG_R14:0x9abc,UC_X86_REG_R15:0xdef0,
                      UC_X86_REG_RBP:STACK+0x9000}
        u.hook_add(UC_HOOK_CODE,self.hook)
        u.hook_add(UC_HOOK_MEM_INVALID,self.invalid)
    def map(self,addr,size):
        self.uc.mem_map(addr,size)
        self.mapped.update(range(addr,addr+size,0x1000))
    def invalid(self,u,access,addr,size,value,user):
        page=addr&~0xfff
        if page in self.mapped:return False
        try:blob=data(page,0x1000)
        except ValueError:return False
        self.map(page,0x1000);u.mem_write(page,blob);return True
    def q(self,a,v):self.uc.mem_write(a,struct.pack('<Q',v))
    def b(self,a,v):self.uc.mem_write(a,bytes([int(v)]))
    def f(self,a,v):self.uc.mem_write(a,struct.pack('<f',v))
    def readq(self,a):return struct.unpack('<Q',bytes(self.uc.mem_read(a,8)))[0]
    def readf(self,a):return struct.unpack('<f',bytes(self.uc.mem_read(a,4)))[0]
    def hook(self,u,addr,size,user):
        self.trace.append(addr)
        if addr in (0xe2f1d0,0xe2f050,0xe75740):self.frame_calls.append(addr)
        if addr==0x1be9bf8:
            dst=u.reg_read(UC_X86_REG_RDI);src=u.reg_read(UC_X86_REG_RSI);n=u.reg_read(UC_X86_REG_RDX)
            u.mem_write(dst,bytes(u.mem_read(src,n)))
            u.reg_write(UC_X86_REG_RAX,dst)
    def call(self,entry,xmm0=0.0,existing=True):
        u=self.uc;rsp=STACK+0x8000;self.q(rsp,STOP)
        for reg,val in self.initial.items():u.reg_write(reg,val)
        u.reg_write(UC_X86_REG_RSP,rsp);u.reg_write(UC_X86_REG_RDI,self.comp)
        u.reg_write(UC_X86_REG_RSI,self.boost)
        u.reg_write(UC_X86_REG_RDX,self.instances[0] if existing else 0)
        u.reg_write(UC_X86_REG_XMM0,struct.unpack('<I',struct.pack('<f',xmm0))[0])
        self.trace=[];self.frame_calls=[]
        try:u.emu_start(entry,STOP,count=10000)
        except Exception as exc:raise RuntimeError((self.version,hex(u.reg_read(UC_X86_REG_RIP)),[hex(v) for v in self.trace[-8:]])) from exc
        assert u.reg_read(UC_X86_REG_RIP)==STOP
        assert u.reg_read(UC_X86_REG_RSP)==rsp+8
        for reg,val in self.initial.items():assert u.reg_read(reg)==val
        return u.reg_read(UC_X86_REG_RAX)&255
    def snapshot(self):
        count=struct.unpack('<i',bytes(self.uc.mem_read(self.active+0xc,4)))[0]
        ages=[];reserves=0.0
        for i in range(count):
            inst=self.readq(self.items+i*8);age=self.readf(inst+0x18)
            duration=self.readf(inst+0x28);ages.append(age)
            reserves+=max(0.0,0.2+duration-age)
        return {'boost_count':count,'ages':ages,'reserves':reserves}
    def frame(self,dt):
        self.call(0xe75240,xmm0=dt)
        return self.snapshot()

# Reproduce exactly why 0.1.0 was incomplete: individual boost base sustain is
# shorter than the accumulated sustain assigned to the live boost instance.
regression=[]
for version,brake in ((0,False),(1,True),(2,True)):
    h=Harness(version,brake=brake,durations=(20.0,),age=2.0)
    before=h.snapshot();after=h.frame(1/60)
    regression.append({'version':version,'brake':brake,'before':before,'after':after})
assert regression[0]['after']==regression[2]['after']
assert regression[1]['after']['boost_count']==0
assert regression[2]['after']['boost_count']==1

# The corrected predicate must match the stock no-brake predicate even when
# historical boost ages exceed their original, unextended sustain durations.
cases=0
for cancel,a,b,grounded,damage,existing in itertools.product((False,True),repeat=6):
    for age in (0.0,0.5,2.0,100.0):
        args=dict(cancel=cancel,bypass_a=a,bypass_b=b,grounded=grounded,
                  damage=0 if damage else -1,age=age)
        stock=Harness(0,brake=False,**args).call(0xe2f1d0,existing=existing)
        revised=Harness(2,brake=True,**args).call(0xe2f1d0,existing=existing)
        assert stock==revised,(args,existing,stock,revised)
        cases+=1

# Execute the actual list update repeatedly: counts, ages and reserve totals
# must match stock coasting, and all accumulated reserves must eventually end.
timelines=[]
for durations in ((4.0,),(4.0,8.0,12.0),(20.0,)):
    stock=Harness(0,brake=False,durations=durations,age=2.0)
    revised=Harness(2,brake=True,durations=durations,age=2.0)
    states=[]
    for frame in range(100):
        before=revised.snapshot()
        baseline=stock.frame(0.25);actual=revised.frame(0.25)
        assert actual==baseline,(durations,frame,actual,baseline)
        if before['boost_count']:assert 0xe2f1d0 in revised.frame_calls
        if actual['boost_count']:
            assert 0xe75740 in revised.frame_calls and 0xe2f050 in revised.frame_calls
        if frame in (0,1,7,15,31,63,99):states.append({'frame':frame+1,**actual})
    assert revised.snapshot()['boost_count']==0,'Normal reserve expiry was disabled'
    timelines.append({'initial_durations':durations,'states':states,'eventually_empty':True})
    cases+=100

# Non-brake invalidation (damage state) still removes active boosts.
for version in (0,2):
    h=Harness(version,brake=True,damage=0,age=2.0)
    assert h.frame(1/60)['boost_count']==0
    cases+=1

report={'version':'0.2.0','all_passed':True,'cases':cases,
        'prior_bug_reproduced':True,'regression':regression,
        'real_boost_update_executed':True,'real_duration_helper_executed':True,
        'duration_helper_stubbed':False,'normal_expiry_verified':True,
        'braking_matches_stock_no_brake':True,'damage_invalidation_preserved':True,
        'abi_and_stack_preserved':True,
        'stubs':['reference release','memmove implemented in test harness',
                 'derived speed calculation after update','derived intensity calculation after update'],
        'timelines':timelines,'gameplay_verified':False}
(HERE/'brake-function-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(f'PASS: {cases} checks. Reproduced 0.1.0 reserve loss; 0.2.0 matches stock coasting through real boost updates and normal expiry.')
