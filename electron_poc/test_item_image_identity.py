import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'external_app'/'v22_parts_codes_fixed'))
from item_image_identity import image_identity
from external_serial_tools import human_to_serial

original='@Ug#2fK3C0p4jQ0ncgR0c;R4;?tZBV%m>h?j+F{ro(RlC)o+GVJAuK@'
compact='@Ug#2fK3C0p4jQ0ncgR0c;R4;?tZBV%m>h?j+F{ro(RXdt$!g37&'
assert image_identity(original) and image_identity(original)==image_identity(compact)
human='21, 0, 1, 70|| {234:101} {234:12} {234:103} {9:[76 76]} {65} |'
packed='21, 0, 1, 70|| {234:[101 12 103]} {9:76} {9:76} {65} |'
def key(text):return image_identity(human_to_serial(text))
assert key(human)==key(packed) and key(human)
for changed in [human.replace('70','60'),human.replace('{234:103}',''),
                human.replace('76 76','76'),human.replace('{234:101} {234:12}','{234:12} {234:101}'),
                human.replace('{65}','{65:0}'),human.replace('21, 0, 1','21, 0, 2')]:
    assert key(changed)!=key(human),changed
assert image_identity('@Unot valid') is None
assert image_identity(original.lower()) != image_identity(original)
print('Serial identity: real firmware pair and scalar/list encoding match; level, header, firmware, order, duplicates and bare parts remain distinct.')
