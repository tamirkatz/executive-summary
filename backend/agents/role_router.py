from typing import Dict, List, Any
from backend.models import BusinessRole


class RoleRelevanceRouterNode:
    """
    Routes insights to relevant business roles based on category.
    """
    
    # Hard-coded CATEGORY→ROLES matrix
    CATEGORY_ROLES_MATRIX = {
        "company": [BusinessRole.CEO, BusinessRole.COO, BusinessRole.CFO, BusinessRole.CPO, BusinessRole.CMO, BusinessRole.CSO],
        "industry": [BusinessRole.CEO, BusinessRole.COO, BusinessRole.CFO, BusinessRole.CPO, BusinessRole.CMO, BusinessRole.CSO],
        "financial": [BusinessRole.CEO, BusinessRole.CFO, BusinessRole.COO],
        "news": [BusinessRole.CEO, BusinessRole.COO, BusinessRole.CPO, BusinessRole.CMO, BusinessRole.CSO],
        "leadership": [BusinessRole.CEO, BusinessRole.COO, BusinessRole.CFO],
        "product": [BusinessRole.CPO, BusinessRole.CEO, BusinessRole.COO],
        "marketing": [BusinessRole.CMO, BusinessRole.CEO, BusinessRole.COO],
        "security": [BusinessRole.CSO, BusinessRole.CEO, BusinessRole.COO],
        "operations": [BusinessRole.COO, BusinessRole.CEO, BusinessRole.CFO],
        "strategy": [BusinessRole.CEO, BusinessRole.COO, BusinessRole.CFO, BusinessRole.CPO, BusinessRole.CMO, BusinessRole.CSO]
    }
    
    def __init__(self):
        pass
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add roles_relevant to every insight based on its category and return tagged insights.
        
        Args:
            state: State dictionary containing insights and profile information
            
        Returns:
            Dictionary with insights_tagged (all insights) and insights_for_role (matching profile.role)
        """
        insights = state.get("insights", [])
        profile_role = state.get("profile", {}).get("role")
        
        insights_tagged = []
        insights_for_role = []
        
        for insight in insights:
            category = insight.get("category", "general")
            
            # Get relevant roles for this category
            relevant_roles = self.CATEGORY_ROLES_MATRIX.get(category, [])
            
            # Add roles_relevant field to insight
            insight["roles_relevant"] = [role.value for role in relevant_roles]
            insights_tagged.append(insight)
            
            # Check if this insight is relevant to the user's role
            if profile_role and profile_role in [role.value for role in relevant_roles]:
                insights_for_role.append(insight)
        
        return {
            "insights_tagged": insights_tagged,
            "insights_for_role": insights_for_role
        } 