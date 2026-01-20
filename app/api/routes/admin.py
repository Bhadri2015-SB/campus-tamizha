"""
Admin routes for database management operations
"""
import json
import logging
from pathlib import Path
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, delete
from app.db.database import get_session
from app.core.deps import get_current_superuser
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.user import User
from app.models.college import College
from app.models.testimonial import Testimonial
from app.models.application import Application
from pydantic import BaseModel
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


class SeedResponse(BaseModel):
    message: str
    details: Dict[str, int]


class SeedApplicationsResponse(BaseModel):
    message: str
    applications_added: int
    applications_skipped: int


class DeleteResponse(BaseModel):
    message: str
    deleted_count: int


@router.post("/seed", response_model=SeedResponse)
async def seed_database(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
):
    """
    Seed database with initial data (admin only)
    - Admin user
    - Colleges from colleges_data.json
    - Sample testimonials
    
    Avoids duplicate entries by checking existing records.
    """
    try:
        logger.info(f"Admin {current_user.email} initiated database seeding")
        
        results = {
            "admin_created": 0,
            "colleges_added": 0,
            "colleges_skipped": 0,
            "testimonials_added": 0,
            "testimonials_skipped": 0,
            "errors": 0
        }
        
        # 1. Seed admin user
        statement = select(User).where(User.username == settings.ADMIN_USERNAME)
        result = await session.execute(statement)
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                is_active=True,
                is_superuser=True
            )
            session.add(admin)
            await session.commit()
            results["admin_created"] = 1
            logger.info(f"Created admin user: {settings.ADMIN_USERNAME}")
        
        # 2. Seed colleges from JSON
        project_root = Path(__file__).parent.parent.parent.parent
        colleges_json_path = project_root / "colleges_data.json"
        
        if colleges_json_path.exists():
            with open(colleges_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            institutions = data.get('institutionDirectoryDto', [])
            logger.info(f"Found {len(institutions)} colleges in JSON file")
            
            for college_data in institutions:
                try:
                    aishe_code = college_data.get('aisheCode')
                    
                    if not aishe_code:
                        results["errors"] += 1
                        continue
                    
                    # Check if college exists
                    statement = select(College).where(College.aishe_code == aishe_code)
                    result = await session.execute(statement)
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        results["colleges_skipped"] += 1
                        continue
                    
                    # Create college
                    college = College(
                        aishe_code=aishe_code,
                        name=college_data.get('name', ''),
                        address=college_data.get('address1'),
                        state_name=college_data.get('stateName'),
                        district_name=college_data.get('districtName'),
                        website=college_data.get('webSite'),
                        management=college_data.get('manegement'),
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
                    results["colleges_added"] += 1
                    
                    # Commit in batches
                    if results["colleges_added"] % 500 == 0:
                        await session.commit()
                        logger.info(f"Committed batch: {results['colleges_added']} colleges")
                
                except Exception as e:
                    results["errors"] += 1
                    logger.error(f"Error processing college: {str(e)}")
                    continue
            
            await session.commit()
            logger.info(f"Colleges seeding completed: {results['colleges_added']} added, {results['colleges_skipped']} skipped")
        else:
            logger.warning(f"colleges_data.json not found at {colleges_json_path}")
        
        # 3. Seed testimonials
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
        
        for testimonial_data in testimonials_data:
            # Check if testimonial exists (by name and college)
            statement = select(Testimonial).where(
                Testimonial.name == testimonial_data['name'],
                Testimonial.college == testimonial_data['college']
            )
            result = await session.execute(statement)
            existing = result.scalar_one_or_none()
            
            if not existing:
                testimonial = Testimonial(**testimonial_data)
                session.add(testimonial)
                results["testimonials_added"] += 1
            else:
                results["testimonials_skipped"] += 1
        
        await session.commit()
        logger.info(f"Testimonials seeding completed: {results['testimonials_added']} added, {results['testimonials_skipped']} skipped")
        
        # 4. Seed mock applications (25 applications)
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
        
        results["applications_added"] = 0
        results["applications_skipped"] = 0
        
        for i in range(25):
            email = f"student{i+1}@example.com"
            
            # Check if application exists
            statement = select(Application).where(Application.email == email)
            result = await session.execute(statement)
            existing = result.scalar_one_or_none()
            
            if existing:
                results["applications_skipped"] += 1
                continue
            
            age_days = random.randint(18*365, 22*365)
            dob = (datetime.now() - timedelta(days=age_days)).strftime("%Y-%m-%d")
            sslc_pct = round(random.uniform(75.0, 98.0), 2)
            hsc_pct = round(random.uniform(75.0, 98.0), 2)
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
                status="pending"
            )
            
            session.add(application)
            results["applications_added"] += 1
        
        await session.commit()
        logger.info(f"Applications seeding completed: {results['applications_added']} added, {results['applications_skipped']} skipped")
        
        return SeedResponse(
            message="Database seeding completed successfully",
            details=results
        )
    
    except SQLAlchemyError as e:
        logger.error(f"Database error during seeding: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred during seeding"
        )
    except Exception as e:
        logger.error(f"Unexpected error during seeding: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.delete("/mock-data/testimonials", response_model=DeleteResponse)
async def delete_mock_testimonials(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
):
    """
    Delete only mock/sample testimonials from database (admin only)
    
    Identifies and deletes the seeded sample testimonials based on known names.
    """
    try:
        logger.info(f"Admin {current_user.email} initiated deletion of mock testimonials")
        
        # Names of mock testimonials to delete
        mock_names = [
            "Rajesh Kumar",
            "Priya Devi",
            "Karthik Selvam",
            "Lakshmi Narayan",
            "Vijay Anand",
            "Aishwarya Rao"
        ]
        
        # Delete testimonials with these names
        statement = delete(Testimonial).where(Testimonial.name.in_(mock_names))
        result = await session.execute(statement)
        await session.commit()
        
        deleted_count = result.rowcount
        logger.info(f"Deleted {deleted_count} mock testimonials")
        
        return DeleteResponse(
            message=f"Successfully deleted {deleted_count} mock testimonials",
            deleted_count=deleted_count
        )
    
    except SQLAlchemyError as e:
        logger.error(f"Database error while deleting mock testimonials: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while deleting testimonials"
        )
    except Exception as e:
        logger.error(f"Unexpected error while deleting mock testimonials: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.delete("/mock-data/applications", response_model=DeleteResponse)
async def delete_mock_applications(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
):
    """
    Delete only mock/sample applications from database (admin only)
    
    Identifies and deletes the seeded sample applications based on email pattern.
    Only deletes applications with emails matching 'student[1-25]@example.com'.
    """
    try:
        logger.info(f"Admin {current_user.email} initiated deletion of mock applications")
        
        # Generate mock email addresses to delete
        mock_emails = [f"student{i}@example.com" for i in range(1, 26)]
        
        # Delete applications with these emails
        statement = delete(Application).where(Application.email.in_(mock_emails))
        result = await session.execute(statement)
        await session.commit()
        
        deleted_count = result.rowcount
        logger.info(f"Deleted {deleted_count} mock applications")
        
        return DeleteResponse(
            message=f"Successfully deleted {deleted_count} mock applications",
            deleted_count=deleted_count
        )
    
    except SQLAlchemyError as e:
        logger.error(f"Database error while deleting mock applications: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while deleting applications"
        )
    except Exception as e:
        logger.error(f"Unexpected error while deleting mock applications: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
