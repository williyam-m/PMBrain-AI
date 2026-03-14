"""
Prompt templates for all PMBrain AI agents.
Centralized prompt management for consistency and versioning.
"""

EVIDENCE_SUMMARIZER_PROMPT = """Analyze this customer feedback and extract structured insights.

Type: {evidence_type}
Segment: {customer_segment}
Source: {source_name}
Text: {text}

Extract and return as JSON:
{{
    "summary": "2-3 sentence summary of the feedback",
    "pain_points": ["list of specific pain points mentioned"],
    "key_quotes": ["memorable direct quotes from the text"],
    "topics": ["relevant topic tags"],
    "sentiment": "positive|negative|neutral|mixed",
    "urgency": 1-10 integer based on severity and impact
}}"""

INSIGHT_CLUSTERING_PROMPT = """Analyze these customer evidence items and cluster them into insight groups.

Product Context: {product_context}

Evidence items:
{evidence_data}

Group related pain points and themes into clusters. Return as JSON:
{{
    "clusters": [
        {{
            "title": "Short insight title",
            "summary": "Detailed summary of the insight",
            "frequency": number_of_related_items,
            "severity": "critical|high|medium|low",
            "segments_affected": ["segment1", "segment2"],
            "representative_quotes": ["quote1", "quote2"],
            "trend_direction": "rising|stable|declining",
            "confidence": 0.0-1.0,
            "topics": ["topic1", "topic2"],
            "evidence_ids": ["id1", "id2"]
        }}
    ]
}}"""

OPPORTUNITY_DISCOVERY_PROMPT = """Based on these product insights, discover product opportunities.

Product: {product_context}
Strategic Goals: {goals}

Insights:
{insight_data}

Generate opportunities that address these insights. Return as JSON:
{{
    "opportunities": [
        {{
            "title": "Feature/improvement title",
            "problem_statement": "Clear problem being solved",
            "affected_segments": ["segment1"],
            "proposed_solution": "Proposed solution description",
            "assumptions": ["assumption1"],
            "risks": ["risk1"],
            "alternatives": ["alternative approach"],
            "implementation_outline": "High-level implementation plan",
            "insight_ids": ["insight_id1"]
        }}
    ]
}}"""

OPPORTUNITY_SCORING_PROMPT = """Score this product opportunity on multiple dimensions.

Product: {product_context}
Goals: {goals}

Opportunity: {title}
Problem: {problem_statement}
Solution: {proposed_solution}
Segments: {segments}
Evidence count: {evidence_count}
Insight count: {insight_count}

Score each dimension from 0-10 and provide confidence. Return as JSON:
{{
    "scores": {{
        "frequency_score": 0-10,
        "revenue_impact": 0-10,
        "retention_impact": 0-10,
        "strategic_alignment": 0-10,
        "effort_estimate": 0-10,
        "confidence_score": 0.0-1.0,
        "reasoning": {{
            "frequency": "why this score",
            "revenue": "why this score",
            "retention": "why this score",
            "alignment": "why this score",
            "effort": "why this score"
        }}
    }}
}}"""

SPEC_GENERATOR_PROMPT = """Generate a complete product specification for this opportunity.

Product: {product_context}

Opportunity: {title}
Problem: {problem_statement}
Solution: {proposed_solution}
Segments: {segments}
Assumptions: {assumptions}
Risks: {risks}

Supporting Insights: {insights}
Evidence Samples: {evidence}

Generate a complete PRD with all sections. Return as JSON:
{{
    "prd": {{
        "title": "...",
        "version": "1.0",
        "overview": "...",
        "goals": ["..."],
        "non_goals": ["..."]
    }},
    "user_stories": [
        {{"role": "...", "action": "...", "benefit": "...", "acceptance_criteria": ["..."]}}
    ],
    "edge_cases": ["..."],
    "non_functional_requirements": ["..."],
    "api_design": [{{"method": "GET/POST", "path": "/api/...", "description": "..."}}],
    "data_model_changes": ["..."],
    "ui_flow": ["..."],
    "engineering_tasks": [{{"task": "...", "estimate": "...", "priority": "P0/P1/P2"}}],
    "qa_checklist": ["..."],
    "readiness_score": {{
        "total": 0-100,
        "validation_rules": true/false,
        "error_states": true/false,
        "edge_cases": true/false,
        "performance_requirements": true/false,
        "security_requirements": true/false
    }}
}}"""

