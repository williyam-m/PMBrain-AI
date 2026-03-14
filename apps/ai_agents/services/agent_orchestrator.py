"""
Agent Orchestration Engine for PMBrain AI.
Implements LangGraph-style state machine for agent workflows.
Each agent is a node that processes state and passes to next node.
ALL responses come from live Gemini API — no mocks.
"""
import logging
import json
from datetime import datetime
from django.utils import timezone

from .gemini_client import gemini, GeminiAPIError
from apps.ai_agents.models import AgentRun

logger = logging.getLogger('pmbrain')


class AgentState:
    """Shared state passed between agents in a workflow."""
    def __init__(self, project, user, initial_data=None):
        self.project = project
        self.user = user
        self.data = initial_data or {}
        self.results = {}
        self.errors = []
        self.agent_runs = []


class BaseAgent:
    """Base class for all AI agents."""
    agent_type = 'base'

    def __init__(self):
        self.ai = gemini

    def run(self, state):
        """Execute agent and return updated state."""
        run = AgentRun.objects.create(
            agent_type=self.agent_type,
            status='running',
            input_data=self._safe_json(state.data),
            organization=state.project.organization,
            project=state.project,
            created_by=state.user,
            started_at=timezone.now()
        )
        state.agent_runs.append(run)

        try:
            result = self.execute(state)
            run.status = 'completed'
            run.output_data = self._safe_json(result)
            run.completed_at = timezone.now()
            if run.started_at:
                run.duration_seconds = (run.completed_at - run.started_at).total_seconds()
            run.save()
            state.results[self.agent_type] = result
            return state

        except GeminiAPIError as e:
            logger.error(f"Agent {self.agent_type} Gemini error: {e}")
            run.status = 'failed'
            run.error_message = f"AI service error: {str(e)}"
            run.completed_at = timezone.now()
            run.save()
            state.errors.append({'agent': self.agent_type, 'error': str(e)})
            return state

        except Exception as e:
            logger.error(f"Agent {self.agent_type} failed: {e}")
            run.status = 'failed'
            run.error_message = str(e)
            run.completed_at = timezone.now()
            run.save()
            state.errors.append({'agent': self.agent_type, 'error': str(e)})
            return state

    def execute(self, state):
        raise NotImplementedError

    def _safe_json(self, data):
        """Make data JSON-serializable."""
        if isinstance(data, dict):
            return {k: self._safe_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._safe_json(i) for i in data]
        elif hasattr(data, 'isoformat'):
            return data.isoformat()
        elif hasattr(data, '__str__') and not isinstance(data, (str, int, float, bool, type(None))):
            return str(data)
        return data


class EvidenceSummarizerAgent(BaseAgent):
    agent_type = 'evidence_summarizer'

    def execute(self, state):
        from apps.evidence.models import RawEvidence

        evidence_items = state.data.get('evidence_ids', [])
        if evidence_items:
            evidence_qs = RawEvidence.objects.filter(
                id__in=evidence_items, project=state.project
            )
        else:
            evidence_qs = RawEvidence.objects.filter(
                project=state.project, is_processed=False
            )[:50]

        if not evidence_qs.exists():
            return {"message": "No unprocessed evidence found", "processed": 0}

        processed = 0
        results = []
        for evidence in evidence_qs:
            prompt = f"""Analyze this customer feedback and extract structured insights.

Type: {evidence.evidence_type}
Segment: {evidence.customer_segment}
Source: {evidence.source_name}
Text: {evidence.text}

Extract and return as JSON:
{{
    "summary": "2-3 sentence summary",
    "pain_points": ["list of specific pain points"],
    "key_quotes": ["memorable quotes from the text"],
    "topics": ["relevant topic tags"],
    "sentiment": "positive|negative|neutral|mixed",
    "urgency": 1-10 integer
}}"""
            result = self.ai.generate(prompt)

            if isinstance(result, dict):
                evidence.summary = result.get('summary', '')
                evidence.pain_points = result.get('pain_points', [])
                evidence.key_quotes = result.get('key_quotes', [])
                evidence.topics = result.get('topics', [])
                evidence.sentiment = result.get('sentiment', evidence.sentiment)
                evidence.urgency = result.get('urgency', evidence.urgency)
                evidence.is_processed = True
                evidence.processed_at = timezone.now()
                evidence.save()
                processed += 1
                results.append({
                    'id': str(evidence.id),
                    'summary': evidence.summary,
                    'pain_points': evidence.pain_points,
                })

        return {"processed": processed, "results": results}


