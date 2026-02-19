import pytest
from httpx import ASGITransport, AsyncClient
from main import app 
from utils.generate_uuid import generate_uuid
from database import init_db_pool 

# passed
@pytest.mark.asyncio
async def test_user_signup():
    await init_db_pool() 
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        
        user_data = {
            "email": f"test_15e3690f-d1fc-487d-b2c7-0d5f03a27b1c@example.com", 
            "password": "SecretPassword123",
            "firstname": "Botty"
        }

        response = await ac.post("/auth/signup", json=user_data)

        # result
        assert response.status_code == 200
        assert "token" in response.json()

# passed
@pytest.mark.asyncio
async def test_user_login():
    await init_db_pool() 
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login_data = {
            "email": "test_15e3690f-d1fc-487d-b2c7-0d5f03a27b1c@example.com",
            "password": "SecretPassword123"
        }
        response = await ac.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        assert "token" in response.json()
        return response.json()["token"]

# passed
@pytest.mark.asyncio
async def test_get_profile():
    await init_db_pool() 
    # Setup
    token = await test_user_login() 
    headers = {"Authorization": f"Bearer {token}"}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/users/me", headers=headers)
        
        assert response.status_code == 200
        assert "email" in response.json()

# passed
@pytest.mark.asyncio
async def test_upload_profile_image():
    token = await test_user_login()
    headers = {"Authorization": f"Bearer {token}"}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create a tiny fake image in memory
        files = {
            "file": ("test_avatar.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...", "image/png")
        }
        
        response = await ac.post("/users/upload-image", headers=headers, files=files)
        
        assert response.status_code == 200
        assert "profileImageUrl" in response.json()

# passed
@pytest.mark.asyncio
async def test_save_personalization():
    token = await test_user_login()
    headers = {"Authorization": f"Bearer {token}"}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        data = {
            "username": "botty",
            "age": 10
        }
        response = await ac.post("/personalization/save", headers=headers, json=data)
        
        assert response.status_code == 200
        assert response.json()["is_personalized"] is True

@pytest.mark.asyncio
async def test_bookmarks_flow():
    token = await test_user_login()
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create Bookmark
        bookmark_data = {
            "surah_no": 1,
            "ayah_no": 1,
            "surah_name_eng": "Al-Fatiha",
            "surah_name_arb": "الفاتحة",
            "type": "verse",
            "total_ayah": 7,
            "ayah": "In the name of Allah..."
        }
        create_res = await ac.post("/bookmarks", headers=headers, json=bookmark_data)
        assert create_res.status_code == 200
        
        # 2. Get Bookmarks
        get_res = await ac.get("/bookmarks", headers=headers)
        assert get_res.status_code == 200
        assert len(get_res.json()) >= 1