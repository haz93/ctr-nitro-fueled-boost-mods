from game_code import *
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64
from unicorn.x86_const import *
import json,math

MEM=0x5000000;STACK=0x6000000
f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
fixtures=json.loads(FIXTURES.read_text(encoding='utf-8'))
assert len(fixtures)==102

def award(blob,mode):
    """Run the game's actual initialization and chain-add arithmetic blocks."""
    u=Uc(UC_ARCH_X86,UC_MODE_64)
    u.mem_map(0xe2e000,0x2000);u.mem_write(0xe2e000,data(0xe2e000,0x2000))
    u.mem_map(MEM,0x10000);u.mem_map(STACK,0x10000)
    incoming=MEM;old=MEM+0x1000;new=MEM+0x2000;old_data=MEM+0x3000
    u.mem_write(incoming,blob)
    def f(addr,value):u.mem_write(addr,struct.pack('<f',value))
    def q(addr,value):u.mem_write(addr,struct.pack('<Q',value))
    def read(addr):return struct.unpack('<f',bytes(u.mem_read(addr,4)))[0]
    ramp,sustain=struct.unpack_from('<2f',blob,0x1c)
    u.reg_write(UC_X86_REG_RSP,STACK+0x8000)
    if mode=='fresh':
        u.reg_write(UC_X86_REG_RAX,incoming);u.reg_write(UC_X86_REG_RBX,new)
        u.emu_start(0xe2efe4,0xe2efea,count=10)
        assert read(new+0x28)==sustain
        return f32(ramp+read(new+0x28))
    if mode=='weaker_chain':
        f(old+0x28,10.0)
        u.reg_write(UC_X86_REG_R15,incoming);u.reg_write(UC_X86_REG_R12,old)
        u.emu_start(0xe2e98c,0xe2e9a6,count=20)
        return read(old+0x28)-10.0
    raise ValueError(mode)

checks=0;endpoints=[];pairs={}
for item in fixtures:
    old=bytes.fromhex(item['original_object_hex']);new=bytes.fromhex(item['modified_object_hex'])
    assert old[:0x20]==new[:0x20] and old[0x24:]==new[0x24:]
    for mode in ('fresh','weaker_chain'):
        original=award(old,mode);modified=award(new,mode)
        assert math.isclose(modified,3*original,rel_tol=8e-6,abs_tol=3e-6),(item['name'],mode,original,modified)
        checks+=1
    endpoints.append({'archive':item['archive'],'name':item['name'],
                      'original_award':item['old_award'],'triple_award':item['new_award']})
    if '_driftBoostList_' in item['name']:
        name,tier=item['name'].rsplit('_',1)
        pairs.setdefault((item['archive'],name),{})[tier]=(old,new)

qualities=0
for key,pair in pairs.items():
    assert set(pair)=={'minBoost','maxBoost'}
    for n in range(21):
        quality=n/20
        values=[]
        for index in (0,1):
            low=pair['minBoost'][index];high=pair['maxBoost'][index]
            blob=bytearray(low)
            for pos in (0x1c,0x20):
                a=struct.unpack_from('<f',low,pos)[0];b=struct.unpack_from('<f',high,pos)[0]
                struct.pack_into('<f',blob,pos,f32(a+f32(f32(b-a)*quality)))
            values.append(award(bytes(blob),'weaker_chain'))
        assert math.isclose(values[1],3*values[0],rel_tol=8e-6,abs_tol=3e-6),(key,quality,values)
        checks+=1;qualities+=1

report={'all_passed':True,'checks':checks,'endpoint_definitions':len(fixtures),
        'quality_samples':qualities,'quality_math':'Float32 linear interpolation sampled from Good/min to Perfect/max endpoints',
        'actual_machine_code_award_blocks_executed':['fresh boost sustain initialization','chain reserve addition'],
        'scope':'Award initialization and addition; full head replacement and full drift control flow are not emulated.',
        'award_multiplier':3,'only_sustain_fields_changed':True,
        'speed_ramp_and_other_object_fields_preserved':True,'endpoints':endpoints,
        'gameplay_verified':False}
out=HERE
(out/'triple-drift-function-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(f'PASS: {checks} award checks; {len(fixtures)} endpoints and {qualities} quality samples. Fresh and chained reserve gains are 3x.')
