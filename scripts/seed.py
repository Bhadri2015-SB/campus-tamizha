"""
Seed script to populate database with initial data
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import AsyncSessionLocal, engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.college import College
from app.models.testimonial import Testimonial
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    """Seed Tamil Nadu colleges from colleges_data.json"""
    try:
        # Load colleges data from JSON file
        colleges_json_path = project_root / "colleges_data.json"
        
        if not colleges_json_path.exists():
            logger.error(f"Colleges data file not found: {colleges_json_path}")
            print(f"✗ Error: colleges_data.json not found at {colleges_json_path}")
            return
        
        logger.info(f"Loading colleges data from {colleges_json_path}")
        with open(colleges_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        institutions = data.get('institutionDirectoryDto', [])
        
        if not institutions:
            logger.warning("No institutions found in colleges_data.json")
            print("✗ No institutions found in the JSON file")
            return
        
        logger.info(f"Found {len(institutions)} colleges in JSON file")
        print(f"\n📚 Processing {len(institutions)} colleges from colleges_data.json...")
        
        async with AsyncSessionLocal() as session:
            added_count = 0
            skipped_count = 0
            error_count = 0
            
            for idx, college_data in enumerate(institutions, 1):
                try:
                    aishe_code = college_data.get('aisheCode')
                    
                    if not aishe_code:
                        logger.warning(f"Skipping college at index {idx}: Missing aisheCode")
                        skipped_count += 1
                        continue
                    
                    # Check if college already exists
                    statement = select(College).where(College.aishe_code == aishe_code)
                    result = await session.execute(statement)
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        skipped_count += 1
                        if idx % 100 == 0:
                            logger.info(f"Progress: {idx}/{len(institutions)} - Skipped (exists): {college_data.get('name', 'Unknown')[:50]}")
                        continue
                    
                    # Create college record
                    college = College(
                        aishe_code=aishe_code,
                        name=college_data.get('name', ''),
                        address=college_data.get('address1'),
                        state_name=college_data.get('stateName'),
                        district_name=college_data.get('districtName'),
                        website=college_data.get('webSite'),
                        management=college_data.get('manegement'),  # Note: typo in source JSON
                        year_of_establishment=college_data.get('yearOfEstablishment'),
                        institution_type=college_data.get('institutionType'),
                        specialized_in=college_data.get('specializedIn'),
                        university_id=college_data.get('universityId'),
                        university_name=college_data.get('universityName'),
                        university_type=college_data.get('universityType'),
                        location=college_data.get('location'),
                        active=True
                    )
                    
                    session.add(college)
                    added_count += 1
                    
                    # Log progress every 100 colleges
                    if idx % 100 == 0:
                        logger.info(f"Progress: {idx}/{len(institutions)} - Added: {college_data.get('name', 'Unknown')[:50]}")
                    
                    # Commit in batches of 500 for better performance
                    if added_count % 500 == 0:
                        await session.commit()
                        logger.info(f"✓ Committed batch: {added_count} colleges added so far")
                        print(f"✓ Committed batch: {added_count} colleges added")
                
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing college at index {idx}: {str(e)}")
                    logger.error(f"College data: {college_data.get('name', 'Unknown')}")
                    continue
            
            # Final commit for remaining colleges
            await session.commit()
            
            print(f"\n{'='*60}")
            print(f"✓ Colleges seeding completed!")
            print(f"  - Added: {added_count}")
            print(f"  - Skipped (already exist): {skipped_count}")
            print(f"  - Errors: {error_count}")
            print(f"  - Total processed: {len(institutions)}")
            print(f"{'='*60}")
            
            logger.info(f"Seeding summary - Added: {added_count}, Skipped: {skipped_count}, Errors: {error_count}")
    
    except FileNotFoundError as e:
        logger.error(f"File not found error: {str(e)}")
        print(f"✗ Error: Could not find colleges_data.json file")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        print(f"✗ Error: Invalid JSON format in colleges_data.json")
    except Exception as e:
        logger.error(f"Unexpected error in seed_colleges: {str(e)}", exc_info=True)
        print(f"✗ Unexpected error: {str(e)}")


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
    try:
        print("\n🌱 Starting database seeding...\n")
        print("="*50)
        
        await seed_admin_user()
        print("="*50)
        
        await seed_colleges()
        print("="*50)
        
        await seed_testimonials()
        print("="*50)
        
        print("\n✅ Database seeding completed successfully!\n")
    
    finally:
        # Dispose of the engine and close all connections
        logger.info("Closing database connections...")
        await engine.dispose()
        logger.info("Database connections closed")
        print("🔒 Database connections closed properly\n")


if __name__ == "__main__":
    asyncio.run(main())
