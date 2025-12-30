def test_ci_pipeline():
    """Test that CI pipeline works"""
    assert True

def test_import_numpy():
    """Test numpy import"""
    import numpy as np
    assert np.__version__ is not None

def test_import_scipy():
    """Test scipy import"""
    import scipy
    assert scipy.__version__ is not None

def test_basic_math():
    """Basic math test"""
    assert 1 + 1 == 2
    assert 2 * 2 == 4
    assert 10 / 2 == 5

def test_strings():
    """String operations test"""
    assert "Scalable".upper() == "SCALABLE"
    assert "Oversight".lower() == "oversight"
    assert len("ADT") == 3
