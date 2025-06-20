from datetime import datetime
from typing import Any, Dict, Optional, List

from pymongo.database import Database


class CompetitorService:
    """Service for managing competitor information for companies."""
    
    def __init__(self, db: Database):
        self.competitors = db.competitors
    
    def getCompetitorsForCompany(self, companyName: str) -> List[Dict[str, Any]]:
        """
        Retrieve all competitors for a given company.
        
        Args:
            companyName: Name of the company to get competitors for
            
        Returns:
            List of competitor dictionaries
        """
        return list(self.competitors.find({"companyName": companyName}))
    
    def addCompetitor(self, companyName: str, competitorData: Dict[str, Any]) -> str:
        """
        Add a new competitor for a company.
        
        Args:
            companyName: Name of the company this competitor is for
            competitorData: Dictionary containing competitor information with fields:
                - name: string
                - sourceDomains: List[str]
                
        Returns:
            The ID of the saved competitor
        """
        # Add company name and timestamps
        competitorData["companyName"] = companyName
        competitorData["created_at"] = datetime.utcnow()
        competitorData["updated_at"] = datetime.utcnow()
        
        result = self.competitors.insert_one(competitorData)
        return str(result.inserted_id)
    
    def getAllTrackedCompetitors(self) -> List[Dict[str, Any]]:
        """
        Retrieve all tracked competitors across all companies.
        
        Returns:
            List of all competitor dictionaries
        """
        return list(self.competitors.find({})) 