IMPACT_PREDICTION_PROMPT = """Predict the impact of shipping this feature.

Feature: {title}
Problem: {problem_statement}
Solution: {proposed_solution}
Segments: {segments}

Predict impact metrics. Return as JSON:
{{
    "predictions": {{
        "adoption": {{
            "30_day": 0.0-1.0,
            "60_day": 0.0-1.0,
            "90_day": 0.0-1.0,
            "methodology": "explanation of prediction basis"
        }},
        "retention_impact": {{
            "churn_reduction": 0.0-1.0,
            "confidence": 0.0-1.0,
            "affected_accounts": estimated_number,
            "at_risk_arr": estimated_dollar_amount
        }},
        "revenue_impact": {{
            "retained_arr": dollar_amount,
            "expansion_arr": dollar_amount,
            "total_impact": dollar_amount,
            "confidence": 0.0-1.0
        }},
        "engagement": {{
            "dau_increase": 0.0-1.0,
            "session_duration_change": 0.0-1.0,
            "feature_usage_frequency": "daily|weekly|monthly"
        }}
    }}
}}"""

WHAT_TO_BUILD_PROMPT = """You are a senior product strategist AI. Analyze all available data and answer:

"{query}"

Product Context:
{context_data}

Provide a data-driven recommendation with citations to the evidence and insights provided. Return as JSON:
{{
    "recommendation": {{
        "feature": "recommended feature name",
        "confidence": 0.0-1.0,
        "summary": "Executive summary of the recommendation with data backing",
        "supporting_evidence": [
            {{"type": "evidence type", "quote": "direct quote", "segment": "customer segment", "source": "data source"}}
        ],
        "expected_impact": {{
            "revenue": "specific revenue impact estimate",
            "retention": "specific retention impact",
            "engagement": "engagement improvement",
            "nps": "expected NPS change"
        }},
        "assumptions": ["assumption1", "assumption2"],
        "risks": ["risk1", "risk2"],
        "alternatives": [
            {{"feature": "alternative name", "score": 0-10, "reason": "why not this"}}
        ],
        "implementation_outline": "phased implementation plan",
        "score_breakdown": {{
            "frequency": 0-10,
            "revenue_impact": 0-10,
            "retention_impact": 0-10,
            "strategic_alignment": 0-10,
            "effort_estimate": 0-10,
            "total_score": 0-10
        }}
    }}
}}"""

WHAT_TO_BUILD_ENHANCED_PROMPT = """You are a senior product strategist AI. Analyze ALL available data including customer evidence, insights, opportunities, codebase capabilities, and market trends. Answer:

"{query}"

Product Context:
{context_data}

Codebase Analysis (if available):
{codebase_data}

Market Trends (if available):
{market_data}

Provide a comprehensive data-driven recommendation. Consider:
1. What customer pain points are most urgent (from evidence)
2. What the existing codebase can support (from code analysis)
3. What market trends make this timely (from trend analysis)
4. What would deliver maximum ROI with available resources

Return as JSON:
{{
    "recommendation": {{
        "feature": "recommended feature name",
        "confidence": 0.0-1.0,
        "summary": "Executive summary with data citations",
        "supporting_evidence": [
            {{"type": "...", "quote": "...", "segment": "...", "source": "..."}}
        ],
        "trend_alignment": "How this aligns with market trends",
        "code_integration_points": ["where in the existing codebase this fits"],
        "expected_impact": {{
            "revenue": "...",
            "retention": "...",
            "engagement": "...",
            "nps": "..."
        }},
        "assumptions": ["..."],
        "risks": ["..."],
        "alternatives": [
            {{"feature": "...", "score": 0-10, "reason": "..."}}
        ],
        "implementation_outline": "...",
        "execution_plan": "Detailed phased plan considering existing code",
        "score_breakdown": {{
            "frequency": 0-10,
            "revenue_impact": 0-10,
            "retention_impact": 0-10,
            "strategic_alignment": 0-10,
            "effort_estimate": 0-10,
            "total_score": 0-10
        }}
    }}
}}"""

