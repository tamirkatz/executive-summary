from datetime import datetime
from typing import Any, Dict, Optional, List

from pymongo.database import Database


class CompanyService:
    """Service for managing tracked company information."""
    
    def __init__(self, db: Database):
        self.companies = db.companies
    
    def getCompanyByName(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a company by name.
        
        Args:
            name: Company name to search for
            
        Returns:
            Company data dictionary or None if not found
        """
        return self.companies.find_one({"name": name})
    
    def saveCompany(self, companyData: Dict[str, Any]) -> str:
        """
        Save a new company to the database.
        
        Args:
            companyData: Dictionary containing company information with fields:
                - name: string
                - sector: string
                - known_keywords: List[str]
                - tags: List[str]
                
        Returns:
            The ID of the saved company
        """
        # Add timestamps
        companyData["created_at"] = datetime.utcnow()
        companyData["updated_at"] = datetime.utcnow()
        
        result = self.companies.insert_one(companyData)
        return str(result.inserted_id)
    
    def updateCompany(self, companyId: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing company.
        
        Args:
            companyId: The ID of the company to update
            updates: Dictionary containing fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        # Add updated timestamp
        updates["updated_at"] = datetime.utcnow()
        
        result = self.companies.update_one(
            {"_id": companyId},
            {"$set": updates}
        )
        return result.modified_count > 0 