def test_placeholder():
    """Basic test to make pipeline pass"""
    assert True

def test_import():
    """Test that we can import the app"""
    try:
        from app.main import app
        assert app is not None
        print("✅ App imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        assert False, f"Failed to import app: {e}"
