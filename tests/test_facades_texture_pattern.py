import importlib.util
from pathlib import Path
import numpy as np
import pytest

spec=importlib.util.spec_from_file_location('facades_pattern',Path(__file__).parents[1]/'tools/facades_texture_pattern.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

@pytest.mark.parametrize('mid',range(101,106))
def test_full_4800mm_repeat_and_dark_edges(mid):
    x=np.array([[.0001,.137,.99,2.35,4.7999]])
    y=np.array([[.0001],[.212],[1.43],[4.7999]])
    a=module.pattern(mid,x,y,[.6,.48,.38])
    np.testing.assert_allclose(a,module.pattern(mid,x+4.8,y+4.8,[.6,.48,.38]),atol=1e-9)
    np.testing.assert_allclose(a[0],a[-1])
    np.testing.assert_allclose(a[:,0],a[:,-1])

def test_brick_panel_horizontal_joint_distinct_from_mortar():
    color=[.6,.48,.38]
    joint=module.pattern(101,np.array([[.04]]),np.array([[1.2]]),color)
    mortar=module.pattern(101,np.array([[.04]]),np.array([[.076]]),color)
    assert np.max(joint)<np.min(mortar)*.2

@pytest.mark.parametrize('mid',range(101,106))
def test_updated_600_1200_modules(mid):
    dims=(1.2,.6) if mid==101 else (.6,1.2)
    x=np.array([[.137,.333,.571]]);y=np.array([[.111],[.213]])
    color=[.6,.48,.38]
    a=module.pattern(mid,x,y,color,panel_dimensions=dims)
    np.testing.assert_allclose(a,module.pattern(mid,x+dims[0],y+dims[1],color,panel_dimensions=dims),atol=1e-9)