class InsightClusteringAgent(BaseAgent):
    agent_type = 'insight_clustering'

    def execute(self, state):
        from apps.evidence.models import RawEvidence
        from apps.insights.models import InsightCluster

        evidence_qs = RawEvidence.objects.filter(
            project=state.project, is_processed=True
        )

        if evidence_qs.count() == 0:
            return {"message": "No processed evidence to cluster", "clusters": 0}

        # Prepare evidence summaries for clustering
        evidence_data = []
        for e in evidence_qs[:100]:
            evidence_data.append({
                'id': str(e.id),
                'type': e.evidence_type,
                'segment': e.customer_segment,
                'summary': e.summary or e.text[:200],
                'pain_points': e.pain_points,
                'topics': e.topics,
            })

        prompt = f"""Analyze these customer evidence items and cluster them into insight groups.

Product Context: {state.project.product_context or state.project.name}

Evidence items:
{json.dumps(evidence_data, indent=2)}

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
        result = self.ai.generate(prompt)
        clusters_data = result.get('clusters', [])

        created_clusters = []
        for cd in clusters_data:
            cluster = InsightCluster.objects.create(
                title=cd.get('title', 'Untitled Insight'),
                summary=cd.get('summary', ''),
                frequency=cd.get('frequency', 1),
                severity=cd.get('severity', 'medium'),
                segments_affected=cd.get('segments_affected', []),
                representative_quotes=cd.get('representative_quotes', []),
                trend_direction=cd.get('trend_direction', 'stable'),
                confidence=cd.get('confidence', 0.5),
                topics=cd.get('topics', []),
                organization=state.project.organization,
                project=state.project,
                created_by=state.user,
            )
            # Link evidence refs
            evidence_ids = cd.get('evidence_ids', [])
            if evidence_ids:
                cluster.evidence_refs.set(
                    RawEvidence.objects.filter(id__in=evidence_ids, project=state.project)
                )
            else:
                # Link all evidence to clusters proportionally
                cluster.evidence_refs.set(evidence_qs[:cd.get('frequency', 5)])

            created_clusters.append({
                'id': str(cluster.id),
                'title': cluster.title,
                'severity': cluster.severity,
                'frequency': cluster.frequency,
            })

        return {"clusters_created": len(created_clusters), "clusters": created_clusters}


class OpportunityDiscoveryAgent(BaseAgent):
    agent_type = 'opportunity_discovery'

    def execute(self, state):
        from apps.insights.models import InsightCluster
        from apps.opportunities.models import Opportunity

        insights = InsightCluster.objects.filter(project=state.project)
        if not insights.exists():
            return {"message": "No insights to generate opportunities from", "opportunities": 0}

        insight_data = []
        for i in insights:
            insight_data.append({
                'id': str(i.id),
                'title': i.title,
                'summary': i.summary,
                'frequency': i.frequency,
                'severity': i.severity,
                'segments': i.segments_affected,
            })

        prompt = f"""Based on these product insights, discover product opportunities.

Product: {state.project.product_context or state.project.name}
Strategic Goals: {json.dumps(state.project.goals or [])}

Insights:
{json.dumps(insight_data, indent=2)}

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
        result = self.ai.generate(prompt)
        opportunities_data = result.get('opportunities', [])

        created = []
        for od in opportunities_data:
            opp = Opportunity.objects.create(
                title=od.get('title', 'Untitled Opportunity'),
                problem_statement=od.get('problem_statement', ''),
                affected_segments=od.get('affected_segments', []),
                proposed_solution=od.get('proposed_solution', ''),
                assumptions=od.get('assumptions', []),
                risks=od.get('risks', []),
                alternatives=od.get('alternatives', []),
                implementation_outline=od.get('implementation_outline', ''),
                status='discovered',
                organization=state.project.organization,
                project=state.project,
                created_by=state.user,
            )
            # Link insights
            insight_ids = od.get('insight_ids', [])
            if insight_ids:
                opp.supporting_insights.set(
                    InsightCluster.objects.filter(id__in=insight_ids, project=state.project)
                )
            else:
                opp.supporting_insights.set(insights[:3])

            # Link evidence from insights
            for insight in opp.supporting_insights.all():
                opp.evidence_refs.add(*insight.evidence_refs.all())

            created.append({
                'id': str(opp.id),
                'title': opp.title,
                'status': opp.status,
            })

        return {"opportunities_created": len(created), "opportunities": created}


