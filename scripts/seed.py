"""
Seed script to populate database with initial data
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.college import College
from app.models.testimonial import Testimonial
from app.core.config import settings


async def seed_admin_user():
    """Create admin user if not exists"""
    async with AsyncSessionLocal() as session:
        statement = select(User).where(User.username == settings.ADMIN_USERNAME)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if not user:
            admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                is_active=True,
                is_superuser=True
            )
            session.add(admin)
            await session.commit()
            print(f"✓ Admin user created: {settings.ADMIN_USERNAME}")
        else:
            print(f"✓ Admin user already exists: {settings.ADMIN_USERNAME}")


async def seed_colleges():
    """Seed Tamil Nadu colleges"""
    colleges_data = [
        {
            "name": "Anna University",
            "city": "Chennai",
            "email": "info@annauniv.edu",
            "whatsapp": "+919876543210",
            "active": True
        },
        {
            "name": "Madras Institute of Technology (MIT)",
            "city": "Chennai",
            "email": "admission@mitindia.edu",
            "whatsapp": "+919876543211",
            "active": True
        },
        {
            "name": "PSG College of Technology",
            "city": "Coimbatore",
            "email": "info@psgtech.edu",
            "whatsapp": "+919876543212",
            "active": True
        },
        {
            "name": "Thiagarajar College of Engineering",
            "city": "Madurai",
            "email": "admission@tce.edu",
            "whatsapp": "+919876543213",
            "active": True
        },
        {
            "name": "Coimbatore Institute of Technology",
            "city": "Coimbatore",
            "email": "info@cit.edu.in",
            "whatsapp": "+919876543214",
            "active": True
        },
        {
            "name": "SSN College of Engineering",
            "city": "Chennai",
            "email": "admission@ssn.edu.in",
            "whatsapp": "+919876543215",
            "active": True
        },
        {
            "name": "Velammal Engineering College",
            "city": "Chennai",
            "email": "info@velammal.edu.in",
            "whatsapp": "+919876543216",
            "active": True
        },
        {
            "name": "Sri Sivasubramaniya Nadar College of Engineering",
            "city": "Kalavakkam",
            "email": "contact@ssn.edu.in",
            "whatsapp": "+919876543217",
            "active": True
        },
        {
            "name": "Kongu Engineering College",
            "city": "Erode",
            "email": "info@kongu.edu",
            "whatsapp": "+919876543218",
            "active": True
        },
        {
            "name": "Kumaraguru College of Technology",
            "city": "Coimbatore",
            "email": "admission@kct.ac.in",
            "whatsapp": "+919876543219",
            "active": True
        }
    ]
    
    async with AsyncSessionLocal() as session:
        for college_data in colleges_data:
            statement = select(College).where(College.name == college_data["name"])
            result = await session.execute(statement)
            existing = result.scalar_one_or_none()
            
            if not existing:
                college = College(**college_data)
                session.add(college)
                print(f"✓ Added college: {college_data['name']}")
        
        await session.commit()
        print(f"\n✓ Total colleges seeded: {len(colleges_data)}")


async def seed_testimonials():
    """Seed testimonials"""
    testimonials_data = [
        {
            "quote": "campus Tamizha made my admission process so smooth! The support team was incredibly helpful.",
            "name": "Rajesh Kumar",
            "college": "Anna University",
            "avatar": "https://i.pravatar.cc/150?img=12",
            "active": True
        },
        {
            "quote": "I got into my dream college through campus Tamizha. Highly recommend their services!",
            "name": "Priya Devi",
            "college": "PSG College of Technology",
            "avatar": "https://i.pravatar.cc/150?img=45",
            "active": True
        },
        {
            "quote": "The best platform for college admissions in Tamil Nadu. Very professional and efficient.",
            "name": "Karthik Selvam",
            "college": "SSN College of Engineering",
            "avatar": "https://i.pravatar.cc/150?img=33",
            "active": True
        },
        {
            "quote": "Thanks to campus Tamizha, I secured admission in my preferred course without any hassle.",
            "name": "Lakshmi Narayan",
            "college": "Thiagarajar College of Engineering",
            "avatar": "https://i.pravatar.cc/150?img=47",
            "active": True
        },
        {
            "quote": "Excellent guidance and support throughout the admission process. Very satisfied!",
            "name": "Vijay Anand",
            "college": "Coimbatore Institute of Technology",
            "avatar": "https://i.pravatar.cc/150?img=15",
            "active": True
        },
        {
            "quote": "campus Tamizha is a game-changer for students seeking quality education in Tamil Nadu.",
            "name": "Aishwarya Rao",
            "college": "Kumaraguru College of Technology",
            "avatar": "https://i.pravatar.cc/150?img=28",
            "active": True
        }
    ]
    
    async with AsyncSessionLocal() as session:
        # Check if testimonials exist
        statement = select(Testimonial)
        result = await session.execute(statement)
        existing = result.scalars().all()
        
        if not existing:
            for testimonial_data in testimonials_data:
                testimonial = Testimonial(**testimonial_data)
                session.add(testimonial)
                print(f"✓ Added testimonial from: {testimonial_data['name']}")
            
            await session.commit()
            print(f"\n✓ Total testimonials seeded: {len(testimonials_data)}")
        else:
            print(f"\n✓ Testimonials already exist ({len(existing)} found)")


async def main():
    """Run all seed functions"""
    print("\n🌱 Starting database seeding...\n")
    print("="*50)
    
    await seed_admin_user()
    print("="*50)
    
    await seed_colleges()
    print("="*50)
    
    await seed_testimonials()
    print("="*50)
    
    print("\n✅ Database seeding completed successfully!\n")


if __name__ == "__main__":
    asyncio.run(main())
