from datetime import datetime
from typing import Any, Dict, Optional, List

from pymongo.database import Database


class DomainRegistryService:
    """Service for managing important domains by category."""
    
    # Seed configuration for static domains
    SEED_DOMAINS = {
        "regulators": [
            "sec.gov",
            "fdic.gov", 
            "federalreserve.gov",
            "occ.gov",
            "finra.org",
            "cfpb.gov",
            "ftc.gov",
            "irs.gov",
            "fincen.gov",
            "ncua.gov"
        ],
        "key_partners": [
            "visa.com",
            "mastercard.com",
            "stripe.com",
            "paypal.com",
            "square.com",
            "adyen.com",
            "worldpay.com",
            "fiserv.com",
            "fisglobal.com",
            "tsys.com"
        ],
        "industry_blogs": {
            "fintech": [
                "finextra.com",
                "pymnts.com",
                "bankingdive.com",
                "americanbanker.com",
                "fintechfutures.com",
                "finovate.com",
                "fintechnews.ch",
                "crowdfundinsider.com",
                "fintechweekly.com",
                "fintechmagazine.com"
            ],
            "ecommerce": [
                "digitalcommerce360.com",
                "ecommercetimes.com",
                "pymnts.com",
                "retailwire.com",
                "internetretailer.com",
                "ecommercebytes.com",
                "practicalecommerce.com",
                "shopify.com/blog",
                "bigcommerce.com/blog",
                "woocommerce.com/blog"
            ],
            "gaming": [
                "gamesindustry.biz",
                "venturebeat.com/games",
                "polygon.com",
                "kotaku.com",
                "ign.com",
                "gameinformer.com",
                "pcgamer.com",
                "eurogamer.net",
                "destructoid.com",
                "joystiq.com"
            ],
            "gambling": [
                "igamingbusiness.com",
                "calvinayre.com",
                "egr.global",
                "gamblinginsider.com",
                "sbcnews.co.uk",
                "casinobeats.com",
                "igaming.org",
                "gamblingcompliance.com",
                "focusgn.com",
                "gamingintelligence.com"
            ]
        }
    }
    
    def __init__(self, db: Database):
        self.domains = db.domains
        self._seed_domains()
    
    def _seed_domains(self):
        """Seed the database with static domains if they don't exist."""
        for category, domains in self.SEED_DOMAINS.items():
            if category == "industry_blogs":
                # Handle nested industry blog categories
                for subcategory, subdomains in domains.items():
                    for domain in subdomains:
                        self._add_domain_if_not_exists(f"{category}.{subcategory}", domain)
            else:
                # Handle flat categories (regulators, key_partners)
                for domain in domains:
                    self._add_domain_if_not_exists(category, domain)
    
    def _add_domain_if_not_exists(self, category: str, domain: str):
        """Add a domain if it doesn't already exist in the category."""
        existing = self.domains.find_one({"category": category, "domain": domain})
        if not existing:
            self.domains.insert_one({
                "category": category,
                "domain": domain,
                "is_seeded": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
    
    def getDomainsByCategory(self, category: str) -> List[Dict[str, Any]]:
        """
        Retrieve all domains for a specific category.
        
        Args:
            category: Category to get domains for (e.g., "regulators", "key_partners", "industry_blogs.fintech")
            
        Returns:
            List of domain dictionaries
        """
        return list(self.domains.find({"category": category}))
    
    def addDomain(self, category: str, domain: str) -> str:
        """
        Add a new domain to a category.
        
        Args:
            category: Category to add the domain to
            domain: Domain name to add
            
        Returns:
            The ID of the saved domain
        """
        domain_data = {
            "category": category,
            "domain": domain,
            "is_seeded": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = self.domains.insert_one(domain_data)
        return str(result.inserted_id)
    
    def getAllDomains(self) -> List[Dict[str, Any]]:
        """
        Retrieve all domains across all categories.
        
        Returns:
            List of all domain dictionaries
        """
        return list(self.domains.find({}))
    
    def getCategories(self) -> List[str]:
        """
        Get all available categories.
        
        Returns:
            List of category names
        """
        return list(self.domains.distinct("category")) 