class OpportunityScoringAgent(BaseAgent):
    agent_type = 'opportunity_scoring'

    def execute(self, state):
        from apps.opportunities.models import Opportunity, OpportunityScore

        opp_id = state.data.get('opportunity_id')
        if opp_id:
            opportunities = Opportunity.objects.filter(id=opp_id, project=state.project)
        else:
            opportunities = Opportunity.objects.filter(
                project=state.project, scores__isnull=True
            ).distinct()

        if not opportunities.exists():
            return {"message": "No opportunities to score", "scored": 0}

        scored = []
        weights = state.project.get_scoring_weights()

        for opp in opportunities:
            prompt = f"""Score this product opportunity on multiple dimensions.

Product: {state.project.product_context or state.project.name}
Goals: {json.dumps(state.project.goals or [])}

Opportunity: {opp.title}
Problem: {opp.problem_statement}
Solution: {opp.proposed_solution}
Segments: {json.dumps(opp.affected_segments)}
Evidence count: {opp.evidence_refs.count()}
Insight count: {opp.supporting_insights.count()}

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
            "revenue": "why",
            "retention": "why",
            "alignment": "why",
            "effort": "why"
        }}
    }}
}}"""
            result = self.ai.generate(prompt)
            scores_data = result.get('scores', {})

            score = OpportunityScore.objects.create(
                opportunity=opp,
                frequency_score=scores_data.get('frequency_score', 5),
                revenue_impact=scores_data.get('revenue_impact', 5),
                retention_impact=scores_data.get('retention_impact', 5),
                strategic_alignment=scores_data.get('strategic_alignment', 5),
                effort_estimate=scores_data.get('effort_estimate', 5),
                confidence_score=scores_data.get('confidence_score', 0.5),
                organization=state.project.organization,
                project=state.project,
                created_by=state.user,
            )
            score.calculate_score(weights)

            scored.append({
                'opportunity_id': str(opp.id),
                'title': opp.title,
                'total_score': score.total_score,
                'confidence': score.confidence_score,
            })

        return {"scored": len(scored), "results": scored}


class SpecGeneratorAgent(BaseAgent):
    agent_type = 'spec_generator'

    def execute(self, state):
        from apps.opportunities.models import Opportunity
        from apps.specs.models import GeneratedArtifact, ArtifactVersion

        opp_id = state.data.get('opportunity_id')
        if not opp_id:
            return {"error": "opportunity_id required"}

        try:
            opp = Opportunity.objects.get(id=opp_id, project=state.project)
        except Opportunity.DoesNotExist:
            return {"error": "Opportunity not found"}

        # Gather context
        insights = list(opp.supporting_insights.values('title', 'summary', 'severity'))
        evidence = list(opp.evidence_refs.values('text', 'evidence_type', 'customer_segment')[:10])

        prompt = f"""Generate a complete product specification for this opportunity.

Product: {state.project.product_context or state.project.name}

Opportunity: {opp.title}
Problem: {opp.problem_statement}
Solution: {opp.proposed_solution}
Segments: {json.dumps(opp.affected_segments)}
Assumptions: {json.dumps(opp.assumptions)}
Risks: {json.dumps(opp.risks)}

Supporting Insights: {json.dumps([dict(i) for i in insights])}
Evidence Samples: {json.dumps([dict(e) for e in evidence])}

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
        result = self.ai.generate(prompt)

        # Create artifact and version
        artifact = GeneratedArtifact.objects.create(
            opportunity=opp,
            artifact_type='prd',
            title=f"PRD: {opp.title}",
            current_version=1,
            status='draft',
            organization=state.project.organization,
            project=state.project,
            created_by=state.user,
        )

        version = ArtifactVersion.objects.create(
            artifact=artifact,
            version_number=1,
            content=result,
            change_summary="Initial AI-generated spec",
            readiness_score=result.get('readiness_score', {}).get('total', 0),
            organization=state.project.organization,
            project=state.project,
            created_by=state.user,
        )

        return {
            "artifact_id": str(artifact.id),
            "version_id": str(version.id),
            "spec": result,
        }


class ImpactPredictionAgent(BaseAgent):
    agent_type = 'impact_prediction'

    def execute(self, state):
        from apps.opportunities.models import Opportunity

        opp_id = state.data.get('opportunity_id')
        if not opp_id:
            return {"error": "opportunity_id required"}

        try:
            opp = Opportunity.objects.get(id=opp_id, project=state.project)
        except Opportunity.DoesNotExist:
            return {"error": "Opportunity not found"}

        prompt = f"""Predict the impact of shipping this feature.