CODE_UNDERSTANDING_PROMPT = """You are a senior software architect. Perform a deep product intelligence analysis of this codebase.

Product Context: {product_context}

File Structure:
{file_structure}

Key Code Files:
{code_samples}

You must:
1. Identify ALL existing product features (user-facing capabilities)
2. Map the full technical architecture
3. Compare against modern SaaS patterns and competitor capabilities
4. Identify missing capabilities and improvement areas
5. Suggest new feature opportunities based on the codebase structure
6. Provide implementation timelines for suggested features

Return as JSON:
{{
    "system_summary": "3-4 paragraph deep description of the system architecture, design patterns, and product capabilities",
    "major_modules": [
        {{"name": "module name", "purpose": "what it does", "files": ["key files"], "dependencies": ["other modules"]}}
    ],
    "existing_features": [
        {{"name": "feature name", "description": "what it does", "completeness": "complete|partial|stub", "category": "auth|data|api|ui|integration|analytics"}}
    ],
    "api_endpoints": [
        {{"method": "GET/POST", "path": "/api/...", "description": "what it does"}}
    ],
    "database_models": [
        {{"name": "model name", "fields": ["field1", "field2"], "relationships": ["related models"]}}
    ],
    "capability_map": {{
        "authentication": "description of auth capabilities",
        "data_processing": "description",
        "api_layer": "description",
        "frontend": "description",
        "integrations": "description"
    }},
    "technology_stack": ["Python", "Django", "etc"],
    "architecture_patterns": [{{"name": "pattern name", "description": "how it is used"}}],
    "missing_capabilities": ["things the codebase doesn't do yet but should based on modern SaaS standards"],
    "improvement_areas": ["technical debt or areas that could be improved"],
    "competitor_comparison": {{
        "detected_product_type": "Type of product this codebase implements",
        "common_competitor_features": [
            {{"feature": "feature name", "status": "present|missing|partial", "importance": "critical|high|medium|low"}}
        ],
        "competitive_gaps": ["features competitors typically have that this product lacks"]
    }},
    "new_feature_opportunities": [
        {{
            "feature_name": "Suggested feature name",
            "problem_statement": "What problem this would solve for users",
            "business_value": "Why this matters commercially",
            "target_users": "Who benefits from this feature",
            "implementation_complexity": "low|medium|high",
            "estimated_timeline": {{
                "week_1": "What gets done in week 1",
                "week_2": "What gets done in week 2",
                "week_3": "What gets done in week 3",
                "week_4": "What gets done in week 4"
            }},
            "engineering_tasks": {{
                "backend": ["backend task 1", "backend task 2"],
                "frontend": ["frontend task 1", "frontend task 2"]
            }},
            "execution_flow": [
                {{"phase": "step name", "description": "what happens", "estimate": "time estimate"}}
            ],
            "code_integration_points": ["where in existing codebase this integrates"],
            "opportunity_scores": {{
                "frequency": 0-10,
                "revenue_impact": 0-10,
                "retention_impact": 0-10,
                "strategic_alignment": 0-10,
                "effort": 0-10,
                "confidence": 0.0-1.0
            }}
        }}
    ]
}}"""

MARKET_TREND_PROMPT = """Analyze current market trends for this type of product.

Product Context: {product_context}

Based on your knowledge of the SaaS industry, B2B software trends, and this specific product category, analyze:
1. What features are trending in similar products
2. What competitors are building
3. What emerging technologies are creating new opportunities
4. What market gaps exist

Return as JSON:
{{
    "trend_summary": "Overview of current market landscape and key trends",
    "emerging_features": [
        {{"feature": "feature name", "description": "what it is", "prevalence": "how common", "relevance": "why it matters for this product"}}
    ],
    "competitor_features": [
        {{"competitor": "competitor name/type", "feature": "feature they have", "competitive_gap": "how this product compares"}}
    ],
    "market_gap_opportunities": [
        {{"opportunity": "gap description", "market_size": "potential impact", "urgency": "high|medium|low", "fit": "how well it fits this product"}}
    ],
    "industry_trends": [
        {{"trend": "trend name", "description": "what's happening", "timeline": "when it matters", "impact": "how it affects this product"}}
    ]
}}"""

FEATURE_DISCOVERY_PROMPT = """Discover new feature opportunities by analyzing all available data sources together.

Product Context: {product_context}
Strategic Goals: {goals}

Customer Evidence Summary:
{evidence_summary}

Insight Clusters:
{insight_data}

Current Opportunities:
{opportunity_data}

Codebase Capabilities (if available):
{codebase_summary}

Market Trends (if available):
{market_trends}

Synthesize all data sources to discover NEW feature opportunities that haven't been identified yet. Consider:
1. Gaps between what customers need and what the code currently supports
2. Market trends that align with customer pain points
3. Integration opportunities in the existing codebase
4. Features that would address multiple pain points simultaneously

Return as JSON:
{{
    "new_feature_opportunities": [
        {{
            "feature_name": "Feature name",
            "problem_statement": "What problem this solves",
            "evidence_links": ["references to supporting evidence"],
            "code_integration_points": ["where in the existing codebase this integrates"],
            "implementation_complexity": "low|medium|high|very_high",
            "execution_plan": "step by step implementation plan",
            "expected_impact": {{
                "revenue": "estimate",
                "retention": "estimate",
                "engagement": "estimate"
            }},
            "trend_alignment": {{
                "trends": ["which market trends this aligns with"],
                "timing": "why now is the right time"
            }},
            "source_type": "evidence|code|trend|combined"
        }}
    ]
}}"""

SPEC_CHAT_PROMPT = """You are editing a product specification. Here is the current spec:

{current_spec}

User request: "{message}"

Apply the requested changes and return the COMPLETE updated spec as JSON (same structure as above).
Also include a "change_summary" field describing what changed."""
