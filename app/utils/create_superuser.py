import asyncio
import sys
import os
from getpass import getpass

# Ensure the app directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.session import AsyncSession, async_session
from app.services.user import UserService
from app.schemas.user import UserCreate

async def create_superuser():
    """
    Create a superuser interactively
    """
    print("Create superuser")
    
    # Get user input
    try:
        username = input("Username: ")
        email = input("Email: ")
        full_name = input("Full name: ")
        password = getpass("Password: ")
        confirm_password = getpass("Confirm password: ")
        
        # Validate input
        if not username or not email or not password:
            print("Username, email, and password are required.")
            return
        
        if password != confirm_password:
            print("Passwords do not match.")
            return
        
        # Create user data
        user_data = {
            "username": username,
            "email": email,
            "full_name": full_name,
            "password": password,
            "is_superuser": True
        }
        
        user_in = UserCreate(**user_data)
        
        # Create user
        async with async_session() as session:
            user_service = UserService(session)
            user = await user_service.create_user(user_in=user_in)
            print(f"Superuser {user.username} created successfully.")
            
    except Exception as e:
        print(f"Error creating superuser: {e}")
        
if __name__ == "__main__":
    asyncio.run(create_superuser()) 