Feature: {opp.title}
Problem: {opp.problem_statement}
Solution: {opp.proposed_solution}
Segments: {json.dumps(opp.affected_segments)}

Predict impact metrics. Return as JSON:
{{
    "predictions": {{
        "adoption": {{
            "30_day": 0.0-1.0,
            "60_day": 0.0-1.0,
            "90_day": 0.0-1.0,
            "methodology": "..."
        }},
        "retention_impact": {{
            "churn_reduction": 0.0-1.0,
            "confidence": 0.0-1.0,
            "affected_accounts": number,
            "at_risk_arr": number
        }},
        "revenue_impact": {{
            "retained_arr": number,
            "expansion_arr": number,
            "total_impact": number,
            "confidence": 0.0-1.0
        }},
        "engagement": {{
            "dau_increase": 0.0-1.0,
            "session_duration_change": 0.0-1.0,
            "feature_usage_frequency": "daily|weekly|monthly"
        }}
    }}
}}"""
        return self.ai.generate(prompt)


class WhatToBuildAgent(BaseAgent):
    """
    The flagship agent: "What should we build next?"
    Enhanced to consider codebase analysis and market trends.
    """
    agent_type = 'what_to_build'

    def execute(self, state):
        from apps.insights.models import InsightCluster
        from apps.opportunities.models import Opportunity
        from apps.evidence.models import RawEvidence

        insights = InsightCluster.objects.filter(project=state.project)
        opportunities = Opportunity.objects.filter(project=state.project)
        evidence_count = RawEvidence.objects.filter(project=state.project).count()

        context_data = {
            'product': state.project.product_context or state.project.name,
            'goals': state.project.goals or [],
            'total_evidence': evidence_count,
            'insights': [
                {
                    'title': i.title, 'summary': i.summary,
                    'frequency': i.frequency, 'severity': i.severity,
                    'trend': i.trend_direction, 'segments': i.segments_affected,
                    'quotes': i.representative_quotes[:3],
                }
                for i in insights[:20]
            ],
            'opportunities': [
                {
                    'title': o.title, 'problem': o.problem_statement,
                    'solution': o.proposed_solution, 'segments': o.affected_segments,
                    'score': o.total_score, 'status': o.status,
                }
                for o in opportunities[:20]
            ],
        }

        # Check for codebase analysis
        codebase_data = "No codebase analysis available."
        try:
            from apps.codebase.models import CodebaseAnalysis
            latest_analysis = CodebaseAnalysis.objects.filter(
                project=state.project, status='completed'
            ).first()
            if latest_analysis:
                codebase_data = json.dumps({
                    'system_summary': latest_analysis.system_summary,
                    'existing_features': latest_analysis.existing_features[:10],
                    'capability_map': latest_analysis.capability_map,
                    'technology_stack': latest_analysis.technology_stack,
                }, indent=2)
        except Exception:
            pass

        # Check for market trends
        market_data = "No market trend analysis available."
        try:
            from apps.codebase.models import MarketTrend
            latest_trend = MarketTrend.objects.filter(project=state.project).first()
            if latest_trend:
                market_data = json.dumps({
                    'trend_summary': latest_trend.trend_summary,
                    'emerging_features': latest_trend.emerging_features[:5],
                    'market_gap_opportunities': latest_trend.market_gap_opportunities[:5],
                }, indent=2)
        except Exception:
            pass

        query = state.data.get('query', 'What should we build next?')

        from .prompt_templates import WHAT_TO_BUILD_ENHANCED_PROMPT
        prompt = WHAT_TO_BUILD_ENHANCED_PROMPT.format(
            query=query,
            context_data=json.dumps(context_data, indent=2),
            codebase_data=codebase_data,
            market_data=market_data,
        )
        return self.ai.generate(prompt)


class SpecChatAgent(BaseAgent):
    """Conversational spec editing agent."""
    agent_type = 'spec_chat'

    def execute(self, state):
        from apps.specs.models import GeneratedArtifact, ArtifactVersion

        artifact_id = state.data.get('artifact_id')
        message = state.data.get('message', '')

        if not artifact_id:
            return {"error": "artifact_id required"}

        try:
            artifact = GeneratedArtifact.objects.get(id=artifact_id, project=state.project)
        except GeneratedArtifact.DoesNotExist:
            return {"error": "Artifact not found"}

        current_version = artifact.versions.first()
        if not current_version:
            return {"error": "No version found"}

        from .prompt_templates import SPEC_CHAT_PROMPT
        prompt = SPEC_CHAT_PROMPT.format(
            current_spec=json.dumps(current_version.content, indent=2),
            message=message,
        )

        result = self.ai.generate(prompt)
        change_summary = result.pop('change_summary', message) if isinstance(result, dict) else message

        new_version = ArtifactVersion.objects.create(
            artifact=artifact,
            version_number=current_version.version_number + 1,
            content=result,
            change_summary=change_summary,
            readiness_score=result.get('readiness_score', {}).get('total', 0) if isinstance(result, dict) and isinstance(result.get('readiness_score'), dict) else 0,
            organization=state.project.organization,
            project=state.project,
            created_by=state.user,
        )
        artifact.current_version = new_version.version_number
        artifact.save()

        return {
            "version_id": str(new_version.id),
            "version_number": new_version.version_number,
            "change_summary": change_summary,
            "spec": result,
        }


class CodeUnderstandingAgent(BaseAgent):
    """Analyzes uploaded codebase to understand structure and capabilities."""
    agent_type = 'code_understanding'

    def execute(self, state):
        file_structure = state.data.get('file_structure', {})
        code_samples = state.data.get('code_samples', {})
        product_context = state.data.get('product_context', '')

        truncated_samples = {}
        total_len = 0
        for path, content in sorted(code_samples.items()):
            if total_len > 30000:
                break
            truncated_samples[path] = content[:3000]
            total_len += len(truncated_samples[path])

        from .prompt_templates import CODE_UNDERSTANDING_PROMPT
        prompt = CODE_UNDERSTANDING_PROMPT.format(
            product_context=product_context,
            file_structure=json.dumps({
                'total_files': file_structure.get('total_files', 0),
                'total_dirs': file_structure.get('total_dirs', 0),
                'languages': file_structure.get('languages', {}),
                'directories': file_structure.get('directories', [])[:50],
                'files': file_structure.get('files', [])[:100],
            }, indent=2),
            code_samples=json.dumps(truncated_samples, indent=1),
        )

        return self.ai.generate(prompt)


class MarketTrendAgent(BaseAgent):
    """Analyzes current market trends for the product category."""
    agent_type = 'market_trend'

    def execute(self, state):
        product_context = state.data.get('product_context', '')
        if not product_context:
            product_context = state.project.product_context or state.project.name

        from .prompt_templates import MARKET_TREND_PROMPT
        prompt = MARKET_TREND_PROMPT.format(product_context=product_context)
        return self.ai.generate(prompt)


class FeatureDiscoveryAgent(BaseAgent):
    """Discovers new features by combining evidence, code analysis, and market trends."""
    agent_type = 'feature_discovery'

    def execute(self, state):
        from apps.evidence.models import RawEvidence
        from apps.insights.models import InsightCluster
        from apps.opportunities.models import Opportunity

        evidence_qs = RawEvidence.objects.filter(project=state.project, is_processed=True)[:20]
        evidence_summary = [
            {'type': e.evidence_type, 'segment': e.customer_segment,
             'summary': e.summary or e.text[:200], 'pain_points': e.pain_points}
            for e in evidence_qs
        ]

        insights = InsightCluster.objects.filter(project=state.project)[:10]
        insight_data = [
            {'title': i.title, 'summary': i.summary, 'frequency': i.frequency,
             'severity': i.severity, 'segments': i.segments_affected}
            for i in insights
        ]

        opps = Opportunity.objects.filter(project=state.project)[:10]
        opp_data = [
            {'title': o.title, 'problem': o.problem_statement, 'status': o.status}
            for o in opps
        ]

        codebase_summary = "No codebase analysis available."
        try:
            from apps.codebase.models import CodebaseAnalysis
            latest = CodebaseAnalysis.objects.filter(
                project=state.project, status='completed'
            ).first()
            if latest:
                codebase_summary = json.dumps({
                    'summary': latest.system_summary,
                    'features': latest.existing_features[:10],
                    'capabilities': latest.capability_map,
                }, indent=2)
        except Exception:
            pass

        market_trends = "No market trend analysis available."
        try:
            from apps.codebase.models import MarketTrend
            latest_trend = MarketTrend.objects.filter(project=state.project).first()
            if latest_trend:
                market_trends = json.dumps({
                    'emerging': latest_trend.emerging_features[:5],
                    'gaps': latest_trend.market_gap_opportunities[:5],
                }, indent=2)
        except Exception:
            pass

        from .prompt_templates import FEATURE_DISCOVERY_PROMPT
        prompt = FEATURE_DISCOVERY_PROMPT.format(
            product_context=state.project.product_context or state.project.name,
            goals=json.dumps(state.project.goals or []),
            evidence_summary=json.dumps(evidence_summary, indent=2),
            insight_data=json.dumps(insight_data, indent=2),
            opportunity_data=json.dumps(opp_data, indent=2),
            codebase_summary=codebase_summary,
            market_trends=market_trends,
        )

        return self.ai.generate(prompt)


# ========================================
# Workflow Orchestrator (LangGraph-style)
# ========================================

class WorkflowOrchestrator:
    """
    LangGraph-style workflow orchestrator.
    Chains agents in defined sequences with conditional routing.
    """

    WORKFLOWS = {
        'full_pipeline': [
            EvidenceSummarizerAgent,
            InsightClusteringAgent,
            OpportunityDiscoveryAgent,
            OpportunityScoringAgent,
        ],
        'evidence_to_insights': [
            EvidenceSummarizerAgent,
            InsightClusteringAgent,
        ],
        'insights_to_opportunities': [
            OpportunityDiscoveryAgent,
            OpportunityScoringAgent,
        ],
        'what_to_build': [
            WhatToBuildAgent,
        ],
        'generate_spec': [
            SpecGeneratorAgent,
        ],
        'predict_impact': [
            ImpactPredictionAgent,
        ],
        'score_opportunities': [
            OpportunityScoringAgent,
        ],
        'edit_spec': [
            SpecChatAgent,
        ],
        'analyze_codebase': [
            CodeUnderstandingAgent,
        ],
        'market_trends': [
            MarketTrendAgent,
        ],
        'feature_discovery': [
            FeatureDiscoveryAgent,
        ],
        'full_discovery': [
            EvidenceSummarizerAgent,
            InsightClusteringAgent,
            OpportunityDiscoveryAgent,
            OpportunityScoringAgent,
            MarketTrendAgent,
            FeatureDiscoveryAgent,
        ],
    }

    @classmethod
    def run_workflow(cls, workflow_name, project, user, input_data=None):
        """Execute a named workflow."""
        agents = cls.WORKFLOWS.get(workflow_name)
        if not agents:
            return {"error": f"Unknown workflow: {workflow_name}"}

        state = AgentState(project, user, input_data or {})

        for AgentClass in agents:
            agent = AgentClass()
            state = agent.run(state)
            if state.errors:
                last_error = state.errors[-1]
                logger.warning(f"Agent {last_error['agent']} had error: {last_error['error']}")

        return {
            "workflow": workflow_name,
            "results": state.results,
            "errors": state.errors,
            "agent_runs": [str(r.id) for r in state.agent_runs],
        }
