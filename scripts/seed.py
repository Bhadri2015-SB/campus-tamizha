"""
Seed script to populate database with initial data

IMPORTANT: This script has been migrated to API endpoints for better control.
Instead of running this script directly, use the following API endpoints:

1. Seed database (requires authentication):
   POST /api/admin/seed
   
2. Delete mock testimonials (requires authentication):
   DELETE /api/admin/mock-data/testimonials

For direct seeding via script, use this file. For production, use the API endpoints.
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
from app.models.application import Application
from app.core.config import settings
import random
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def seed_admin_user():
    """Create admin user if not exists"""
    async with AsyncSessionLocal() as session:
        try:
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
                logger.info(f"✓ Admin user created: {settings.ADMIN_USERNAME}")
                print(f"✓ Admin user created: {settings.ADMIN_USERNAME}")
            else:
                logger.info(f"✓ Admin user already exists: {settings.ADMIN_USERNAME}")
                print(f"✓ Admin user already exists: {settings.ADMIN_USERNAME}")
        except Exception as e:
            logger.error(f"Error creating admin user: {str(e)}")
            print(f"✗ Error creating admin user: {str(e)}")
            await session.rollback()
            raise


async def seed_colleges():
    """Seed Tamil Nadu colleges from colleges_data.json (avoids duplicates)"""
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
                    
                    # Check if college already exists (avoid duplicate)
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
    """Seed sample testimonials (avoids duplicates)"""
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
        try:
            added_count = 0
            skipped_count = 0
            
            for testimonial_data in testimonials_data:
                # Check if testimonial exists (by name and college to avoid duplicates)
                statement = select(Testimonial).where(
                    Testimonial.name == testimonial_data['name'],
                    Testimonial.college == testimonial_data['college']
                )
                result = await session.execute(statement)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    testimonial = Testimonial(**testimonial_data)
                    session.add(testimonial)
                    added_count += 1
                    logger.info(f"✓ Added testimonial from: {testimonial_data['name']}")
                    print(f"✓ Added testimonial from: {testimonial_data['name']}")
                else:
                    skipped_count += 1
                    logger.info(f"⊘ Skipped existing testimonial: {testimonial_data['name']}")
            
            await session.commit()
            print(f"\n✓ Testimonials seeding completed!")
            print(f"  - Added: {added_count}")
            print(f"  - Skipped (already exist): {skipped_count}")
            logger.info(f"Testimonials added: {added_count}, skipped: {skipped_count}")
        except Exception as e:
            logger.error(f"Error seeding testimonials: {str(e)}")
            print(f"✗ Error seeding testimonials: {str(e)}")
            await session.rollback()
            raise


async def seed_applications():
    """Seed 25 mock applications (avoids duplicates)"""    
    # Sample data for generating mock applications
    first_names = ["Arun", "Priya", "Karthik", "Deepa", "Rajesh", "Lakshmi", "Vijay", "Sowmya", 
                   "Suresh", "Divya", "Kumar", "Meena", "Ravi", "Saranya", "Ganesh", "Kavitha",
                   "Naveen", "Nithya", "Prakash", "Ramya", "Senthil", "Sneha", "Vignesh", "Yamini", "Balaji"]
    
    cities = ["Chennai", "Coimbatore", "Madurai", "Trichy", "Salem", "Tirunelveli", "Erode", "Vellore"]
    districts = ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Tirunelveli", "Erode", "Vellore"]
    schools = ["St. Mary's School", "DAV Public School", "National Higher Secondary School", 
               "Bharathi Vidya Bhavan", "Government Higher Secondary School", "Kendriya Vidyalaya"]
    boards = ["State Board", "CBSE", "ICSE", "Matriculation"]
    colleges_list = ["Anna University", "PSG College of Technology", "SSN College of Engineering",
                     "Thiagarajar College of Engineering", "Coimbatore Institute of Technology"]
    courses_list = ["Computer Science Engineering", "Mechanical Engineering", "Electronics and Communication Engineering",
                    "Civil Engineering", "Electrical and Electronics Engineering", "Information Technology"]
    statuses = ["pending", "in_progress", "approved", "rejected"]
    
    async with AsyncSessionLocal() as session:
        try:
            added_count = 0
            skipped_count = 0
            
            for i in range(25):
                # Generate unique email
                email = f"student{i+1}@example.com"
                
                # Check if application with this email exists (avoid duplicates)
                statement = select(Application).where(Application.email == email)
                result = await session.execute(statement)
                existing = result.scalar_one_or_none()
                
                if existing:
                    skipped_count += 1
                    logger.info(f"⊘ Skipped existing application: {email}")
                    continue
                
                # Generate random birth date (18-22 years old)
                age_days = random.randint(18*365, 22*365)
                dob = (datetime.now() - timedelta(days=age_days)).strftime("%Y-%m-%d")
                
                # Generate random percentages
                sslc_pct = round(random.uniform(75.0, 98.0), 2)
                hsc_pct = round(random.uniform(75.0, 98.0), 2)
                
                # Randomly select 1-3 colleges and courses
                num_colleges = random.randint(1, 3)
                selected_colleges = random.sample(colleges_list, num_colleges)
                selected_courses = random.sample(courses_list, num_colleges)
                
                application = Application(
                    name=first_names[i],
                    email=email,
                    mobile=f"98{random.randint(10000000, 99999999)}",
                    city=random.choice(cities),
                    dob=dob,
                    gender=random.choice(["Male", "Female"]),
                    sslc_percentage=sslc_pct,
                    hsc_percentage=hsc_pct,
                    school_name=random.choice(schools),
                    district=random.choice(districts),
                    board=random.choice(boards),
                    college=selected_colleges,
                    course=selected_courses,
                    notes=f"Mock application {i+1} - Sample data for testing",
                    status=random.choice(statuses),
                    admin_notes=None if random.random() > 0.5 else "Sample admin note"
                )
                
                session.add(application)
                added_count += 1
                logger.info(f"✓ Added application from: {first_names[i]} ({email})")
                print(f"✓ Added application {i+1}/25: {first_names[i]}")
            
            await session.commit()
            print(f"\n✓ Applications seeding completed!")
            print(f"  - Added: {added_count}")
            print(f"  - Skipped (already exist): {skipped_count}")
            logger.info(f"Applications added: {added_count}, skipped: {skipped_count}")
        except Exception as e:
            logger.error(f"Error seeding applications: {str(e)}")
            print(f"✗ Error seeding applications: {str(e)}")
            await session.rollback()
            raise


async def main():
    """Run all seed functions"""
    try:
        print("\n" + "="*70)
        print("🌱 CAMPUS TAMIZHA - DATABASE SEEDING")
        print("="*70)
        print("\nNote: API endpoints are now available for seeding:")
        print("  - POST /api/admin/seed (requires authentication)")
        print("  - DELETE /api/admin/mock-data/testimonials (requires authentication)")
        print("  - DELETE /api/admin/mock-data/applications (requires authentication)")
        print("\nProceeding with direct database seeding...\n")
        print("="*70)
        
        logger.info("Starting database seeding")
        
        # Seed admin user
        print("\n[1/4] Seeding Admin User...")
        await seed_admin_user()
        print("="*70)
        
        # Seed colleges
        print("\n[2/4] Seeding Colleges from JSON...")
        await seed_colleges()
        print("="*70)
        
        # Seed testimonials
        print("\n[3/4] Seeding Testimonials...")
        await seed_testimonials()
        print("="*70)
        
        # Seed applications
        print("\n[4/4] Seeding Mock Applications...")
        await seed_applications()
        print("="*70)
        
        print("\n✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("="*70 + "\n")
        logger.info("Database seeding completed successfully")
    
    except Exception as e:
        logger.error(f"Fatal error during seeding: {str(e)}", exc_info=True)
        print(f"\n❌ SEEDING FAILED: {str(e)}\n")
        raise
    
    finally:
        # Dispose of the engine and close all connections
        logger.info("Closing database connections...")
        await engine.dispose()
        logger.info("Database connections closed")
        print("🔒 Database connections closed properly\n")


if __name__ == "__main__":
    asyncio.run(main())
