import pytest
from backend.video_engine.frames.sampler import FrameSampler

def test_sampler():
    sampler = FrameSampler(2.0)
    assert sampler.should_sample(1.0) == True
    assert sampler.should_sample(1.1) == False
    assert sampler.should_sample(1.5) == True
