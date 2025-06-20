from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.config import config


class EnrichedProfile(BaseModel):
    """Structured output for enriched user profile data."""
    company: str = Field(description="The company name")
    role: str = Field(description="The user's business role")
    description: str = Field(description="A brief description of what the company does")
    industry: str = Field(description="The primary industry sector")
    sector: str = Field(description="The primary sector of the company")
    clients_industries: List[str] = Field(description="The main industries of the clients of the company")
    competitors: List[str] = Field(description="List of main competitors", max_items=10)
    known_clients: List[str] = Field(description="List of notable clients or customers", max_items=10)
    partners: List[str] = Field(description="List of partners of the company", max_items=10)


class UserProfileEnrichmentAgent:
    """Enriches user profile data with company information using OpenAI."""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.1,
            api_key=config.OPENAI_API_KEY
        )
        
        # Few-shot examples for better performance
        self.examples = [
            {
                "company": "Stripe",
                "role": "CEO",
                "description": "A technology company that builds economic infrastructure for the internet, enabling businesses to accept payments and manage their finances online",
                "industry": "Fintech",
                "sector": "Technology",
                "clients_industries": ["E-commerce", "SaaS", "Marketplace", "Gig Economy"],
                "competitors": ["PayPal", "Square", "Adyen", "Checkout.com", "Braintree"],
                "known_clients": ["Amazon", "Uber", "Shopify", "Lyft", "DoorDash"],
                "partners": ["Shopify", "WooCommerce", "Salesforce", "HubSpot", "Zapier"]
            },
            {
                "company": "Shopify",
                "role": "CPO",
                "description": "A commerce platform that allows anyone to set up an online store and sell their products, with tools for marketing, payments, and shipping",
                "industry": "E-commerce",
                "sector": "Technology",
                "clients_industries": ["Retail", "Fashion", "Beauty", "Home & Garden", "Food & Beverage"],
                "competitors": ["WooCommerce", "BigCommerce", "Wix", "Squarespace", "Magento"],
                "known_clients": ["Kylie Cosmetics", "Allbirds", "Gymshark", "Fashion Nova", "MVMT"],
                "partners": ["Stripe", "PayPal", "Google", "Facebook", "TikTok"]
            },
            {
                "company": "Nuvei",
                "role": "CRO",
                "description": "A global payments technology company that provides payment processing solutions for merchants and businesses worldwide",
                "industry": "Fintech",
                "sector": "Financial Services",
                "clients_industries": ["Gaming", "Gambling", "E-commerce", "Travel", "Entertainment"],
                "competitors": ["Stripe", "Adyen", "Checkout.com", "PayPal", "Square"],
                "known_clients": ["DraftKings", "Skillz", "FanDuel", "BetMGM", "Caesars"],
                "partners": ["Visa", "Mastercard", "American Express", "Discover", "JCB"]
            }
        ]
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("user", "Please enrich the profile for:\n\nCompany: {company}\nRole: {role}")
        ])
        
        # Create the runnable chain with structured output
        self.chain = (
            {"company": RunnablePassthrough(), "role": RunnablePassthrough()}
            | self.prompt
            | self.llm.with_structured_output(EnrichedProfile)
        )
    
    def _get_system_prompt(self) -> str:
        """Generate the system prompt with few-shot examples."""
        examples_text = "\n\n".join([
            f"Company: {ex['company']}\n"
            f"Role: {ex['role']}\n"
            f"Description: {ex['description']}\n"
            f"Industry: {ex['industry']}\n"
            f"Sector: {ex['sector']}\n"
            f"Clients Industries: {', '.join(ex['clients_industries'])}\n"
            f"Competitors: {', '.join(ex['competitors'])}\n"
            f"Known Clients: {', '.join(ex['known_clients'])}\n"
            f"Partners: {', '.join(ex['partners'])}"
            for ex in self.examples
        ])
        
        return f"""You are an expert business analyst who enriches user profile data with comprehensive company information.

Your task is to provide accurate, up-to-date information about companies based on their name and the user's role.

Here are some examples of the expected output format:

{examples_text}

Guidelines:
1. Provide accurate, factual information about the company
2. Focus on well-known, established competitors, clients, and partners
3. Keep descriptions concise but informative
4. Use the most relevant industry and sector classifications
5. Ensure all information is current and accurate
6. If you're unsure about specific details, provide the most likely information based on the company's known profile
7. Distinguish between industry (specific business area) and sector (broader economic category)
8. List the main industries that the company's clients operate in

Output the information in the exact structured format shown in the examples."""
    
    def enrich_profile(self, company: str, role: str) -> Dict[str, Any]:
        """
        Enrich user profile with company information.
        
        Args:
            company: Company name
            role: User's business role
            
        Returns:
            Dictionary containing enriched profile data
        """
        try:
            # Run the chain with structured output
            result = self.chain.invoke({
                "company": company,
                "role": role
            })
            
            # Convert to dictionary
            return result.model_dump()
            
        except Exception as e:
            # Fallback to basic information if enrichment fails
            return {
                "company": company,
                "role": role,
                "description": f"A company in the business sector",
                "industry": "Unknown",
                "sector": "Unknown",
                "clients_industries": [],
                "competitors": [],
                "known_clients": [],
                "partners": []
            }
    
    def enrich_profile_async(self, company: str, role: str) -> Dict[str, Any]:
        """
        Async version of enrich_profile.
        
        Args:
            company: Company name
            role: User's business role
            
        Returns:
            Dictionary containing enriched profile data
        """
        try:
            # Run the chain asynchronously with structured output
            result = self.chain.ainvoke({
                "company": company,
                "role": role
            })
            
            # Convert to dictionary
            return result.model_dump()
            
        except Exception as e:
            # Fallback to basic information if enrichment fails
            return {
                "company": company,
                "role": role,
                "description": f"A company in the business sector",
                "industry": "Unknown",
                "sector": "Unknown",
                "clients_industries": [],
                "competitors": [],
                "known_clients": [],
                "partners": []
            } 